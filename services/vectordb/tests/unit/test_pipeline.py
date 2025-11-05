"""
Tests for pipeline module.
"""
import pytest
import uuid
from vectosvc.core.pipeline import (
    _split_text,
    _hash_id,
    _make_point_id,
    _build_chunks,
    _normalize_topics,
)
from vectosvc.core.schemas import SectionSegment


class TestTextSplitting:
    """Tests for chunking functions."""
    
    def test_split_text_basic(self):
        """Test chunking básico."""
        text = "a" * 1000
        chunks = _split_text(text, size=900, overlap=150)
        assert len(chunks) >= 2
        assert len(chunks[0]) <= 900
    
    def test_split_text_exact_size(self):
        """Test texto exacto al tamaño del chunk."""
        text = "a" * 900
        chunks = _split_text(text, size=900, overlap=150)
        assert len(chunks) == 1
        assert len(chunks[0]) == 900
    
    def test_split_text_small(self):
        """Test texto más pequeño que chunk size."""
        text = "Small text"
        chunks = _split_text(text, size=900, overlap=150)
        assert len(chunks) == 1
        assert chunks[0] == "Small text"
    
    def test_split_text_overlap(self):
        """Test overlap entre chunks."""
        text = "0123456789" * 100  # 1000 chars
        chunks = _split_text(text, size=400, overlap=100)
        assert len(chunks) >= 3
        # Cada chunk debe ser <= 400 chars
        for chunk in chunks:
            assert len(chunk) <= 400
    
    def test_split_text_empty(self):
        """Test texto vacío."""
        chunks = _split_text("", size=900, overlap=150)
        assert chunks == []
    
    def test_split_text_whitespace_only(self):
        """Test solo espacios en blanco."""
        chunks = _split_text("   \n\t  ", size=900, overlap=150)
        assert chunks == []
    
    def test_split_text_zero_size(self):
        """Test con size=0 retorna texto completo."""
        text = "Test text"
        chunks = _split_text(text, size=0, overlap=0)
        assert chunks == ["Test text"]


class TestHashing:
    """Tests for hashing functions."""
    
    def test_hash_id_deterministic(self):
        """Hash debe ser determinístico."""
        h1 = _hash_id("doc1", "chunk0")
        h2 = _hash_id("doc1", "chunk0")
        assert h1 == h2
    
    def test_hash_id_different_inputs(self):
        """Inputs diferentes deben generar hashes diferentes."""
        h1 = _hash_id("doc1", "chunk0")
        h2 = _hash_id("doc1", "chunk1")
        h3 = _hash_id("doc2", "chunk0")
        assert h1 != h2
        assert h1 != h3
    
    def test_hash_id_format(self):
        """Hash debe ser SHA-1 hex (40 caracteres)."""
        h = _hash_id("test")
        assert len(h) == 40
        assert all(c in "0123456789abcdef" for c in h)
    
    def test_make_point_id_stable(self):
        """Point ID debe ser estable (UUID5)."""
        id1 = _make_point_id("doc1", 0, "hash123")
        id2 = _make_point_id("doc1", 0, "hash123")
        assert id1 == id2
    
    def test_make_point_id_uuid_format(self):
        """Point ID debe ser UUID válido."""
        point_id = _make_point_id("doc1", 0, "hash123")
        # Verificar que es un UUID válido
        parsed = uuid.UUID(point_id)
        assert str(parsed) == point_id
    
    def test_make_point_id_different_inputs(self):
        """Inputs diferentes generan IDs diferentes."""
        id1 = _make_point_id("doc1", 0, "hash1")
        id2 = _make_point_id("doc1", 1, "hash1")
        id3 = _make_point_id("doc2", 0, "hash1")
        assert id1 != id2
        assert id1 != id3


class TestBuildChunks:
    """Tests for chunk building."""
    
    def test_build_chunks_single_segment(self):
        """Test chunking de un segmento simple."""
        segments = [
            SectionSegment(
                order=0,
                section_path="Introduction",
                text="a" * 1000
            )
        ]
        chunks = _build_chunks(segments, chunk_size=400, chunk_overlap=100)
        assert len(chunks) >= 3
        assert all("chunk_index" in c for c in chunks)
        assert all("text" in c for c in chunks)
        assert all("hash" in c for c in chunks)
    
    def test_build_chunks_multiple_segments(self):
        """Test chunking de múltiples segmentos."""
        segments = [
            SectionSegment(order=0, section_path="abstract", text="a" * 500, is_abstract=True),
            SectionSegment(order=1, section_path="Introduction", text="b" * 500),
        ]
        chunks = _build_chunks(segments, chunk_size=300, chunk_overlap=50)
        
        # Verificar que hay chunks de ambos segmentos
        assert len(chunks) >= 4
        
        # Verificar chunk_index incrementales
        for i, chunk in enumerate(chunks):
            assert chunk["chunk_index"] == i
        
        # Verificar flags
        abstract_chunks = [c for c in chunks if c["is_abstract"]]
        assert len(abstract_chunks) >= 1
    
    def test_build_chunks_preserves_metadata(self):
        """Test que metadata del segmento se preserva."""
        segments = [
            SectionSegment(
                order=5,
                section_path="Results > Sleep Metrics",
                text="Test results " * 50,
                is_conclusion=True
            )
        ]
        chunks = _build_chunks(segments, chunk_size=300, chunk_overlap=50)
        
        for chunk in chunks:
            assert chunk["section_order"] == 5
            assert chunk["section_path"] == "Results > Sleep Metrics"
            assert chunk["is_conclusion"] is True
            assert chunk["is_abstract"] is False
    
    def test_build_chunks_empty_segments(self):
        """Test con segmentos vacíos."""
        segments = [
            SectionSegment(order=0, section_path="empty", text=""),
            SectionSegment(order=1, section_path="valid", text="Valid text"),
        ]
        chunks = _build_chunks(segments, chunk_size=300, chunk_overlap=50)
        # Solo debe haber chunk del segmento válido
        assert len(chunks) == 1
        assert chunks[0]["text"] == "Valid text"


class TestNormalizeTopics:
    """Tests for topic normalization."""
    
    def test_normalize_single_topic(self):
        """Test normalización de un topic."""
        result = _normalize_topics("Sleep_Health")
        assert result == ["sleep_health"]
    
    def test_normalize_list_topics(self):
        """Test normalización de lista de topics."""
        result = _normalize_topics(["Sleep Health", "Insomnia", "Cognitive Function"])
        assert len(result) == 3
        assert "sleep health" in result
        assert "insomnia" in result
    
    def test_normalize_removes_duplicates(self):
        """Test que se eliminan duplicados."""
        result = _normalize_topics(["sleep", "Sleep", "SLEEP"])
        assert result == ["sleep"]
    
    def test_normalize_sorts(self):
        """Test que se ordenan alfabéticamente."""
        result = _normalize_topics(["zebra", "apple", "monkey"])
        assert result == ["apple", "monkey", "zebra"]
    
    def test_normalize_strips_whitespace(self):
        """Test que se eliminan espacios."""
        result = _normalize_topics(["  sleep  ", " insomnia "])
        assert result == ["insomnia", "sleep"]
    
    def test_normalize_empty_values(self):
        """Test con valores vacíos."""
        result = _normalize_topics(["", "valid", None, "  ", "another"])
        assert result == ["another", "valid"]
    
    def test_normalize_none_input(self):
        """Test con input None."""
        result = _normalize_topics(None)
        assert result == []
