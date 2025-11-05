from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, MutableMapping, Optional

from infra import ServiceSettings, get_settings
from infra.env import load_environment
from holistic_agent import (
    holistic_coordinator,
    mental_guardian,
    physical_guardian,
    spiritual_guardian,
)

from .agent_executor import AgentExecutor, AgentExecutionResult
from .exceptions import AgentExecutionError, ServiceError, UnsupportedCategoryError, VectorQueryError
from .vector_queries import VectorQueryRecord, VectorQueryRunner

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AdviceRequest:
    trace_id: str
    category: str
    user_profile: Mapping[str, Any]
    preferences: Optional[Mapping[str, Any]]
    context: Any = None


@dataclass(frozen=True, slots=True)
class AgentDefinition:
    name: str
    category: str
    dimension: str
    agent_entry: Any
    app_name: str
    fallback: bool = False


class HolisticAdviceService:
    """Orquesta la selección de agentes, consultas vectoriales y ensamblado de respuestas."""

    SUPPORTED_CATEGORIES = {"mind", "body", "soul", "holistic"}

    def __init__(
        self,
        *,
        settings: Optional[ServiceSettings] = None,
        vector_runner: Optional[VectorQueryRunner] = None,
    ) -> None:
        load_environment(override=False)
        self._settings = settings or get_settings()
        self._vector_runner = vector_runner or VectorQueryRunner(settings=self._settings)
        self._agents = {
            "mind": AgentDefinition(
                name="mental_guardian",
                category="mind",
                dimension="mente",
                agent_entry=mental_guardian,
                app_name="mental_guardian",
            ),
            "body": AgentDefinition(
                name="physical_guardian",
                category="body",
                dimension="cuerpo",
                agent_entry=physical_guardian,
                app_name="physical_guardian",
            ),
            "soul": AgentDefinition(
                name="spiritual_guardian",
                category="soul",
                dimension="alma",
                agent_entry=spiritual_guardian,
                app_name="spiritual_guardian",
            ),
            "holistic": AgentDefinition(
                name="holistic_coordinator",
                category="holistic",
                dimension="integral",
                agent_entry=holistic_coordinator,
                app_name="holistic_agent",
                fallback=True,
            ),
        }
        self._category_aliases = {
            "mente": "mind",
            "mental": "mind",
            "cuerpo": "body",
            "fisico": "body",
            "físico": "body",
            "alma": "soul",
            "espiritual": "soul",
            "holistico": "holistic",
            "holístico": "holistic",
            "integral": "holistic",
            "overall": "holistic",
            "general": "holistic",
        }

    @property
    def settings(self) -> ServiceSettings:
        return self._settings

    def generate_advice(self, request: AdviceRequest) -> dict[str, Any]:
        logger.info(
            "HolisticAdviceService: inicio de ejecución",
            extra={"trace_id": request.trace_id, "category": request.category},
        )

        agent = self._select_agent(request.category)
        prompt = self._build_prompt(
            category=agent.category,
            user_profile=request.user_profile,
            preferences=request.preferences,
            context=request.context,
        )

        vector_records: list[VectorQueryRecord] = []
        if prompt:
            logger.info(
                "HolisticAdviceService: ejecutando búsqueda vectorial",
                extra={"trace_id": request.trace_id, "category": agent.category},
            )
            vector_records = self._run_vector_query(
                trace_id=request.trace_id,
                query_text=prompt,
            )
        else:
            logger.info(
                "HolisticAdviceService: se omite consulta vectorial (sin contexto)",
                extra={"trace_id": request.trace_id, "category": agent.category},
            )

        result = self._run_agent(
            request=request,
            agent=agent,
            prompt=prompt or f"Genera recomendaciones para la dimensión {agent.dimension}.",
            vector_records=vector_records,
        )

        normalized = self._normalize_agent_output(dict(result), dimension=agent.dimension)
        agent_runs = [
            {
                "agent_name": agent.name,
                "status": "completed",
                "latency_ms": result.latency_ms,
                "input_context": self._build_input_context(
                    request=request,
                    prompt=prompt,
                    vector_records=vector_records,
                ),
                "output_payload": {
                    "raw_text": result.raw_text,
                    "structured": normalized["raw"],
                },
                "vector_queries": [record.to_dict() for record in vector_records],
            }
        ]

        response = {
            "status": "success",
            "data": {
                "summary": normalized["summary"],
                "recommendations": normalized["recommendations"],
                "agent_runs": agent_runs,
            },
            "error": None,
            "meta": {
                "trace_id": request.trace_id,
                "model_version": self._settings.model_version,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

        logger.info(
            "HolisticAdviceService: ejecución completada",
            extra={
                "trace_id": request.trace_id,
                "agent_name": agent.name,
                "latency_ms": result.latency_ms,
            },
        )
        return response

    # ------------------------------------------------------------------ #
    # Internos

    def _select_agent(self, category: str) -> AgentDefinition:
        normalized = (category or "").strip().lower()
        mapped = self._category_aliases.get(normalized, normalized)
        if mapped in self._agents:
            return self._agents[mapped]
        raise UnsupportedCategoryError(category=category)

    def _run_vector_query(self, *, trace_id: str, query_text: str) -> list[VectorQueryRecord]:
        try:
            return self._vector_runner.run(
                trace_id=trace_id,
                query_text=query_text,
                top_k=self._settings.vector_top_k,
            )
        except VectorQueryError:
            raise
        except ServiceError:
            raise
        except Exception as exc:  # pragma: no cover - defensivo
            logger.exception(
                "HolisticAdviceService: error inesperado al consultar vector store",
                extra={"trace_id": trace_id},
            )
            raise VectorQueryError(message="Error inesperado al consultar la base vectorial.") from exc

    def _run_agent(
        self,
        *,
        request: AdviceRequest,
        agent: AgentDefinition,
        prompt: str,
        vector_records: list[VectorQueryRecord],
    ) -> AgentExecutionResult:
        initial_state = self._build_initial_state(vector_records)
        user_id = (
            request.user_profile.get("id")
            or request.user_profile.get("auth_user_id")
            or request.user_profile.get("user_id")
            or request.trace_id
        )
        executor = AgentExecutor(agent=agent.agent_entry, app_name=agent.app_name)

        try:
            return executor.run(
                trace_id=request.trace_id,
                user_id=str(user_id),
                prompt=prompt,
                initial_state=initial_state if initial_state else None,
            )
        except ServiceError:
            raise
        except Exception as exc:
            logger.exception(
                "HolisticAdviceService: fallo ejecutando agente",
                extra={"trace_id": request.trace_id, "agent_name": agent.name},
            )
            raise AgentExecutionError(
                message="No fue posible completar la ejecución del agente.",
                details={"reason": str(exc)},
            ) from exc

    def _normalize_agent_output(self, payload: Mapping[str, Any], *, dimension: str) -> dict[str, Any]:
        summary = self._extract_summary(payload)
        recommendations = self._extract_recommendations(payload, dimension=dimension)
        return {
            "summary": summary,
            "recommendations": recommendations,
            "raw": payload,
        }

    @staticmethod
    def _extract_summary(payload: Mapping[str, Any]) -> str:
        summary = payload.get("summary")

        if isinstance(summary, str) and summary.strip():
            return summary.strip()

        if isinstance(summary, Mapping):
            for key in ("message", "text", "description", "summary"):
                value = summary.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

        if isinstance(summary, Iterable) and not isinstance(summary, (str, bytes)):
            joined = " ".join(str(item) for item in summary if item)
            if joined.strip():
                return joined.strip()

        # Fallback con acciones si existen.
        actions = payload.get("actions")
        if isinstance(actions, list) and actions:
            first = actions[0]
            if isinstance(first, str):
                return first.strip()
            if isinstance(first, Mapping):
                for key in ("description", "summary", "text"):
                    value = first.get(key)
                    if isinstance(value, str) and value.strip():
                        return value.strip()

        raw_text = payload.get("raw_text")
        if isinstance(raw_text, str) and raw_text.strip():
            return raw_text.strip()

        return "Se generó un plan preliminar basado en la información disponible."

    def _extract_recommendations(
        self,
        payload: Mapping[str, Any],
        *,
        dimension: str,
    ) -> list[dict[str, Any]]:
        raw_recommendations = payload.get("recommendations")
        if not raw_recommendations:
            raw_recommendations = payload.get("actions")

        normalized: list[dict[str, Any]] = []

        if isinstance(raw_recommendations, Mapping):
            raw_recommendations = list(raw_recommendations.values())

        if isinstance(raw_recommendations, Iterable) and not isinstance(raw_recommendations, (str, bytes)):
            for idx, item in enumerate(raw_recommendations, start=1):
                title = f"Recomendación #{idx}"
                description: str | None = None
                confidence: float | None = None
                metadata: dict[str, Any] = {}

                if isinstance(item, Mapping):
                    for key in ("description", "summary", "text", "action", "message"):
                        value = item.get(key)
                        if isinstance(value, str) and value.strip():
                            description = value.strip()
                            break
                    confidence_raw = item.get("confidence") or item.get("score")
                    if isinstance(confidence_raw, (int, float)):
                        confidence = float(confidence_raw)
                    if "title" in item and isinstance(item["title"], str):
                        title = item["title"]
                    metadata = {
                        key: value
                        for key, value in item.items()
                        if key not in {"description", "summary", "text", "action", "message", "confidence", "score", "title"}
                    }
                elif isinstance(item, str):
                    description = item.strip()

                if description:
                    normalized.append(
                        {
                            "title": title,
                            "description": description,
                            "dimension": dimension,
                            "confidence": round(confidence, 4) if confidence is not None else None,
                            "metadata": metadata,
                        }
                    )

        return normalized or self._default_recommendations(dimension=dimension)

    @staticmethod
    def _default_recommendations(*, dimension: str) -> list[dict[str, Any]]:
        templates = {
            "mente": [
                "Introduce una pausa consciente de respiración 10 minutos antes de iniciar la jornada.",
                "Agenda una conversación semanal con tu red de apoyo para hablar de avances y bloqueos emocionales.",
            ],
            "cuerpo": [
                "Integra 20 minutos diarios de movilidad articular y activación cardiovascular ligera.",
                "Planifica menús con proteína magra y verduras de hoja para estabilizar energía durante la semana.",
            ],
            "alma": [
                "Reserva 15 minutos al día para una práctica de gratitud o journaling reflexivo.",
                "Experimenta con un ritual sencillo (velas, música suave) que conecte con tu propósito personal.",
            ],
            "integral": [
                "Sincroniza horarios de descanso, alimentación y enfoque espiritual con micro-revisiones semanales.",
                "Documenta avances clave y celebra micro logros mediante una retro semanal los viernes.",
            ],
        }
        selected = templates.get(dimension, templates["integral"])
        return [
            {
                "title": f"Acción #{idx}",
                "description": tip,
                "dimension": dimension,
                "confidence": None,
                "metadata": {},
            }
            for idx, tip in enumerate(selected, start=1)
        ]

    def _build_input_context(
        self,
        *,
        request: AdviceRequest,
        prompt: str | None,
        vector_records: list[VectorQueryRecord],
    ) -> MutableMapping[str, Any]:
        context: MutableMapping[str, Any] = {
            "category": request.category,
            "user_profile": dict(request.user_profile),
            "preferences": dict(request.preferences) if request.preferences else {},
            "context": request.context,
        }
        if prompt:
            context["prompt"] = prompt
        if vector_records:
            context["vector_query_text"] = vector_records[0].query_text
        return context

    def _build_initial_state(self, records: list[VectorQueryRecord]) -> dict[str, Any]:
        if not records:
            return {}
        state = {}
        first = records[0]
        hits = []
        for hit in first.response_payload.get("hits", []):
            payload = hit.get("payload") or {}
            text = payload.get("text") or payload.get("chunk")
            if not text:
                continue
            hits.append(
                {
                    "text": text,
                    "score": hit.get("score"),
                    "metadata": {
                        key: value
                        for key, value in payload.items()
                        if key not in {"text", "chunk"}
                    },
                }
            )
        if hits:
            state["knowledge_query"] = first.query_text
            state["knowledge_context"] = hits
        return state

    def _build_prompt(
        self,
        *,
        category: str,
        user_profile: Mapping[str, Any],
        preferences: Optional[Mapping[str, Any]],
        context: Any,
    ) -> str:
        segments: list[str] = []

        name = user_profile.get("name") or user_profile.get("full_name")
        if name:
            segments.append(f"Nombre de la persona: {name}")

        if user_profile.get("age"):
            segments.append(f"Edad: {user_profile['age']}")

        if user_profile.get("locale"):
            segments.append(f"Idioma preferido: {user_profile['locale']}")

        if goals := user_profile.get("goals"):
            if isinstance(goals, (list, tuple)):
                segments.append("Objetivos declarados: " + ", ".join(map(str, goals)))
            elif isinstance(goals, str):
                segments.append("Objetivos declarados: " + goals)

        if preferences:
            focus = preferences.get("focus") or preferences.get("primary_focus")
            if isinstance(focus, (list, tuple)):
                segments.append("Áreas prioritarias: " + ", ".join(map(str, focus)))
            elif isinstance(focus, str):
                segments.append("Áreas prioritarias: " + focus)

        if isinstance(context, str) and context.strip():
            segments.append(context.strip())
        elif isinstance(context, Mapping):
            for key in ("problem", "symptoms", "history", "notes", "query"):
                value = context.get(key)
                if isinstance(value, str) and value.strip():
                    segments.append(value.strip())
                elif isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
                    segments.extend(str(item).strip() for item in value if item)
        elif isinstance(context, Iterable) and not isinstance(context, (str, bytes)):
            segments.extend(str(item).strip() for item in context if item)

        if not segments:
            return ""

        category_label = {
            "mind": "salud mental",
            "body": "bienestar físico",
            "soul": "crecimiento espiritual",
            "holistic": "bienestar integral",
        }.get(category, category)

        preamble = (
            f"Genera un plan de recomendaciones para la dimensión {category_label}. "
            "Usa lenguaje claro, empático y estructurado."
        )

        segments.insert(0, preamble)
        prompt = "\n".join(segment for segment in segments if segment)
        return prompt[:2000]


__all__ = ["AdviceRequest", "AgentDefinition", "HolisticAdviceService"]