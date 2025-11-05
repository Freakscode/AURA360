from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Iterable, Optional

from infra import EmbeddingError, ServiceSettings, get_settings
from infra.env import load_environment
from infra.embeddings import embed_text
from infra.vector_store import QdrantService, VectorStoreError
from qdrant_client.http import models as qmodels

from .exceptions import VectorQueryError

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class VectorQueryRecord:
    """Representa una consulta realizada contra el almacén vectorial."""

    vector_store: str
    embedding_model: str
    query_text: str
    top_k: int
    response_payload: dict[str, Any]
    confidence_score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "vector_store": self.vector_store,
            "embedding_model": self.embedding_model,
            "query_text": self.query_text,
            "top_k": self.top_k,
            "response_payload": self.response_payload,
            "confidence_score": self.confidence_score,
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
                points = self._qdrant.search(query_embedding=embedding, top_k=limit)
                search_elapsed = (time.perf_counter() - search_start) * 1000.0
                logger.info(
                    "VectorQueryRunner: búsqueda completada en %.2f ms (hits=%d)",
                    search_elapsed,
                    len(points),
                    extra={"trace_id": trace_id},
                )

                hits_payload = [self._serialize_point(point) for point in points]
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

    @staticmethod
    def _serialize_point(point: qmodels.ScoredPoint) -> dict[str, Any]:
        payload = point.payload or {}
        return {
            "id": getattr(point, "id", None),
            "score": float(point.score or 0.0),
            "payload": payload,
        }


__all__ = ["VectorQueryRecord", "VectorQueryRunner"]