"""Servicio de vectorización de snapshots de contexto de usuario."""

from __future__ import annotations

import logging
from typing import Any

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

__all__ = ["UserContextVectorizer", "VectorizationError"]


class VectorizationError(RuntimeError):
    """Error durante la vectorización de un snapshot."""


class UserContextVectorizer:
    """Envía snapshots de contexto de usuario al vectordb service para embedding.

    Este servicio maneja la comunicación con el vectordb service para ingestar
    snapshots como documentos vectorizados en la colección user_context.
    """

    def __init__(
        self,
        vectordb_url: str | None = None,
        api_key: str | None = None,
        timeout: int = 30,
    ):
        """Inicializa el vectorizador.

        Args:
            vectordb_url: URL base del vectordb service (default: desde settings)
            api_key: API key para autenticación (default: desde settings)
            timeout: Timeout en segundos para requests HTTP
        """
        self.vectordb_url = vectordb_url or getattr(
            settings, "VECTORDB_SERVICE_URL", "http://localhost:8000"
        )
        self.api_key = api_key or getattr(
            settings, "VECTORDB_SERVICE_API_KEY", None
        )
        self.timeout = timeout

    def vectorize_snapshot(
        self,
        snapshot: Any,  # UserContextSnapshot model instance
        *,
        topic_classifier: Any | None = None,
    ) -> dict[str, Any]:
        """Vectoriza un snapshot y lo ingesta en Qdrant.

        Args:
            snapshot: Instancia de UserContextSnapshot
            topic_classifier: Opcional TopicClassifier para clasificar topics
                             Si no se provee, intenta importar de agents service

        Returns:
            Dict con response del vectordb service

        Raises:
            VectorizationError: Si falla la vectorización
        """
        # Clasificar topics si no están ya presentes
        topics = snapshot.topics or []
        if not topics and topic_classifier:
            try:
                topics = topic_classifier.classify(snapshot.consolidated_text)
                snapshot.topics = topics
                snapshot.save(update_fields=["topics"])
            except Exception as exc:
                logger.warning(
                    f"Failed to classify topics for snapshot {snapshot.id}: {exc}"
                )
                # Continuar sin topics, no es crítico

        # Mapear snapshot_type a category
        category_mapping = {
            "mind": "mente",
            "body": "cuerpo",
            "soul": "alma",
            "holistic": "mente",  # Default para holistic
        }
        category = category_mapping.get(snapshot.snapshot_type, "mente")

        # Preparar payload para ingestion
        payload = {
            "doc_id": f"user_context_{snapshot.id}",
            "text": snapshot.consolidated_text,
            "category": category,
            "locale": "es-CO",
            "source_type": "user_context",  # Distingue del corpus general
            "embedding_model": getattr(
                settings, "EMBEDDING_MODEL", "text-embedding-3-small"
            ),
            "version": "1.0.0",
            "metadata": {
                "user_id": str(snapshot.auth_user_id),
                "snapshot_type": snapshot.snapshot_type,
                "timeframe": snapshot.timeframe,
                "created_at": snapshot.created_at.isoformat(),
                "topics": topics,
                "confidence_score": float(snapshot.confidence_score),
                **snapshot.metadata,
            },
        }

        # POST a /ingest en vectordb service
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = requests.post(
                f"{self.vectordb_url}/ingest",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.Timeout as exc:
            raise VectorizationError(
                f"Timeout vectorizing snapshot {snapshot.id}"
            ) from exc
        except requests.RequestException as exc:
            raise VectorizationError(
                f"HTTP error vectorizing snapshot {snapshot.id}: {exc}"
            ) from exc

        try:
            result = response.json()
        except ValueError as exc:
            raise VectorizationError(
                f"Invalid JSON response from vectordb service"
            ) from exc

        # Actualizar snapshot con tracking de vectorización
        snapshot.vectorized_at = timezone.now()
        snapshot.vector_doc_id = payload["doc_id"]
        snapshot.save(update_fields=["vectorized_at", "vector_doc_id"])

        logger.info(
            f"Successfully vectorized snapshot {snapshot.id} "
            f"(user={snapshot.auth_user_id}, type={snapshot.snapshot_type})"
        )

        return result

    def delete_snapshot_from_vector_store(
        self,
        snapshot: Any,  # UserContextSnapshot model instance
    ) -> bool:
        """Elimina un snapshot del vector store (GDPR compliance).

        Args:
            snapshot: Instancia de UserContextSnapshot

        Returns:
            True si se eliminó exitosamente, False en caso contrario
        """
        if not snapshot.vector_doc_id:
            logger.warning(
                f"Snapshot {snapshot.id} was not vectorized, skipping deletion"
            )
            return False

        # Llamar a endpoint de delete en vectordb
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = requests.delete(
                f"{self.vectordb_url}/api/documents/{snapshot.vector_doc_id}",
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()

            logger.info(
                f"Deleted vector document {snapshot.vector_doc_id} "
                f"for snapshot {snapshot.id}"
            )
            return True

        except requests.RequestException as exc:
            logger.error(
                f"Failed to delete vector document {snapshot.vector_doc_id}: {exc}",
                exc_info=True,
            )
            return False

    def batch_vectorize_snapshots(
        self,
        snapshots: list[Any],  # List of UserContextSnapshot instances
        *,
        topic_classifier: Any | None = None,
    ) -> dict[str, Any]:
        """Vectoriza múltiples snapshots en batch.

        Args:
            snapshots: Lista de instancias de UserContextSnapshot
            topic_classifier: Opcional TopicClassifier

        Returns:
            Dict con "succeeded", "failed", y "errors"
        """
        succeeded = []
        failed = []
        errors = []

        for snapshot in snapshots:
            try:
                result = self.vectorize_snapshot(
                    snapshot, topic_classifier=topic_classifier
                )
                succeeded.append(
                    {"snapshot_id": str(snapshot.id), "result": result}
                )
            except VectorizationError as exc:
                failed.append(str(snapshot.id))
                errors.append(
                    {"snapshot_id": str(snapshot.id), "error": str(exc)}
                )

        logger.info(
            f"Batch vectorization complete: {len(succeeded)} succeeded, "
            f"{len(failed)} failed"
        )

        return {
            "succeeded": succeeded,
            "failed": failed,
            "errors": errors,
            "total": len(snapshots),
        }
