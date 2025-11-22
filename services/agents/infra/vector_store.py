"""Abstracciones de acceso a Qdrant.

Centraliza la inicialización del cliente y operaciones comunes para upsert y
búsquedas de documentos vectorizados.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from typing import Any, Iterable, Mapping, MutableMapping, Sequence

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels


LOGGER = logging.getLogger(__name__)


class VectorStoreError(RuntimeError):
    """Errores relacionados con operaciones en el almacén vectorial."""


@dataclass(slots=True)
class VectorDocument:
    """Representa un documento listo para ser indexado en Qdrant."""

    id: str
    text: str
    embedding: Sequence[float]
    metadata: Mapping[str, Any] | None = None


class QdrantService:
    """Facade sobre el cliente oficial de Qdrant."""

    def __init__(
        self,
        collection_name: str,
        *,
        url: str | None = None,
        api_key: str | None = None,
        prefer_grpc: bool = False,
    ) -> None:
        resolved_url = url or os.getenv("QDRANT_URL") or "http://localhost:6333"
        resolved_api_key = api_key or os.getenv("QDRANT_API_KEY") or None

        self._collection = collection_name
        self._client = QdrantClient(
            url=resolved_url,
            api_key=resolved_api_key,
            prefer_grpc=prefer_grpc,
        )

    @property
    def collection(self) -> str:
        return self._collection

    def ensure_collection(
        self,
        vector_size: int,
        *,
        distance: qmodels.Distance = qmodels.Distance.COSINE,
        on_disk: bool = True,
    ) -> None:
        """Crea la colección si no existe."""

        try:
            self._client.get_collection(self._collection)
        except Exception:
            self._create_collection(
                vector_size=vector_size,
                distance=distance,
                on_disk=on_disk,
            )

    def recreate_collection(
        self,
        vector_size: int,
        *,
        distance: qmodels.Distance = qmodels.Distance.COSINE,
        on_disk: bool = True,
    ) -> None:
        """Elimina y vuelve a crear la colección."""

        try:
            self._client.delete_collection(self._collection)
        except Exception:
            LOGGER.debug("Colección %s no existía o no pudo eliminarse", self._collection)

        self._create_collection(vector_size=vector_size, distance=distance, on_disk=on_disk)

    def upsert_documents(self, documents: Iterable[VectorDocument]) -> None:
        """Inserta o actualiza documentos."""

        doc_list = list(documents)
        if not doc_list:
            LOGGER.warning("No se recibieron documentos para upsert en %s", self._collection)
            return

        ids = [doc.id for doc in doc_list]
        vectors = [list(doc.embedding) for doc in doc_list]
        payloads: list[MutableMapping[str, Any]] = []

        for doc in doc_list:
            payload: MutableMapping[str, Any] = {"text": doc.text}
            if doc.metadata:
                payload.update({k: v for k, v in doc.metadata.items()})
            payloads.append(payload)

        batch = qmodels.Batch(ids=ids, vectors=vectors, payloads=payloads)

        try:
            self._client.upsert(collection_name=self._collection, points=batch)
        except Exception as exc:  # pragma: no cover - errores del cliente
            raise VectorStoreError("Falló el upsert en Qdrant") from exc

    def search(
        self,
        query_embedding: Sequence[float],
        *,
        top_k: int = 5,
        score_threshold: float | None = None,
        filters: qmodels.Filter | None = None,
    ) -> list[qmodels.ScoredPoint]:
        """Realiza una búsqueda vectorial y retorna puntos puntuados."""

        try:
            return self._client.search(
                collection_name=self._collection,
                query_vector=list(query_embedding),
                limit=top_k,
                score_threshold=score_threshold,
                query_filter=filters,
            )
        except Exception as exc:  # pragma: no cover - errores del cliente
            raise VectorStoreError("Falló la búsqueda en Qdrant") from exc

    # ------------------------------------------------------------------
    # Internos
    def _create_collection(
        self,
        *,
        vector_size: int,
        distance: qmodels.Distance,
        on_disk: bool,
    ) -> None:
        try:
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=qmodels.VectorParams(
                    size=vector_size,
                    distance=distance,
                    on_disk=on_disk,
                ),
            )
        except Exception as exc:  # pragma: no cover - errores del cliente
            raise VectorStoreError("No se pudo crear la colección en Qdrant") from exc

