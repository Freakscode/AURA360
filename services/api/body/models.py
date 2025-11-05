"""Modelos de datos para hábitos corporales."""

from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone


class TimestampedModel(models.Model):
    """Modelo base que agrega timestamps estándar."""

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp de creación."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp de última actualización."
    )

    class Meta:
        abstract = True


class ActivityType(models.TextChoices):
    """Tipos de actividad física soportados."""

    CARDIO = 'cardio', 'Cardio'
    STRENGTH = 'strength', 'Fuerza'
    FLEXIBILITY = 'flexibility', 'Flexibilidad'
    MINDFULNESS = 'mindfulness', 'Mindfulness'


class ActivityIntensity(models.TextChoices):
    """Intensidad percibida de la sesión."""

    LOW = 'low', 'Baja'
    MODERATE = 'moderate', 'Moderada'
    HIGH = 'high', 'Alta'


class MealType(models.TextChoices):
    """Momentos del día para registros de comida."""

    BREAKFAST = 'breakfast', 'Desayuno'
    LUNCH = 'lunch', 'Comida'
    DINNER = 'dinner', 'Cena'
    SNACK = 'snack', 'Snack'


class SleepQuality(models.TextChoices):
    """Calidad subjetiva del sueño."""

    POOR = 'poor', 'Deficiente'
    FAIR = 'fair', 'Regular'
    GOOD = 'good', 'Buena'
    EXCELLENT = 'excellent', 'Excelente'


class BodyActivity(TimestampedModel):
    """Sesión de actividad física registrada por un usuario."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identificador único de la sesión de actividad."
    )
    auth_user_id = models.UUIDField(
        db_index=True,
        help_text="ID del usuario en Supabase (auth.users.id)."
    )
    activity_type = models.CharField(
        max_length=32,
        choices=ActivityType.choices,
        help_text="Tipo de actividad realizada."
    )
    intensity = models.CharField(
        max_length=16,
        choices=ActivityIntensity.choices,
        default=ActivityIntensity.MODERATE,
        help_text="Intensidad percibida de la actividad."
    )
    duration_minutes = models.PositiveIntegerField(
        help_text="Duración de la sesión en minutos."
    )
    session_date = models.DateField(
        default=timezone.now,
        help_text="Fecha en la que se realizó la actividad."
    )
    notes = models.TextField(
        null=True,
        blank=True,
        help_text="Notas opcionales o contexto adicional."
    )

    class Meta:
        db_table = 'body_activities'
        ordering = ['-session_date', '-created_at']
        verbose_name = 'Actividad Física'
        verbose_name_plural = 'Actividades Físicas'


class NutritionLog(TimestampedModel):
    """Registro de ingesta alimentaria."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identificador del registro nutricional."
    )
    auth_user_id = models.UUIDField(
        db_index=True,
        help_text="ID del usuario en Supabase (auth.users.id)."
    )
    meal_type = models.CharField(
        max_length=16,
        choices=MealType.choices,
        help_text="Momento del día al que pertenece la comida."
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        help_text="Fecha y hora en la que se consumió la comida."
    )
    items = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de alimentos incluidos en la comida."
    )
    calories = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Calorías estimadas de la comida."
    )
    protein = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Proteínas (g)."
    )
    carbs = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Carbohidratos (g)."
    )
    fats = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Grasas (g)."
    )
    notes = models.TextField(
        null=True,
        blank=True,
        help_text="Notas adicionales relacionadas a la comida."
    )

    class Meta:
        db_table = 'body_nutrition_logs'
        ordering = ['-timestamp', '-created_at']
        verbose_name = 'Registro Nutricional'
        verbose_name_plural = 'Registros Nutricionales'


class SleepLog(TimestampedModel):
    """Registro de periodo de sueño."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identificador del registro de sueño."
    )
    auth_user_id = models.UUIDField(
        db_index=True,
        help_text="ID del usuario en Supabase (auth.users.id)."
    )
    bedtime = models.DateTimeField(
        help_text="Hora de irse a dormir."
    )
    wake_time = models.DateTimeField(
        help_text="Hora de despertar."
    )
    duration_hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        help_text="Duración total del sueño en horas."
    )
    quality = models.CharField(
        max_length=16,
        choices=SleepQuality.choices,
        default=SleepQuality.GOOD,
        help_text="Calidad del sueño reportada."
    )
    notes = models.TextField(
        null=True,
        blank=True,
        help_text="Notas adicionales sobre el sueño."
    )

    class Meta:
        db_table = 'body_sleep_logs'
        ordering = ['-wake_time', '-created_at']
        verbose_name = 'Registro de Sueño'
        verbose_name_plural = 'Registros de Sueño'


class NutritionPlan(TimestampedModel):
    """
    Plan nutricional estructurado para un usuario.
    
    Este modelo almacena planes completos de alimentación que incluyen:
    - Metadatos del plan (versión, vigencia, fuente)
    - Información del sujeto (usuario, demografía)
    - Evaluación y diagnóstico (métricas corporales, objetivos)
    - Directivas del plan (comidas, porciones, restricciones, sustituciones)
    - Suplementos y recomendaciones
    
    La estructura sigue el esquema JSON Schema nutrition-plan.schema.json
    y utiliza JSONField para máxima flexibilidad y extensibilidad.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identificador único del plan nutricional."
    )
    
    auth_user_id = models.UUIDField(
        db_index=True,
        help_text="ID del usuario en Supabase (auth.users.id) al que pertenece este plan."
    )
    
    # Campos principales extraídos para facilitar consultas
    title = models.CharField(
        max_length=255,
        help_text="Título del plan nutricional."
    )
    
    language = models.CharField(
        max_length=10,
        default='es',
        help_text="Idioma del plan (ISO 639-1)."
    )
    
    issued_at = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de emisión del plan."
    )
    
    valid_until = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Fecha de expiración del plan."
    )
    
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Indica si el plan está activo o archivado."
    )
    
    # Estructura completa del plan en JSON
    plan_data = models.JSONField(
        help_text=(
            "Estructura completa del plan nutricional siguiendo el esquema JSON. "
            "Incluye: plan (metadatos, source), subject (demographics), "
            "assessment (timeseries, diagnoses, goals), directives (meals, "
            "restrictions, substitutions), supplements, recommendations, "
            "activity_guidance y free_text."
        )
    )
    
    # Metadatos de origen
    source_kind = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        help_text="Tipo de fuente: pdf, image, text, web."
    )
    
    source_uri = models.TextField(
        null=True,
        blank=True,
        help_text="URI o path del documento fuente."
    )
    
    extracted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora de extracción del plan desde la fuente."
    )
    
    extractor = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="Nombre del sistema o método que extrajo el plan."
    )

    class Meta:
        db_table = 'nutrition_plans'
        ordering = ['-issued_at', '-created_at']
        verbose_name = 'Plan Nutricional'
        verbose_name_plural = 'Planes Nutricionales'
        indexes = [
            models.Index(fields=['auth_user_id', 'is_active']),
            models.Index(fields=['auth_user_id', 'valid_until']),
        ]

    def __str__(self):
        return f"{self.title} - {self.auth_user_id}"
    
    @property
    def is_valid(self):
        """Verifica si el plan aún está vigente."""
        if not self.valid_until:
            return self.is_active
        from django.utils import timezone
        return self.is_active and self.valid_until >= timezone.now().date()
    
    def get_meals(self):
        """Extrae las comidas del plan."""
        return self.plan_data.get('directives', {}).get('meals', [])
    
    def get_restrictions(self):
        """Extrae las restricciones alimentarias."""
        return self.plan_data.get('directives', {}).get('restrictions', [])
    
    def get_substitutions(self):
        """Extrae las tablas de intercambio."""
        return self.plan_data.get('directives', {}).get('substitutions', [])
    
    def get_supplements(self):
        """Extrae los suplementos recomendados."""
        return self.plan_data.get('supplements', [])
    
    def get_goals(self):
        """Extrae los objetivos nutricionales."""
        return self.plan_data.get('assessment', {}).get('goals', [])

