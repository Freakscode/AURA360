from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    doc_id: str
    text: Optional[str] = None
    url: Optional[str] = None
    filename: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    chunk_size: int = 900
    chunk_overlap: int = 150
    consolidate_citations: bool = True
    category: Optional[str] = Field(default=None, description="Classification bucket: mente/cuerpo/alma.")
    locale: Optional[str] = Field(default=None, description="Locale code such as es-CO.")
    source_type: Optional[str] = Field(default=None, description="Origen del documento (paper, blog, etc).")
    embedding_model: Optional[str] = Field(default=None, description="Modelo de embeddings utilizado en ingesta.")
    version: Optional[str] = Field(default=None, description="Versión semántica del embedding/documento.")
    valid_from: Optional[int] = Field(default=None, description="Timestamp (epoch seconds) que indica vigencia del contenido.")


class SearchFilter(BaseModel):
    must: Dict[str, Any] = Field(default_factory=dict)
    should: Dict[str, Any] = Field(default_factory=dict)


class SearchQuery(BaseModel):
    query: str
    limit: int = 10
    filter: Optional[SearchFilter] = None
    ef_search: Optional[int] = None


class Hit(BaseModel):
    id: str | int
    score: float
    payload: Dict[str, Any]


class PaperMeta(BaseModel):
    doc_id: str
    title: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    doi: Optional[str] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    lang: Optional[str] = None
    topics: List[str] = Field(default_factory=list)
    mesh_terms: List[str] = Field(default_factory=list)
    source: Optional[str] = None


class SectionSegment(BaseModel):
    order: int
    section_path: str
    text: str
    is_abstract: bool = False
    is_conclusion: bool = False


class ParsedDocument(BaseModel):
    meta: PaperMeta
    segments: List[SectionSegment]


class IngestJobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class IngestJob(BaseModel):
    job_id: str
    status: IngestJobStatus
    doc_id: Optional[str] = None
    processed_chunks: Optional[int] = None
    total_chunks: Optional[int] = None
    error: Optional[str] = None
