"""Modelos para gestión de artículos científicos."""

from __future__ import annotations

import uuid

from django.db import models


class ClinicalPaper(models.Model):
    """
    Artículo científico almacenado en AWS S3.

    Este modelo gestiona la metadata de papers científicos (PDFs)
    que están almacenados en S3 y son utilizados como referencia
    para las recomendaciones de IA basadas en evidencia clínica.
    """

    # Identificador único
    doc_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_index=True,
        help_text="Identificador único del documento."
    )

    # -------------------------------------------------------------------------
    # INFORMACIÓN BIBLIOGRÁFICA
    # -------------------------------------------------------------------------
    title = models.CharField(
        max_length=500,
        help_text="Título del artículo científico."
    )

    authors = models.TextField(
        help_text="Autores del artículo (separados por comas o formato libre)."
    )

    journal = models.CharField(
        max_length=200,
        blank=True,
        help_text="Nombre del journal o revista científica."
    )

    publication_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Año de publicación."
    )

    doi = models.CharField(
        max_length=100,
        blank=True,
        unique=True,
        null=True,
        help_text="Digital Object Identifier (DOI) del artículo."
    )

    abstract = models.TextField(
        blank=True,
        help_text="Abstract o resumen del artículo."
    )

    keywords = models.JSONField(
        default=list,
        blank=True,
        help_text="Palabras clave del artículo."
    )

    # -------------------------------------------------------------------------
    # ALMACENAMIENTO EN S3
    # -------------------------------------------------------------------------
    s3_key = models.CharField(
        max_length=500,
        unique=True,
        db_index=True,
        help_text="Ruta completa del archivo en S3 (key)."
    )

    s3_bucket = models.CharField(
        max_length=100,
        help_text="Nombre del bucket S3."
    )

    s3_region = models.CharField(
        max_length=50,
        default='us-east-1',
        help_text="Región de AWS donde está el bucket."
    )

    file_size_bytes = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Tamaño del archivo en bytes."
    )

    # -------------------------------------------------------------------------
    # CLASIFICACIÓN Y BÚSQUEDA
    # -------------------------------------------------------------------------
    topics = models.JSONField(
        default=list,
        blank=True,
        db_index=True,
        help_text=(
            "Topics biomédicos asignados automáticamente "
            "(ej. ['cardiology', 'nutrition', 'diabetes'])."
        )
    )

    # -------------------------------------------------------------------------
    # QUALITY ASSESSMENT (Analizado por Gemini)
    # -------------------------------------------------------------------------
    # Nivel de evidencia científica (1=más bajo, 5=más alto)
    # 5: Meta-análisis/Systematic Reviews
    # 4: RCT (Randomized Controlled Trials)
    # 3: Cohorte/Caso-Control
    # 2: Series de casos
    # 1: Opinión de expertos/Case reports
    evidence_level = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Nivel de evidencia científica (1-5). 5=Meta-análisis, 1=Opinión experta."
    )

    # Calidad metodológica (1-10)
    quality_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        db_index=True,
        help_text="Calidad metodológica del estudio (1.0-10.0). Evaluado por Gemini."
    )

    # Confiabilidad/rigor (1-10)
    reliability_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Nivel de confiabilidad/rigor del estudio (1.0-10.0)."
    )

    # Relevancia clínica (1-10)
    clinical_relevance = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Relevancia para práctica clínica (1.0-10.0)."
    )

    # Tipo de estudio
    study_type = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        help_text="Tipo de estudio (Meta-analysis, RCT, Cohort, Review, etc)."
    )

    # Tamaño de muestra (si aplica)
    sample_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Tamaño de muestra del estudio."
    )

    # Impact factor del journal (si está disponible)
    impact_factor = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Impact factor del journal (si disponible)."
    )

    # Resumen de hallazgos clave (generado por Gemini)
    key_findings = models.TextField(
        blank=True,
        help_text="Resumen de hallazgos clave del paper (generado por IA)."
    )

    # Limitaciones identificadas (generado por Gemini)
    limitations = models.TextField(
        blank=True,
        help_text="Limitaciones identificadas del estudio (generado por IA)."
    )

    # Score compuesto para ranking
    # Calculado como: (evidence_level * 0.3) + (quality_score * 0.4) + (reliability_score * 0.3)
    composite_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        db_index=True,
        help_text="Score compuesto para ranking (calculado automáticamente)."
    )

    # -------------------------------------------------------------------------
    # METADATA DE GESTIÓN
    # -------------------------------------------------------------------------
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de carga del documento."
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Última actualización de metadata."
    )

    uploaded_by = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID del usuario que subió el documento."
    )

    is_public = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Si es público, cualquier profesional puede acceder."
    )

    # -------------------------------------------------------------------------
    # METADATA ADICIONAL
    # -------------------------------------------------------------------------
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadata adicional flexible (citations, impact_factor, etc)."
    )

    class Meta:
        db_table = 'clinical_papers'
        ordering = ['-publication_year', '-uploaded_at']
        verbose_name = 'Artículo Científico'
        verbose_name_plural = 'Artículos Científicos'
        indexes = [
            models.Index(fields=['publication_year', 'journal']),
            models.Index(fields=['uploaded_at']),
            models.Index(fields=['is_public']),
        ]

    def __str__(self):
        return f"{self.title} ({self.publication_year or 'N/A'})"

    def get_s3_url(self) -> str:
        """
        Retorna la URL base de S3 (sin presigned, solo para referencia).
        """
        return f"https://{self.s3_bucket}.s3.{self.s3_region}.amazonaws.com/{self.s3_key}"

    def has_doi(self) -> bool:
        """Verifica si el artículo tiene DOI asignado."""
        return bool(self.doi)

    def calculate_composite_score(self) -> float | None:
        """
        Calcula el score compuesto para ranking basado en:
        - Evidence Level (30%)
        - Quality Score (40%)
        - Reliability Score (30%)

        Returns:
            float: Score compuesto (0-10) o None si faltan datos
        """
        if not all([self.evidence_level, self.quality_score, self.reliability_score]):
            return None

        # Normalizar evidence_level a escala 0-10
        evidence_normalized = (self.evidence_level / 5.0) * 10.0

        # Calcular promedio ponderado
        composite = (
            (evidence_normalized * 0.3) +
            (float(self.quality_score) * 0.4) +
            (float(self.reliability_score) * 0.3)
        )

        return round(composite, 2)

    def save(self, *args, **kwargs):
        """Override save para calcular composite_score automáticamente."""
        # Calcular composite score si hay datos
        calculated_score = self.calculate_composite_score()
        if calculated_score is not None:
            self.composite_score = calculated_score

        super().save(*args, **kwargs)

    def get_quality_badge(self) -> str:
        """
        Retorna un badge visual basado en el composite_score.

        Returns:
            str: Emoji representando la calidad
        """
        if not self.composite_score:
            return "⚪"

        score = float(self.composite_score)
        if score >= 8.5:
            return "🟢"  # Excelente
        elif score >= 7.0:
            return "🟡"  # Bueno
        elif score >= 5.0:
            return "🟠"  # Moderado
        else:
            return "🔴"  # Bajo
