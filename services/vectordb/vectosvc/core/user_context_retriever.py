"""Weighted retrieval service combining user context and general corpus.

This module implements weighted retrieval that prioritizes user-specific context
over general biomedical knowledge, enabling more personalized recommendations.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from loguru import logger
from qdrant_client import models as qm

from vectosvc.config import service_settings, settings
from vectosvc.core.embeddings import Embeddings
from vectosvc.core.qdrant_store import store


class WeightedSearchResult:
    """Result from weighted retrieval combining user context and general corpus."""

    def __init__(
        self,
        doc_id: str,
        text: str,
        score: float,
        weighted_score: float,
        source_collection: str,
        category: str,
        source_type: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ):
        self.doc_id = doc_id
        self.text = text
        self.score = score  # Original cosine similarity score
        self.weighted_score = weighted_score  # Boosted score for ranking
        self.source_collection = source_collection
        self.category = category
        self.source_type = source_type
        self.payload = payload or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "doc_id": self.doc_id,
            "text": self.text,
            "score": round(self.score, 4),
            "weighted_score": round(self.weighted_score, 4),
            "source_collection": self.source_collection,
            "category": self.category,
            "source_type": self.source_type,
            "metadata": self.payload,
        }


class UserContextRetriever:
    """Retriever with weighted search across user_context and general collections.

    Search strategy:
    1. Query user_context collection (filtered by user_id) → boost scores × 1.5
    2. Query general collection (with category/guardian filters) → scores × 1.0
    3. Merge results and re-rank by weighted_score
    4. Return top-K combined results

    This ensures user's personalized context (mood, activity, IKIGAI) has more
    weight than general biomedical literature.
    """

    def __init__(
        self,
        user_context_weight: float = 1.5,
        general_weight: float = 1.0,
        embedding_model: Optional[str] = None,
    ):
        """Initialize weighted retriever.

        Args:
            user_context_weight: Multiplier for user_context scores (default: 1.5)
            general_weight: Multiplier for general corpus scores (default: 1.0)
            embedding_model: Embedding model name (default: from settings)
        """
        self.user_context_weight = user_context_weight
        self.general_weight = general_weight
        self.embedding_service = Embeddings(model_name=embedding_model or settings.embedding_model)

    def weighted_search(
        self,
        query: str,
        user_id: Optional[str] = None,
        category: Optional[str] = None,
        guardian_type: Optional[str] = None,
        topics: Optional[List[str]] = None,
        top_k: int = 10,
        user_context_limit: int = 5,
        general_limit: int = 10,
    ) -> List[WeightedSearchResult]:
        """Perform weighted retrieval across user context and general corpus.

        Args:
            query: Search query text
            user_id: User UUID for filtering user_context collection
            category: Category filter (mente, cuerpo, alma)
            guardian_type: Guardian type for topic filtering (mental, physical, spiritual)
            topics: Explicit topic filters
            top_k: Number of final results to return after merging
            user_context_limit: Max results from user_context collection
            general_limit: Max results from general collection

        Returns:
            List of WeightedSearchResult sorted by weighted_score descending
        """
        start = time.perf_counter()

        # Generate query embedding
        query_vector = self.embedding_service.encode([query])[0].tolist()

        results: List[WeightedSearchResult] = []

        # 1. Search user_context collection (if user_id provided)
        if user_id:
            try:
                user_context_results = self._search_user_context(
                    query_vector=query_vector,
                    user_id=user_id,
                    category=category,
                    limit=user_context_limit,
                )
                logger.info(
                    f"User context search: found {len(user_context_results)} results for user={user_id}"
                )
                results.extend(user_context_results)
            except Exception as exc:
                logger.warning(f"User context search failed for user={user_id}: {exc}")
                # Continue without user context results

        # 2. Search general collection
        try:
            general_results = self._search_general(
                query_vector=query_vector,
                category=category,
                guardian_type=guardian_type,
                topics=topics,
                limit=general_limit,
            )
            logger.info(f"General corpus search: found {len(general_results)} results")
            results.extend(general_results)
        except Exception as exc:
            logger.error(f"General corpus search failed: {exc}")
            # If general search fails but we have user_context results, continue
            if not results:
                raise

        # 3. Sort by weighted_score descending and take top-K
        results.sort(key=lambda r: r.weighted_score, reverse=True)
        final_results = results[:top_k]

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            f"Weighted search completed: query_len={len(query)} user_id={user_id} "
            f"category={category} results={len(final_results)} took_ms={elapsed_ms}"
        )

        return final_results

    def _search_user_context(
        self,
        query_vector: List[float],
        user_id: str,
        category: Optional[str] = None,
        limit: int = 5,
    ) -> List[WeightedSearchResult]:
        """Search user_context collection with boosted scores.

        Args:
            query_vector: Query embedding
            user_id: User UUID filter
            category: Optional category filter
            limit: Max results

        Returns:
            List of WeightedSearchResult with boosted scores
        """
        # Build filter for user_context
        filter_conditions = [
            qm.FieldCondition(key="user_id", match=qm.MatchValue(value=user_id)),
            qm.FieldCondition(key="source_type", match=qm.MatchValue(value="user_context")),
            qm.FieldCondition(key="version", match=qm.MatchValue(value=service_settings.embedding_version)),
        ]

        if category:
            filter_conditions.append(
                qm.FieldCondition(key="category", match=qm.MatchValue(value=category))
            )

        qdrant_filter = qm.Filter(must=filter_conditions)

        # Search user_context collection
        hits = store.client.search(
            collection_name="user_context",
            query_vector=query_vector,
            limit=limit,
            query_filter=qdrant_filter,
            with_payload=True,
            timeout=service_settings.vector_query_timeout,
        )

        results = []
        for hit in hits:
            payload = hit.payload or {}
            results.append(
                WeightedSearchResult(
                    doc_id=payload.get("doc_id", str(hit.id)),
                    text=payload.get("text", ""),
                    score=hit.score,
                    weighted_score=hit.score * self.user_context_weight,  # Boost score
                    source_collection="user_context",
                    category=payload.get("category", "unknown"),
                    source_type=payload.get("source_type"),
                    payload=payload,
                )
            )

        return results

    def _search_general(
        self,
        query_vector: List[float],
        category: Optional[str] = None,
        guardian_type: Optional[str] = None,
        topics: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[WeightedSearchResult]:
        """Search general collection (holistic_agents corpus).

        Args:
            query_vector: Query embedding
            category: Optional category filter
            guardian_type: Guardian type for topic filtering
            topics: Explicit topic filters
            limit: Max results

        Returns:
            List of WeightedSearchResult with standard scores
        """
        # Build filter for general collection
        filter_conditions = [
            qm.FieldCondition(
                key="version", match=qm.MatchValue(value=service_settings.embedding_version)
            ),
        ]

        if category:
            filter_conditions.append(
                qm.FieldCondition(key="category", match=qm.MatchValue(value=category))
            )

        # Guardian-specific topic filtering
        if guardian_type and not topics:
            topics = self._get_guardian_topics(guardian_type)

        if topics:
            filter_conditions.append(
                qm.FieldCondition(key="topics", match=qm.MatchAny(any=topics))
            )

        qdrant_filter = qm.Filter(must=filter_conditions)

        # Search general collection
        collection_name = settings.collection_name  # Default holistic_agents collection
        hits = store.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=qdrant_filter,
            with_payload=True,
            timeout=service_settings.vector_query_timeout,
        )

        results = []
        for hit in hits:
            payload = hit.payload or {}
            results.append(
                WeightedSearchResult(
                    doc_id=payload.get("doc_id", str(hit.id)),
                    text=payload.get("text", ""),
                    score=hit.score,
                    weighted_score=hit.score * self.general_weight,  # Standard score
                    source_collection=collection_name,
                    category=payload.get("category", "unknown"),
                    source_type=payload.get("source_type"),
                    payload=payload,
                )
            )

        return results

    def _get_guardian_topics(self, guardian_type: str) -> List[str]:
        """Map guardian type to relevant topics.

        Args:
            guardian_type: mental, physical, or spiritual

        Returns:
            List of topic IDs relevant to the guardian
        """
        # Topic mappings for each Guardian type
        GUARDIAN_TOPICS = {
            "mental": [
                "mental_health",
                "stress_response",
                "cognitive_function",
                "sleep_disorders",
                "anxiety",
                "depression",
                "mindfulness",
                "neuroplasticity",
                "mood_regulation",
            ],
            "physical": [
                "cardiovascular_health",
                "exercise_physiology",
                "nutrition",
                "metabolic_health",
                "physical_activity",
                "chronic_disease",
                "body_composition",
                "injury_prevention",
                "rehabilitation",
            ],
            "spiritual": [
                "holistic_health",
                "mind_body_connection",
                "life_purpose",
                "well_being",
                "resilience",
                "personal_growth",
                "meaning_making",
                "social_connection",
            ],
        }

        return GUARDIAN_TOPICS.get(guardian_type.lower(), [])
