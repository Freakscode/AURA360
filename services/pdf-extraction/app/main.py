"""FastAPI application for PDF extraction service."""

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .config import settings
from .models.nutrition_plan import NutritionPlan
from .services.callback_service import CallbackError, CallbackService
from .services.django_mapper import DjangoMapper, DjangoMapperError
from .services.llm_service import LLMExtractionError, LLMService

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize services
llm_service = LLMService(
    api_key=settings.gemini_api_key,
    model=settings.gemini_model,
    timeout=settings.gemini_timeout
)

callback_service = CallbackService(
    callback_url=settings.django_callback_url,
    callback_token=settings.django_callback_token,
    timeout=settings.django_callback_timeout
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info(f"Starting {settings.service_name}")
    logger.info(f"Gemini Model: {settings.gemini_model}")
    yield
    logger.info(f"Shutting down {settings.service_name}")


app = FastAPI(
    title="PDF Extraction Service",
    description="Gemini-powered nutrition plan extraction from PDFs",
    version="0.2.0",
    lifespan=lifespan
)


class ExtractionResponse(BaseModel):
    """Response model for extraction endpoint."""

    success: bool
    data: NutritionPlan
    metadata: dict


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": settings.service_name}


@app.post("/extract", response_model=ExtractionResponse)
async def extract_from_pdf(
    file: UploadFile = File(..., description="PDF file to extract data from")
) -> ExtractionResponse:
    """
    Extract structured nutrition plan data from a PDF file.

    Args:
        file: Uploaded PDF file

    Returns:
        Extracted nutrition plan data in JSON format

    Raises:
        HTTPException: If extraction fails
    """
    # Validate file type
    if not file.content_type or file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Only PDF files are accepted."
        )

    # Validate file size
    max_size_bytes = settings.max_pdf_size_mb * 1024 * 1024
    file_contents = await file.read()
    file_size = len(file_contents)

    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {file_size / (1024 * 1024):.2f} MB. Maximum size is {settings.max_pdf_size_mb} MB."
        )

    logger.info(f"Processing PDF: {file.filename} ({file_size / 1024:.2f} KB)")

    try:
        # Extract structured data using Gemini
        logger.info("Extracting structured data with Gemini...")
        extracted_data = llm_service.extract_nutrition_plan(file_contents)

        logger.info("Extraction successful")

        # Return response
        return ExtractionResponse(
            success=True,
            data=extracted_data,
            metadata={
                "filename": file.filename,
                "size_bytes": file_size,
            }
        )

    except LLMExtractionError as e:
        logger.error(f"LLM extraction error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract structured data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


class IngestionRequest(BaseModel):
    """Request model for ingestion endpoint."""

    job_id: str
    auth_user_id: str
    source_uri: str
    title: str | None = None
    metadata: dict | None = None


class IngestionResponse(BaseModel):
    """Response model for ingestion endpoint."""

    job_id: str
    status: str


async def process_and_callback(
    pdf_bytes: bytes,
    job_id: str,
    auth_user_id: str,
    source_uri: str,
    title: str | None,
):
    """Background task to process PDF and send callback."""
    try:
        logger.info(f"Starting background processing for job {job_id}")

        # Extract structured data using Gemini
        extracted_data = llm_service.extract_nutrition_plan(pdf_bytes)

        # Map to Django format
        payload = DjangoMapper.map_to_django_format(
            extraction=extracted_data,
            auth_user_id=auth_user_id,
            job_id=job_id,
            source_uri=source_uri,
            title=title,
        )

        # Send callback to Django
        callback_result = await callback_service.send_callback(payload)

        logger.info(f"Job {job_id} completed successfully, nutrition plan ID: {callback_result.get('id')}")

    except (LLMExtractionError, DjangoMapperError, CallbackError) as e:
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Job {job_id} unexpected error: {e}", exc_info=True)


@app.post("/ingest", response_model=IngestionResponse)
async def ingest_nutrition_plan(
    job_id: str = Form(..., description="Job ID for tracking"),
    auth_user_id: str = Form(..., description="User UUID from Supabase"),
    source_uri: str = Form(..., description="URI of the source PDF"),
    title: str = Form(None, description="Optional title for the plan"),
    file: UploadFile = File(..., description="PDF file to process"),
    background_tasks: BackgroundTasks = None,
) -> IngestionResponse:
    """
    Ingest a nutrition plan PDF for async processing.

    This endpoint accepts a PDF file and metadata, queues it for processing,
    and returns immediately. The extraction results will be sent to the
    configured Django callback URL.

    Args:
        job_id: Job ID for tracking
        auth_user_id: User UUID from Supabase
        source_uri: URI of the source PDF
        title: Optional title for the plan
        file: Uploaded PDF file
        background_tasks: FastAPI background tasks

    Returns:
        Job status with job_id

    Raises:
        HTTPException: If request is invalid
    """
    # Validate file type
    if not file.content_type or file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Only PDF files are accepted."
        )

    # Read file contents
    file_contents = await file.read()
    file_size = len(file_contents)

    # Validate file size
    max_size_bytes = settings.max_pdf_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {file_size / (1024 * 1024):.2f} MB. Maximum size is {settings.max_pdf_size_mb} MB."
        )

    logger.info(
        f"Received ingestion request - Job: {job_id}, User: {auth_user_id}, "
        f"File: {file.filename} ({file_size / 1024:.2f} KB)"
    )

    # Queue background processing
    background_tasks.add_task(
        process_and_callback,
        file_contents,
        job_id,
        auth_user_id,
        source_uri,
        title,
    )

    logger.info(f"Job {job_id} queued for processing")

    return IngestionResponse(job_id=job_id, status="queued")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "internal_error",
            "detail": "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.service_port,
        reload=True,
        log_level=settings.log_level.lower()
    )
