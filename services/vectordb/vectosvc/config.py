from dataclasses import dataclass

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass(frozen=True)
class ServiceSettings:
    """Configuración compartida para componentes de servicio/API."""

    collection_name: str
    embedding_model: str
    embedding_version: str
    vector_query_timeout: int
    vector_query_retry_delay: float
    vector_query_max_retries: int

    @classmethod
    def from_settings(cls, settings: "Settings") -> "ServiceSettings":
        return cls(
            collection_name=settings.collection_name,
            embedding_model=settings.embedding_model,
            embedding_version=settings.embedding_version,
            vector_query_timeout=settings.vector_query_timeout,
            vector_query_retry_delay=settings.vector_query_retry_delay,
            vector_query_max_retries=settings.vector_query_max_retries,
        )


class Settings(BaseSettings):
    """Configuración central de vectosvc."""
    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: str | None = Field(default=None, alias="QDRANT_API_KEY")
    qdrant_grpc: str | None = Field(default=None, alias="QDRANT_GRPC")
    prefer_grpc: bool = Field(default=False, alias="PREFER_GRPC")

    collection_name: str = Field(default="holistic_memory", alias="VECTOR_COLLECTION_NAME")
    vector_distance: str = Field(default="cosine", alias="VECTOR_DISTANCE")

    embedding_model: str = Field(
        default="gemini-embedding-001",
        alias="DEFAULT_EMBEDDING_MODEL",
        description="Modelo de embeddings utilizado para consultas e ingesta.",
    )
    embedding_dim: int = Field(default=768, alias="EMBEDDING_DIM")
    embedding_version: str = Field(default="2025.10.27", alias="EMBEDDING_VERSION")

    vector_query_timeout: int = Field(default=8, alias="VECTOR_QUERY_TIMEOUT")
    vector_query_retry_delay: float = Field(default=0.5, alias="VECTOR_QUERY_RETRY_DELAY")
    vector_query_max_retries: int = Field(default=2, alias="VECTOR_QUERY_MAX_RETRIES")

    broker_url: str = Field(default="redis://localhost:6379/0", alias="BROKER_URL")
    result_backend: str = Field(default="redis://localhost:6379/1", alias="RESULT_BACKEND")

    grobid_url: str = Field(default="http://localhost:8070", alias="GROBID_URL")
    grobid_timeout: int = Field(default=60, alias="GROBID_TIMEOUT")

    gcs_project: str | None = Field(default=None, alias="GCS_PROJECT")
    gcs_user_project: str | None = Field(default=None, alias="GCS_USER_PROJECT")

    auto_topics: bool = Field(default=False, alias="AUTO_TOPICS")
    topic_top_k: int = Field(default=3, alias="TOPIC_TOP_K")
    topic_threshold: float = Field(default=0.34, alias="TOPIC_THRESHOLD")
    topic_config_path: str | None = Field(default=None, alias="TOPIC_CONFIG_PATH")

    cache_embeddings: bool = Field(default=True, alias="CACHE_EMBEDDINGS")
    cache_embedding_ttl: int = Field(default=604800, alias="CACHE_EMBEDDING_TTL")
    cache_search_results: bool = Field(default=False, alias="CACHE_SEARCH_RESULTS")
    cache_search_ttl: int = Field(default=120, alias="CACHE_SEARCH_TTL")

    supabase_api_url: str | None = Field(default=None, alias="SUPABASE_API_URL")
    supabase_service_role_key: str | None = Field(default=None, alias="SUPABASE_SERVICE_ROLE_KEY")

    deepseek_api_url: str | None = Field(default=None, alias="DEEPSEEK_API_URL")
    deepseek_api_key: str | None = Field(default=None, alias="DEEPSEEK_API_KEY")
    deepseek_timeout: int = Field(default=60, alias="DEEPSEEK_TIMEOUT")

    nutrition_plan_download_timeout: int = Field(default=30, alias="NUTRITION_PLAN_DOWNLOAD_TIMEOUT")
    nutrition_plan_callback_timeout: int = Field(default=15, alias="NUTRITION_PLAN_CALLBACK_TIMEOUT")
    nutrition_plan_prompt_max_chars: int = Field(default=12000, alias="NUTRITION_PLAN_PROMPT_MAX_CHARS")
    nutrition_plan_llm_model: str = Field(default="deepseek-7b", alias="NUTRITION_PLAN_LLM_MODEL")
    nutrition_plan_llm_temperature: float = Field(default=0.15, alias="NUTRITION_PLAN_LLM_TEMPERATURE")
    nutrition_plan_llm_max_output_tokens: int = Field(default=1400, alias="NUTRITION_PLAN_LLM_MAX_OUTPUT_TOKENS")
    nutrition_plan_llm_response_excerpt: int = Field(default=1200, alias="NUTRITION_PLAN_LLM_RESPONSE_EXCERPT")
    nutrition_plan_text_excerpt: int = Field(default=1500, alias="NUTRITION_PLAN_TEXT_EXCERPT")


settings = Settings()
service_settings = ServiceSettings.from_settings(settings)
