"""Tests de integración para guardian routing especializado."""

from unittest.mock import MagicMock, patch

import pytest

from infra.settings import GUARDIAN_KNOWLEDGE_DOMAINS
from services.guardian_retrieval import GuardianKnowledgeRetriever
from services.topic_classifier import TopicClassifier
from services.vector_queries import VectorQueryRecord, VectorSearchFilters


@pytest.fixture
def mock_topic_classifier():
    """Mock de TopicClassifier."""
    classifier = MagicMock(spec=TopicClassifier)
    classifier.classify.return_value = [
        "sleep_health",
        "insomnia",
        "circadian_rhythm",
    ]
    return classifier


@pytest.fixture
def mock_vector_runner():
    """Mock de VectorQueryRunner."""
    runner = MagicMock()

    def mock_run(trace_id, query_text, top_k=5, filters=None):
        # Simular respuesta con hits
        hits = [
            {
                "id": "doc1",
                "score": 0.85,
                "payload": {
                    "text": "Sleep hygiene is important for...",
                    "category": "cuerpo",
                    "topics": ["sleep_health"],
                    "is_abstract": True,
                    "year": 2023,
                },
            },
            {
                "id": "doc2",
                "score": 0.78,
                "payload": {
                    "text": "Insomnia treatment involves...",
                    "category": "cuerpo",
                    "topics": ["insomnia", "sleep_health"],
                    "is_abstract": False,
                    "year": 2021,
                },
            },
        ]

        record = VectorQueryRecord(
            vector_store="qdrant",
            embedding_model="text-embedding-3-small",
            query_text=query_text,
            top_k=top_k,
            response_payload={"hits": hits},
            confidence_score=0.815,
            filters_applied=filters,
        )
        return [record]

    runner.run.side_effect = mock_run
    return runner


@pytest.fixture
def guardian_retriever(mock_topic_classifier, mock_vector_runner):
    """Instancia de GuardianKnowledgeRetriever con mocks."""
    return GuardianKnowledgeRetriever(
        topic_classifier=mock_topic_classifier,
        vector_runner=mock_vector_runner,
    )


class TestGuardianKnowledgeRetriever:
    """Tests de integración para GuardianKnowledgeRetriever."""

    def test_retrieve_for_mental_with_relevant_topics(self, guardian_retriever, mock_vector_runner):
        """Mental Guardian debe buscar con topics mentales."""
        context = "Estoy muy estresado y ansioso últimamente"
        trace_id = "test-trace-123"

        results = guardian_retriever.retrieve_for_mental(
            trace_id=trace_id,
            context=context,
            user_topics=["mental_health", "stress_response", "sleep_health"],
        )

        # Verificar que se llamó al vector runner
        assert mock_vector_runner.run.called
        call_args = mock_vector_runner.run.call_args

        # Verificar que se pasaron filtros
        filters = call_args.kwargs.get("filters")
        assert filters is not None
        assert filters.category == "mente"
        # Debe filtrar solo topics del dominio mental
        assert set(filters.topics).issubset(set(GUARDIAN_KNOWLEDGE_DOMAINS["mental"]))

        # Verificar resultados
        assert isinstance(results, list)
        assert len(results) > 0
        assert isinstance(results[0], VectorQueryRecord)

    def test_retrieve_for_physical_with_sleep_topics(self, guardian_retriever, mock_vector_runner):
        """Physical Guardian debe buscar con topics físicos."""
        context = "Tengo problemas para dormir y me despierto temprano"
        trace_id = "test-trace-456"

        results = guardian_retriever.retrieve_for_physical(
            trace_id=trace_id,
            context=context,
            user_topics=["sleep_health", "insomnia", "circadian_rhythm"],
        )

        # Verificar filtros
        call_args = mock_vector_runner.run.call_args
        filters = call_args.kwargs.get("filters")

        assert filters is not None
        assert filters.category == "cuerpo"
        assert "sleep_health" in filters.topics
        assert "insomnia" in filters.topics
        assert "circadian_rhythm" in filters.topics
        assert filters.boost_abstracts is True
        assert filters.boost_recent is True

        # Verificar resultados
        assert len(results) > 0

    def test_retrieve_for_spiritual_with_purpose_topics(self, guardian_retriever, mock_vector_runner):
        """Spiritual Guardian debe buscar con topics espirituales."""
        context = "Busco encontrar mi propósito de vida"
        trace_id = "test-trace-789"

        results = guardian_retriever.retrieve_for_spiritual(
            trace_id=trace_id,
            context=context,
            user_topics=["aging_longevity", "mental_health"],
        )

        # Verificar filtros
        call_args = mock_vector_runner.run.call_args
        filters = call_args.kwargs.get("filters")

        assert filters is not None
        assert filters.category == "alma"
        # Solo topics que están en el dominio spiritual
        assert set(filters.topics).issubset(set(GUARDIAN_KNOWLEDGE_DOMAINS["spiritual"]))

        assert len(results) > 0

    def test_retrieve_classifies_topics_if_not_provided(self, guardian_retriever, mock_topic_classifier):
        """Debe clasificar topics si no se proporcionan."""
        context = "Test context"
        trace_id = "test-trace-class"

        guardian_retriever.retrieve_for_mental(
            trace_id=trace_id,
            context=context,
            user_topics=None,  # No se proporcionan topics
        )

        # Verificar que se llamó al clasificador
        mock_topic_classifier.classify.assert_called_once_with(context)

    def test_retrieve_handles_no_relevant_topics(self, guardian_retriever, mock_vector_runner):
        """Debe manejar caso donde no hay topics relevantes en el dominio."""
        context = "Test context"
        trace_id = "test-trace-no-relevant"

        # Topics que NO están en el dominio mental
        results = guardian_retriever.retrieve_for_mental(
            trace_id=trace_id,
            context=context,
            user_topics=["nutrition", "exercise_physiology"],  # Topics de physical, no mental
        )

        # Debe usar fallback con todos los topics del dominio
        call_args = mock_vector_runner.run.call_args
        filters = call_args.kwargs.get("filters")

        assert filters is not None
        assert len(filters.topics) > 0
        # Debe usar topics del dominio mental como fallback
        assert set(filters.topics).issubset(set(GUARDIAN_KNOWLEDGE_DOMAINS["mental"]))

        assert len(results) > 0

    def test_retrieve_handles_vector_query_error(self, guardian_retriever, mock_vector_runner):
        """Debe manejar errores de búsqueda vectorial con fallback."""
        # Simular error en primera llamada, éxito en fallback
        mock_vector_runner.run.side_effect = [
            Exception("Qdrant connection error"),
            [
                VectorQueryRecord(
                    vector_store="qdrant",
                    embedding_model="test",
                    query_text="test",
                    top_k=5,
                    response_payload={"hits": []},
                    confidence_score=0.0,
                )
            ],
        ]

        context = "Test context"
        trace_id = "test-trace-error"

        results = guardian_retriever.retrieve_for_mental(
            trace_id=trace_id,
            context=context,
            user_topics=["mental_health"],
        )

        # Debe intentar fallback
        assert mock_vector_runner.run.call_count == 2
        # Primera llamada con topics, segunda sin topics
        first_call_filters = mock_vector_runner.run.call_args_list[0].kwargs.get("filters")
        second_call_filters = mock_vector_runner.run.call_args_list[1].kwargs.get("filters")

        assert len(first_call_filters.topics) > 0
        assert len(second_call_filters.topics) == 0  # Fallback sin topics

    def test_retrieve_with_custom_top_k(self, guardian_retriever, mock_vector_runner):
        """Debe respetar top_k personalizado."""
        context = "Test context"
        trace_id = "test-trace-topk"

        guardian_retriever.retrieve_for_mental(
            trace_id=trace_id,
            context=context,
            user_topics=["mental_health"],
            top_k=10,
        )

        call_args = mock_vector_runner.run.call_args
        assert call_args.kwargs.get("top_k") == 10


class TestGuardianDomainSeparation:
    """Tests que verifican separación correcta de dominios."""

    def test_mental_domain_topics(self):
        """Verifica topics del dominio mental."""
        mental_topics = GUARDIAN_KNOWLEDGE_DOMAINS["mental"]

        assert "mental_health" in mental_topics
        assert "cognitive_function" in mental_topics
        assert "stress_response" in mental_topics
        assert "neurodegeneration" in mental_topics

        # Topics que NO deben estar en mental
        assert "nutrition" not in mental_topics
        assert "exercise_physiology" not in mental_topics

    def test_physical_domain_topics(self):
        """Verifica topics del dominio físico."""
        physical_topics = GUARDIAN_KNOWLEDGE_DOMAINS["physical"]

        assert "nutrition" in physical_topics
        assert "exercise_physiology" in physical_topics
        assert "sleep_health" in physical_topics
        assert "gut_microbiome" in physical_topics
        assert "metabolism_disorders" in physical_topics

    def test_spiritual_domain_topics(self):
        """Verifica topics del dominio espiritual."""
        spiritual_topics = GUARDIAN_KNOWLEDGE_DOMAINS["spiritual"]

        assert "aging_longevity" in spiritual_topics
        # Overlap intencional con mental
        assert "mental_health" in spiritual_topics
        assert "stress_response" in spiritual_topics

    def test_domains_have_no_unexpected_overlap(self):
        """Verifica que el overlap entre dominios sea solo el esperado."""
        mental = set(GUARDIAN_KNOWLEDGE_DOMAINS["mental"])
        physical = set(GUARDIAN_KNOWLEDGE_DOMAINS["physical"])
        spiritual = set(GUARDIAN_KNOWLEDGE_DOMAINS["spiritual"])

        # Overlap esperado entre mental y spiritual
        expected_overlap = {"mental_health", "stress_response"}
        actual_overlap = mental & spiritual

        assert actual_overlap == expected_overlap

        # No debe haber overlap entre mental y physical
        assert len(mental & physical) == 0


class TestVectorSearchFilters:
    """Tests para VectorSearchFilters."""

    def test_filters_construction(self):
        """Debe construir filtros correctamente."""
        filters = VectorSearchFilters(
            category="mente",
            topics=["mental_health", "stress_response"],
            min_year=2020,
            locale="es-CO",
            boost_abstracts=True,
            boost_recent=True,
        )

        assert filters.category == "mente"
        assert len(filters.topics) == 2
        assert filters.min_year == 2020
        assert filters.locale == "es-CO"
        assert filters.boost_abstracts is True
        assert filters.boost_recent is True

    def test_filters_defaults(self):
        """Debe usar valores por defecto."""
        filters = VectorSearchFilters()

        assert filters.category is None
        assert filters.topics == []
        assert filters.min_year is None
        assert filters.locale is None
        assert filters.boost_abstracts is True
        assert filters.boost_recent is True
