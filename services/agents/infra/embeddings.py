"""Utilidades para generar embeddings con FastEmbed y Gemini."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os
from math import sqrt
from typing import Any, Sequence

from google import genai

try:
    from fastembed import TextEmbedding
except ImportError:  # pragma: no cover - dependencia opcional
    TextEmbedding = None  # type: ignore[assignment]


class EmbeddingError(RuntimeError):
    """Errores relacionados con la generación de embeddings."""


@dataclass(slots=True)
class EmbeddingConfig:
    model: str = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    )
    api_key: str | None = None
    backend: str | None = os.getenv("EMBEDDING_BACKEND")
    normalize: bool = os.getenv("EMBEDDING_NORMALIZE", "true").lower() != "false"


def _final_config(
    *,
    model: str | None,
    api_key: str | None,
    backend: str | None,
    normalize: bool | None,
) -> EmbeddingConfig:
    defaults = EmbeddingConfig()
    resolved_backend = backend.strip() if isinstance(backend, str) else backend
    if isinstance(defaults.backend, str):
        default_backend = defaults.backend.strip() or None
    else:
        default_backend = defaults.backend
    return EmbeddingConfig(
        model=model or defaults.model,
        api_key=api_key or defaults.api_key,
        backend=resolved_backend or default_backend,
        normalize=normalize if normalize is not None else defaults.normalize,
    )


def _resolve_backend(config: EmbeddingConfig) -> str:
    if config.backend:
        backend = config.backend.strip().lower()
        if backend:
            return backend
    if config.model.startswith("models/"):
        return "gemini"
    return "fastembed"


def _resolve_api_key(explicit: str | None = None) -> str:
    api_key = explicit or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EmbeddingError(
            "No se encontró GOOGLE_API_KEY. Configura la variable de entorno "
            "o pasa la clave explícitamente."
        )
    return api_key


def _client(config: EmbeddingConfig) -> genai.Client:
    api_key = _resolve_api_key(config.api_key)
    return genai.Client(api_key=api_key)


@lru_cache(maxsize=4)
def _fastembed_model(model_name: str):
    if TextEmbedding is None:
        raise EmbeddingError(
            "FastEmbed no está disponible. Instala la dependencia 'fastembed' para habilitar este backend."
        )
    try:
        return TextEmbedding(model_name=model_name)
    except Exception as error:  # pragma: no cover - inicialización fallida
        raise EmbeddingError(
            f"No se pudo inicializar FastEmbed con el modelo '{model_name}'."
        ) from error


def _normalize(vector: Sequence[float]) -> list[float]:
    norm_sq = sum(value * value for value in vector)
    if norm_sq <= 0:
        return [float(value) for value in vector]
    norm = sqrt(norm_sq)
    return [float(value) / norm for value in vector]


def _prepare_values(values: Sequence[float], *, normalize: bool) -> list[float]:
    vector = [float(value) for value in values]
    if normalize:
        vector = _normalize(vector)
    return vector


def _embed_with_fastembed(texts: Sequence[str], config: EmbeddingConfig) -> list[list[float]]:
    try:
        embedder = _fastembed_model(config.model)
        embeddings: list[list[float]] = []
        for vector in embedder.embed(texts):
            embeddings.append(_prepare_values(vector, normalize=config.normalize))
        return embeddings
    except EmbeddingError:
        raise
    except Exception as error:
        raise EmbeddingError("Error generando embeddings con FastEmbed.") from error


def _should_fallback(error: Exception) -> bool:
    if isinstance(error, AttributeError):
        return True
    message = str(error).lower()
    hints = ("no attribute", "not found", "missing", "does not exist")
    return "batch_embed_contents" in message and any(hint in message for hint in hints)


def _extract_embedding_values(response: object) -> Sequence[float]:
    embedding = getattr(response, "embedding", None)
    if embedding is None:
        embeddings_attr = getattr(response, "embeddings", None)
        if embeddings_attr:
            embedding = embeddings_attr[0]
    values = getattr(embedding, "values", None) if embedding is not None else None
    if values is None:
        raise EmbeddingError(
            "Respuesta inválida de embed_content: falta embedding.values o embeddings[0].values."
        )
    return values


def _embed_with_gemini(texts: Sequence[str], config: EmbeddingConfig) -> list[list[float]]:
    client = _client(config)

    def _content_payload(text: str) -> dict[str, Any]:
        return {"parts": [{"text": text}]}

    try:
        response = client.models.batch_embed_contents(
            model=config.model,
            contents=[_content_payload(text) for text in texts],
        )
    except Exception as error:
        if not _should_fallback(error):
            raise EmbeddingError("Error generando embeddings con batch_embed_contents.") from error
    else:
        embeddings_attr = getattr(response, "embeddings", None)
        if not embeddings_attr:
            raise EmbeddingError(
                "Respuesta inválida de batch_embed_contents: falta embeddings."
            )
        vectors: list[list[float]] = []
        for embedding in embeddings_attr:
            values = getattr(embedding, "values", None)
            if values is None:
                raise EmbeddingError(
                    "Respuesta inválida de batch_embed_contents: falta embedding.values."
                )
            vectors.append(_prepare_values(values, normalize=config.normalize))
        if len(vectors) != len(texts):
            raise EmbeddingError(
                "El servicio de embeddings devolvió un número inesperado de vectores."
            )
        return vectors

    embeddings: list[list[float]] = []
    for text in texts:
        try:
            single_response = client.models.embed_content(
                model=config.model,
                contents=[_content_payload(text)],
            )
        except Exception as single_error:
            raise EmbeddingError(
                "Error generando embeddings con embed_content tras falla en batch_embed_contents."
            ) from single_error

        values = _extract_embedding_values(single_response)
        embeddings.append(_prepare_values(values, normalize=config.normalize))

    return embeddings


def embed_texts(
    texts: Sequence[str],
    *,
    model: str | None = None,
    api_key: str | None = None,
    backend: str | None = None,
    normalize: bool | None = None,
) -> list[list[float]]:
    if not texts:
        return []

    config = _final_config(
        model=model,
        api_key=api_key,
        backend=backend,
        normalize=normalize,
    )

    resolved_backend = _resolve_backend(config)
    config.backend = resolved_backend

    if resolved_backend == "fastembed":
        return _embed_with_fastembed(texts, config)
    if resolved_backend == "gemini":
        return _embed_with_gemini(texts, config)

    raise EmbeddingError(
        f"Backend de embeddings desconocido: {resolved_backend!r}. Usa 'fastembed' o 'gemini'."
    )


def embed_text(
    text: str,
    *,
    model: str | None = None,
    api_key: str | None = None,
    backend: str | None = None,
    normalize: bool | None = None,
) -> list[float]:
    if not text:
        raise EmbeddingError("El texto para embebido no puede estar vacío.")

    [embedding] = embed_texts(
        [text],
        model=model,
        api_key=api_key,
        backend=backend,
        normalize=normalize,
    )
    return embedding


__all__ = ["EmbeddingConfig", "EmbeddingError", "embed_text", "embed_texts"]
