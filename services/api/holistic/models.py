from __future__ import annotations

import uuid

from django.db import models


class TimestampedModel(models.Model):
    """Modelo base con timestamps estándar."""

    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp de creación.")
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp de última actualización.",
    )

    class Meta:
        abstract = True


class HolisticCategory(models.TextChoices):
    """Categorías soportadas por los agentes holísticos."""

    MIND = "mind", "Mente"
    BODY = "body", "Cuerpo"
    SOUL = "soul", "Alma"


class HolisticRequestStatus(models.TextChoices):
    """Estados posibles de una solicitud holística."""

    PENDING = "pending", "Pendiente"
    COMPLETED = "completed", "Completada"
    FAILED = "failed", "Fallida"


class HolisticAgentRunStatus(models.TextChoices):
    """Estados de ejecución para los agentes."""

    PENDING = "pending", "Pendiente"
    RUNNING = "running", "En ejecución"
    COMPLETED = "completed", "Completada"
    FAILED = "failed", "Fallida"


class HolisticRequest(TimestampedModel):
    """Solicitud principal recibida desde el cliente."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Identificador del usuario en el sistema externo.",
    )
    category = models.CharField(
        max_length=16,
        choices=HolisticCategory.choices,
        help_text="Categoría solicitada por el cliente.",
    )
    status = models.CharField(
        max_length=16,
        choices=HolisticRequestStatus.choices,
        default=HolisticRequestStatus.PENDING,
        help_text="Estado actual de la solicitud.",
    )
    trace_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Identificador de trazabilidad correlacionado con agentes y logs.",
    )
    request_payload = models.JSONField(
        default=dict,
        help_text="Payload original recibido desde el cliente.",
    )
    response_payload = models.JSONField(
        null=True,
        blank=True,
        help_text="Respuesta final enviada al cliente.",
    )
    error_type = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="Categoría de error si la solicitud falla.",
    )

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("category",), name="holistic_request_category_idx"),
            models.Index(fields=("trace_id",), name="holistic_request_trace_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.user_id}::{self.category}::{self.trace_id}"


class HolisticAgentRun(TimestampedModel):
    """Registro de una ejecución de agente dentro de una solicitud holística."""

    request = models.ForeignKey(
        HolisticRequest,
        related_name="agent_runs",
        on_delete=models.CASCADE,
        help_text="Solicitud asociada a la ejecución del agente.",
    )
    agent_name = models.CharField(
        max_length=128,
        help_text="Nombre o identificador del agente invocado.",
    )
    status = models.CharField(
        max_length=16,
        choices=HolisticAgentRunStatus.choices,
        default=HolisticAgentRunStatus.PENDING,
        help_text="Estado actual de la ejecución del agente.",
    )
    latency_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Latencia total de la ejecución del agente en milisegundos.",
    )
    input_context = models.JSONField(
        default=dict,
        blank=True,
        help_text="Contexto estructurado enviado al agente.",
    )
    output_payload = models.JSONField(
        default=dict,
        blank=True,
        help_text="Respuesta cruda retornada por el agente.",
    )
    error_type = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="Categoría de error si la ejecución falló.",
    )

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("agent_name",), name="holistic_agent_run_agent_idx"),
            models.Index(fields=("status",), name="holistic_agent_run_status_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.agent_name}::{self.status}"


class HolisticVectorQuery(TimestampedModel):
    """Auditoría de consultas vectoriales realizadas por los agentes."""

    agent_run = models.ForeignKey(
        HolisticAgentRun,
        related_name="vector_queries",
        on_delete=models.CASCADE,
        help_text="Ejecución de agente asociada a la consulta vectorial.",
    )
    vector_store = models.CharField(
        max_length=128,
        help_text="Nombre del almacén vectorial utilizado.",
    )
    embedding_model = models.CharField(
        max_length=128,
        help_text="Modelo de embeddings utilizado para la consulta.",
    )
    query_text = models.TextField(help_text="Texto de la consulta realizada.")
    top_k = models.PositiveIntegerField(
        default=5,
        help_text="Número de resultados solicitados al servicio vectorial.",
    )
    response_payload = models.JSONField(
        default=dict,
        blank=True,
        help_text="Respuesta completa del servicio vectorial.",
    )
    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Confianza agregada de los resultados retornados.",
    )

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("vector_store",), name="holistic_vector_store_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.vector_store}::{self.embedding_model}"


class HolisticAgentProfile(TimestampedModel):
    """Configuración de agentes por categoría."""

    category = models.CharField(
        max_length=16,
        choices=HolisticCategory.choices,
        help_text="Categoría a la que aplica el perfil de agente.",
    )
    primary_agent = models.CharField(
        max_length=128,
        help_text="Identificador del agente principal a invocar.",
    )
    fallback_agents = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de agentes alternos en orden de prioridad.",
    )
    embedding_model = models.CharField(
        max_length=128,
        help_text="Modelo de embeddings recomendado para la categoría.",
    )
    prompt_template = models.TextField(
        help_text="Plantilla de prompt base utilizada por el agente.",
    )
    version = models.CharField(
        max_length=32,
        default="1.0.0",
        help_text="Versión de la configuración del perfil.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indica si el perfil está activo para su categoría.",
    )

    class Meta:
        ordering = ("category", "-version")
        unique_together = ("category", "version")
        indexes = [
            models.Index(fields=("category", "is_active"), name="holistic_profile_active_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.category}::{self.version}"
