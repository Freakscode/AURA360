from __future__ import annotations

import hashlib
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import httpx
import numpy as np
from loguru import logger

from vectosvc.config import service_settings, settings
from vectosvc.core.embeddings import Embeddings
from vectosvc.core.parsers import extract_plain_text, fetch_tei, parse_tei
from vectosvc.core.qdrant_store import QdrantStore, store
from vectosvc.core.repos import repository_for
from vectosvc.core.schemas import (
    IngestRequest,
    PaperMeta,
    ParsedDocument,
    SectionSegment,
)
from vectosvc.core import topics as topic_classifier


# Global pipeline metrics collector
class PipelineMetrics:
    """Colector de métricas de pipeline de ingesta."""
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.total_documents = 0
        self.total_chunks = 0
        self.total_errors = 0
        self.phase_times = {
            "download": [],
            "parse_tei": [],
            "chunking": [],
            "embeddings": [],
            "upsert": [],
            "topics": [],
            "total": [],
        }
    
    def record_phase(self, phase: str, duration: float):
        """Registra el tiempo de una fase."""
        if phase in self.phase_times:
            self.phase_times[phase].append(duration)
    
    def record_document(self, chunk_count: int):
        """Registra un documento procesado exitosamente."""
        self.total_documents += 1
        self.total_chunks += chunk_count
    
    def record_error(self):
        """Registra un error de ingesta."""
        self.total_errors += 1
    
    def get_stats(self) -> Dict:
        """Retorna estadísticas agregadas."""
        stats = {
            "total_documents": self.total_documents,
            "total_chunks": self.total_chunks,
            "total_errors": self.total_errors,
            "phase_stats": {},
        }
        
        for phase, times in self.phase_times.items():
            if times:
                stats["phase_stats"][phase] = {
                    "count": len(times),
                    "total_seconds": round(sum(times), 3),
                    "mean_seconds": round(sum(times) / len(times), 3),
                    "min_seconds": round(min(times), 3),
                    "max_seconds": round(max(times), 3),
                }
        
        return stats


# Singleton global
pipeline_metrics = PipelineMetrics()


@contextmanager
def _time_phase(phase: str):
    """Context manager para medir tiempo de una fase."""
    start = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start
        pipeline_metrics.record_phase(phase, duration)


def _split_text(text: str, size: int = 900, overlap: int = 150) -> List[str]:
    if size <= 0:
        return [text]
    text = text.strip()
    if not text:
        return []
    chunks: List[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + size)
        segment = text[start:end].strip()
        if segment:
            chunks.append(segment)
        if end == n:
            break
        start = max(0, end - overlap)
    return chunks


def _hash_id(*parts: str) -> str:
    h = hashlib.sha1()
    for p in parts:
        h.update(p.encode("utf-8"))
    return h.hexdigest()


def _make_point_id(doc_id: str, chunk_index: int, chunk_hash: str) -> str:
    """Create a stable UUID for Qdrant point IDs."""

    raw = f"{doc_id}::{chunk_index}::{chunk_hash}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, raw))


def ingest_one(req_dict: Dict) -> int:
    """
    Ingesta un documento en el pipeline completo con métricas por fase.
    
    Fases instrumentadas:
    - download: descarga de fuente (URL/GCS/etc)
    - parse_tei: parsing GROBID TEI/XML
    - chunking: segmentación de texto
    - embeddings: generación de vectores
    - upsert: inserción en Qdrant
    - topics: clasificación automática (opcional)
    
    Returns:
        Número de chunks generados
    """
    start_total = time.perf_counter()
    
    try:
        req = IngestRequest.model_validate(req_dict)
        if not (req.text or req.url):
            raise ValueError("Provide text or url for ingestion")

        parsed = _obtain_parsed_document(req)

        # Apply metadata overrides
        overrides = req.metadata or {}
        if overrides.get("topics"):
            parsed.meta.topics = _normalize_topics(overrides.get("topics"))
        if overrides.get("lang"):
            parsed.meta.lang = str(overrides["lang"]).lower()
        if overrides.get("journal"):
            parsed.meta.journal = overrides.get("journal")
        if overrides.get("year"):
            try:
                parsed.meta.year = int(overrides.get("year"))
            except (TypeError, ValueError):
                pass
        if overrides.get("mesh_terms"):
            parsed.meta.mesh_terms = _normalize_topics(overrides.get("mesh_terms"))
        if overrides.get("title"):
            parsed.meta.title = overrides.get("title")
        if overrides.get("source"):
            parsed.meta.source = overrides.get("source")

        doc_version = int(overrides.get("doc_version", 1))
        tags = overrides.get("tags", [])

        category = req.category or overrides.get("category")
        if not category:
            # TODO: Derivar categoría automáticamente a partir del dominio del documento.
            category = "unknown"

        locale = req.locale or overrides.get("locale") or parsed.meta.lang or "unknown"
        source_type = req.source_type or overrides.get("source_type") or overrides.get("source") or parsed.meta.source
        version = req.version or overrides.get("version") or service_settings.embedding_version
        embedding_model = (
            req.embedding_model
            or overrides.get("embedding_model")
            or settings.embedding_model
        )
        valid_from = req.valid_from or overrides.get("valid_from") or int(time.time())
        now = int(time.time())

        # Fase 3: Chunking
        with _time_phase("chunking"):
            chunk_records = _build_chunks(
                parsed.segments,
                chunk_size=req.chunk_size,
                chunk_overlap=req.chunk_overlap,
            )

        if not chunk_records:
            raise ValueError(f"No chunks produced for doc_id={req.doc_id}")

        # Fase 4: Embeddings
        with _time_phase("embeddings"):
            emb = Embeddings(model_name=embedding_model)
            vectors = emb.encode([chunk["text"] for chunk in chunk_records])

        # Determinar colección de destino basada en source_type
        target_collection = store.get_collection_for_source_type(source_type)
        store.ensure_collection(vector_size=vectors.shape[1], on_disk=True, collection_name=target_collection)

        ids: List[str] = []
        payloads: List[Dict] = []
        vec_list: List[List[float]] = []

        for chunk, vec in zip(chunk_records, vectors):
            cid = _make_point_id(parsed.meta.doc_id, chunk["chunk_index"], chunk["hash"])
            ids.append(cid)

            # Base payload común para todos los documentos
            payload = {
                "doc_id": parsed.meta.doc_id,
                "chunk_index": chunk["chunk_index"],
                "text": chunk["text"],
                "section_path": chunk["section_path"],
                "section_order": chunk["section_order"],
                "is_abstract": chunk["is_abstract"],
                "is_conclusion": chunk["is_conclusion"],
                "lang": parsed.meta.lang or "unknown",
                "locale": locale,
                "category": category,
                "source_type": source_type,
                "title": parsed.meta.title,
                "authors": parsed.meta.authors,
                "doi": parsed.meta.doi,
                "journal": parsed.meta.journal,
                "year": parsed.meta.year,
                "topics": parsed.meta.topics,
                "mesh_terms": parsed.meta.mesh_terms,
                "source": parsed.meta.source,
                "tags": tags,
                "created_at": now,
                "valid_from": valid_from,
                "embedding_model": embedding_model,
                "version": version,
                "doc_version": doc_version,
                "hash": chunk["hash"],
                "confidence_score": overrides.get("confidence_score", 1.0),
            }

            # Agregar campos específicos para user_context
            if source_type == "user_context":
                payload["user_id"] = overrides.get("user_id")
                payload["snapshot_type"] = overrides.get("snapshot_type")
                payload["timeframe"] = overrides.get("timeframe")

            payloads.append(payload)
            vec_list.append(vec.tolist())

        # Fase 5: Upsert a Qdrant (con routing dinámico)
        with _time_phase("upsert"):
            store.upsert(ids, vec_list, payloads, collection_name=target_collection)
        
        logger.info(
            "Ingested doc_id={} chunks={} collection={} source_type={} journal={} year={} category={} locale={} embedding_model={} version={}",
            parsed.meta.doc_id,
            len(chunk_records),
            target_collection,
            source_type,
            parsed.meta.journal,
            parsed.meta.year,
            category,
            locale,
            embedding_model,
            version,
        )

        # Fase 6: Topics (opcional)
        if settings.auto_topics:
            with _time_phase("topics"):
                doc_vector = np.mean(vectors, axis=0)
                norm = np.linalg.norm(doc_vector)
                if norm > 0:
                    doc_vector = doc_vector / norm
                    matches = topic_classifier.assign_topics(
                        doc_vector,
                        top_k=settings.topic_top_k,
                        threshold=settings.topic_threshold,
                        config_path=settings.topic_config_path,
                    )
                    if matches:
                        topic_ids = [match.topic_id for match in matches]
                        score_payload = [
                            {
                                "id": match.topic_id,
                                "name": match.name,
                                "score": round(match.score, 4),
                            }
                            for match in matches
                        ]
                        store.set_topics(
                            parsed.meta.doc_id, topic_ids, score_payload, collection_name=target_collection
                        )
        
        # Registrar documento exitoso
        total_time = time.perf_counter() - start_total
        pipeline_metrics.record_phase("total", total_time)
        pipeline_metrics.record_document(len(chunk_records))
        
        return len(chunk_records)
    
    except Exception as e:
        pipeline_metrics.record_error()
        raise


def _obtain_parsed_document(req: IngestRequest) -> ParsedDocument:
    """Obtiene el documento parseado desde la fuente, instrumentado con métricas."""
    source = req.metadata.get("source") if req.metadata else None

    if req.url:
        # Fase 1: Descarga
        with _time_phase("download"):
            pdf_bytes = _download_source(req.url)
            filename = req.filename or Path(req.url).name or "document.pdf"
        
        # Fase 2: Parsing TEI
        try:
            with _time_phase("parse_tei"):
                tei_xml = fetch_tei(
                    pdf_bytes,
                    filename=filename,
                    consolidate_citations=req.consolidate_citations,
                )
                parsed = parse_tei(tei_xml, doc_id=req.doc_id, source=source)
        except Exception as exc:  # pragma: no cover - fallback path
            logger.warning("GROBID failed for doc_id={} ({}). Falling back to plain text", req.doc_id, exc)
            with _time_phase("parse_tei"):  # También medir el fallback
                parsed = extract_plain_text(pdf_bytes, doc_id=req.doc_id, source=source)
        return parsed

    if req.text:
        # Texto plano sin parsing (rápido)
        meta = PaperMeta(doc_id=req.doc_id, source=source)
        segments = [
            SectionSegment(order=0, section_path=req.metadata.get("section", "body") if req.metadata else "body", text=req.text)
        ]
        return ParsedDocument(meta=meta, segments=segments)

    raise ValueError("Unsupported ingestion payload")


def _download_source(url: str) -> bytes:
    """Fetch bytes from any supported repository.

    Supports:
      - Local paths and file:// URIs
      - HTTP/HTTPS URLs
      - gs://bucket/key (Google Cloud Storage)
    """
    repo = repository_for(url)
    return repo.read(url)


def _build_chunks(
    segments: Iterable[SectionSegment],
    chunk_size: int,
    chunk_overlap: int,
) -> List[Dict[str, object]]:
    chunks: List[Dict[str, object]] = []
    chunk_index = 0

    for segment in segments:
        pieces = _split_text(segment.text, chunk_size, chunk_overlap)
        for local_idx, piece in enumerate(pieces):
            if not piece:
                continue
            chunk_hash = _hash_id(str(segment.order), str(local_idx), piece[:64])
            chunks.append(
                {
                    "chunk_index": chunk_index,
                    "section_order": segment.order,
                    "section_path": segment.section_path,
                    "is_abstract": segment.is_abstract,
                    "is_conclusion": segment.is_conclusion,
                    "text": piece,
                    "hash": chunk_hash,
                }
            )
            chunk_index += 1

    return chunks


def _normalize_topics(value: str | Iterable[str] | None) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        tokens = [value]
    else:
        tokens = list(value)
    normalised = []
    for token in tokens:
        if not token or token is None:
            continue
        cleaned = str(token).strip().lower()
        if cleaned:  # skip empty strings after stripping
            normalised.append(cleaned)
    return sorted(set(normalised))
