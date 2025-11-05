"""Modelos de datos para la aplicación de usuarios."""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class UserTier(models.TextChoices):
    """
    Enumeración de los niveles de membresía disponibles.
    Debe coincidir exactamente con la restricción CHECK en la base de datos.
    """
    FREE = 'free', 'Free'
    PREMIUM = 'premium', 'Premium'


class GlobalRole(models.TextChoices):
    """
    Rol global asociado al usuario según Supabase.
    """
    ADMIN_SISTEMA = 'AdminSistema', 'Admin. Sistema'
    ADMIN_INSTITUCION = 'AdminInstitucion', 'Admin. Institución'
    ADMIN_INSTITUCION_SALUD = 'AdminInstitucionSalud', 'Admin. Institución Salud'
    PROFESIONAL_SALUD = 'ProfesionalSalud', 'Profesional Salud'
    PACIENTE = 'Paciente', 'Paciente'
    INSTITUCION = 'Institucion', 'Institución'
    GENERAL = 'General', 'General'


class BillingPlan(models.TextChoices):
    """
    Plan comercial asignado al usuario.
    """
    INDIVIDUAL = 'individual', 'Individual'
    INSTITUTION = 'institution', 'Institution'
    CORPORATE = 'corporate', 'Corporate'
    B2B2C = 'b2b2c', 'B2B2C'
    TRIAL = 'trial', 'Trial'


class AppUser(models.Model):
    """
    Modelo de usuario de la aplicación.
    
    Este modelo refleja la tabla public.app_users en Supabase. Los campos están
    sincronizados automáticamente con auth.users mediante triggers de base de datos.
    
    Campos:
        - id: Clave sustituta para joins internos (bigserial)
        - auth_user_id: UUID que vincula con auth.users.id (clave natural)
        - full_name: Nombre completo legal del usuario
        - age: Edad en años (debe ser >= 0)
        - email: Email principal de contacto (único, case-insensitive)
        - phone_number: Teléfono opcional (formato E.164 preferido)
        - gender: Descriptor de género auto-identificado (texto libre)
        - tier: Plan de membresía ('free' | 'premium')
        - role_global: Rol primario del usuario en el ecosistema AURA365
        - is_independent: True cuando opera fuera de instituciones (B2C)
        - billing_plan: Plan comercial asignado (individual, corporate, etc.)
        - created_at: Timestamp de creación del registro
        - updated_at: Timestamp de última actualización (auto-actualizado por trigger)
    
    Nota: managed=False porque Supabase maneja las migraciones de esta tabla.
    """
    
    # Clave primaria (sustituta)
    id = models.BigAutoField(
        primary_key=True,
        help_text="Clave sustituta para joins internos"
    )
    
    # Clave natural - vincula con Supabase Auth
    auth_user_id = models.UUIDField(
        unique=True,
        db_index=True,
        help_text="Foreign key a auth.users.id para vinculación con autenticación"
    )
    
    # Campos de perfil
    full_name = models.TextField(
        help_text="Nombre completo legal mostrado en la aplicación"
    )
    
    age = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Edad en años; debe ser >= 0"
    )
    
    email = models.TextField(
        unique=True,
        db_index=True,
        help_text="Email principal de contacto. Debe ser único (case-insensitive)"
    )
    
    phone_number = models.TextField(
        null=True,
        blank=True,
        help_text="Teléfono de contacto opcional (formato E.164 preferido)"
    )
    
    gender = models.TextField(
        null=True,
        blank=True,
        help_text="Descriptor de género auto-identificado (texto libre)"
    )
    
    # Sistema de membresía
    tier = models.CharField(
        max_length=20,
        choices=UserTier.choices,
        default=UserTier.FREE,
        help_text="Plan de membresía del usuario"
    )

    role_global = models.CharField(
        max_length=32,
        choices=GlobalRole.choices,
        default=GlobalRole.GENERAL,
        help_text="Rol global asignado al usuario en el ecosistema AURA365",
    )

    is_independent = models.BooleanField(
        default=False,
        help_text="True si el usuario opera fuera de instituciones (modelo B2C).",
    )

    billing_plan = models.CharField(
        max_length=16,
        choices=BillingPlan.choices,
        default=BillingPlan.INDIVIDUAL,
        help_text="Plan comercial asignado (individual, institution, corporate, etc.).",
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp de creación del registro"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp de última actualización (auto-actualizado por trigger)"
    )
    
    class Meta:
        db_table = 'app_users'
        managed = False  # Supabase maneja las migraciones, no Django
        ordering = ['-created_at']
        verbose_name = 'Usuario de Aplicación'
        verbose_name_plural = 'Usuarios de Aplicación'
        indexes = [
            # Índices explícitos (aunque ya existen en Supabase)
            models.Index(fields=['auth_user_id'], name='idx_auth_user_id'),
            models.Index(fields=['email'], name='idx_email'),
            models.Index(fields=['role_global'], name='app_users_role_global_idx'),
            models.Index(fields=['billing_plan'], name='app_users_billing_plan_idx'),
        ]
    
    def __str__(self):
        """Representación en string del usuario."""
        return f"{self.full_name} ({self.email})"
    
    def __repr__(self):
        """Representación detallada para debugging."""
        return (
            f"<AppUser id={self.id} "
            f"auth_user_id={self.auth_user_id} "
            f"email={self.email} "
            f"tier={self.tier} "
            f"role_global={self.role_global} "
            f"billing_plan={self.billing_plan} "
            f"is_independent={self.is_independent}>"
        )
    
    @property
    def is_premium(self):
        """Helper para verificar si el usuario tiene membresía premium."""
        return self.tier == UserTier.PREMIUM
    
    @property
    def is_free(self):
        """Helper para verificar si el usuario tiene membresía gratuita."""
        return self.tier == UserTier.FREE
    
    def get_tier_display_name(self):
        """Obtiene el nombre legible del tier."""
        return self.get_tier_display()

    @property
    def global_role(self) -> GlobalRole:
        """Devuelve la enumeración del rol global."""
        try:
            return GlobalRole(self.role_global)
        except ValueError:
            return GlobalRole.GENERAL

    @property
    def billing_plan_enum(self) -> BillingPlan:
        """Devuelve la enumeración del plan comercial."""
        try:
            return BillingPlan(self.billing_plan)
        except ValueError:
            return BillingPlan.INDIVIDUAL

    @property
    def operates_independently(self) -> bool:
        """True cuando el usuario opera fuera de instituciones."""
        return bool(self.is_independent)

    @property
    def is_admin(self) -> bool:
        """Indica si el usuario posee un rol administrativo."""
        return self.global_role in {
            GlobalRole.ADMIN_SISTEMA,
            GlobalRole.ADMIN_INSTITUCION,
            GlobalRole.ADMIN_INSTITUCION_SALUD,
        }


class ReportFrequency(models.TextChoices):
    """Periodicidades soportadas para reportes programados."""

    MONTHLY = 'monthly', 'Mensual'
    WEEKLY = 'weekly', 'Semanal'
    ON_DEMAND = 'on_demand', 'Bajo demanda'


class QuotaPeriod(models.TextChoices):
    """Periodos de reinicio para cuotas de consumo."""

    DAILY = 'daily', 'Diaria'
    WEEKLY = 'weekly', 'Semanal'
    MONTHLY = 'monthly', 'Mensual'
    UNLIMITED = 'unlimited', 'Ilimitada'


class SubscriptionTier(models.Model):
    """Plan de suscripción parametrizable para usuarios."""

    code = models.CharField(
        max_length=32,
        unique=True,
        help_text="Identificador estable del plan (ej. free, core, plus, premium).",
    )
    name = models.CharField(
        max_length=64,
        help_text="Nombre legible del plan mostrado en la interfaz.",
    )
    monthly_price = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)],
        help_text="Precio mensual de referencia en USD para cálculos de facturación.",
    )
    report_frequency = models.CharField(
        max_length=16,
        choices=ReportFrequency.choices,
        default=ReportFrequency.MONTHLY,
        help_text="Frecuencia de generación automática de reportes metabólicos.",
    )
    reports_per_period = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Número máximo de reportes por periodo. Null indica ilimitado.",
    )
    realtime_interval_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=(
            "Intervalo mínimo en minutos para actualizaciones en tiempo real. "
            "Null deshabilita la funcionalidad."
        ),
    )
    chatbot_messages_per_day = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Mensajes del chatbot permitidos por día. Null indica sin acceso.",
    )
    scientific_library_access = models.BooleanField(
        default=False,
        help_text="Permite acceder a referencias de la biblioteca científica.",
    )
    preventive_recommendations = models.BooleanField(
        default=False,
        help_text="Habilita recomendaciones proactivas basadas en IA.",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Configuraciones adicionales específicas del plan.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['monthly_price']
        verbose_name = 'Plan de Suscripción'
        verbose_name_plural = 'Planes de Suscripción'

    def __str__(self):
        return f"{self.name} ({self.code})"


class UsageQuota(models.Model):
    """Regla de consumo por recurso asociada a un plan."""

    tier = models.ForeignKey(
        SubscriptionTier,
        on_delete=models.CASCADE,
        related_name='quotas',
        help_text="Plan al que pertenece la cuota.",
    )
    resource_code = models.CharField(
        max_length=64,
        help_text="Recurso controlado (ej. metabolic_report, chatbot_session).",
    )
    limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Cantidad máxima por periodo. Null representa ilimitado.",
    )
    period = models.CharField(
        max_length=16,
        choices=QuotaPeriod.choices,
        default=QuotaPeriod.MONTHLY,
        help_text="Periodo en el que se reinicia la cuota.",
    )
    notes = models.TextField(
        blank=True,
        help_text="Descripción del alcance de la cuota o excepciones.",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Campos adicionales (p. ej. intervalo horario, ventana rolling).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tier', 'resource_code')
        verbose_name = 'Cuota de Consumo'
        verbose_name_plural = 'Cuotas de Consumo'

    def __str__(self):
        limit_text = 'ilimitado' if self.limit is None else str(self.limit)
        return f"{self.tier.code}:{self.resource_code} -> {limit_text}/{self.period}"


class UsageLedger(models.Model):
    """Registro de consumos aplicados a usuarios."""

    user = models.ForeignKey(
        AppUser,
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        related_name='usage_events',
        help_text="Usuario asociado al consumo registrado.",
    )
    resource_code = models.CharField(
        max_length=64,
        help_text="Recurso consumido (ej. chatbot_session).",
    )
    amount = models.PositiveIntegerField(
        default=1,
        help_text="Cantidad consumida en el evento.",
    )
    occurred_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp en que se registró el consumo.",
    )
    quota = models.ForeignKey(
        UsageQuota,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usage_events',
        help_text="Cuota aplicada en el momento del consumo.",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Datos adicionales (p. ej. origen, identificador de reporte).",
    )

    class Meta:
        ordering = ['-occurred_at']
        verbose_name = 'Movimiento de Consumo'
        verbose_name_plural = 'Movimientos de Consumo'
        indexes = [
            models.Index(fields=['resource_code', 'occurred_at'], name='idx_usage_resource'),
            models.Index(fields=['user', 'occurred_at'], name='idx_usage_user_time'),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.resource_code} ({self.amount})"
