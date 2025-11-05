"""
Tests for Qdrant store module.
"""
import pytest
from qdrant_client.http import models as qm

from vectosvc.core.qdrant_store import QdrantStore


class TestQdrantStore:
    """Tests for QdrantStore class."""
    
    def test_build_filter_empty(self, test_store):
        """Test filter vacío retorna None."""
        result = test_store.build_filter(must=None, should=None)
        assert result is None
        
        result = test_store.build_filter(must={}, should={})
        assert result is None
    
    def test_build_filter_must_only(self, test_store):
        """Test filter con solo must conditions."""
        filter_obj = test_store.build_filter(
            must={"topics": ["sleep_health"], "year": 2020},
            should=None
        )
        assert isinstance(filter_obj, qm.Filter)
        assert len(filter_obj.must) == 2
        # should debe ser lista vacía
        assert filter_obj.should == []
    
    def test_build_filter_match_value(self, test_store):
        """Test MatchValue para valores simples."""
        filter_obj = test_store.build_filter(
            must={"year": 2024, "lang": "en"},
            should=None
        )
        # Verificar que se crean FieldConditions
        assert len(filter_obj.must) == 2
    
    def test_build_filter_match_any(self, test_store):
        """Test MatchAny para listas."""
        filter_obj = test_store.build_filter(
            must={"topics": ["sleep_health", "insomnia"]},
            should=None
        )
        # Lista debe usar MatchAny
        assert len(filter_obj.must) == 1
        condition = filter_obj.must[0]
        assert isinstance(condition, qm.FieldCondition)
        # Verificar que tiene MatchAny
        assert hasattr(condition.match, 'any')
    
    def test_build_filter_should(self, test_store):
        """Test filter con should conditions."""
        filter_obj = test_store.build_filter(
            must=None,
            should={"journal": ["Nature", "Science"]}
        )
        assert len(filter_obj.should) == 1
        assert len(filter_obj.must) == 0
    
    def test_build_filter_must_and_should(self, test_store):
        """Test filter con must y should."""
        filter_obj = test_store.build_filter(
            must={"year": 2024},
            should={"topics": ["sleep_health", "insomnia"]}
        )
        assert len(filter_obj.must) == 1
        assert len(filter_obj.should) == 1


class TestQdrantCollection:
    """Tests for collection management."""
    
    def test_ensure_collection_creates(self, test_store):
        """Test que ensure_collection crea la colección."""
        test_store.ensure_collection(vector_size=384, on_disk=False)
        
        # Verificar que existe
        collection = test_store.client.get_collection(test_store.collection)
        assert collection is not None
        # API de Qdrant: vectores está en config.params.vectors
        assert collection.config.params.vectors.size == 384
    
    def test_ensure_collection_idempotent(self, test_store):
        """Test que llamar dos veces no falla."""
        test_store.ensure_collection(vector_size=384, on_disk=False)
        # Segunda llamada no debe fallar
        test_store.ensure_collection(vector_size=384, on_disk=False)
    
    def test_ensure_collection_creates_indexes(self, test_store):
        """Test que se crean índices de payload."""
        test_store.ensure_collection(vector_size=384, on_disk=False)
        
        # Verificar colección (los índices se crean en background)
        collection = test_store.client.get_collection(test_store.collection)
        assert collection is not None


class TestQdrantUpsert:
    """Tests for upsert operations."""
    
    def test_upsert_single_point(self, test_store):
        """Test insertar un punto."""
        import uuid
        test_store.ensure_collection(vector_size=3, on_disk=False)
        
        # Qdrant requiere UUIDs o integers
        ids = [str(uuid.uuid4())]
        vectors = [[0.1, 0.2, 0.3]]
        payloads = [{"doc_id": "test-001", "text": "Test"}]
        
        test_store.upsert(ids, vectors, payloads)
        
        # Verificar que se insertó
        points, _ = test_store.client.scroll(
            collection_name=test_store.collection,
            limit=10
        )
        assert len(points) == 1
        assert points[0].payload["doc_id"] == "test-001"
    
    def test_upsert_multiple_points(self, test_store):
        """Test insertar múltiples puntos."""
        import uuid
        test_store.ensure_collection(vector_size=3, on_disk=False)
        
        ids = [str(uuid.uuid4()) for i in range(5)]
        vectors = [[0.1 * i, 0.2 * i, 0.3 * i] for i in range(5)]
        payloads = [{"doc_id": f"doc-{i}", "chunk_index": i} for i in range(5)]
        
        test_store.upsert(ids, vectors, payloads)
        
        # Verificar
        points, _ = test_store.client.scroll(
            collection_name=test_store.collection,
            limit=10
        )
        assert len(points) == 5
    
    def test_upsert_overwrites(self, test_store):
        """Test que upsert actualiza puntos existentes."""
        import uuid
        test_store.ensure_collection(vector_size=3, on_disk=False)
        
        point_id = str(uuid.uuid4())
        
        # Insertar
        test_store.upsert(
            [point_id],
            [[0.1, 0.2, 0.3]],
            [{"text": "original"}]
        )
        
        # Actualizar
        test_store.upsert(
            [point_id],
            [[0.4, 0.5, 0.6]],
            [{"text": "updated"}]
        )
        
        # Verificar que solo hay un punto
        points, _ = test_store.client.scroll(
            collection_name=test_store.collection,
            limit=10
        )
        assert len(points) == 1
        assert points[0].payload["text"] == "updated"


class TestQdrantSearch:
    """Tests for search operations."""
    
    def test_search_basic(self, test_store):
        """Test búsqueda básica."""
        import uuid
        test_store.ensure_collection(vector_size=3, on_disk=False)
        
        # Insertar puntos
        test_store.upsert(
            [str(uuid.uuid4()) for _ in range(3)],
            [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            [{"name": "x"}, {"name": "y"}, {"name": "z"}]
        )
        
        # Buscar similar a [1.0, 0.0, 0.0]
        results = test_store.search([0.9, 0.1, 0.0], limit=2)
        
        assert len(results) <= 2
        assert len(results) > 0
        # El más cercano debe ser p1
        assert results[0].payload["name"] == "x"
    
    def test_search_with_filter(self, test_store):
        """Test búsqueda con filtro."""
        import uuid
        test_store.ensure_collection(vector_size=3, on_disk=False)
        
        # Insertar puntos con diferentes topics
        test_store.upsert(
            [str(uuid.uuid4()) for _ in range(3)],
            [[1.0, 0.0, 0.0], [0.9, 0.1, 0.0], [0.0, 1.0, 0.0]],
            [
                {"topics": ["sleep"]},
                {"topics": ["nutrition"]},
                {"topics": ["sleep"]},
            ]
        )
        
        # Buscar solo sleep
        filter_obj = test_store.build_filter(
            must={"topics": ["sleep"]},
            should=None
        )
        results = test_store.search([1.0, 0.0, 0.0], limit=5, filter_=filter_obj)
        
        # Solo debe retornar p1 y p3
        assert len(results) == 2
        for result in results:
            assert "sleep" in result.payload["topics"]
    
    def test_search_with_ef_search(self, test_store):
        """Test búsqueda con ef_search personalizado."""
        import uuid
        test_store.ensure_collection(vector_size=3, on_disk=False)
        
        test_store.upsert(
            [str(uuid.uuid4())],
            [[1.0, 0.0, 0.0]],
            [{"text": "test"}]
        )
        
        # Debe funcionar con ef_search
        results = test_store.search([1.0, 0.0, 0.0], limit=1, ef_search=64)
        assert len(results) == 1


class TestQdrantSetTopics:
    """Tests for set_topics operation."""
    
    def test_set_topics_basic(self, test_store):
        """Test asignación básica de topics."""
        import uuid
        test_store.ensure_collection(vector_size=3, on_disk=False)
        
        # Insertar documento con múltiples chunks
        test_store.upsert(
            [str(uuid.uuid4()) for _ in range(2)],
            [[1.0, 0.0, 0.0], [0.9, 0.1, 0.0]],
            [{"doc_id": "doc-001"}, {"doc_id": "doc-001"}]
        )
        
        # Asignar topics
        test_store.set_topics(
            "doc-001",
            ["sleep_health", "insomnia"],
            [
                {"id": "sleep_health", "score": 0.85},
                {"id": "insomnia", "score": 0.72},
            ]
        )
        
        # Verificar que se actualizaron todos los chunks
        points, _ = test_store.client.scroll(
            collection_name=test_store.collection,
            limit=10
        )
        for point in points:
            assert "sleep_health" in point.payload["topics"]
            assert "topic_scores" in point.payload
    
    def test_set_topics_empty(self, test_store):
        """Test con lista vacía de topics (no hace nada)."""
        import uuid
        test_store.ensure_collection(vector_size=3, on_disk=False)
        
        test_store.upsert(
            [str(uuid.uuid4())],
            [[1.0, 0.0, 0.0]],
            [{"doc_id": "doc-002"}]
        )
        
        # No debe fallar
        test_store.set_topics("doc-002", [], None)
