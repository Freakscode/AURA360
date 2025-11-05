"""
Integration tests for complete ingestion flow.
"""
import pytest
from qdrant_client.http import models as qm

from vectosvc.core.pipeline import ingest_one
from vectosvc.core.qdrant_store import store
from vectosvc.config import settings


class TestIngestionFlow:
    """Tests for end-to-end ingestion."""
    
    def test_ingest_text_end_to_end(self, sample_ingest_request):
        """Test completo: text → chunks → embeddings → Qdrant."""
        chunk_count = ingest_one(sample_ingest_request)
        
        assert chunk_count > 0
        assert isinstance(chunk_count, int)
        
        # Verificar en Qdrant (usa el store global, no test_store)
        doc_id = sample_ingest_request["doc_id"]
        points, _ = store.client.scroll(
            collection_name=settings.collection_name,
            limit=100,
            with_payload=True,
            scroll_filter=qm.Filter(
                must=[qm.FieldCondition(key="doc_id", match=qm.MatchValue(value=doc_id))]
            )
        )
        
        assert len(points) == chunk_count
        
        # Verificar estructura de payload
        first_point = points[0]
        assert first_point.payload["doc_id"] == doc_id
        assert "chunk_index" in first_point.payload
        assert "text" in first_point.payload
        assert "section_path" in first_point.payload
        assert "created_at" in first_point.payload
        assert "embedding_model" in first_point.payload
    
    def test_ingest_preserves_metadata(self, sample_ingest_request):
        """Test que metadata se preserva en chunks."""
        chunk_count = ingest_one(sample_ingest_request)
        
        doc_id = sample_ingest_request["doc_id"]
        points, _ = store.client.scroll(
            collection_name=settings.collection_name,
            limit=100,
            with_payload=True,
            scroll_filter=qm.Filter(
                must=[qm.FieldCondition(key="doc_id", match=qm.MatchValue(value=doc_id))]
            )
        )
        
        # Verificar metadata en todos los chunks
        for point in points:
            assert point.payload["year"] == 2024
            assert point.payload["journal"] == "Test Journal"
            assert "sleep_health" in point.payload["topics"]
            assert "cognitive_function" in point.payload["topics"]
    
    def test_ingest_chunk_indices(self, sample_ingest_request):
        """Test que chunk_index es incremental."""
        chunk_count = ingest_one(sample_ingest_request)
        
        doc_id = sample_ingest_request["doc_id"]
        points, _ = store.client.scroll(
            collection_name=settings.collection_name,
            limit=100,
            with_payload=True,
            scroll_filter=qm.Filter(
                must=[qm.FieldCondition(key="doc_id", match=qm.MatchValue(value=doc_id))]
            )
        )
        
        # Ordenar por chunk_index
        sorted_points = sorted(points, key=lambda p: p.payload["chunk_index"])
        
        # Verificar secuencia
        for i, point in enumerate(sorted_points):
            assert point.payload["chunk_index"] == i
    
    def test_ingest_vectors_normalized(self, sample_ingest_request):
        """Test que vectores están normalizados (si usa cosine)."""
        import numpy as np
        
        chunk_count = ingest_one(sample_ingest_request)
        
        doc_id = sample_ingest_request["doc_id"]
        points, _ = store.client.scroll(
            collection_name=settings.collection_name,
            limit=10,
            with_payload=False,
            with_vectors=True,
            scroll_filter=qm.Filter(
                must=[qm.FieldCondition(key="doc_id", match=qm.MatchValue(value=doc_id))]
            )
        )
        
        if settings.vector_distance.lower() == "cosine":
            # Vectores deben estar normalizados
            for point in points:
                vec = np.array(point.vector)
                norm = np.linalg.norm(vec)
                # Norm debe ser ~1.0 (con tolerancia por float32)
                assert abs(norm - 1.0) < 0.01
    
    def test_ingest_idempotent(self, sample_ingest_request):
        """Test que re-ingestar el mismo documento es idempotente."""
        # Primera ingesta
        count1 = ingest_one(sample_ingest_request)
        
        # Segunda ingesta del mismo documento
        count2 = ingest_one(sample_ingest_request)
        
        assert count1 == count2
        
        # Verificar que no se duplicaron chunks
        doc_id = sample_ingest_request["doc_id"]
        points, _ = store.client.scroll(
            collection_name=settings.collection_name,
            limit=200,
            scroll_filter=qm.Filter(
                must=[qm.FieldCondition(key="doc_id", match=qm.MatchValue(value=doc_id))]
            )
        )
        
        # Debe haber exactamente count1 chunks (no duplicados)
        assert len(points) == count1
    
    def test_ingest_metadata_override(self):
        """Test que metadata override funciona."""
        req = {
            "doc_id": "test-override-001",
            "text": "Test document " * 50,
            "chunk_size": 300,
            "chunk_overlap": 50,
            "metadata": {
                "topics": ["original_topic"],
                "year": 2020,
            }
        }
        
        ingest_one(req)
        
        # Re-ingestar con metadata diferente
        req["metadata"]["topics"] = ["new_topic", "another_topic"]
        req["metadata"]["year"] = 2024
        
        ingest_one(req)
        
        # Verificar que se actualizó
        points, _ = store.client.scroll(
            collection_name=settings.collection_name,
            limit=10,
            scroll_filter=qm.Filter(
                must=[qm.FieldCondition(key="doc_id", match=qm.MatchValue(value="test-override-001"))]
            )
        )
        
        for point in points:
            assert point.payload["year"] == 2024
            assert "new_topic" in point.payload["topics"]
            assert "original_topic" not in point.payload["topics"]


class TestIngestionErrors:
    """Tests for error handling in ingestion."""
    
    def test_ingest_empty_text_fails(self):
        """Test que texto vacío falla apropiadamente."""
        req = {
            "doc_id": "test-empty",
            "text": "",
            "chunk_size": 300,
            "chunk_overlap": 50,
        }
        
        with pytest.raises(ValueError, match="text or url"):
            ingest_one(req)
    
    def test_ingest_no_text_no_url_fails(self):
        """Test que falla si no hay text ni url."""
        req = {
            "doc_id": "test-no-content",
            "chunk_size": 300,
            "chunk_overlap": 50,
        }
        
        with pytest.raises(ValueError, match="text or url"):
            ingest_one(req)
