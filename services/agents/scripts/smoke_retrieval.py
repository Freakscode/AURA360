"""Smoke test para validar la recuperación contextual del agente holístico usando vectorial_db.

IMPORTANTE: Este test asume que el servicio vectorial ya tiene documentos indexados.
Para ingestar documentos, usa los scripts del servicio vectorial_db directamente.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import sys
from typing import Sequence

from infra.env import load_environment
from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Carga variables definidas en .env del proyecto.
load_environment(override=False)

from holistic_agent import holistic_coordinator
from infra import EmbeddingConfig, VectorServiceClient, VectorServiceConfig

APP_NAME = "holistic_smoke_test"
USER_ID = "smoke_user"
QUERY_TEXT = "Necesito recomendaciones para reducir el estrés en el trabajo"


def _print_event(event) -> None:
    parts = getattr(event.content, "parts", []) if event.content else []
    texts = [part.text for part in parts if getattr(part, "text", None)]
    if texts:
        print(f"[{event.author}] {' '.join(texts)}")


async def _run_agent_interaction(
    runner: InMemoryRunner,
    session_id: str,
    message: str,
) -> tuple[str | None, Sequence]:
    content = genai_types.Content(
        role="user",
        parts=[genai_types.Part.from_text(text=message)],
    )
    print("\n=== Ejecución del agente ADK ===")
    final_text: str | None = None
    events = []
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=content,
    ):
        events.append(event)
        _print_event(event)
        parts = getattr(event.content, "parts", []) if event.content else []
        texts = [part.text for part in parts if getattr(part, "text", None)]
        if event.is_final_response() and texts:
            final_text = " ".join(texts).strip()
    return final_text, events


async def main() -> None:
    base_url = os.getenv("VECTOR_SERVICE_URL")
    api_key = os.getenv("VECTOR_SERVICE_API_KEY")
    collection_name = os.getenv("VECTOR_SERVICE_COLLECTION_NAME")

    default_config = VectorServiceConfig()
    config = VectorServiceConfig(
        base_url=base_url or default_config.base_url,
        api_key=api_key or default_config.api_key,
        timeout=default_config.timeout,
        verify_ssl=default_config.verify_ssl,
        collection_name=collection_name or default_config.collection_name,
    )

    resolved_collection = config.collection_name
    if not resolved_collection:
        raise RuntimeError(
            "VECTOR_SERVICE_COLLECTION_NAME no está configurada. Define la colección objetivo antes de ejecutar el smoke test."
        )

    client = VectorServiceClient(config, collection_name=resolved_collection)

    embedding_model = os.getenv("EMBEDDING_MODEL") or EmbeddingConfig().model
    embedding_api_key = os.getenv("GOOGLE_API_KEY")
    embedding_backend = os.getenv("EMBEDDING_BACKEND")
    embedding_config = EmbeddingConfig(
        model=embedding_model,
        api_key=embedding_api_key,
        backend=embedding_backend,
    )

    print(f"Usando colección: {resolved_collection}")
    print("=== Prueba de búsqueda directa ===")
    search_result = client.search(
        query_text=QUERY_TEXT,
        limit=3,
        embedding_config=embedding_config,
    )
    hits = search_result.get("hits", [])
    print(f"Resultados encontrados: {len(hits)}")
    for hit in hits[:2]:
        score = hit.get("score")
        hit_id = hit.get("id")
        print(f"  - Score: {score:.3f} ID: {hit_id}")

    runner = InMemoryRunner(agent=holistic_coordinator, app_name=APP_NAME)
    session = await runner.session_service.create_session(app_name=APP_NAME, user_id=USER_ID)

    final_response, events = await _run_agent_interaction(runner, session.id, QUERY_TEXT)

    refreshed_session = await runner.session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session.id,
    )
    knowledge_context = refreshed_session.state.get("knowledge_context", [])
    knowledge_summary = refreshed_session.state.get("knowledge_summary", {})

    print("\n=== Estado final ===")
    print(
        json.dumps(
            {
                "knowledge_query": refreshed_session.state.get("knowledge_query"),
                "knowledge_context": knowledge_context,
                "knowledge_summary": knowledge_summary,
            },
            indent=2,
            ensure_ascii=False,
        )
    )

    print("\n=== Resumen final del agente ===")
    if final_response:
        print(final_response)
    else:
        print("No se recibió respuesta final del agente.")
    print(f"\nEventos totales generados: {len(list(events))}")


if __name__ == "__main__":
    asyncio.run(main())
