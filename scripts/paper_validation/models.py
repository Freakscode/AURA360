"""Modelos Pydantic para el pipeline de validación de papers."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class HolisticCategory(str, Enum):
    """Categorías holísticas principales."""

    MIND = "mente"
    BODY = "cuerpo"
    SOUL = "alma"


class PipelineStatus(str, Enum):
    """Estados posibles de un paper en el pipeline."""

    PENDING = "pending"
    VALIDATED = "validated"
    UPLOADED = "uploaded"
    INGESTED = "ingested"
    FAILED = "failed"
    REJECTED = "rejected"


class ValidationMode(str, Enum):
    """Modos de validación disponibles."""

    INTERACTIVE = "interactive"
    AUTO = "auto"
    SKIP = "skip"


class PaperMetadata(BaseModel):
    """Metadata opcional de un paper."""

    title: Optional[str] = None
    authors: Optional[List[str]] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None
    url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    mesh_terms: List[str] = Field(default_factory=list)

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1900 or v > 2100):
            raise ValueError(f"Año inválido: {v}")
        return v


class PaperEntry(BaseModel):
    """Entrada de paper con su categorización y estado en el pipeline."""

    doc_id: str
    filename: str
    local_path: Optional[Path] = None
    category: HolisticCategory
    topics: List[str] = Field(default_factory=list)
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    metadata: PaperMetadata = Field(default_factory=PaperMetadata)

    # Estados del pipeline
    validated: bool = False
    modified: bool = False
    gcs_uri: Optional[str] = None
    s3_uri: Optional[str] = None
    qdrant_point_ids: List[str] = Field(default_factory=list)
    status: PipelineStatus = PipelineStatus.PENDING

    # Tracking
    validation_timestamp: Optional[datetime] = None
    upload_timestamp: Optional[datetime] = None
    ingestion_timestamp: Optional[datetime] = None
    error_message: Optional[str] = None

    @field_validator("local_path")
    @classmethod
    def validate_local_path(cls, v: Optional[Path]) -> Optional[Path]:
        if v is not None and not isinstance(v, Path):
            return Path(v)
        return v

    @property
    def cloud_uri(self) -> Optional[str]:
        """Retorna el URI de cloud storage (GCS o S3)."""
        return self.gcs_uri or self.s3_uri

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario serializable."""
        data = self.model_dump(mode="json")
        # Convertir Path a string
        if self.local_path:
            data["local_path"] = str(self.local_path)
        return data


class ValidationResult(BaseModel):
    """Resultado de la validación de un paper."""

    paper: PaperEntry
    action: str  # validated, modified, rejected, skipped
    original_category: Optional[HolisticCategory] = None
    original_topics: List[str] = Field(default_factory=list)
    changes_made: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = None


class UploadResult(BaseModel):
    """Resultado de la subida a cloud storage."""

    doc_id: str
    success: bool
    cloud_uri: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class IngestionResult(BaseModel):
    """Resultado de la ingesta a Qdrant."""

    doc_id: str
    success: bool
    job_id: Optional[str] = None
    point_ids: List[str] = Field(default_factory=list)
    chunks_processed: int = 0
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class PipelineReport(BaseModel):
    """Reporte consolidado del pipeline."""

    # Metadata del run
    run_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    config_used: Dict[str, Any] = Field(default_factory=dict)

    # Estadísticas de validación
    total_papers: int = 0
    validated_manually: int = 0
    auto_approved: int = 0
    modified: int = 0
    rejected: int = 0
    skipped: int = 0

    # Estadísticas de upload
    upload_success: int = 0
    upload_failed: int = 0

    # Estadísticas de ingesta
    ingestion_success: int = 0
    ingestion_failed: int = 0
    total_chunks: int = 0

    # Distribución
    category_distribution: Dict[str, int] = Field(default_factory=dict)
    topic_distribution: Dict[str, int] = Field(default_factory=dict)

    # Resultados detallados
    validation_results: List[ValidationResult] = Field(default_factory=list)
    upload_results: List[UploadResult] = Field(default_factory=list)
    ingestion_results: List[IngestionResult] = Field(default_factory=list)

    # Errores
    errors: List[str] = Field(default_factory=list)

    @property
    def duration_seconds(self) -> Optional[float]:
        """Duración del pipeline en segundos."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def to_markdown(self) -> str:
        """Genera reporte en formato Markdown."""
        md = f"""# Reporte de Pipeline - {self.run_id}

## Resumen Ejecutivo

- **Inicio:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
- **Fin:** {self.end_time.strftime('%Y-%m-%d %H:%M:%S') if self.end_time else 'En curso'}
- **Duración:** {self.duration_seconds:.1f}s ({self.duration_seconds/60:.1f}min)

## Validación

- **Total papers:** {self.total_papers}
- **Validados manualmente:** {self.validated_manually}
- **Auto-aprobados:** {self.auto_approved}
- **Modificados:** {self.modified}
- **Rechazados:** {self.rejected}
- **Omitidos:** {self.skipped}

## Cloud Storage

- **Subidos exitosamente:** {self.upload_success}
- **Fallos:** {self.upload_failed}

## Qdrant

- **Ingestados exitosamente:** {self.ingestion_success}
- **Fallidos:** {self.ingestion_failed}
- **Total chunks procesados:** {self.total_chunks}

## Distribución por Categoría

"""
        for category, count in sorted(self.category_distribution.items()):
            md += f"- **{category}:** {count} papers\n"

        md += "\n## Top 10 Tópicos\n\n"
        sorted_topics = sorted(self.topic_distribution.items(), key=lambda x: x[1], reverse=True)
        for topic, count in sorted_topics[:10]:
            md += f"- **{topic}:** {count} papers\n"

        if self.errors:
            md += f"\n## Errores ({len(self.errors)})\n\n"
            for i, error in enumerate(self.errors[:20], 1):
                md += f"{i}. {error}\n"
            if len(self.errors) > 20:
                md += f"\n... y {len(self.errors) - 20} errores más.\n"

        return md


class PipelineConfig(BaseModel):
    """Configuración del pipeline unificado."""

    # Paths locales
    local_papers_dir: Path
    categorization_file: Path

    # Cloud Storage
    cloud_provider: str = "gcs"  # gcs or s3
    gcs_bucket: Optional[str] = None
    gcs_project: Optional[str] = None
    s3_bucket: Optional[str] = None
    s3_region: Optional[str] = "us-east-1"

    # Qdrant
    qdrant_url: str
    qdrant_api_key: Optional[str] = None
    qdrant_collection: str = "holistic_memory"

    # Vector DB Service
    vectordb_api_url: Optional[str] = "http://localhost:8001"

    # Validación
    validation_mode: ValidationMode = ValidationMode.INTERACTIVE
    auto_approve_threshold: float = Field(0.90, ge=0.0, le=1.0)
    batch_size: int = Field(10, ge=1, le=100)

    # Opciones
    skip_upload: bool = False
    skip_ingestion: bool = False
    dry_run: bool = False

    # Logging
    log_level: str = "INFO"
    log_file: Optional[Path] = None

    @field_validator("cloud_provider")
    @classmethod
    def validate_cloud_provider(cls, v: str) -> str:
        if v not in ["gcs", "s3"]:
            raise ValueError(f"cloud_provider debe ser 'gcs' o 's3', recibido: {v}")
        return v

    @field_validator("local_papers_dir", "categorization_file")
    @classmethod
    def validate_paths(cls, v: Path) -> Path:
        if not isinstance(v, Path):
            return Path(v)
        return v

    def validate_config(self) -> None:
        """Valida que la configuración sea consistente."""
        if self.cloud_provider == "gcs" and not self.gcs_bucket:
            raise ValueError("gcs_bucket es requerido cuando cloud_provider='gcs'")
        if self.cloud_provider == "s3" and not self.s3_bucket:
            raise ValueError("s3_bucket es requerido cuando cloud_provider='s3'")

        if not self.local_papers_dir.exists():
            raise ValueError(f"local_papers_dir no existe: {self.local_papers_dir}")

        if not self.categorization_file.exists():
            raise ValueError(f"categorization_file no existe: {self.categorization_file}")
