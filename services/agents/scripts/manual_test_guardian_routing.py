#!/usr/bin/env python3
"""
Script de validación de guardian routing especializado.

Envía requests de prueba a diferentes categorías y verifica que:
1. Los topics se clasifican correctamente
2. Cada Guardian recibe documentos de su dominio especializado
3. El boosting funciona (abstracts y papers recientes tienen mayor score)

Uso:
    python scripts/test_guardian_routing.py
"""

import json
import logging
import sys
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from infra.settings import GUARDIAN_KNOWLEDGE_DOMAINS
from services.guardian_retrieval import GuardianKnowledgeRetriever
from services.topic_classifier import get_topic_classifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Casos de prueba por categoría
TEST_CASES = {
    "mental": [
        {
            "context": "Últimamente me siento muy estresado y ansioso, tengo dificultad para concentrarme en el trabajo",
            "expected_topics": ["mental_health", "stress_response", "cognitive_function"],
        },
        {
            "context": "He notado problemas de memoria y olvido frecuente de cosas importantes",
            "expected_topics": ["cognitive_function", "mental_health"],
        },
    ],
    "physical": [
        {
            "context": "Tengo problemas para dormir, me despierto a las 3am y no puedo volver a dormir",
            "expected_topics": ["sleep_health", "insomnia", "circadian_rhythm"],
        },
        {
            "context": "Quiero mejorar mi alimentación y perder peso de forma saludable",
            "expected_topics": ["nutrition", "obesity", "metabolism_disorders"],
        },
        {
            "context": "Necesito una rutina de ejercicio que se adapte a mi estilo de vida sedentario",
            "expected_topics": ["exercise_physiology", "cardiovascular_health"],
        },
    ],
    "spiritual": [
        {
            "context": "Siento que me falta un propósito claro en la vida, quiero encontrar mi ikigai",
            "expected_topics": ["aging_longevity", "mental_health"],
        },
        {
            "context": "Tengo 18 años y no sé qué carrera estudiar, me siento perdido",
            "expected_topics": ["adolescent_health", "mental_health"],
        },
    ],
}


def validate_topic_classification():
    """Valida que el clasificador de topics funciona correctamente."""
    logger.info("=" * 80)
    logger.info("VALIDANDO CLASIFICACIÓN DE TOPICS")
    logger.info("=" * 80)

    classifier = get_topic_classifier()
    all_passed = True

    for category, test_cases in TEST_CASES.items():
        logger.info(f"\n🔍 Categoría: {category.upper()}")

        for i, test_case in enumerate(test_cases, 1):
            context = test_case["context"]
            expected = test_case["expected_topics"]

            logger.info(f"\n  Test {i}:")
            logger.info(f"    Contexto: {context[:80]}...")

            try:
                topics = classifier.classify(context)
                logger.info(f"    ✅ Topics clasificados: {topics}")

                # Verificar si algún topic esperado está presente
                found = any(topic in topics for topic in expected)
                if found:
                    logger.info(f"    ✅ Al menos un topic esperado encontrado")
                else:
                    logger.warning(f"    ⚠️  Topics esperados: {expected}")
                    logger.warning(f"    ⚠️  Ningún topic esperado encontrado")
                    all_passed = False

            except Exception as e:
                logger.error(f"    ❌ Error clasificando: {e}")
                all_passed = False

    return all_passed


def validate_guardian_routing():
    """Valida que el routing a cada Guardian funciona correctamente."""
    logger.info("\n" + "=" * 80)
    logger.info("VALIDANDO ROUTING POR GUARDIAN")
    logger.info("=" * 80)

    retriever = GuardianKnowledgeRetriever()
    all_passed = True

    guardian_methods = {
        "mental": retriever.retrieve_for_mental,
        "physical": retriever.retrieve_for_physical,
        "spiritual": retriever.retrieve_for_spiritual,
    }

    for category, test_cases in TEST_CASES.items():
        logger.info(f"\n🧠 Guardian: {category.upper()}")
        retrieve_method = guardian_methods[category]

        for i, test_case in enumerate(test_cases, 1):
            context = test_case["context"]

            logger.info(f"\n  Test {i}:")
            logger.info(f"    Contexto: {context[:80]}...")

            try:
                results = retrieve_method(
                    trace_id=f"test-{category}-{i}",
                    context=context,
                    top_k=5,
                )

                if not results:
                    logger.warning(f"    ⚠️  Sin resultados de búsqueda")
                    continue

                record = results[0]
                hits = record.response_payload.get("hits", [])

                logger.info(f"    ✅ Documentos encontrados: {len(hits)}")
                logger.info(f"    📊 Confidence score: {record.confidence_score:.4f}")

                # Verificar filtros aplicados
                if record.filters_applied:
                    logger.info(f"    🔧 Filtros aplicados:")
                    logger.info(f"       - Categoría: {record.filters_applied.category}")
                    logger.info(f"       - Topics: {record.filters_applied.topics}")
                    logger.info(f"       - Boost abstracts: {record.filters_applied.boost_abstracts}")
                    logger.info(f"       - Boost recientes: {record.filters_applied.boost_recent}")

                    # Verificar que los topics están en el dominio del Guardian
                    guardian_domain = set(GUARDIAN_KNOWLEDGE_DOMAINS[category])
                    filtered_topics = set(record.filters_applied.topics)

                    if filtered_topics.issubset(guardian_domain):
                        logger.info(f"    ✅ Topics dentro del dominio del Guardian")
                    else:
                        logger.warning(f"    ⚠️  Algunos topics fuera del dominio")
                        all_passed = False

                # Analizar documentos retornados
                if hits:
                    logger.info(f"    📄 Top 3 documentos:")
                    for j, hit in enumerate(hits[:3], 1):
                        score = hit.get("score", 0)
                        payload = hit.get("payload", {})
                        doc_topics = payload.get("topics", [])
                        is_abstract = payload.get("is_abstract", False)
                        year = payload.get("year", "N/A")
                        boost_applied = hit.get("boost_applied", 0.0)

                        logger.info(f"       {j}. Score: {score:.4f} (boost: +{boost_applied:.2f})")
                        logger.info(f"          Topics: {doc_topics}")
                        logger.info(f"          Abstract: {is_abstract} | Año: {year}")

            except Exception as e:
                logger.error(f"    ❌ Error en búsqueda: {e}")
                all_passed = False

    return all_passed


def validate_boosting():
    """Valida que el boosting de metadata funciona."""
    logger.info("\n" + "=" * 80)
    logger.info("VALIDANDO BOOSTING DE METADATA")
    logger.info("=" * 80)

    retriever = GuardianKnowledgeRetriever()
    context = "Necesito información sobre técnicas de manejo de estrés y ansiedad"

    logger.info(f"\n🔍 Contexto de prueba: {context}")

    try:
        results = retriever.retrieve_for_mental(
            trace_id="test-boosting",
            context=context,
            top_k=10,
        )

        if not results:
            logger.warning("⚠️  Sin resultados para validar boosting")
            return False

        record = results[0]
        hits = record.response_payload.get("hits", [])

        # Analizar distribución de boosting
        abstract_count = 0
        recent_count = 0
        total_boost = 0.0

        for hit in hits:
            payload = hit.get("payload", {})
            boost = hit.get("boost_applied", 0.0)
            total_boost += boost

            if payload.get("is_abstract") or payload.get("is_conclusion"):
                abstract_count += 1

            year = payload.get("year", 0)
            if year >= 2020:
                recent_count += 1

        logger.info(f"\n📊 Estadísticas de boosting:")
        logger.info(f"   - Documentos con boost: {sum(1 for h in hits if h.get('boost_applied', 0) > 0)}/{len(hits)}")
        logger.info(f"   - Abstracts/Conclusions: {abstract_count}")
        logger.info(f"   - Papers recientes (2020+): {recent_count}")
        logger.info(f"   - Boost promedio: {total_boost / len(hits):.4f}")

        # Verificar que al menos algunos documentos tienen boost
        boosted_count = sum(1 for h in hits if h.get("boost_applied", 0) > 0)
        if boosted_count > 0:
            logger.info(f"✅ Boosting funcionando correctamente")
            return True
        else:
            logger.warning(f"⚠️  Ningún documento tiene boost aplicado")
            return False

    except Exception as e:
        logger.error(f"❌ Error validando boosting: {e}")
        return False


def main():
    """Ejecuta todas las validaciones."""
    logger.info("\n" + "=" * 80)
    logger.info("VALIDACIÓN DE GUARDIAN ROUTING ESPECIALIZADO")
    logger.info("=" * 80)

    try:
        # Validar clasificación de topics
        topics_ok = validate_topic_classification()

        # Validar routing por Guardian
        routing_ok = validate_guardian_routing()

        # Validar boosting
        boosting_ok = validate_boosting()

        # Resumen final
        logger.info("\n" + "=" * 80)
        logger.info("RESUMEN DE VALIDACIÓN")
        logger.info("=" * 80)
        logger.info(f"✅ Clasificación de topics: {'PASSED' if topics_ok else 'FAILED'}")
        logger.info(f"✅ Routing por Guardian: {'PASSED' if routing_ok else 'FAILED'}")
        logger.info(f"✅ Boosting de metadata: {'PASSED' if boosting_ok else 'FAILED'}")

        all_passed = topics_ok and routing_ok and boosting_ok

        if all_passed:
            logger.info("\n🎉 Todas las validaciones pasaron correctamente!")
            return 0
        else:
            logger.warning("\n⚠️  Algunas validaciones fallaron. Revisa los logs arriba.")
            return 1

    except Exception as e:
        logger.error(f"\n❌ Error durante la validación: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
