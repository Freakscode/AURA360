from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Mapping, Optional

from infra.env import load_environment

from google.adk.runners import InMemoryRunner
from google.adk.sessions import Session
from google.adk.sessions.state import State
from google.genai import types as genai_types

logger = logging.getLogger(__name__)


class AgentExecutionResult(dict):
    """Representa el resultado normalizado del agente."""

    raw_text: str
    latency_ms: int

    def __init__(self, payload: Mapping[str, Any], *, raw_text: str, latency_ms: int) -> None:
        super().__init__(payload)
        self.raw_text = raw_text
        self.latency_ms = latency_ms


class AgentExecutor:
    """Encapsula la ejecución de un agente Google ADK y normaliza la salida final."""

    def __init__(self, *, agent: Any, app_name: str) -> None:
        self._agent = agent
        self._app_name = app_name
        load_environment(override=False)

    def run(
        self,
        *,
        trace_id: str,
        user_id: str,
        prompt: str,
        initial_state: Optional[Mapping[str, Any]] = None,
    ) -> AgentExecutionResult:
        """Ejecuta el agente de forma síncrona (envoltorio sobre `_run_async`)."""
        return asyncio.run(self._run_async(
            trace_id=trace_id,
            user_id=user_id,
            prompt=prompt,
            initial_state=initial_state,
        ))

    async def _run_async(
        self,
        *,
        trace_id: str,
        user_id: str,
        prompt: str,
        initial_state: Optional[Mapping[str, Any]] = None,
    ) -> AgentExecutionResult:
        """Implementación asíncrona de la ejecución del agente."""
        start_time = time.perf_counter()
        runner = InMemoryRunner(self._agent, app_name=self._app_name)
        
        # Crear sesión con argumentos nombrados (keyword-only)
        session: Session = await runner.session_service.create_session(
            app_name=self._app_name,
            user_id=user_id,
            state=initial_state,
        )

        new_message = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=prompt)],
        )

        event_stream = runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=new_message,
        )

        final_text: str | None = None
        async for event in event_stream:
            is_final = getattr(event, "is_final_response", None)
            content = getattr(event, "content", None)
            if callable(is_final) and is_final() and content:
                final_text = self._content_to_text(content)
                if final_text:
                    break

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        if final_text is None or not final_text.strip():
            logger.error(
                "AgentExecutor: el agente no generó respuesta final",
                extra={"trace_id": trace_id, "app_name": self._app_name},
            )
            raise RuntimeError("El agente terminó sin producir respuesta final.")

        payload = self._parse_output(final_text, trace_id=trace_id)
        return AgentExecutionResult(payload, raw_text=final_text, latency_ms=latency_ms)

    @staticmethod
    def _content_to_text(content: genai_types.Content) -> str:
        """Convierte un contenido multimodal de Google GenAI en texto plano."""
        if not content or not getattr(content, "parts", None):
            return ""

        fragments: list[str] = []
        for part in content.parts:
            text = getattr(part, "text", None)
            if isinstance(text, str) and text.strip():
                fragments.append(text.strip())
                continue

            # Para respuestas en JSON embebido.
            function_response = getattr(part, "function_response", None)
            if function_response and getattr(function_response, "response", None):
                fragments.append(json.dumps(function_response.response))

            # Ignoramos otros tipos (audio, imágenes) para mantener simplicidad.
        return "\n\n".join(fragments).strip()

    @staticmethod
    def _parse_output(raw_text: str, *, trace_id: str) -> dict[str, Any]:
        """Intenta convertir la salida del agente a JSON, tolerando texto envolvente."""
        stripped = raw_text.strip()
        if not stripped:
            return {"summary": "", "recommendations": []}

        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            # Intento de detectar JSON dentro del texto.
            start = stripped.find("{")
            end = stripped.rfind("}")
            if start != -1 and end != -1 and end > start:
                snippet = stripped[start : end + 1]
                try:
                    return json.loads(snippet)
                except json.JSONDecodeError:
                    logger.warning(
                        "AgentExecutor: no fue posible parsear JSON desde la respuesta. Usando fallback.",
                        extra={"trace_id": trace_id, "snippet": snippet[:120]},
                    )
        return {
            "summary": stripped[:200],
            "recommendations": [],
        }


__all__ = ["AgentExecutor", "AgentExecutionResult"]