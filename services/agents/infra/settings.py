from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Ruta absoluta al directorio raíz del proyecto (donde está .env)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class ServiceSettings(BaseSettings):
    """Configuración central del servicio de agentes holísticos."""

    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),  # Ruta absoluta al .env del proyecto
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",  # Ignora variables de entorno no definidas en el modelo
    )

    app_name: str = Field(default="agents-service")
    model_version: str = Field(
        default="1.0.0",
        validation_alias=AliasChoices("AGENT_SERVICE_MODEL_VERSION", "agent_service_model_version"),
    )

    vector_service_url: str = Field(
        default="http://localhost:6333",
        validation_alias=AliasChoices("AGENT_SERVICE_QDRANT_URL", "agent_service_qdrant_url"),
    )
    vector_service_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("AGENT_SERVICE_QDRANT_API_KEY", "agent_service_qdrant_api_key"),
    )
    vector_collection_name: str = Field(
        default="holistic_agents",
        validation_alias=AliasChoices("AGENT_SERVICE_VECTOR_COLLECTION", "agent_service_vector_collection"),
    )
    vector_timeout: float = Field(
        default=30.0,
        validation_alias=AliasChoices("AGENT_SERVICE_TIMEOUT", "agent_service_timeout"),
    )
    vector_verify_ssl: bool = Field(
        default=True,
        validation_alias=AliasChoices("AGENT_SERVICE_VECTOR_VERIFY_SSL", "agent_service_vector_verify_ssl"),
    )
    vector_top_k: int = Field(
        default=5,
        validation_alias=AliasChoices("AGENT_SERVICE_VECTOR_TOP_K", "agent_service_vector_top_k"),
    )
    vector_store_name: str = Field(
        default="qdrant",
        validation_alias=AliasChoices("AGENT_SERVICE_VECTOR_STORE_NAME", "agent_service_vector_store_name"),
    )
    vector_retry_attempts: int = Field(
        default=2,
        validation_alias=AliasChoices("AGENT_SERVICE_VECTOR_RETRIES", "agent_service_vector_retries"),
    )
    vector_retry_backoff_seconds: float = Field(
        default=1.0,
        validation_alias=AliasChoices("AGENT_SERVICE_VECTOR_BACKOFF", "agent_service_vector_backoff"),
    )

    embedding_model: str = Field(
        default="text-embedding-3-small",
        validation_alias=AliasChoices("AGENT_DEFAULT_EMBEDDING_MODEL", "agent_default_embedding_model"),
    )
    embedding_backend: str | None = Field(
        default=None,
        validation_alias=AliasChoices("AGENT_SERVICE_EMBEDDING_BACKEND", "agent_service_embedding_backend"),
    )
    embedding_normalize: bool = Field(
        default=True,
        validation_alias=AliasChoices("AGENT_SERVICE_EMBEDDING_NORMALIZE", "agent_service_embedding_normalize"),
    )
    embedding_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("AGENT_SERVICE_EMBEDDING_API_KEY", "agent_service_embedding_api_key"),
    )

    default_recommendation_horizon_days: int = Field(
        default=21,
        validation_alias=AliasChoices(
            "AGENT_SERVICE_RECOMMENDATION_HORIZON_DAYS", "agent_service_recommendation_horizon_days"
        ),
    )

    @model_validator(mode="after")
    def _apply_legacy_envs(self) -> "ServiceSettings":
        """Soporta variables heredadas del servicio original."""
        legacy_url = os.getenv("VECTOR_SERVICE_URL") or os.getenv("QDRANT_URL")
        if legacy_url and not self.vector_service_url:
            object.__setattr__(self, "vector_service_url", legacy_url)

        legacy_key = os.getenv("VECTOR_SERVICE_API_KEY") or os.getenv("QDRANT_API_KEY")
        if legacy_key and not self.vector_service_api_key:
            object.__setattr__(self, "vector_service_api_key", legacy_key)

        legacy_collection = (
            os.getenv("VECTOR_SERVICE_COLLECTION_NAME")
            or os.getenv("HOLISTIC_VECTOR_COLLECTION_NAME")
        )
        if legacy_collection and not self.vector_collection_name:
            object.__setattr__(self, "vector_collection_name", legacy_collection)

        legacy_timeout = os.getenv("VECTOR_SERVICE_TIMEOUT")
        if legacy_timeout and not os.getenv("AGENT_SERVICE_TIMEOUT"):
            try:
                object.__setattr__(self, "vector_timeout", float(legacy_timeout))
            except ValueError:
                pass

        legacy_verify_ssl = os.getenv("VECTOR_SERVICE_VERIFY_SSL")
        if legacy_verify_ssl and not os.getenv("AGENT_SERVICE_VECTOR_VERIFY_SSL"):
            lowered = legacy_verify_ssl.lower()
            object.__setattr__(self, "vector_verify_ssl", lowered not in {"false", "0"})

        legacy_model = os.getenv("EMBEDDING_MODEL")
        if legacy_model and not self.embedding_model:
            object.__setattr__(self, "embedding_model", legacy_model)

        legacy_backend = os.getenv("EMBEDDING_BACKEND")
        if legacy_backend and not self.embedding_backend:
            object.__setattr__(self, "embedding_backend", legacy_backend)

        legacy_normalize = os.getenv("EMBEDDING_NORMALIZE")
        if legacy_normalize and not os.getenv("AGENT_SERVICE_EMBEDDING_NORMALIZE"):
            lowered = legacy_normalize.lower()
            object.__setattr__(self, "embedding_normalize", lowered not in {"false", "0"})

        return self

    @field_validator("vector_retry_attempts")
    @classmethod
    def _ensure_retry_attempts(cls, value: int) -> int:
        return max(1, value)

    @field_validator("vector_top_k")
    @classmethod
    def _ensure_vector_top_k(cls, value: int) -> int:
        return max(1, value)

    @property
    def resolved_embedding_api_key(self) -> str | None:
        """Devuelve la API key final para embeddings, usando GOOGLE_API_KEY como fallback."""
        return self.embedding_api_key or os.getenv("GOOGLE_API_KEY")


# Dominios de conocimiento especializados por Guardian
GUARDIAN_KNOWLEDGE_DOMAINS = {
    "mental": [
        "mental_health",
        "cognitive_function",
        "neurodegeneration",
        "stress_response",
        "neuroendocrine",
        "metabolic_brain",
        "chronic_pain",
    ],
    "physical": [
        "nutrition",
        "exercise_physiology",
        "sleep_health",
        "circadian_rhythm",
        "sleep_deprivation",
        "insomnia",
        "hypersomnia",
        "obstructive_sleep_apnea",
        "sleep_medicine",
        "gut_microbiome",
        "metabolism_disorders",
        "obesity",
        "type2_diabetes",
        "insulin_signaling",
        "cardiovascular_health",
        "chrononutrition",
        "liver_health",
        "immunometabolism",
        "endocrine_disorders",
        "inflammation",
        "oxidative_stress",
    ],
    "spiritual": [
        "aging_longevity",
        "mental_health",  # Overlap with mental for holistic approach
        "stress_response",  # Overlap with mental for holistic approach
        "reproductive_health",
        "pcos",
        "adolescent_health",
    ],
}


@lru_cache(maxsize=1)
def get_settings() -> ServiceSettings:
    """Retorna la configuración cacheada del servicio."""
    return ServiceSettings()


__all__ = ["ServiceSettings", "get_settings", "GUARDIAN_KNOWLEDGE_DOMAINS"]