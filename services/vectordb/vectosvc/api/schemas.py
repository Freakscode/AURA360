from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl, constr


class HolisticCategory(str, Enum):
    MIND = "mente"
    BODY = "cuerpo"
    SOUL = "alma"

    @classmethod
    def list_values(cls) -> List[str]:
        return [member.value for member in cls]


class HolisticSearchFilters(BaseModel):
    must: Dict[str, Any] = Field(default_factory=dict)
    should: Dict[str, Any] = Field(default_factory=dict)


class HolisticSearchRequest(BaseModel):
    trace_id: constr(strip_whitespace=True, min_length=1)
    query: constr(strip_whitespace=True, min_length=1)
    category: HolisticCategory
    locale: Optional[constr(strip_whitespace=True, min_length=2, max_length=10)] = None
    top_k: int = Field(default=5, ge=1, le=50)
    embedding_model: Optional[constr(strip_whitespace=True, min_length=1)] = None
    filters: Optional[HolisticSearchFilters] = None


class HolisticSearchResult(BaseModel):
    document_id: str = Field(..., alias="doc_id")
    score: float
    confidence_score: Optional[float] = None
    category: HolisticCategory
    source_type: Optional[str] = None
    chunk: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding_model: Optional[str] = None
    version: Optional[str] = None

    class Config:
        populate_by_name = True


class HolisticSearchResponseData(BaseModel):
    results: List[HolisticSearchResult] = Field(default_factory=list)


class HolisticSearchError(BaseModel):
    type: str
    message: str
    details: Optional[Dict[str, Any]] = None


class HolisticSearchResponseMeta(BaseModel):
    trace_id: str
    took_ms: int
    collection: str


class HolisticSearchResponse(BaseModel):
    status: Literal["success", "error"]
    data: Optional[HolisticSearchResponseData] = None
    error: Optional[HolisticSearchError] = None
    meta: HolisticSearchResponseMeta

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "success",
                    "data": {
                        "results": [
                            {
                                "document_id": "doc-123",
                                "score": 0.83,
                                "confidence_score": 0.81,
                                "category": "mente",
                                "source_type": "paper",
                                "chunk": "Texto del fragmento…",
                                "metadata": {"title": "Ejemplo"},
                                "embedding_model": "text-embedding-3-small",
                                "version": "2025.10.27",
                            }
                        ]
                    },
                    "error": None,
                    "meta": {
                        "trace_id": "trace-abc",
                        "took_ms": 123,
                        "collection": "holistic_memory",
                    },
                }
            ]
        }
    }


class NutritionPlanSource(BaseModel):
    kind: Literal["supabase", "http", "https", "local"] = Field(..., description="Origen del archivo PDF.")
    path: constr(strip_whitespace=True, min_length=1)
    bucket: Optional[constr(strip_whitespace=True, min_length=1)] = None
    public_url: Optional[HttpUrl] = Field(default=None, description="URL pública opcional para descargar el PDF.")


class NutritionPlanCallback(BaseModel):
    url: HttpUrl
    token: Optional[constr(strip_whitespace=True, min_length=1)] = None


class NutritionPlanIngestRequest(BaseModel):
    job_id: constr(strip_whitespace=True, min_length=1)
    auth_user_id: constr(strip_whitespace=True, min_length=1)
    source: NutritionPlanSource
    metadata: Dict[str, Any] = Field(default_factory=dict)
    callback: Optional[NutritionPlanCallback] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "job_id": "0e7a1d50-12f4-4d5d-8b75-230eb1fe14c2",
                    "auth_user_id": "c7c8492d-ffbb-42ed-8cbb-1a3fc97237a7",
                    "source": {
                        "kind": "supabase",
                        "bucket": "nutrition-plans",
                        "path": "nutrition-plans/c7c8492d-ffbb-42ed-8cbb-1a3fc97237a7/plan.pdf",
                        "public_url": "https://supabase.example.com/storage/v1/object/public/nutrition-plans/c7c8492d-ffbb-42ed-8cbb-1a3fc97237a7/plan.pdf",
                    },
                    "metadata": {
                        "title": "Plan hipocalórico octubre",
                        "language": "es",
                        "notes": "Paciente con objetivo de reducción de grasa corporal",
                    },
                    "callback": {
                        "url": "https://backend.example.com/internal/nutrition-plans/ingest-callback/",
                        "token": "backend-shared-secret",
                    },
                }
            ]
        }
    }


class WeightedSearchRequest(BaseModel):
    """Request for weighted retrieval combining user context and general corpus."""

    trace_id: constr(strip_whitespace=True, min_length=1)
    query: constr(strip_whitespace=True, min_length=1)
    user_id: Optional[constr(strip_whitespace=True, min_length=1)] = Field(
        None, description="User UUID for filtering user_context collection"
    )
    category: Optional[HolisticCategory] = Field(None, description="Category filter (mente, cuerpo, alma)")
    guardian_type: Optional[str] = Field(None, description="Guardian type: mental, physical, spiritual")
    topics: Optional[List[str]] = Field(None, description="Explicit topic filters")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of final results after merging")
    user_context_limit: int = Field(default=5, ge=1, le=20, description="Max results from user_context")
    general_limit: int = Field(default=10, ge=1, le=30, description="Max results from general corpus")
    embedding_model: Optional[constr(strip_whitespace=True, min_length=1)] = None


class WeightedSearchResult(BaseModel):
    """Single result from weighted retrieval."""

    doc_id: str
    text: str
    score: float = Field(..., description="Original cosine similarity score")
    weighted_score: float = Field(..., description="Boosted score for ranking")
    source_collection: str = Field(..., description="Collection origin (user_context or general)")
    category: str
    source_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WeightedSearchResponseData(BaseModel):
    results: List[WeightedSearchResult] = Field(default_factory=list)


class WeightedSearchResponse(BaseModel):
    status: Literal["success", "error"]
    data: Optional[WeightedSearchResponseData] = None
    error: Optional[Dict[str, Any]] = None
    meta: Dict[str, Any]