from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from infra import EmbeddingError, ServiceSettings, get_settings
from infra.env import load_environment
from infra.embeddings import embed_text
from infra.vector_store import QdrantService, VectorStoreError
from qdrant_client.http import models as qmodels

from .exceptions import VectorQueryError

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class VectorSearchFilters:
    """Filtros para búsqueda vectorial especializada."""

    category: Optional[str] = None  # "mente", "cuerpo", "alma"
    topics: list[str] = field(default_factory=list)  # Lista de topics biomédicos
    min_year: Optional[int] = None  # Año mínimo de publicación
    locale: Optional[str] = None  # e.g., "es-CO"
    boost_abstracts: bool = True  # Dar mayor peso a abstracts/conclusions
    boost_recent: bool = True  # Dar mayor peso a papers recientes


@dataclass(slots=True)
class VectorQueryRecord:
    """Representa una consulta realizada contra el almacén vectorial."""

    vector_store: str
    embedding_model: str
    query_text: str
    top_k: int
    response_payload: dict[str, Any]
    confidence_score: float
    filters_applied: Optional[VectorSearchFilters] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "vector_store": self.vector_store,
            "embedding_model": self.embedding_model,
            "query_text": self.query_text,
            "top_k": self.top_k,
            "response_payload": self.response_payload,
            "confidence_score": self.confidence_score,
            "filters_applied": (
                {
                    "category": self.filters_applied.category,
                    "topics": self.filters_applied.topics,
                    "min_year": self.filters_applied.min_year,
                    "locale": self.filters_applied.locale,
                    "boost_abstracts": self.filters_applied.boost_abstracts,
                    "boost_recent": self.filters_applied.boost_recent,
                }
                if self.filters_applied
                else None
            ),
        }


class VectorQueryRunner:
    """Ejecuta consultas contra Qdrant con reintentos y métricas básicas."""

    def __init__(
        self,
        *,
        settings: Optional[ServiceSettings] = None,
        qdrant_service: Optional[QdrantService] = None,
    ) -> None:
        load_environment(override=False)
        self._settings = settings or get_settings()
        self._qdrant = qdrant_service or QdrantService(
            collection_name=self._settings.vector_collection_name,
            url=self._settings.vector_service_url,
            api_key=self._settings.vector_service_api_key,
        )

    def run(
        self,
        *,
        trace_id: str,
        query_text: str,
        top_k: Optional[int] = None,
        filters: Optional[VectorSearchFilters] = None,
    ) -> list[VectorQueryRecord]:
        clean_query = query_text.strip()
        if not clean_query:
            logger.info("VectorQueryRunner: query vacía, no se ejecutará búsqueda", extra={"trace_id": trace_id})
            return []

        limit = top_k or self._settings.vector_top_k
        attempts = max(1, self._settings.vector_retry_attempts)
        backoff_seconds = max(0.1, self._settings.vector_retry_backoff_seconds)

        embedding_model = self._settings.embedding_model
        backend = self._settings.embedding_backend
        normalize = self._settings.embedding_normalize
        api_key = self._settings.resolved_embedding_api_key

        # Construir filtros Qdrant
        query_filter = self._build_qdrant_filter(filters) if filters else None

        last_exception: Exception | None = None

        for attempt in range(1, attempts + 1):
            try:
                start_time = time.perf_counter()
                embedding = embed_text(
                    clean_query,
                    model=embedding_model,
                    api_key=api_key,
                    backend=backend,
                    normalize=normalize,
                )
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                logger.info(
                    "VectorQueryRunner: embeddings generados en %.2f ms",
                    elapsed_ms,
                    extra={"trace_id": trace_id},
                )

                search_start = time.perf_counter()
                points = self._qdrant.search(
                    query_embedding=embedding, top_k=limit, filters=query_filter
                )
                search_elapsed = (time.perf_counter() - search_start) * 1000.0
                logger.info(
                    "VectorQueryRunner: búsqueda completada en %.2f ms (hits=%d)",
                    search_elapsed,
                    len(points),
                    extra={"trace_id": trace_id, "filters": filters is not None},
                )

                # Aplicar boosting si está habilitado
                hits_payload = [self._serialize_point(point) for point in points]
                if filters and (filters.boost_abstracts or filters.boost_recent):
                    hits_payload = self._apply_boosting(hits_payload, filters)
                    # Re-ordenar por score ajustado
                    hits_payload.sort(key=lambda x: x.get("score", 0.0), reverse=True)

                confidence = (
                    sum(hit.get("score") or 0.0 for hit in hits_payload) / len(hits_payload)
                    if hits_payload
                    else 0.0
                )

                record = VectorQueryRecord(
                    vector_store=self._settings.vector_store_name,
                    embedding_model=embedding_model,
                    query_text=clean_query,
                    top_k=limit,
                    response_payload={"hits": hits_payload},
                    confidence_score=round(confidence, 4),
                    filters_applied=filters,
                )
                return [record]
            except EmbeddingError as exc:
                logger.error(
                    "VectorQueryRunner: error generando embeddings: %s",
                    exc,
                    extra={"trace_id": trace_id},
                )
                raise VectorQueryError(message="No fue posible generar embeddings para la consulta.") from exc
            except (VectorStoreError, Exception) as exc:
                last_exception = exc
                logger.warning(
                    "VectorQueryRunner: fallo consultando Qdrant (intento %d/%d): %s",
                    attempt,
                    attempts,
                    exc,
                    extra={"trace_id": trace_id},
                )
                if attempt == attempts:
                    break
                time.sleep(backoff_seconds * attempt)

        assert last_exception is not None
        raise VectorQueryError(
            message="No fue posible completar la búsqueda vectorial tras reintentos.",
            details={"reason": str(last_exception)},
        ) from last_exception

    def _build_qdrant_filter(self, filters: VectorSearchFilters) -> qmodels.Filter:
        """Construye filtro Qdrant basado en VectorSearchFilters."""
        must_conditions = []

        # Filtro por categoría
        if filters.category:
            must_conditions.append(
                qmodels.FieldCondition(
                    key="category", match=qmodels.MatchValue(value=filters.category)
                )
            )

        # Filtro por topics (OR entre topics)
        if filters.topics:
            # Usar should para que cualquier topic coincida
            topic_conditions = [
                qmodels.FieldCondition(
                    key="topics", match=qmodels.MatchAny(any=filters.topics)
                )
            ]
            must_conditions.extend(topic_conditions)

        # Filtro por año mínimo
        if filters.min_year:
            must_conditions.append(
                qmodels.FieldCondition(
                    key="year", range=qmodels.Range(gte=filters.min_year)
                )
            )

        # Filtro por locale
        if filters.locale:
            must_conditions.append(
                qmodels.FieldCondition(
                    key="locale", match=qmodels.MatchValue(value=filters.locale)
                )
            )

        return qmodels.Filter(must=must_conditions) if must_conditions else None

    def _apply_boosting(
        self, hits: list[dict[str, Any]], filters: VectorSearchFilters
    ) -> list[dict[str, Any]]:
        """Aplica boosting a los scores basado en metadata."""
        import datetime

        current_year = datetime.datetime.now().year

        for hit in hits:
            payload = hit.get("payload", {})
            original_score = hit.get("score", 0.0)
            boost = 0.0

            # Boost por abstract/conclusion
            if filters.boost_abstracts:
                if payload.get("is_abstract") or payload.get("is_conclusion"):
                    boost += 0.2

            # Boost por año reciente
            if filters.boost_recent:
                year = payload.get("year", 0)
                if year >= 2020:
                    boost += 0.15
                elif year >= 2015:
                    boost += 0.1

            # Aplicar boost
            hit["score"] = min(1.0, original_score + boost)
            hit["original_score"] = original_score
            hit["boost_applied"] = boost

        return hits

    @staticmethod
    def _serialize_point(point: qmodels.ScoredPoint) -> dict[str, Any]:
        payload = point.payload or {}
        return {
            "id": getattr(point, "id", None),
            "score": float(point.score or 0.0),
            "payload": payload,
        }


__all__ = ["VectorQueryRecord", "VectorQueryRunner", "VectorSearchFilters"]