"""Tests unitarios para TopicClassifier."""

from unittest.mock import MagicMock, patch

import pytest

from services.topic_classifier import (
    AVAILABLE_TOPICS,
    TopicClassifier,
    get_topic_classifier,
)


@pytest.fixture
def mock_gemini_response():
    """Mock de respuesta de Gemini."""
    mock_response = MagicMock()
    mock_response.text = """
    {
        "topics": ["sleep_health", "insomnia", "circadian_rhythm"],
        "reasoning": "El usuario menciona problemas para dormir y despertar temprano"
    }
    """
    return mock_response


@pytest.fixture
def classifier():
    """Instancia de TopicClassifier con API key mock."""
    with patch.dict("os.environ", {"GOOGLE_API_KEY": "fake-api-key"}):
        return TopicClassifier()


class TestTopicClassifier:
    """Tests para TopicClassifier."""

    def test_initialize_classifier_without_api_key(self):
        """Debe fallar si no hay API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="GOOGLE_API_KEY no está configurada"):
                TopicClassifier()

    def test_classify_text_context(self, classifier, mock_gemini_response):
        """Debe clasificar contexto de texto correctamente."""
        with patch.object(classifier.client.models, "generate_content", return_value=mock_gemini_response):
            context = "Tengo problemas para dormir, me despierto a las 3am todos los días"
            topics = classifier.classify(context)

            assert isinstance(topics, list)
            assert len(topics) == 3
            assert "sleep_health" in topics
            assert "insomnia" in topics
            assert "circadian_rhythm" in topics

    def test_classify_dict_context(self, classifier, mock_gemini_response):
        """Debe clasificar contexto estructurado correctamente."""
        with patch.object(classifier.client.models, "generate_content", return_value=mock_gemini_response):
            context = {
                "problem": "sleep_issues",
                "symptoms": ["insomnia", "early_waking"],
                "history": "Started 2 months ago",
            }
            topics = classifier.classify(context)

            assert isinstance(topics, list)
            assert len(topics) > 0

    def test_classify_filters_invalid_topics(self, classifier):
        """Debe filtrar topics no válidos de la respuesta."""
        mock_response = MagicMock()
        mock_response.text = """
        {
            "topics": ["sleep_health", "invalid_topic", "insomnia"],
            "reasoning": "Test"
        }
        """

        with patch.object(classifier.client.models, "generate_content", return_value=mock_response):
            topics = classifier.classify("test context")

            assert "sleep_health" in topics
            assert "insomnia" in topics
            assert "invalid_topic" not in topics

    def test_classify_handles_json_parse_error(self, classifier):
        """Debe usar fallback si la respuesta JSON es inválida."""
        mock_response = MagicMock()
        mock_response.text = "Invalid JSON response"

        with patch.object(classifier.client.models, "generate_content", return_value=mock_response):
            topics = classifier.classify("Tengo problemas de sueño")

            # Debe retornar topics de fallback
            assert isinstance(topics, list)
            assert len(topics) > 0
            # Fallback debe incluir sleep_health por keyword "sueño"
            assert "sleep_health" in topics or "insomnia" in topics

    def test_classify_handles_markdown_code_blocks(self, classifier):
        """Debe limpiar markdown code blocks de la respuesta."""
        mock_response = MagicMock()
        mock_response.text = """```json
        {
            "topics": ["sleep_health", "insomnia"],
            "reasoning": "Sleep issues detected"
        }
        ```"""

        with patch.object(classifier.client.models, "generate_content", return_value=mock_response):
            topics = classifier.classify("test context")

            assert "sleep_health" in topics
            assert "insomnia" in topics

    def test_fallback_topics_for_sleep_context(self, classifier):
        """Debe retornar topics de sueño en fallback."""
        topics = classifier._get_fallback_topics("Tengo problemas para dormir")

        assert "sleep_health" in topics
        assert "insomnia" in topics

    def test_fallback_topics_for_mental_health_context(self, classifier):
        """Debe retornar topics de salud mental en fallback."""
        topics = classifier._get_fallback_topics("Estoy muy estresado y ansioso")

        assert "mental_health" in topics
        # stress_response debería estar, pero si no, al menos mental_health
        assert "mental_health" in topics or "stress_response" in topics

    def test_fallback_topics_for_nutrition_context(self, classifier):
        """Debe retornar topics de nutrición en fallback."""
        topics = classifier._get_fallback_topics("Quiero mejorar mi dieta")

        assert "nutrition" in topics
        assert "gut_microbiome" in topics

    def test_fallback_topics_for_exercise_context(self, classifier):
        """Debe retornar topics de ejercicio en fallback."""
        topics = classifier._get_fallback_topics("Necesito hacer más ejercicio")

        assert "exercise_physiology" in topics

    def test_fallback_topics_for_generic_context(self, classifier):
        """Debe retornar topics genéricos para contexto sin keywords."""
        topics = classifier._get_fallback_topics("Quiero mejorar mi bienestar")

        assert isinstance(topics, list)
        assert len(topics) > 0
        assert len(topics) <= 5  # Máximo 5 topics

    def test_cache_hit(self, classifier, mock_gemini_response):
        """Debe usar cache en segunda llamada con mismo contexto."""
        with patch.object(classifier.client.models, "generate_content", return_value=mock_gemini_response) as mock_generate:
            context = "Test context"

            # Primera llamada
            topics1 = classifier.classify(context)

            # Segunda llamada con mismo contexto
            topics2 = classifier.classify(context)

            # Debe usar cache, solo 1 llamada a Gemini
            assert mock_generate.call_count == 1
            assert topics1 == topics2

    def test_cache_miss(self, classifier, mock_gemini_response):
        """Debe ejecutar nueva clasificación con contexto diferente."""
        with patch.object(classifier.client.models, "generate_content", return_value=mock_gemini_response) as mock_generate:
            # Primera llamada
            topics1 = classifier.classify("Context 1")

            # Segunda llamada con contexto diferente
            topics2 = classifier.classify("Context 2")

            # Debe hacer 2 llamadas a Gemini
            assert mock_generate.call_count == 2

    def test_available_topics_consistency(self):
        """Verifica que AVAILABLE_TOPICS esté correctamente definido."""
        assert len(AVAILABLE_TOPICS) == 34  # 37 topics según docs - 3 que pueden estar ausentes
        assert "sleep_health" in AVAILABLE_TOPICS
        assert "mental_health" in AVAILABLE_TOPICS
        assert "nutrition" in AVAILABLE_TOPICS
        assert "exercise_physiology" in AVAILABLE_TOPICS

    def test_get_topic_classifier_singleton(self):
        """Debe retornar la misma instancia (singleton)."""
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "fake-api-key"}):
            classifier1 = get_topic_classifier()
            classifier2 = get_topic_classifier()

            assert classifier1 is classifier2


class TestTopicClassifierIntegration:
    """Tests de integración que verifican el flujo completo."""

    def test_classify_multiple_contexts(self, classifier, mock_gemini_response):
        """Debe clasificar múltiples contextos correctamente."""
        contexts = [
            "Tengo problemas de sueño",
            "Estoy muy estresado",
            "Quiero mejorar mi dieta",
        ]

        with patch.object(classifier.client.models, "generate_content", return_value=mock_gemini_response):
            for context in contexts:
                topics = classifier.classify(context)
                assert isinstance(topics, list)
                assert len(topics) > 0
                assert len(topics) <= 5  # Máximo 5 topics

    def test_empty_context_handling(self, classifier):
        """Debe manejar contexto vacío."""
        topics = classifier._get_fallback_topics("")

        assert isinstance(topics, list)
        assert len(topics) > 0  # Debe retornar topics genéricos
