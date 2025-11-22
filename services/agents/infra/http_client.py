"""Cliente HTTP para el servicio vectorial basado en vectosvc."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
import os
from typing import Any, Sequence

import requests

logger = logging.getLogger(__name__)

# TODO: Agregar pruebas unitarias para VectorServiceClient.describe_collection y
#  VectorServiceClient.get_collection_vector_size cuando exista infraestructura en agents-service/tests.

from .embeddings import EmbeddingConfig, EmbeddingError, embed_texts


class VectorServiceError(RuntimeError):
    """Errores al interactuar con el servicio vectorial."""


def _load_collection_name() -> str | None:
    """Obtiene el nombre de colección desde la variable estándar o su alias legado."""
    primary = os.getenv("VECTOR_SERVICE_COLLECTION_NAME")
    if primary and primary.strip():
        return primary
    legacy = os.getenv("HOLISTIC_VECTOR_COLLECTION_NAME")
    if legacy and legacy.strip():
        return legacy
    return None


@dataclass(slots=True)
class VectorServiceConfig:
    """Configuración del cliente vectorial.

    La colección se lee desde `VECTOR_SERVICE_COLLECTION_NAME` (preferido) o desde el alias legado
    `HOLISTIC_VECTOR_COLLECTION_NAME`.
    """

    base_url: str = os.getenv("VECTOR_SERVICE_URL", "https://qdrant.vectorial-db.orb.local/")
    api_key: str | None = os.getenv("VECTOR_SERVICE_API_KEY")
    timeout: float = float(os.getenv("VECTOR_SERVICE_TIMEOUT", "15.0"))
    verify_ssl: bool = os.getenv("VECTOR_SERVICE_VERIFY_SSL", "true").lower() != "false"
    collection_name: str | None = field(default_factory=_load_collection_name)


class VectorServiceClient:
    """Cliente para el API REST de vectosvc."""

    def __init__(
        self,
        config: VectorServiceConfig | None = None,
        *,
        collection_name: str | None = None,
    ) -> None:
        self._config = config or VectorServiceConfig()
        self._collection_name = collection_name or self._config.collection_name
        if not self._collection_name:
            raise ValueError(
                "VectorServiceClient requiere un nombre de colección. "
                "Configura VECTOR_SERVICE_COLLECTION_NAME (preferido) o HOLISTIC_VECTOR_COLLECTION_NAME, "
                "o pásalo al constructor."
            )
        self._session = requests.Session()
        if self._config.api_key:
            self._session.headers.update({"Authorization": f"Bearer {self._config.api_key}"})

    def _ensure_query_vector(
        self,
        *,
        query_text: str | None,
        query_vector: Sequence[float] | None,
        embedding_config: EmbeddingConfig | None,
    ) -> Sequence[float]:
        if query_vector is not None:
            return query_vector
        if query_text is None or not query_text.strip():
            raise ValueError(
                "Se requiere query_vector o un query_text no vacío para generar el vector de búsqueda."
            )

        config = embedding_config or EmbeddingConfig()
        try:
            embeddings = embed_texts(
                [query_text],
                model=config.model,
                api_key=config.api_key,
            )
        except EmbeddingError as exc:
            raise VectorServiceError(
                "No se pudo generar el vector de consulta mediante el servicio de embeddings."
            ) from exc
        except Exception as exc:  # pragma: no cover - errores inesperados del cliente
            raise VectorServiceError(
                "Error inesperado al solicitar embeddings para la consulta."
            ) from exc

        if not embeddings or not embeddings[0]:
            raise VectorServiceError(
                "El servicio de embeddings no devolvió un vector para la consulta proporcionada."
            )
        return embeddings[0]

    def _request(self, method: str, path: str, *, json: Any | None = None) -> Any:
        url = f"{self._config.base_url.rstrip('/')}/{path.lstrip('/')}"
        try:
            response = self._session.request(
                method,
                url,
                json=json,
                timeout=self._config.timeout,
                verify=self._config.verify_ssl,
            )
        except requests.RequestException as exc:
            raise VectorServiceError(f"Error de red al invocar {url}: {exc}") from exc

        if response.status_code >= 400:
            raise VectorServiceError(
                f"Respuesta {response.status_code} al invocar {url}: {response.text}"
            )

        if response.content:
            return response.json()
        return None

    # ------------------------------------------------------------------
    # API pública
    def describe_collection(self, collection_name: str) -> dict[str, Any]:
        """Describe una colección gestionada por vectosvc."""
        try:
            raw_response = self._request("GET", f"/collections/{collection_name}")
        except ValueError as exc:
            raise VectorServiceError(
                f"Respuesta inválida al describir la colección '{collection_name}': cuerpo no es JSON."
            ) from exc

        if not isinstance(raw_response, dict):
            raise VectorServiceError(
                f"Respuesta inválida al describir la colección '{collection_name}': se esperaba un objeto JSON."
            )

        logger.debug(
            "Respuesta completa de describe_collection para '%s': %s",
            collection_name,
            raw_response,
        )
        return raw_response

    def get_collection_vector_size(self, collection_name: str) -> int:
        """Obtiene la dimensión del vector configurada para una colección."""
        description = self.describe_collection(collection_name)
        try:
            size = (
                description["result"]["config"]["params"]["vectors"]["size"]
            )
        except (KeyError, TypeError) as exc:
            raise VectorServiceError(
                f"No se pudo resolver la dimensión de la colección '{collection_name}': campo 'size' ausente."
            ) from exc

        if not isinstance(size, int) or isinstance(size, bool):
            raise VectorServiceError(
                f"No se pudo resolver la dimensión de la colección '{collection_name}': valor inválido {size!r}."
            )

        logger.debug(
            "Dimensión detectada para la colección '%s': %d",
            collection_name,
            size,
        )
        return size

    def search(
        self,
        *,
        query_text: str | None = None,
        query_vector: Sequence[float] | None = None,
        limit: int = 10,
        with_payload: bool = True,
        filter: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        embedding_config: EmbeddingConfig | None = None,
    ) -> dict[str, Any]:
        """Realiza una búsqueda semántica contra Qdrant.

        Args:
            query_text: Texto a embeder para la consulta. Mutuamente excluyente con query_vector.
            query_vector: Vector ya calculado para la consulta. Tiene prioridad sobre query_text.
            limit: Número máximo de resultados a devolver.
            with_payload: Indica si se debe devolver el payload de cada vector.
            filter: Filtro estructurado compatible con Qdrant.
            params: Parámetros adicionales para el motor de búsqueda (por ejemplo, ``ef_search``).
            embedding_config: Configuración opcional para generar embeddings cuando solo se provea texto.

        Returns:
            Respuesta JSON devuelta por el endpoint de búsqueda de Qdrant.
        """
        vector = self._ensure_query_vector(
            query_text=query_text,
            query_vector=query_vector,
            embedding_config=embedding_config,
        )

        payload: dict[str, Any] = {
            "vector": list(vector),
            "limit": limit,
            "with_payload": with_payload,
        }
        if filter is not None:
            payload["filter"] = filter
        if params is not None:
            payload["params"] = params

        return self._request(
            "POST",
            f"/collections/{self._collection_name}/points/search",
            json=payload,
        )


__all__ = ["VectorServiceClient", "VectorServiceConfig", "VectorServiceError"]

