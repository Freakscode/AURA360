"""Services module for body app."""

from __future__ import annotations

# Re-export storage services for backward compatibility
from .storage import (
    NutritionPlanIngestionError,
    NutritionPlanStorageError,
    NutritionPlanStorageResult,
    build_metadata_from_request,
    enqueue_nutrition_plan_ingestion,
    store_nutrition_plan_pdf,
)

__all__ = [
    "NutritionPlanIngestionError",
    "NutritionPlanStorageError",
    "NutritionPlanStorageResult",
    "build_metadata_from_request",
    "enqueue_nutrition_plan_ingestion",
    "store_nutrition_plan_pdf",
]
