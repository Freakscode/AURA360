from __future__ import annotations

import time
from typing import Any, Dict, Iterable, List, Optional, Sequence
from loguru import logger

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from vectosvc.config import service_settings, settings


class QdrantStore:
    def __init__(self, client: Optional[QdrantClient] = None):
        grpc_kwargs: Dict[str, Any] = {}
        if settings.qdrant_grpc:
            _, _, port = settings.qdrant_grpc.rpartition(":")
            if port:
                try:
                    grpc_kwargs["grpc_port"] = int(port)
                except ValueError:
                    logger.warning("Invalid QDRANT_GRPC port value: {}", port)
            else:
                logger.warning("QDRANT_GRPC provided without port: {}", settings.qdrant_grpc)
        if settings.prefer_grpc:
            grpc_kwargs["prefer_grpc"] = True

        self.client = client or QdrantClient(url=settings.qdrant_url, **grpc_kwargs)
        self.collection = settings.collection_name

    def ensure_collection(self, vector_size: int, distance: str | None = None, on_disk: bool = True) -> None:
        distance = (distance or settings.vector_distance).lower()
        dmap = {
            "cosine": qm.Distance.COSINE,
            "dot": qm.Distance.DOT,
            "euclid": qm.Distance.EUCLID,
        }
        params = qm.VectorParams(
            size=vector_size,
            distance=dmap.get(distance, qm.Distance.COSINE),
            on_disk=on_disk,
        )
        exists = False
        try:
            self.client.get_collection(self.collection)
            exists = True
        except Exception:
            exists = False

        if not exists:
            logger.info("Creating collection '{}' (size={}, distance={}, on_disk={})",
                        self.collection, vector_size, distance, on_disk)
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=params,
                hnsw_config=qm.HnswConfigDiff(m=16, ef_construct=256),
                optimizers_config=qm.OptimizersConfigDiff(
                    indexing_threshold=20000,
                    memmap_threshold=20000,
                    max_segment_size=200000,
                ),
            )

        # Useful payload indexes for typical filters
        self._ensure_payload_index("doc_id", qm.PayloadSchemaType.KEYWORD)
        self._ensure_payload_index("category", qm.PayloadSchemaType.KEYWORD)
        self._ensure_payload_index("locale", qm.PayloadSchemaType.KEYWORD)
        self._ensure_payload_index("lang", qm.PayloadSchemaType.KEYWORD)
        self._ensure_payload_index("source_type", qm.PayloadSchemaType.KEYWORD)
        self._ensure_payload_index("topics", qm.PayloadSchemaType.KEYWORD)
        self._ensure_payload_index("journal", qm.PayloadSchemaType.KEYWORD)
        self._ensure_payload_index("year", qm.PayloadSchemaType.INTEGER)
        self._ensure_payload_index("doc_version", qm.PayloadSchemaType.INTEGER)
        self._ensure_payload_index("version", qm.PayloadSchemaType.KEYWORD)
        self._ensure_payload_index("created_at", qm.PayloadSchemaType.INTEGER)
        self._ensure_payload_index("embedding_model", qm.PayloadSchemaType.KEYWORD)
        self._ensure_payload_index("confidence_score", qm.PayloadSchemaType.FLOAT)

    def _ensure_payload_index(self, field: str, schema: qm.PayloadSchemaType) -> None:
        try:
            self.client.create_payload_index(
                collection_name=self.collection,
                field_name=field,
                field_schema=schema,
            )
        except Exception as exc:
            message = str(exc).lower()
            if "already exists" in message or "field with name" in message:
                return
            logger.debug("create_payload_index skipped field={} reason={}", field, exc)

    def upsert(self, ids: Iterable[str | int], vectors: Iterable[list[float] | Any], payloads: Iterable[Dict[str, Any]]) -> None:
        points = []
        for id_, vec, pl in zip(ids, vectors, payloads):
            points.append(qm.PointStruct(id=id_, vector=vec, payload=pl))

        try:
            self.client.upsert(self.collection, points=points, wait=True)
        except Exception as exc:
            logger.error(
                "Qdrant upsert failed for collection={} ids_sample={} error={}",
                self.collection,
                ids[:3],
                exc,
            )
            raise

    def set_topics(
        self,
        doc_id: str,
        topics: Sequence[str],
        scores: Sequence[Dict[str, Any]] | None = None,
    ) -> None:
        if not topics:
            return
        payload: Dict[str, Any] = {"topics": list(topics)}
        if scores:
            payload["topic_scores"] = list(scores)

        payload_filter = qm.Filter(
            must=[
                qm.FieldCondition(
                    key="doc_id",
                    match=qm.MatchValue(value=doc_id),
                )
            ]
        )
        selector = qm.FilterSelector(filter=payload_filter)

        try:
            self.client.set_payload(
                collection_name=self.collection,
                payload=payload,
                points=selector,
                wait=True,
            )
        except Exception as exc:  # pragma: no cover
            logger.error(
                "Failed to set topics for doc_id={} payload={} error={}",
                doc_id,
                payload,
                exc,
            )
            raise

    def search(
        self,
        query_vector: list[float],
        limit: int = 10,
        filter_: Optional[qm.Filter] = None,
        with_payload: bool = True,
        ef_search: Optional[int] = None,
    ):
        params = qm.SearchParams(hnsw_ef=ef_search) if ef_search else None
        return self.client.search(
            self.collection,
            query_vector=query_vector,
            limit=limit,
            query_filter=filter_,
            with_payload=with_payload,
            search_params=params,
            timeout=service_settings.vector_query_timeout,
        )

    def search_with_retry(
        self,
        query_vector: list[float],
        limit: int = 10,
        filter_: Optional[qm.Filter] = None,
        with_payload: bool = True,
        ef_search: Optional[int] = None,
    ):
        attempts = service_settings.vector_query_max_retries + 1
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            try:
                return self.search(
                    query_vector=query_vector,
                    limit=limit,
                    filter_=filter_,
                    with_payload=with_payload,
                    ef_search=ef_search,
                )
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Qdrant search attempt {}/{} failed: {}",
                    attempt,
                    attempts,
                    exc,
                )
                if attempt >= attempts:
                    break
                time.sleep(service_settings.vector_query_retry_delay * attempt)

        if last_error is not None:
            raise last_error
        return []

    def build_filter(self, must: Dict[str, Any] | None, should: Dict[str, Any] | None) -> Optional[qm.Filter]:
        if not must and not should:
            return None

        def to_conditions(dct: Dict[str, Any]) -> List[qm.Condition]:
            conds: List[qm.Condition] = []
            for k, v in dct.items():
                if isinstance(v, list):
                    conds.append(qm.FieldCondition(key=k, match=qm.MatchAny(any=v)))
                else:
                    conds.append(qm.FieldCondition(key=k, match=qm.MatchValue(value=v)))
            return conds

        return qm.Filter(
            must=to_conditions(must or {}),
            should=to_conditions(should or {}),
        )


# Singleton-ish default store
store = QdrantStore()
