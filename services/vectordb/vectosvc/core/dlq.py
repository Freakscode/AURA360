"""
Dead Letter Queue (DLQ) para auditoría y manejo de fallos persistentes.

Almacena en Redis los jobs que fallaron después de múltiples reintentos,
permitiendo análisis posterior y reintento manual.
"""
from __future__ import annotations

import json
import time
import traceback
from typing import Any, Dict, List, Optional

import redis
from loguru import logger

from vectosvc.config import settings


class DLQ:
    """
    Dead Letter Queue para almacenar jobs fallidos de forma persistente.
    
    Utiliza Redis Lists para almacenar jobs fallidos con toda su información
    de contexto (payload, error, traceback, timestamps).
    
    Estructura de entrada DLQ:
    {
        "job_id": str,
        "doc_id": str,
        "request": dict,  # Payload original del IngestRequest
        "error": str,
        "traceback": str,
        "attempts": int,
        "first_attempt_at": int,  # timestamp
        "failed_at": int,  # timestamp del último fallo
        "error_phase": str,  # download, parse_tei, embeddings, etc
    }
    """
    
    DLQ_KEY = "dlq:ingestion_failures"
    DLQ_STATS_KEY = "dlq:stats"
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Inicializa conexión Redis para DLQ."""
        self._redis = redis_client
        
        if self._redis is None:
            try:
                # Usar misma configuración que broker
                url_parts = settings.broker_url.replace("redis://", "").split("/")
                host_port = url_parts[0].split(":")
                host = host_port[0] if len(host_port) > 0 else "localhost"
                port = int(host_port[1]) if len(host_port) > 1 else 6379
                db = 3  # Use DB 3 for DLQ (0=broker, 1=results, 2=cache)
                
                self._redis = redis.Redis(
                    host=host,
                    port=port,
                    db=db,
                    decode_responses=True  # Para facilitar JSON
                )
                self._redis.ping()
                logger.info("DLQ initialized on Redis {}:{} db={}", host, port, db)
            except Exception as e:
                logger.error("Failed to initialize DLQ: {}", e)
                raise
    
    def push(
        self,
        job_id: str,
        doc_id: str,
        request: Dict[str, Any],
        error: Exception,
        attempts: int = 1,
        error_phase: Optional[str] = None,
        first_attempt_at: Optional[int] = None,
    ) -> None:
        """
        Envía un job fallido al DLQ.
        
        Args:
            job_id: ID del job de Celery
            doc_id: ID del documento
            request: Payload original del IngestRequest
            error: Excepción que causó el fallo
            attempts: Número de intentos realizados
            error_phase: Fase donde ocurrió el error (download, parse_tei, etc)
            first_attempt_at: Timestamp del primer intento
        """
        now = int(time.time())
        
        entry = {
            "job_id": job_id,
            "doc_id": doc_id,
            "request": request,
            "error": str(error),
            "error_type": type(error).__name__,
            "traceback": traceback.format_exc(),
            "attempts": attempts,
            "first_attempt_at": first_attempt_at or now,
            "failed_at": now,
            "error_phase": error_phase or "unknown",
        }
        
        try:
            # Push a lista Redis
            self._redis.lpush(self.DLQ_KEY, json.dumps(entry))
            
            # Incrementar contador de stats
            self._redis.hincrby(self.DLQ_STATS_KEY, "total_failures", 1)
            self._redis.hincrby(self.DLQ_STATS_KEY, f"by_phase:{error_phase or 'unknown'}", 1)
            self._redis.hincrby(self.DLQ_STATS_KEY, f"by_error:{type(error).__name__}", 1)
            
            logger.warning(
                "Job pushed to DLQ: job_id={} doc_id={} error={} attempts={}",
                job_id,
                doc_id,
                type(error).__name__,
                attempts
            )
        except Exception as e:
            logger.error("Failed to push to DLQ: {}", e)
    
    def list_failures(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Lista jobs fallidos en el DLQ.
        
        Args:
            limit: Máximo número de entradas a retornar
            offset: Offset para paginación
            
        Returns:
            Lista de entradas DLQ (más recientes primero)
        """
        try:
            # LRANGE retorna más recientes primero (LPUSH)
            entries = self._redis.lrange(
                self.DLQ_KEY,
                offset,
                offset + limit - 1
            )
            
            return [json.loads(entry) for entry in entries]
        except Exception as e:
            logger.error("Failed to list DLQ entries: {}", e)
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del DLQ.
        
        Returns:
            Diccionario con estadísticas agregadas
        """
        try:
            total = self._redis.llen(self.DLQ_KEY)
            stats_raw = self._redis.hgetall(self.DLQ_STATS_KEY) or {}
            
            # Agrupar stats por categoría
            by_phase: Dict[str, int] = {}
            by_error: Dict[str, int] = {}
            
            for key, value in stats_raw.items():
                if key.startswith("by_phase:"):
                    phase = key.replace("by_phase:", "")
                    by_phase[phase] = int(value)
                elif key.startswith("by_error:"):
                    error_type = key.replace("by_error:", "")
                    by_error[error_type] = int(value)
            
            return {
                "total_entries": total,
                "total_failures": int(stats_raw.get("total_failures", 0)),
                "by_phase": by_phase,
                "by_error": by_error,
            }
        except Exception as e:
            logger.error("Failed to get DLQ stats: {}", e)
            return {
                "total_entries": 0,
                "total_failures": 0,
                "by_phase": {},
                "by_error": {},
            }
    
    def clear(self) -> int:
        """
        Limpia completamente el DLQ.
        
        Returns:
            Número de entradas eliminadas
        """
        try:
            count = self._redis.llen(self.DLQ_KEY)
            self._redis.delete(self.DLQ_KEY)
            self._redis.delete(self.DLQ_STATS_KEY)
            logger.info("DLQ cleared: {} entries removed", count)
            return count
        except Exception as e:
            logger.error("Failed to clear DLQ: {}", e)
            return 0
    
    def retry_entry(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Recupera una entrada del DLQ para reintento manual.
        
        Args:
            index: Índice de la entrada (0 = más reciente)
            
        Returns:
            Entrada del DLQ si existe, None en caso contrario
        """
        try:
            # Obtener entrada
            entry_json = self._redis.lindex(self.DLQ_KEY, index)
            if not entry_json:
                return None
            
            entry = json.loads(entry_json)
            
            # Remover del DLQ (opcional, según lógica de negocio)
            # self._redis.lset(self.DLQ_KEY, index, "__DELETED__")
            # self._redis.lrem(self.DLQ_KEY, 1, "__DELETED__")
            
            return entry
        except Exception as e:
            logger.error("Failed to retry DLQ entry: {}", e)
            return None


# Singleton global
dlq = DLQ()

