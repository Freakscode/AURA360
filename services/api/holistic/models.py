from __future__ import annotations

import uuid
from decimal import Decimal

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
    HOLISTIC = "holistic", "Integral"


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


class SnapshotType(models.TextChoices):
    """Tipos de snapshots de contexto de usuario."""

    MIND = "mind", "Mind"
    BODY = "body", "Body"
    SOUL = "soul", "Soul"
    HOLISTIC = "holistic", "Holistic"


class TimeframeChoices(models.TextChoices):
    """Ventanas temporales para agregación de datos."""

    SEVEN_DAYS = "7d", "7 días"
    THIRTY_DAYS = "30d", "30 días"
    NINETY_DAYS = "90d", "90 días"


class UserContextSnapshot(TimestampedModel):
    """Snapshot consolidado del contexto del usuario para RAG personalizado.

    Este modelo almacena agregaciones del estado actual del usuario que luego
    se vectorizan y se usan para búsquedas con mayor peso que el corpus general.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auth_user_id = models.UUIDField(
        db_index=True,
        help_text="ID del usuario en Supabase auth.users",
    )
    snapshot_type = models.CharField(
        max_length=16,
        choices=SnapshotType.choices,
        help_text="Tipo de snapshot: mind, body, soul, o holistic",
    )
    timeframe = models.CharField(
        max_length=8,
        choices=TimeframeChoices.choices,
        default=TimeframeChoices.SEVEN_DAYS,
        help_text="Ventana temporal de los datos agregados",
    )
    consolidated_text = models.TextField(
        help_text="Texto consolidado listo para embedding"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadata adicional específica del snapshot (stats, etc.)",
    )
    topics = models.JSONField(
        default=list,
        blank=True,
        help_text="Topics biomédicos clasificados para este snapshot",
    )
    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Score de confianza del snapshot (0.00-1.00)",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Indica si este snapshot está activo (solo uno por tipo/timeframe)",
    )

    # Tracking de vectorización
    vectorized_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp de cuando se vectorizó en Qdrant",
    )
    vector_doc_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="ID del documento en Qdrant",
    )

    # GDPR compliance
    user_consent_given = models.BooleanField(
        default=False,
        help_text="Usuario dio consentimiento para almacenar embeddings",
    )
    consent_given_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp del consentimiento",
    )

    class Meta:
        db_table = "user_context_snapshots"
        ordering = ("-created_at",)
        indexes = [
            models.Index(
                fields=["auth_user_id", "is_active"],
                name="user_context_user_active_idx",
            ),
            models.Index(
                fields=["snapshot_type", "timeframe"],
                name="user_context_type_time_idx",
            ),
            models.Index(
                fields=["vectorized_at"],
                name="user_context_vectorized_idx",
            ),
        ]
        # Solo un snapshot activo por usuario/tipo/timeframe
        constraints = [
            models.UniqueConstraint(
                fields=["auth_user_id", "snapshot_type", "timeframe"],
                condition=models.Q(is_active=True),
                name="unique_active_snapshot_per_user_type_time",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.auth_user_id}::{self.snapshot_type}::{self.timeframe}"


class MoodLevel(models.TextChoices):
    """Niveles de estado de ánimo."""

    VERY_LOW = "very_low", "Muy bajo"
    LOW = "low", "Bajo"
    MODERATE = "moderate", "Moderado"
    GOOD = "good", "Bueno"
    EXCELLENT = "excellent", "Excelente"


class MoodEntry(TimestampedModel):
    """Registro de estado de ánimo del usuario.

    Sincronizado desde la app mobile. Usado para generar snapshots de contexto mental.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auth_user_id = models.UUIDField(
        db_index=True,
        help_text="ID del usuario en Supabase auth.users",
    )
    recorded_at = models.DateTimeField(
        db_index=True,
        help_text="Timestamp cuando el usuario registró este mood",
    )
    level = models.CharField(
        max_length=16,
        choices=MoodLevel.choices,
        help_text="Nivel de estado de ánimo",
    )
    note = models.TextField(
        blank=True,
        default="",
        help_text="Nota opcional del usuario sobre su estado",
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags categorizing the mood (e.g., ['work_stress', 'tired'])",
    )

    class Meta:
        db_table = "mood_entries"
        ordering = ("-recorded_at",)
        indexes = [
            models.Index(
                fields=["auth_user_id", "recorded_at"],
                name="mood_entry_user_time_idx",
            ),
            models.Index(
                fields=["level"],
                name="mood_entry_level_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.auth_user_id}::{self.level}@{self.recorded_at}"


class UserProfileExtended(TimestampedModel):
    """Perfil extendido del usuario: IKIGAI + contexto psicosocial.

    Complementa AppUser con datos de soul/spiritual dimension.
    """

    auth_user_id = models.UUIDField(
        primary_key=True,
        help_text="ID del usuario en Supabase auth.users (1-to-1 con AppUser)",
    )

    # IKIGAI dimensions
    ikigai_passion = models.JSONField(
        default=list,
        blank=True,
        help_text="Lo que amas hacer (lista de strings)",
    )
    ikigai_mission = models.JSONField(
        default=list,
        blank=True,
        help_text="Lo que el mundo necesita (lista de strings)",
    )
    ikigai_vocation = models.JSONField(
        default=list,
        blank=True,
        help_text="Por lo que te pueden pagar (lista de strings)",
    )
    ikigai_profession = models.JSONField(
        default=list,
        blank=True,
        help_text="En lo que eres bueno (lista de strings)",
    )
    ikigai_statement = models.TextField(
        blank=True,
        default="",
        help_text="Declaración personal de propósito de vida",
    )

    # Psychosocial context
    psychosocial_context = models.TextField(
        blank=True,
        default="",
        help_text="Contexto psicosocial del usuario",
    )
    support_network = models.TextField(
        blank=True,
        default="",
        help_text="Red de apoyo del usuario",
    )
    current_stressors = models.TextField(
        blank=True,
        default="",
        help_text="Estresores actuales del usuario",
    )

    class Meta:
        db_table = "user_profiles_extended"
        ordering = ("-updated_at",)

    def __str__(self) -> str:
        return f"{self.auth_user_id}::extended_profile"


class IntakeSubmissionStatus(models.TextChoices):
    """Estados del flujo de intake holístico."""

    PENDING = "pending", "Pendiente"
    PROCESSING = "processing", "En proceso"
    READY = "ready", "Lista"
    FAILED = "failed", "Fallida"


class IntakeSubmission(TimestampedModel):
    """Registro de una entrevista/ formulario inicial enviado por un usuario."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auth_user_id = models.UUIDField(
        db_index=True,
        help_text="ID del usuario en Supabase auth.users",
    )
    trace_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="Identificador de trazabilidad para correlacionar etapas del pipeline.",
    )
    answers = models.JSONField(
        default=dict,
        blank=True,
        help_text="Mapa question_id -> valor normalizado del cuestionario (12 reactivos).",
    )
    free_text = models.CharField(
        max_length=280,
        blank=True,
        default="",
        help_text="Campo libre final provisto por el participante (máx. 280 caracteres).",
    )
    status = models.CharField(
        max_length=16,
        choices=IntakeSubmissionStatus.choices,
        default=IntakeSubmissionStatus.PENDING,
        help_text="Estado actual del procesamiento del intake.",
    )
    processing_stage = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Última etapa completada (ej. collected, contextualized, report_ready).",
    )
    vectorize_snapshot = models.BooleanField(
        default=True,
        help_text="Si es True, el snapshot holístico generado se vectoriza en Qdrant.",
    )
    estimated_wait_seconds = models.PositiveSmallIntegerField(
        default=60,
        help_text="Tiempo estimado de espera mostrado al usuario.",
    )
    report_url = models.URLField(
        max_length=512,
        blank=True,
        null=True,
        help_text="URL firmada del PDF personalizado, si ya está disponible.",
    )
    report_storage_path = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Ruta interna en el storage donde vive el PDF final.",
    )
    report_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadata adicional del reporte (checksum, número de páginas, etc.).",
    )
    failure_reason = models.TextField(
        blank=True,
        default="",
        help_text="Descripción breve del fallo cuando status=failed.",
    )
    last_error_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp del último error registrado para este intake.",
    )

    class Meta:
        db_table = "intake_submissions"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["auth_user_id", "status"], name="intake_user_status_idx"),
            models.Index(fields=["trace_id"], name="intake_trace_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.auth_user_id}::intake::{self.id}"
