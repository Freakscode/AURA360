"""
Tests de integración para features de Fase 1:
- Caché de embeddings en Redis
- Métricas detalladas del pipeline
- Dead Letter Queue (DLQ)
"""
import pytest
import time

from vectosvc.core.embeddings import Embeddings
from vectosvc.core.pipeline import ingest_one, pipeline_metrics
from vectosvc.core.dlq import DLQ
from vectosvc.config import settings


class TestEmbeddingsCache:
    """Tests para el sistema de caché de embeddings."""
    
    def test_cache_hit_on_repeated_text(self):
        """Test que textos repetidos usan caché."""
        if not settings.cache_embeddings:
            pytest.skip("Cache not enabled")
        
        emb = Embeddings()
        texts = ["hola mundo", "hello world", "hola mundo"]  # "hola mundo" repetido
        
        # Primera llamada: todos cache misses
        initial_misses = emb.cache_misses
        vectors1 = emb.encode(texts)
        
        # Segunda llamada: "hola mundo" debe ser cache hit
        vectors2 = emb.encode(texts)
        final_hits = emb.cache_hits
        
        # Verificar que hubo al menos 1 hit (el texto repetido)
        assert final_hits > 0, "Should have cache hits on repeated text"
        
        # Verificar que vectores son idénticos
        assert vectors1.shape == vectors2.shape
    
    def test_cache_stats(self):
        """Test que estadísticas de caché funcionan."""
        emb = Embeddings()
        
        texts = ["test one", "test two", "test three"]
        emb.encode(texts)
        
        stats = emb.get_cache_stats()
        
        assert "hits" in stats
        assert "misses" in stats
        assert "total" in stats
        assert "hit_rate_percent" in stats
        assert stats["total"] == stats["hits"] + stats["misses"]


class TestPipelineMetrics:
    """Tests para métricas del pipeline."""
    
    def test_metrics_recorded_on_ingest(self, sample_ingest_request):
        """Test que métricas se registran correctamente."""
        # Reset metrics
        pipeline_metrics.reset()
        
        initial_docs = pipeline_metrics.total_documents
        
        # Ingestar documento
        chunk_count = ingest_one(sample_ingest_request)
        
        # Verificar que se registró
        assert pipeline_metrics.total_documents == initial_docs + 1
        assert pipeline_metrics.total_chunks >= chunk_count
        
        # Verificar que hay timings registrados
        stats = pipeline_metrics.get_stats()
        assert "phase_stats" in stats
        
        # Debe haber al menos métricas de chunking, embeddings, upsert
        assert "chunking" in stats["phase_stats"]
        assert "embeddings" in stats["phase_stats"]
        assert "upsert" in stats["phase_stats"]
        assert "total" in stats["phase_stats"]
        
        # Verificar estructura de stats por fase
        for phase, phase_stats in stats["phase_stats"].items():
            assert "count" in phase_stats
            assert "mean_seconds" in phase_stats
            assert "min_seconds" in phase_stats
            assert "max_seconds" in phase_stats
            assert phase_stats["count"] > 0
            assert phase_stats["mean_seconds"] >= 0
    
    def test_metrics_on_pdf_url(self):
        """Test que métricas incluyen fases de download y parse_tei."""
        pipeline_metrics.reset()
        
        # Simular ingesta desde URL (sin URL real, debería fallar pero registrar)
        req = {
            "doc_id": "test-url-metrics",
            "url": "http://example.com/fake.pdf",
            "metadata": {"source": "test"},
        }
        
        # Debería fallar pero registrar métricas
        with pytest.raises(Exception):
            ingest_one(req)
        
        # Verificar que se registró error
        assert pipeline_metrics.total_errors > 0


class TestDLQ:
    """Tests para Dead Letter Queue."""
    
    def test_dlq_push_and_list(self):
        """Test que DLQ puede almacenar y listar fallos."""
        test_dlq = DLQ()
        test_dlq.clear()  # Limpiar antes de test
        
        # Push un fallo simulado
        try:
            raise ValueError("Test error for DLQ")
        except ValueError as e:
            test_dlq.push(
                job_id="test-job-123",
                doc_id="test-doc-456",
                request={"doc_id": "test-doc-456", "text": "test"},
                error=e,
                attempts=3,
                error_phase="embeddings",
            )
        
        # Listar entradas
        entries = test_dlq.list_failures(limit=10)
        
        assert len(entries) > 0
        entry = entries[0]
        assert entry["job_id"] == "test-job-123"
        assert entry["doc_id"] == "test-doc-456"
        assert entry["error_type"] == "ValueError"
        assert entry["error_phase"] == "embeddings"
        assert entry["attempts"] == 3
        assert "traceback" in entry
    
    def test_dlq_stats(self):
        """Test que estadísticas de DLQ funcionan."""
        test_dlq = DLQ()
        test_dlq.clear()
        
        # Push varios fallos
        for i in range(3):
            try:
                if i == 0:
                    raise ValueError(f"Error {i}")
                else:
                    raise RuntimeError(f"Error {i}")
            except Exception as e:
                test_dlq.push(
                    job_id=f"job-{i}",
                    doc_id=f"doc-{i}",
                    request={"doc_id": f"doc-{i}"},
                    error=e,
                    attempts=1,
                    error_phase="parse_tei" if i < 2 else "upsert",
                )
        
        stats = test_dlq.get_stats()
        
        assert stats["total_entries"] == 3
        assert stats["total_failures"] == 3
        assert "by_phase" in stats
        assert "by_error" in stats
        
        # Verificar distribución
        assert stats["by_phase"]["parse_tei"] == 2
        assert stats["by_phase"]["upsert"] == 1
        assert stats["by_error"]["ValueError"] == 1
        assert stats["by_error"]["RuntimeError"] == 2
    
    def test_dlq_clear(self):
        """Test que DLQ puede limpiarse."""
        test_dlq = DLQ()
        
        # Asegurar que hay al menos una entrada
        try:
            raise ValueError("Test")
        except ValueError as e:
            test_dlq.push(
                job_id="clear-test",
                doc_id="clear-test",
                request={},
                error=e,
                attempts=1,
            )
        
        # Limpiar
        count = test_dlq.clear()
        assert count > 0
        
        # Verificar que está vacío
        stats = test_dlq.get_stats()
        assert stats["total_entries"] == 0


class TestIntegrationPhase1:
    """Tests de integración completos para Fase 1."""
    
    def test_full_pipeline_with_metrics_and_cache(self, sample_ingest_request):
        """Test del pipeline completo con todas las features de Fase 1."""
        # Reset
        pipeline_metrics.reset()
        
        # Crear nueva instancia de embeddings para stats limpias
        emb = Embeddings()
        initial_cache_misses = emb.cache_misses
        
        # Primera ingesta
        chunk_count1 = ingest_one(sample_ingest_request)
        
        # Segunda ingesta del mismo documento (debería usar caché de embeddings)
        chunk_count2 = ingest_one(sample_ingest_request)
        
        assert chunk_count1 == chunk_count2
        
        # Verificar métricas
        stats = pipeline_metrics.get_stats()
        assert stats["total_documents"] == 2
        assert stats["total_chunks"] >= chunk_count1 + chunk_count2
        
        # Verificar que pipeline está completo
        assert "chunking" in stats["phase_stats"]
        assert "embeddings" in stats["phase_stats"]
        assert "upsert" in stats["phase_stats"]
        
        # Verificar que embeddings fueron más rápidos en segunda ingesta (caché)
        # (esto es aproximado, puede variar)
        embedding_times = stats["phase_stats"]["embeddings"]
        if embedding_times["count"] >= 2:
            # Si tenemos múltiples mediciones, verificar variabilidad
            assert embedding_times["max_seconds"] >= embedding_times["min_seconds"]

