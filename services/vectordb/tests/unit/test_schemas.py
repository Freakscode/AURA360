"""
Tests for Pydantic schemas.
"""
import pytest
from vectosvc.core.schemas import (
    IngestRequest,
    SearchQuery,
    SearchFilter,
    PaperMeta,
    SectionSegment,
    ParsedDocument,
    IngestJob,
    IngestJobStatus,
)


class TestIngestRequest:
    """Tests for IngestRequest schema."""
    
    def test_basic_text_request(self):
        """Test creación básica con texto."""
        req = IngestRequest(doc_id="test-001", text="Hello world")
        assert req.doc_id == "test-001"
        assert req.text == "Hello world"
        assert req.chunk_size == 900  # default
        assert req.chunk_overlap == 150  # default
    
    def test_url_request(self):
        """Test creación con URL."""
        req = IngestRequest(
            doc_id="test-002",
            url="https://example.com/paper.pdf"
        )
        assert req.url == "https://example.com/paper.pdf"
        assert req.text is None
    
    def test_with_metadata(self):
        """Test con metadata completo."""
        req = IngestRequest(
            doc_id="test-003",
            text="Test",
            metadata={
                "topics": ["sleep_health"],
                "year": 2024,
                "journal": "Nature"
            }
        )
        assert req.metadata["topics"] == ["sleep_health"]
        assert req.metadata["year"] == 2024
    
    def test_custom_chunking(self):
        """Test con parámetros de chunking personalizados."""
        req = IngestRequest(
            doc_id="test-004",
            text="Test",
            chunk_size=500,
            chunk_overlap=100
        )
        assert req.chunk_size == 500
        assert req.chunk_overlap == 100


class TestSearchQuery:
    """Tests for SearchQuery schema."""
    
    def test_basic_query(self):
        """Test query básico."""
        query = SearchQuery(query="sleep deprivation")
        assert query.query == "sleep deprivation"
        assert query.limit == 10  # default
        assert query.filter is None
    
    def test_with_filter(self):
        """Test con filtros."""
        query = SearchQuery(
            query="melatonin",
            limit=20,
            filter=SearchFilter(
                must={"topics": ["sleep_health"], "year": 2024},
                should={}
            )
        )
        assert query.limit == 20
        assert query.filter.must["topics"] == ["sleep_health"]
    
    def test_with_ef_search(self):
        """Test con parámetro HNSW ef_search."""
        query = SearchQuery(query="test", ef_search=256)
        assert query.ef_search == 256


class TestPaperMeta:
    """Tests for PaperMeta schema."""
    
    def test_minimal_meta(self):
        """Test metadata mínimo."""
        meta = PaperMeta(doc_id="test-001")
        assert meta.doc_id == "test-001"
        assert meta.title is None
        assert meta.authors == []
        assert meta.topics == []
    
    def test_full_meta(self):
        """Test metadata completo."""
        meta = PaperMeta(
            doc_id="test-002",
            title="Test Paper",
            authors=["Smith J", "Doe A"],
            doi="10.1234/test",
            journal="Nature",
            year=2024,
            lang="en",
            topics=["sleep_health", "insomnia"],
            mesh_terms=["Sleep", "Melatonin"],
            source="pubmed"
        )
        assert meta.title == "Test Paper"
        assert len(meta.authors) == 2
        assert meta.year == 2024
        assert "sleep_health" in meta.topics


class TestSectionSegment:
    """Tests for SectionSegment schema."""
    
    def test_basic_segment(self):
        """Test segmento básico."""
        seg = SectionSegment(
            order=0,
            section_path="Introduction",
            text="This is the introduction."
        )
        assert seg.order == 0
        assert seg.section_path == "Introduction"
        assert seg.is_abstract is False
        assert seg.is_conclusion is False
    
    def test_abstract_segment(self):
        """Test segmento de abstract."""
        seg = SectionSegment(
            order=0,
            section_path="abstract",
            text="Abstract text",
            is_abstract=True
        )
        assert seg.is_abstract is True
        assert seg.is_conclusion is False
    
    def test_conclusion_segment(self):
        """Test segmento de conclusión."""
        seg = SectionSegment(
            order=10,
            section_path="Conclusions",
            text="Conclusion text",
            is_conclusion=True
        )
        assert seg.is_conclusion is True


class TestParsedDocument:
    """Tests for ParsedDocument schema."""
    
    def test_parsed_document(self):
        """Test documento parseado completo."""
        meta = PaperMeta(doc_id="test-001", title="Test")
        segments = [
            SectionSegment(order=0, section_path="abstract", text="Abstract", is_abstract=True),
            SectionSegment(order=1, section_path="Introduction", text="Intro"),
        ]
        doc = ParsedDocument(meta=meta, segments=segments)
        
        assert doc.meta.doc_id == "test-001"
        assert len(doc.segments) == 2
        assert doc.segments[0].is_abstract is True


class TestIngestJob:
    """Tests for IngestJob schema."""
    
    def test_queued_job(self):
        """Test job en cola."""
        job = IngestJob(
            job_id="job-123",
            status=IngestJobStatus.QUEUED
        )
        assert job.status == IngestJobStatus.QUEUED
        assert job.doc_id is None
        assert job.error is None
    
    def test_completed_job(self):
        """Test job completado."""
        job = IngestJob(
            job_id="job-456",
            status=IngestJobStatus.COMPLETED,
            doc_id="test-001",
            processed_chunks=45,
            total_chunks=45
        )
        assert job.status == IngestJobStatus.COMPLETED
        assert job.processed_chunks == 45
        assert job.error is None
    
    def test_failed_job(self):
        """Test job fallido."""
        job = IngestJob(
            job_id="job-789",
            status=IngestJobStatus.FAILED,
            error="Connection timeout"
        )
        assert job.status == IngestJobStatus.FAILED
        assert job.error == "Connection timeout"
