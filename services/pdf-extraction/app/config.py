"""Configuration settings for PDF extraction service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Service settings
    service_name: str = "pdf-extraction-service"
    service_port: int = 8002
    log_level: str = "INFO"

    # Google Gemini settings
    gemini_api_key: str = "AIzaSyDurj7hebJLQkLqhqcDikRbg17QK1qsW64"
    gemini_model: str = "gemini-2.0-flash-exp"
    gemini_timeout: int = 300  # 5 minutes

    # PDF processing
    max_pdf_size_mb: int = 10
    pdf_max_pages: int = 50

    # Django backend integration
    django_callback_url: str = "http://localhost:9000/dashboard/internal/nutrition-plans/ingest-callback/"
    django_callback_token: str = "dev-callback-secret-token"
    django_callback_timeout: int = 30

    class Config:
        env_file = ".env"
        env_prefix = "PDF_EXTRACTION_"


settings = Settings()
