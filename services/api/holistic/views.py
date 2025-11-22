from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from django.conf import settings
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    HolisticAgentProfile,
    HolisticAgentRunStatus,
    HolisticRequest,
    HolisticRequestStatus,
)
from .serializers import HolisticAdviceRequestSerializer, HolisticAdviceResponseSerializer
from .services import (
    call_agent_service,
    create_agent_run,
    fetch_user_profile,
    persist_vector_queries,
)

logger = logging.getLogger(__name__)


class HolisticAdviceView(APIView):
    """Endpoint principal para orquestar la asesoría holística."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        request_serializer = HolisticAdviceRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        payload = request_serializer.validated_data

        trace_id = uuid.uuid4()
        user_id: str = payload["user_id"]
        category: str = payload["category"]
        metadata: dict[str, Any] = payload.get("metadata", {})

        logger.info(
            "Solicitud holística recibida.",
            extra={
                "trace_id": str(trace_id),
                "holistic_user_id": user_id,
                "holistic_category": category,
            },
        )

        holistic_request = HolisticRequest.objects.create(
            user_id=user_id,
            category=category,
            status=HolisticRequestStatus.PENDING,
            trace_id=trace_id,
            request_payload={
                "user_id": user_id,
                "category": category,
                "metadata": metadata,
            },
        )

        user_profile = fetch_user_profile(user_id)
        agent_profile = (
            HolisticAgentProfile.objects.filter(category=category, is_active=True)
            .order_by("-version")
            .first()
        )

        if agent_profile is None:
            logger.warning(
                "No existe HolisticAgentProfile activo para la categoría solicitada.",
                extra={"trace_id": str(trace_id), "holistic_category": category},
            )
            holistic_request.status = HolisticRequestStatus.FAILED
            holistic_request.error_type = "agent_profile_not_found"
            holistic_request.save(update_fields=["status", "error_type", "updated_at"])
            response_serializer = HolisticAdviceResponseSerializer(
                data={
                    "trace_id": str(trace_id),
                    "status": HolisticRequestStatus.FAILED,
                    "result": None,
                    "error": {
                        "type": "agent_profile_not_found",
                        "message": str(_("No hay perfil de agente disponible para la categoría solicitada.")),
                    },
                }
            )
            response_serializer.is_valid(raise_exception=True)
            return Response(response_serializer.data, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        agent_payload = {
            "trace_id": str(trace_id),
            "user": user_profile,
            "category": category,
            "metadata": metadata,
            "request_context": holistic_request.request_payload,
            "agent_profile": {
                "primary_agent": agent_profile.primary_agent,
                "fallback_agents": agent_profile.fallback_agents,
                "embedding_model": agent_profile.embedding_model,
                "prompt_template": agent_profile.prompt_template,
                "version": agent_profile.version,
            },
        }

        timeout = getattr(settings, "HOLISTIC_AGENT_REQUEST_TIMEOUT", 120)
        retry_delay = getattr(settings, "HOLISTIC_AGENT_RETRY_DELAY", 2)
        max_attempts = 2

        agent_response: dict[str, Any] = {}
        attempt = 0
        while attempt < max_attempts:
            agent_response = call_agent_service(agent_payload, str(trace_id), timeout=timeout)
            if agent_response.get("status") == "success":
                break

            error_type = (agent_response.get("error") or {}).get("type")
            logger.warning(
                "Fallo al invocar servicio de agentes (intento %s).",
                attempt + 1,
                extra={
                    "trace_id": str(trace_id),
                    "holistic_category": category,
                    "error_type": error_type,
                },
            )
            attempt += 1
            if attempt >= max_attempts:
                break
            if error_type not in {"timeout", "request_exception"}:
                break
            time.sleep(retry_delay)

        agent_status = agent_response.get("status")
        latency_ms = agent_response.get("latency_ms")
        agent_data = agent_response.get("data")
        agent_error = agent_response.get("error")

        run_status = HolisticAgentRunStatus.COMPLETED if agent_status == "success" else HolisticAgentRunStatus.FAILED

        with transaction.atomic():
            agent_run = create_agent_run(
                holistic_request,
                agent_name=agent_profile.primary_agent,
                status=run_status,
                latency_ms=latency_ms,
                input_context=agent_payload,
                output_payload=agent_data if agent_status == "success" else agent_error or {},
                error_type=(agent_error or {}).get("type") if agent_error else None,
            )

            if agent_status == "success":
                holistic_request.status = HolisticRequestStatus.COMPLETED
                holistic_request.response_payload = agent_data
                holistic_request.error_type = None
                holistic_request.save(
                    update_fields=["status", "response_payload", "error_type", "updated_at"]
                )
                vector_queries = (agent_data or {}).get("vector_queries") if isinstance(agent_data, dict) else None
                if vector_queries:
                    persist_vector_queries(agent_run, vector_queries)
            else:
                holistic_request.status = HolisticRequestStatus.FAILED
                holistic_request.response_payload = agent_data
                holistic_request.error_type = (agent_error or {}).get("type") if agent_error else "unknown_error"
                holistic_request.save(
                    update_fields=["status", "response_payload", "error_type", "updated_at"]
                )

        response_serializer = HolisticAdviceResponseSerializer(
            data={
                "trace_id": str(trace_id),
                "status": holistic_request.status,
                "result": agent_data if agent_status == "success" else None,
                "error": agent_error if agent_error else None,
            }
        )
        response_serializer.is_valid(raise_exception=True)

        if agent_status == "success":
            logger.info(
                "Respuesta holística generada correctamente.",
                extra={"trace_id": str(trace_id), "holistic_user_id": user_id},
            )
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        http_status = self._map_error_to_status(agent_error)
        logger.error(
            "Fallo al generar respuesta holística.",
            extra={
                "trace_id": str(trace_id),
                "holistic_user_id": user_id,
                "error_type": (agent_error or {}).get("type"),
            },
        )
        return Response(response_serializer.data, status=http_status)

    @staticmethod
    def _map_error_to_status(error: dict[str, Any] | None) -> int:
        if not error:
            return status.HTTP_500_INTERNAL_SERVER_ERROR

        error_type = error.get("type")
        if error_type == "timeout":
            return status.HTTP_504_GATEWAY_TIMEOUT
        if error_type in {"request_exception", "response_error"}:
            return status.HTTP_502_BAD_GATEWAY
        if error_type == "configuration_error":
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        return status.HTTP_500_INTERNAL_SERVER_ERROR
