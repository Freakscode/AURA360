"""Agente responsable de recuperar y sintetizar conocimiento desde el servicio vectorial."""

from __future__ import annotations

import logging
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.sessions.state import State
from google.genai import types as genai_types

from infra import (
    EmbeddingConfig,
    VectorServiceClient,
    VectorServiceConfig,
    VectorServiceError,
)


LOGGER = logging.getLogger(__name__)

MODEL_NAME = "gemini-2.5-flash"


def _extract_user_prompt(content: genai_types.Content | None) -> str:
    if not content or not getattr(content, "parts", None):
        return ""
    texts: list[str] = []
    for part in content.parts:
        text = getattr(part, "text", None)
        if text:
            texts.append(text)
    return "\n".join(texts).strip()


class KnowledgeRetrievalCallback:
    """Callback que consulta el servicio vectorial y persiste resultados en el estado."""

    def __init__(
        self,
        *,
        state_key: str = "knowledge_context",
        limit: int = 5,
        score_threshold: float | None = None,
        client: VectorServiceClient | None = None,
        embedding_config: EmbeddingConfig | None = None,
    ) -> None:
        self.state_key = state_key
        self.limit = limit
        self.score_threshold = score_threshold
        self.client = client or VectorServiceClient(VectorServiceConfig())
        self.embedding_config = embedding_config

    def __call__(self, *, callback_context) -> None:  # type: ignore[override]
        state: State = callback_context.state
        user_prompt = _extract_user_prompt(callback_context.user_content)
        if not user_prompt:
            LOGGER.warning(
                "No se encontró contenido textual en la solicitud del usuario;"
                " se omitirá la recuperación de conocimiento."
            )
            state[self.state_key] = []
            return None

        LOGGER.info(
            "KnowledgeRetrievalCallback: ejecutando búsqueda con prompt='%s' (len=%d), backend=%s, modelo=%s",
            user_prompt[:120].replace("\n", " "),
            len(user_prompt),
            getattr(self.embedding_config, "backend", None),
            getattr(self.embedding_config, "model", None),
        )
        try:
            response = self.client.search(
                query_text=user_prompt,
                limit=self.limit,
                embedding_config=self.embedding_config,
            )
        except VectorServiceError as exc:
            LOGGER.error("Fallo consultando servicio vectorial: %s", exc)
            state[self.state_key] = []
            return None

        hits = response.get("hits", [])
        LOGGER.info(
            "KnowledgeRetrievalCallback: Qdrant devolvió %d resultados",
            len(hits),
        )
        contexts: list[dict[str, Any]] = []
        for hit in hits:
            payload = hit.get("payload") or {}
            text = payload.get("text") or payload.get("chunk")
            if not text:
                continue
            metadata = {k: v for k, v in payload.items() if k not in {"text", "chunk"}}
            score = hit.get("score")
            contexts.append(
                {
                    "text": text,
                    "score": score,
                    "metadata": metadata,
                }
            )

        state["knowledge_query"] = user_prompt
        state[self.state_key] = contexts
        return None


knowledge_retriever = LlmAgent(
    name="knowledge_retriever",
    model=MODEL_NAME,
    description="Resume el contexto recuperado desde Qdrant para el resto del pipeline.",
    instruction="""
        En session_state['knowledge_context'] tienes una lista de fragmentos recuperados,
        cada uno con 'text', 'score' y 'metadata'.
        Devuelve sólo un JSON con el formato {
            "summary": str,
            "chunks": [
                {"text": str, "score": float, "metadata": {...}, "insights": [str, ...]}
            ],
            "usage_tips": [str, ...]
        }
        - "summary": síntesis en ≤80 palabras.
        - "chunks": selecciona hasta 3 fragmentos relevantes y resume su aporte.
        - "usage_tips": recomendaciones concretas de cómo usar la información recuperada.
        Si knowledge_context está vacío, devuelve {"summary": "", "chunks": [], "usage_tips": []}.
    """,
    output_key="knowledge_summary",
    before_agent_callback=[KnowledgeRetrievalCallback()],
)


__all__ = ["knowledge_retriever"]

