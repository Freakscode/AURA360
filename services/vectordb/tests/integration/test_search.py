"""
Integration tests for search functionality.
"""
import pytest
import numpy as np

from vectosvc.core.pipeline import ingest_one
from vectosvc.core.embeddings import Embeddings
from vectosvc.core.qdrant_store import store


class TestSearchIntegration:
    """Tests for end-to-end search."""
    
    def test_search_basic(self):
        """Test búsqueda semántica básica."""
        # Ingestar documentos
        ingest_one({
            "doc_id": "search-test-001",
            "text": "Sleep deprivation affects cognitive performance and memory consolidation.",
            "chunk_size": 500,
            "chunk_overlap": 0
        })
        
        ingest_one({
            "doc_id": "search-test-002",
            "text": "Nutrition and diet play important roles in metabolic health and weight management.",
            "chunk_size": 500,
            "chunk_overlap": 0
        })
        
        # Buscar algo relacionado con sleep
        emb = Embeddings()
        query_vec = emb.encode(["sleep memory cognitive"])[0].tolist()
        
        hits = store.search(query_vec, limit=5)
        
        assert len(hits) > 0
        # El hit más relevante debe ser del documento sobre sleep
        assert hits[0].payload["doc_id"] == "search-test-001"
        assert hits[0].score > 0.3  # similitud razonable
    
    def test_search_with_filters(self):
        """Test búsqueda con filtros."""
        from qdrant_client.http import models as qm
        
        # Ingestar con diferentes topics
        ingest_one({
            "doc_id": "filter-test-001",
            "text": "Sleep and circadian rhythms regulate melatonin production.",
            "metadata": {"topics": ["sleep_health"]},
            "chunk_size": 500,
            "chunk_overlap": 0
        })
        
        ingest_one({
            "doc_id": "filter-test-002",
            "text": "Dietary patterns influence insulin sensitivity and glucose metabolism.",
            "metadata": {"topics": ["nutrition"]},
            "chunk_size": 500,
            "chunk_overlap": 0
        })
        
        # Buscar con filtro de topic
        emb = Embeddings()
        query_vec = emb.encode(["health and wellness"])[0].tolist()
        
        filter_obj = store.build_filter(
            must={"topics": ["sleep_health"]},
            should=None
        )
        
        hits = store.search(query_vec, limit=5, filter_=filter_obj)
        
        # Solo debe retornar documentos con topic sleep_health (filtro funciona)
        assert len(hits) > 0
        for hit in hits:
            assert "sleep_health" in hit.payload["topics"]
        
        # Buscar específicamente nuestro documento ingresado
        unique_filter = store.build_filter(
            must={"doc_id": "filter-test-001"},
            should=None
        )
        hits_specific = store.search(query_vec, limit=1, filter_=unique_filter)
        assert len(hits_specific) == 1
        assert hits_specific[0].payload["doc_id"] == "filter-test-001"
    
    def test_search_relevance_ranking(self):
        """Test que resultados están ordenados por relevancia."""
        # Ingestar documentos con diferentes niveles de relevancia
        ingest_one({
            "doc_id": "rank-test-001",
            "text": "Sleep deprivation and sleep restriction lead to cognitive impairment.",
            "chunk_size": 500,
            "chunk_overlap": 0
        })
        
        ingest_one({
            "doc_id": "rank-test-002",
            "text": "Cognitive performance is affected by many factors including attention.",
            "chunk_size": 500,
            "chunk_overlap": 0
        })
        
        ingest_one({
            "doc_id": "rank-test-003",
            "text": "Nutrition plays a role in health outcomes.",
            "chunk_size": 500,
            "chunk_overlap": 0
        })
        
        # Buscar específicamente sobre sleep and cognition
        emb = Embeddings()
        query_vec = emb.encode(["sleep deprivation cognitive impairment"])[0].tolist()
        
        hits = store.search(query_vec, limit=3)
        
        assert len(hits) >= 2
        # rank-test-001 debe ser el más relevante
        assert hits[0].payload["doc_id"] == "rank-test-001"
        # Los scores deben estar en orden descendente
        for i in range(len(hits) - 1):
            assert hits[i].score >= hits[i + 1].score
    
    def test_search_limit(self):
        """Test que limit funciona correctamente."""
        # Ingestar múltiples documentos
        for i in range(10):
            ingest_one({
                "doc_id": f"limit-test-{i:03d}",
                "text": f"Document {i} about various health topics and research.",
                "chunk_size": 500,
                "chunk_overlap": 0
            })
        
        emb = Embeddings()
        query_vec = emb.encode(["health research"])[0].tolist()
        
        # Buscar con diferentes límites
        hits_5 = store.search(query_vec, limit=5)
        hits_3 = store.search(query_vec, limit=3)
        
        assert len(hits_5) == 5
        assert len(hits_3) == 3
        
        # Los primeros 3 de hits_5 deben ser iguales a hits_3
        for i in range(3):
            assert hits_5[i].id == hits_3[i].id
    
    def test_search_multiquery(self):
        """Test búsquedas con diferentes queries sobre el mismo corpus."""
        # Ingestar corpus diverso
        ingest_one({
            "doc_id": "multi-001",
            "text": "Sleep disorders include insomnia, sleep apnea, and narcolepsy.",
            "chunk_size": 500,
            "chunk_overlap": 0
        })
        
        ingest_one({
            "doc_id": "multi-002",
            "text": "Obesity is associated with metabolic syndrome and type 2 diabetes.",
            "chunk_size": 500,
            "chunk_overlap": 0
        })
        
        ingest_one({
            "doc_id": "multi-003",
            "text": "Exercise improves cardiovascular health and cognitive function.",
            "chunk_size": 500,
            "chunk_overlap": 0
        })
        
        emb = Embeddings()
        
        # Query 1: sobre sleep
        vec1 = emb.encode(["sleep disorders insomnia"])[0].tolist()
        hits1 = store.search(vec1, limit=1)
        assert hits1[0].payload["doc_id"] == "multi-001"
        
        # Query 2: sobre metabolism
        vec2 = emb.encode(["obesity diabetes metabolic"])[0].tolist()
        hits2 = store.search(vec2, limit=1)
        assert hits2[0].payload["doc_id"] == "multi-002"
        
        # Query 3: sobre exercise
        vec3 = emb.encode(["exercise cardiovascular"])[0].tolist()
        hits3 = store.search(vec3, limit=1)
        assert hits3[0].payload["doc_id"] == "multi-003"
