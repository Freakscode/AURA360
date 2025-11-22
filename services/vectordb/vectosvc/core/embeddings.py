from __future__ import annotations

import hashlib
from typing import Dict, Iterable, List, Optional, Tuple
import os
import numpy as np
from loguru import logger
import redis

from vectosvc.config import settings


class Embeddings:
    """Wrapper around FastEmbed with Redis caching (namespaced por modelo).

    El caché utiliza Redis para almacenar embeddings ya calculados,
    reduciendo significativamente el tiempo de procesamiento para textos
    repetidos o similares.

    Estrategia de caché:
    - Key: emb:v2:{hash(model_name)}:{sha256(text)[:16]}
    - Value: numpy array serializado como bytes
    - TTL: configurable (default 7 días)

    Usage:
        emb = Embeddings()
        vecs = emb.encode(["hola mundo"])  # -> np.ndarray (n, d)
    """

    def __init__(self, model_name: str | None = None, redis_client: Optional[redis.Redis] = None):
        self.model_name = model_name or settings.embedding_model
        self._impl = None
        self.dim: Optional[int] = None
        self.is_gemini = self.model_name.startswith("gemini-embedding")
        self.cache_enabled = settings.cache_embeddings
        self._cache_prefix = self._build_cache_prefix(self.model_name)
        
        # Métricas de caché
        self.cache_hits = 0
        self.cache_misses = 0

        # Redis client para caché
        self._redis: Optional[redis.Redis] = redis_client
        if self.cache_enabled and self._redis is None:
            try:
                # Extraer host y puerto del broker_url
                # Format: redis://host:port/db
                url_parts = settings.broker_url.replace("redis://", "").split("/")
                host_port = url_parts[0].split(":")
                host = host_port[0] if len(host_port) > 0 else "localhost"
                port = int(host_port[1]) if len(host_port) > 1 else 6379
                db = 2  # Use DB 2 for cache (0=broker, 1=results)
                
                self._redis = redis.Redis(host=host, port=port, db=db, decode_responses=False)
                self._redis.ping()  # Test connection
                logger.info("Redis cache initialized for embeddings ({}:{})", host, port)
            except Exception as e:
                logger.warning("Redis cache unavailable ({}), proceeding without cache", e)
                self.cache_enabled = False
                self._redis = None

        if self.is_gemini:
            try:
                from google import genai  # type: ignore
                from google.genai import types  # noqa: F401

                api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
                if not api_key:
                    raise RuntimeError("Falta GOOGLE_API_KEY/GEMINI_API_KEY para gemini-embedding")
                self._gemini_client = genai.Client(api_key=api_key)
                self.dim = settings.embedding_dim
                logger.info("Gemini embedding client inicializado: {}", self.model_name)
            except Exception as e:  # pragma: no cover
                logger.warning("Gemini client no disponible ({}).", e)
                self._gemini_client = None
        else:
            try:
                from fastembed import TextEmbedding

                self._impl = TextEmbedding(model_name=self.model_name)
                logger.info("FastEmbed model loaded: {}", self.model_name)
            except Exception as e:  # pragma: no cover
                logger.warning(
                    "FastEmbed not available ({}). Falling back to random embeddings; install fastembed.",
                    e,
                )
                self._impl = None

    def _build_cache_prefix(self, model_name: str) -> str:
        """Construye un prefijo estable por modelo para las keys de caché."""
        model_hash = hashlib.sha256(model_name.encode("utf-8")).hexdigest()[:8]
        return f"emb:v2:{model_hash}:"

    def _text_key(self, text: str) -> str:
        """Genera una key de Redis para un texto dado."""
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        return f"{self._cache_prefix}{text_hash}"

    def _get_cached(self, texts: List[str]) -> Tuple[Dict[int, np.ndarray], List[int]]:
        """
        Busca embeddings en caché.
        
        Returns:
            - Dict[int, np.ndarray]: Mapa de índice -> vector para hits
            - List[int]: Índices de textos no encontrados (misses)
        """
        cached: Dict[int, np.ndarray] = {}
        misses: List[int] = []

        if not self.cache_enabled or self._redis is None:
            return cached, list(range(len(texts)))

        try:
            # Batch GET con pipeline
            pipe = self._redis.pipeline(transaction=False)
            keys = [self._text_key(text) for text in texts]
            for key in keys:
                pipe.get(key)
            results = pipe.execute()

            for idx, value in enumerate(results):
                if value is not None:
                    try:
                        # Deserializar numpy array
                        vec = np.frombuffer(value, dtype=np.float32)
                        if vec.size > 0:
                            cached[idx] = vec
                            self.cache_hits += 1
                            if self.dim is None:
                                self.dim = int(vec.shape[0])
                        else:
                            misses.append(idx)
                            self.cache_misses += 1
                    except Exception as e:
                        logger.debug("Failed to deserialize cached embedding at idx={}: {}", idx, e)
                        misses.append(idx)
                        self.cache_misses += 1
                else:
                    misses.append(idx)
                    self.cache_misses += 1

        except Exception as e:
            logger.warning("Cache lookup failed: {}, falling back to compute", e)
            misses = list(range(len(texts)))

        return cached, misses

    def _store_cached(self, texts: List[str], indices: List[int], vectors: np.ndarray) -> None:
        """
        Almacena embeddings en caché.
        
        Args:
            texts: Lista completa de textos
            indices: Índices de los textos a cachear
            vectors: Vectores correspondientes a esos índices
        """
        if not self.cache_enabled or self._redis is None or len(indices) == 0:
            return

        try:
            pipe = self._redis.pipeline(transaction=False)
            for i, idx in enumerate(indices):
                key = self._text_key(texts[idx])
                value = vectors[i].tobytes()
                pipe.setex(key, settings.cache_embedding_ttl, value)
            pipe.execute()
            logger.debug("Cached {} embeddings", len(indices))
        except Exception as e:
            logger.warning("Failed to store embeddings in cache: {}", e)

    def _compute_embeddings(self, texts: List[str]) -> Optional[np.ndarray]:
        """Calcula embeddings según el backend configurado."""
        if len(texts) == 0:
            return None

        if self.is_gemini:
            if self._gemini_client is None:
                raise RuntimeError("Gemini client no inicializado")
            vecs = []
            for text in texts:
                resp = self._gemini_client.models.embed_content(
                    model=self.model_name,
                    contents=text,
                    config={
                        "output_dimensionality": settings.embedding_dim,
                    },
                )
                emb = resp.embeddings[0].values
                vecs.append(emb)
            return np.array(vecs, dtype=np.float32)

        if self._impl is not None:
            vecs = list(self._impl.embed(texts))
            return np.array(vecs, dtype=np.float32)

        return None

    def encode(self, texts: Iterable[str]) -> np.ndarray:
        """
        Codifica textos a vectores, utilizando caché cuando está disponible.
        
        Flujo:
        1. Busca en caché Redis
        2. Calcula solo los embeddings faltantes (cache misses)
        3. Almacena los nuevos embeddings en caché
        4. Retorna array completo en el orden original
        """
        texts = list(texts)
        if len(texts) == 0:
            return np.empty((0, self.dim), dtype=np.float32)

        # Paso 1: Intentar recuperar desde caché
        cached, misses = self._get_cached(texts)

        computed: Optional[np.ndarray] = None
        if len(misses) > 0:
            miss_texts = [texts[idx] for idx in misses]

            try:
                computed = self._compute_embeddings(miss_texts)
            except Exception as e:
                logger.error("Error computing embeddings with model {}: {}", self.model_name, e)
                rng = np.random.default_rng(0)
                dim = self.dim or settings.embedding_dim
                computed = rng.standard_normal((len(miss_texts), dim)).astype(np.float32)

            if computed is None or computed.size == 0:
                computed = None
            else:
                if settings.vector_distance.lower() == "cosine":
                    norms = np.linalg.norm(computed, axis=1, keepdims=True) + 1e-12
                    computed = computed / norms

                self.dim = int(computed.shape[1])
                self._store_cached(texts, misses, computed)

        # Determinar dimensión final
        result_dim: Optional[int] = None
        if computed is not None:
            result_dim = computed.shape[1]
        elif cached:
            first_vec = next(iter(cached.values()))
            result_dim = int(first_vec.shape[0])

        if result_dim is None:
            result_dim = self.dim or settings.embedding_dim

        self.dim = result_dim
        result = np.zeros((len(texts), result_dim), dtype=np.float32)

        if computed is not None:
            for i, idx in enumerate(misses):
                result[idx] = computed[i]

        for idx, vec in cached.items():
            if vec.shape[0] == result_dim:
                result[idx] = vec
            elif vec.shape[0] > result_dim:
                logger.debug(
                    "Cached embedding trimmed for model={} expected_dim={} cached_dim={}",
                    self.model_name,
                    result_dim,
                    vec.shape[0],
                )
                result[idx] = vec[:result_dim]
            else:
                logger.debug(
                    "Cached embedding padded for model={} expected_dim={} cached_dim={}",
                    self.model_name,
                    result_dim,
                    vec.shape[0],
                )
                padded = np.zeros(result_dim, dtype=np.float32)
                padded[: vec.shape[0]] = vec
                result[idx] = padded

        return result

    def get_cache_stats(self) -> Dict[str, int]:
        """Retorna estadísticas de uso del caché."""
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0
        return {
            "hits": self.cache_hits,
            "misses": self.cache_misses,
            "total": total,
            "hit_rate_percent": round(hit_rate, 2),
        }
