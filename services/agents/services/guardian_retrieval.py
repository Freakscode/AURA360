"""
Servicio de recuperación especializada de conocimiento por Guardian.

Cada Guardian (mental, physical, spiritual) tiene su propio dominio de topics
y estrategia de búsqueda optimizada.
"""

from __future__ import annotations

import logging
from typing import Optional
import requests

from infra.settings import GUARDIAN_KNOWLEDGE_DOMAINS, ServiceSettings, get_settings

from .topic_classifier import TopicClassifier, get_topic_classifier
from .vector_queries import VectorQueryRecord, VectorQueryRunner, VectorSearchFilters

logger = logging.getLogger(__name__)


class GuardianKnowledgeRetriever:
    """Recuperación especializada de conocimiento por Guardian."""

    def __init__(
        self,
        *,
        settings: Optional[ServiceSettings] = None,
        topic_classifier: Optional[TopicClassifier] = None,
        vector_runner: Optional[VectorQueryRunner] = None,
    ):
        """
        Inicializa el retriever.

        Args:
            settings: Configuración del servicio
            topic_classifier: Clasificador de topics (usa singleton si no se proporciona)
            vector_runner: Runner de queries vectoriales
        """
        self._settings = settings or get_settings()
        self._classifier = topic_classifier or get_topic_classifier()
        self._vector_runner = vector_runner or VectorQueryRunner(settings=self._settings)

    def retrieve_for_mental(
        self,
        *,
        trace_id: str,
        context: str,
        user_topics: list[str] | None = None,
        top_k: int | None = None,
    ) -> list[VectorQueryRecord]:
        """
        Recupera conocimiento especializado para Mental Guardian.

        Topics: mental_health, cognitive_function, neurodegeneration, stress_response, etc.

        Args:
            trace_id: ID de trazabilidad
            context: Contexto del usuario
            user_topics: Topics detectados del usuario (si ya se clasificó)
            top_k: Número de resultados a retornar

        Returns:
            Lista de records con resultados de búsqueda
        """
        return self._retrieve_for_guardian(
            trace_id=trace_id,
            guardian_type="mental",
            context=context,
            user_topics=user_topics,
            top_k=top_k,
        )

    def retrieve_for_physical(
        self,
        *,
        trace_id: str,
        context: str,
        user_topics: list[str] | None = None,
        top_k: int | None = None,
    ) -> list[VectorQueryRecord]:
        """
        Recupera conocimiento especializado para Physical Guardian.

        Topics: nutrition, exercise_physiology, sleep_health, gut_microbiome, etc.

        Args:
            trace_id: ID de trazabilidad
            context: Contexto del usuario
            user_topics: Topics detectados del usuario (si ya se clasificó)
            top_k: Número de resultados a retornar

        Returns:
            Lista de records con resultados de búsqueda
        """
        return self._retrieve_for_guardian(
            trace_id=trace_id,
            guardian_type="physical",
            context=context,
            user_topics=user_topics,
            top_k=top_k,
        )

    def retrieve_for_spiritual(
        self,
        *,
        trace_id: str,
        context: str,
        user_topics: list[str] | None = None,
        top_k: int | None = None,
    ) -> list[VectorQueryRecord]:
        """
        Recupera conocimiento especializado para Spiritual Guardian.

        Topics: aging_longevity, mental_health (overlap), stress_response (overlap),
                reproductive_health, pcos, adolescent_health.

        Args:
            trace_id: ID de trazabilidad
            context: Contexto del usuario
            user_topics: Topics detectados del usuario (si ya se clasificó)
            top_k: Número de resultados a retornar

        Returns:
            Lista de records con resultados de búsqueda
        """
        return self._retrieve_for_guardian(
            trace_id=trace_id,
            guardian_type="spiritual",
            context=context,
            user_topics=user_topics,
            top_k=top_k,
        )

    def retrieve_weighted(
        self,
        *,
        trace_id: str,
        context: str,
        user_id: Optional[str] = None,
        guardian_type: str,
        user_topics: list[str] | None = None,
        top_k: int | None = None,
        user_context_limit: int = 5,
        general_limit: int = 10,
    ) -> list[VectorQueryRecord]:
        """
        Recupera conocimiento con weighted retrieval (user_context × 1.5 + general × 1.0).

        Este método integra el contexto personalizado del usuario (mood, actividad, IKIGAI)
        con el corpus general de conocimiento, dando mayor peso al contexto del usuario.

        Args:
            trace_id: ID de trazabilidad
            context: Contexto del usuario
            user_id: UUID del usuario para filtrar user_context
            guardian_type: Tipo de Guardian (mental, physical, spiritual)
            user_topics: Topics detectados del usuario
            top_k: Número de resultados finales a retornar
            user_context_limit: Max resultados de user_context
            general_limit: Max resultados de corpus general

        Returns:
            Lista de VectorQueryRecord con resultados ordenados por weighted_score
        """
        if user_topics is None:
            user_topics = self._classifier.classify(context)
            logger.info(
                f"WeightedRetrieval[{guardian_type}]: Topics clasificados: {user_topics}",
                extra={"trace_id": trace_id},
            )

        # Mapear guardian_type a categoría en vectordb
        category_mapping = {
            "mental": "mente",
            "physical": "cuerpo",
            "spiritual": "alma",
        }
        category = category_mapping.get(guardian_type)

        # Obtener dominio de conocimiento del Guardian para filtrado de topics
        guardian_domain = GUARDIAN_KNOWLEDGE_DOMAINS.get(guardian_type, [])
        relevant_topics = list(set(user_topics) & set(guardian_domain)) if guardian_domain else []

        if not relevant_topics and guardian_domain:
            # Fallback: usar topics del dominio del Guardian
            relevant_topics = guardian_domain[:5]

        logger.info(
            f"WeightedRetrieval[{guardian_type}]: Llamando weighted search con {len(relevant_topics or [])} topics",
            extra={"trace_id": trace_id, "user_id": user_id, "relevant_topics": relevant_topics},
        )

        # Llamar al endpoint de weighted search en vectordb service
        try:
            vectordb_url = self._settings.vectordb_service_url
            response = requests.post(
                f"{vectordb_url}/api/v1/holistic/weighted-search",
                json={
                    "trace_id": trace_id,
                    "query": context,
                    "user_id": user_id,
                    "category": category,
                    "guardian_type": guardian_type,
                    "topics": relevant_topics if relevant_topics else None,
                    "top_k": top_k or self._settings.vector_top_k,
                    "user_context_limit": user_context_limit,
                    "general_limit": general_limit,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "success":
                error_msg = data.get("error", {}).get("message", "Unknown error")
                logger.error(
                    f"WeightedRetrieval[{guardian_type}]: API returned error: {error_msg}",
                    extra={"trace_id": trace_id},
                )
                raise Exception(f"Weighted search failed: {error_msg}")

            # Convertir respuesta a VectorQueryRecord format
            results_data = data.get("data", {}).get("results", [])
            meta = data.get("meta", {})

            # Construir hits en formato compatible con VectorQueryRecord
            hits = []
            for result in results_data:
                hits.append({
                    "id": result.get("doc_id"),
                    "score": result.get("weighted_score"),  # Usar weighted_score para ranking
                    "payload": {
                        "text": result.get("text"),
                        "doc_id": result.get("doc_id"),
                        "category": result.get("category"),
                        "source_type": result.get("source_type"),
                        "source_collection": result.get("source_collection"),
                        "original_score": result.get("score"),  # Preservar score original
                        "weighted_score": result.get("weighted_score"),
                        **result.get("metadata", {}),
                    },
                })

            record = VectorQueryRecord(
                query_text=context,
                top_k=len(hits),
                response_payload={"hits": hits},
                latency_ms=meta.get("took_ms", 0),
            )

            logger.info(
                f"WeightedRetrieval[{guardian_type}]: Recuperados {len(hits)} resultados "
                f"(user_context: {sum(1 for h in hits if h['payload'].get('source_collection') == 'user_context')}, "
                f"general: {sum(1 for h in hits if h['payload'].get('source_collection') != 'user_context')})",
                extra={"trace_id": trace_id},
            )

            return [record]

        except requests.RequestException as exc:
            logger.error(
                f"WeightedRetrieval[{guardian_type}]: HTTP error calling weighted search: {exc}",
                extra={"trace_id": trace_id},
            )
            # Fallback a búsqueda tradicional sin weighted
            logger.info(
                f"WeightedRetrieval[{guardian_type}]: Falling back to traditional retrieval",
                extra={"trace_id": trace_id},
            )
            return self._retrieve_for_guardian(
                trace_id=trace_id,
                guardian_type=guardian_type,
                context=context,
                user_topics=user_topics,
                top_k=top_k,
            )
        except Exception as exc:
            logger.error(
                f"WeightedRetrieval[{guardian_type}]: Unexpected error in weighted retrieval: {exc}",
                extra={"trace_id": trace_id},
            )
            # Fallback a búsqueda tradicional
            return self._retrieve_for_guardian(
                trace_id=trace_id,
                guardian_type=guardian_type,
                context=context,
                user_topics=user_topics,
                top_k=top_k,
            )

    def _retrieve_for_guardian(
        self,
        *,
        trace_id: str,
        guardian_type: str,
        context: str,
        user_topics: list[str] | None,
        top_k: int | None,
    ) -> list[VectorQueryRecord]:
        """
        Implementación interna de recuperación especializada.

        Args:
            trace_id: ID de trazabilidad
            guardian_type: Tipo de Guardian (mental, physical, spiritual)
            context: Contexto del usuario
            user_topics: Topics detectados del usuario
            top_k: Número de resultados

        Returns:
            Lista de records con resultados
        """
        # Clasificar contexto si no se proporcionaron topics
        if user_topics is None:
            user_topics = self._classifier.classify(context)
            logger.info(
                f"GuardianRetrieval[{guardian_type}]: Topics clasificados: {user_topics}",
                extra={"trace_id": trace_id},
            )

        # Obtener dominio de conocimiento del Guardian
        guardian_domain = GUARDIAN_KNOWLEDGE_DOMAINS.get(guardian_type, [])
        if not guardian_domain:
            logger.warning(
                f"GuardianRetrieval[{guardian_type}]: No se encontró dominio de conocimiento",
                extra={"trace_id": trace_id},
            )
            guardian_domain = []

        # Filtrar topics relevantes: intersección entre user_topics y guardian_domain
        relevant_topics = list(set(user_topics) & set(guardian_domain))

        if not relevant_topics:
            logger.info(
                f"GuardianRetrieval[{guardian_type}]: Sin topics relevantes en el dominio. "
                f"Usando dominio completo como fallback.",
                extra={"trace_id": trace_id, "user_topics": user_topics, "guardian_domain": guardian_domain},
            )
            # Fallback: usar todos los topics del dominio del Guardian
            relevant_topics = guardian_domain[:5]  # Limitar a 5 para no hacer filtro muy amplio

        logger.info(
            f"GuardianRetrieval[{guardian_type}]: Buscando con {len(relevant_topics)} topics: {relevant_topics}",
            extra={"trace_id": trace_id},
        )

        # Mapear guardian_type a categoría en vectordb
        category_mapping = {
            "mental": "mente",
            "physical": "cuerpo",
            "spiritual": "alma",
        }
        category = category_mapping.get(guardian_type)

        # Construir filtros
        filters = VectorSearchFilters(
            category=category,
            topics=relevant_topics,
            boost_abstracts=True,  # Priorizar abstracts/conclusions
            boost_recent=True,  # Priorizar papers recientes (2015+)
        )

        # Ejecutar búsqueda vectorial
        try:
            results = self._vector_runner.run(
                trace_id=trace_id,
                query_text=context,
                top_k=top_k,
                filters=filters,
            )

            logger.info(
                f"GuardianRetrieval[{guardian_type}]: Búsqueda completada con {len(results)} records",
                extra={"trace_id": trace_id},
            )

            return results

        except Exception as exc:
            logger.error(
                f"GuardianRetrieval[{guardian_type}]: Error en búsqueda vectorial: {exc}",
                extra={"trace_id": trace_id},
            )
            # Intentar fallback sin filtros de topics
            logger.info(
                f"GuardianRetrieval[{guardian_type}]: Intentando fallback sin filtros de topics",
                extra={"trace_id": trace_id},
            )
            try:
                fallback_filters = VectorSearchFilters(
                    category=category,
                    topics=[],  # Sin filtro de topics
                    boost_abstracts=True,
                    boost_recent=True,
                )
                results = self._vector_runner.run(
                    trace_id=trace_id,
                    query_text=context,
                    top_k=top_k,
                    filters=fallback_filters,
                )
                logger.info(
                    f"GuardianRetrieval[{guardian_type}]: Fallback exitoso con {len(results)} records",
                    extra={"trace_id": trace_id},
                )
                return results
            except Exception as fallback_exc:
                logger.error(
                    f"GuardianRetrieval[{guardian_type}]: Fallback también falló: {fallback_exc}",
                    extra={"trace_id": trace_id},
                )
                # Retornar lista vacía en caso de fallo total
                return []


__all__ = ["GuardianKnowledgeRetriever"]
