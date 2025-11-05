from __future__ import annotations

from datetime import datetime
import time
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger

from vectosvc.api.schemas import (
    HolisticSearchRequest,
    HolisticSearchResponse,
    HolisticSearchResponseData,
    HolisticSearchResponseMeta,
    HolisticSearchResult,
    NutritionPlanIngestRequest,
)
from vectosvc.config import service_settings, settings
from vectosvc.core.dlq import dlq
from vectosvc.core.embeddings import Embeddings
from vectosvc.core.pipeline import pipeline_metrics
from vectosvc.core.qdrant_store import store
from vectosvc.core.schemas import Hit, IngestJob, IngestRequest, SearchQuery
from vectosvc.worker.tasks import (
    enqueue_batch,
    enqueue_ingest,
    enqueue_nutrition_plan,
    get_job_status,
)

app = FastAPI(title="vectosvc", version="0.1.0")

_embedding_service = Embeddings()
_embedding_services: Dict[str, Embeddings] = {"__default__": _embedding_service}
_start_time = datetime.utcnow()


@app.get("/readyz")
def readyz():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/metrics")
def metrics() -> Dict[str, Any]:
    """
    Endpoint de métricas básicas del sistema.
    
    Retorna estadísticas sobre:
    - Colección Qdrant (documentos, chunks, tamaño)
    - Sistema (version, uptime)
    - Configuración (modelo de embeddings, colección)
    - Caché (hits, misses, hit rate)
    """
    try:
        # Stats de colección Qdrant
        collection_info = store.client.get_collection(settings.collection_name)
        
        # Contar documentos únicos (grouping by doc_id sería ideal, pero scroll es más simple)
        unique_docs = set()
        offset = None
        while True:
            points, next_offset = store.client.scroll(
                collection_name=settings.collection_name,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            if not points:
                break
            for point in points:
                if "doc_id" in point.payload:
                    unique_docs.add(point.payload["doc_id"])
            if next_offset is None:
                break
            offset = next_offset
        
        # Calcular uptime
        uptime_seconds = (datetime.utcnow() - _start_time).total_seconds()
        
        # Stats de caché de embeddings
        cache_stats = _embedding_service.get_cache_stats()
        
        # Stats del pipeline de ingesta
        pipeline_stats = pipeline_metrics.get_stats()
        
        return {
            "service": {
                "name": "vectosvc",
                "version": "0.1.0",
                "uptime_seconds": uptime_seconds,
            },
            "collection": {
                "name": settings.collection_name,
                "total_points": collection_info.points_count,
                "total_documents": len(unique_docs),
                "vector_size": collection_info.config.params.vectors.size,
                "distance_metric": collection_info.config.params.vectors.distance.value,
                "on_disk_payload": collection_info.config.params.on_disk_payload,
            },
            "cache": {
                "embeddings_enabled": settings.cache_embeddings,
                "embeddings_ttl_seconds": settings.cache_embedding_ttl,
                **cache_stats,
            },
            "pipeline": pipeline_stats,
            "config": {
                "embedding_model": _embedding_service.model_name,
                "qdrant_url": settings.qdrant_url,
                "auto_topics_enabled": settings.auto_topics,
            },
        }
    except Exception as e:
        logger.exception("Failed to fetch metrics")
        raise HTTPException(500, f"Failed to fetch metrics: {str(e)}")


@app.post("/ingest", status_code=202)
def ingest(req: IngestRequest):
    try:
        job_id = enqueue_ingest(req)
        return {"job_id": job_id, "status": "queued"}
    except Exception as e:
        logger.exception("Failed to enqueue ingest")
        raise HTTPException(500, str(e))

@app.post("/ingest/batch", status_code=202)
def ingest_batch(requests: List[IngestRequest]):
    if not requests:
        raise HTTPException(400, "No ingestion requests provided")
    try:
        job_ids = enqueue_batch(requests)
        return {"job_ids": job_ids, "status": "queued"}
    except Exception as e:
        logger.exception("Failed to enqueue batch ingest")
        raise HTTPException(500, str(e))


@app.post("/api/ingest/nutrition-plan", status_code=202)
def ingest_nutrition_plan(req: NutritionPlanIngestRequest):
    try:
        job_id = enqueue_nutrition_plan(req)
        return {"job_id": job_id, "status": "queued"}
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Failed to enqueue nutrition plan ingest")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc)) from exc


@app.get("/jobs/{job_id}", response_model=IngestJob)
def job_status(job_id: str):
    try:
        return get_job_status(job_id)
    except Exception as e:
        logger.exception("Failed to fetch job status")
        raise HTTPException(500, str(e))


def _log_with_trace(event: str, trace_id: str, **kwargs: Any) -> None:
    logger.bind(trace_id=trace_id).info(event, **kwargs)


def _get_embedding_service(model_name: str) -> Embeddings:
    if not model_name:
        return _embedding_services["__default__"]

    if model_name not in _embedding_services:
        _embedding_services[model_name] = Embeddings(model_name=model_name)
    return _embedding_services[model_name]


def _calculate_confidence_score(raw_score: float | None) -> float | None:
    if raw_score is None:
        return None
    # TODO: Ajustar fórmula de confianza una vez tengamos distribución real de scores.
    bounded = max(min(raw_score, 1.0), -1.0)
    return round((bounded + 1.0) / 2.0, 4)


def _success_response(
    *,
    trace_id: str,
    took_ms: int,
    results: List[HolisticSearchResult],
) -> HolisticSearchResponse:
    return HolisticSearchResponse(
        status="success",
        data=HolisticSearchResponseData(results=results),
        error=None,
        meta=HolisticSearchResponseMeta(
            trace_id=trace_id,
            took_ms=took_ms,
            collection=service_settings.collection_name,
        ),
    )


def _error_response(
    *,
    trace_id: str,
    status_code: int,
    error_type: str,
    message: str,
    details: Dict[str, Any] | None = None,
) -> JSONResponse:
    body = HolisticSearchResponse(
        status="error",
        data=None,
        error={
            "type": error_type,
            "message": message,
            "details": details or {},
        },
        meta=HolisticSearchResponseMeta(
            trace_id=trace_id,
            took_ms=0,
            collection=service_settings.collection_name,
        ),
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())


@app.post(
    "/api/v1/holistic/search",
    response_model=HolisticSearchResponse,
    responses={
        400: {"model": HolisticSearchResponse},
        500: {"model": HolisticSearchResponse},
    },
)
def holistic_search(payload: HolisticSearchRequest):
    start = time.perf_counter()
    trace_id = payload.trace_id

    _log_with_trace(
        "holistic.search.request.received",
        trace_id,
        query=payload.query,
        category=payload.category.value,
        locale=payload.locale,
        top_k=payload.top_k,
        embedding_model=payload.embedding_model,
    )

    embedding_model = payload.embedding_model or service_settings.embedding_model

    try:
        embedding_service = _get_embedding_service(embedding_model)
        vector = embedding_service.encode([payload.query])[0].tolist()
    except Exception as exc:
        _log_with_trace(
            "holistic.search.embedding_failed",
            trace_id,
            error=str(exc),
        )
        return _error_response(
            trace_id=trace_id,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_type="embedding_error",
            message="Failed to generate embeddings for the query.",
            details={"exception": str(exc), "embedding_model": embedding_model},
        )

    filter_must: Dict[str, Any] = {
        "category": payload.category.value,
        "version": service_settings.embedding_version,
    }
    if payload.locale:
        filter_must["locale"] = payload.locale

    filter_should: Dict[str, Any] = {}

    if payload.filters:
        filter_must.update(payload.filters.must or {})
        filter_should.update(payload.filters.should or {})

    qdrant_filter = store.build_filter(filter_must, filter_should)

    try:
        hits = store.search_with_retry(
            vector,
            limit=payload.top_k,
            filter_=qdrant_filter,
        )
    except Exception as exc:
        _log_with_trace(
            "holistic.search.qdrant_failed",
            trace_id,
            error=str(exc),
        )
        return _error_response(
            trace_id=trace_id,
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_type="vector_store_error",
            message="Vector store search failed.",
            details={"exception": str(exc)},
        )

    results: List[HolisticSearchResult] = []
    for hit in hits:
        payload_data = hit.payload or {}

        result_metadata = {
            key: value
            for key, value in payload_data.items()
            if key
            not in {
                "doc_id",
                "text",
                "category",
                "source_type",
                "embedding_model",
                "version",
            }
        }

        results.append(
            HolisticSearchResult(
                doc_id=payload_data.get("doc_id", str(hit.id)),
                score=hit.score,
                confidence_score=_calculate_confidence_score(hit.score),
                category=payload_data.get("category", payload.category.value),
                source_type=payload_data.get("source_type"),
                chunk=payload_data.get("text", ""),
                metadata=result_metadata,
                embedding_model=payload_data.get("embedding_model", embedding_model),
                version=payload_data.get("version", service_settings.embedding_version),
            )
        )

    took_ms = int((time.perf_counter() - start) * 1000)

    _log_with_trace(
        "holistic.search.request.completed",
        trace_id,
        took_ms=took_ms,
        results=len(results),
    )

    # TODO: Exponer métricas Prometheus una vez esté disponible el registro.

    return _success_response(
        trace_id=trace_id,
        took_ms=took_ms,
        results=results,
    )


@app.post("/search")
def search(q: SearchQuery):
    vec = _embedding_service.encode([q.query])[0].tolist()

    filt = None
    if q.filter:
        filt = store.build_filter(q.filter.must, q.filter.should)

    hits = store.search_with_retry(vec, limit=q.limit, filter_=filt, ef_search=q.ef_search)
    data = [
        Hit(id=h.id, score=h.score, payload=h.payload).model_dump()
        for h in hits
    ]
    return {"hits": data}


@app.get("/dlq")
def dlq_list(limit: int = 100, offset: int = 0):
    """
    Lista entradas en el Dead Letter Queue.
    
    Retorna jobs que fallaron después de agotar reintentos,
    con toda la información para debugging y reintento manual.
    """
    try:
        entries = dlq.list_failures(limit=limit, offset=offset)
        stats = dlq.get_stats()
        return {
            "entries": entries,
            "stats": stats,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.exception("Failed to fetch DLQ entries")
        raise HTTPException(500, str(e))


@app.get("/dlq/stats")
def dlq_stats():
    """
    Obtiene estadísticas agregadas del DLQ.
    
    Incluye:
    - Total de fallos
    - Distribución por fase (download, parse_tei, embeddings, etc)
    - Distribución por tipo de error
    """
    try:
        stats = dlq.get_stats()
        return stats
    except Exception as e:
        logger.exception("Failed to fetch DLQ stats")
        raise HTTPException(500, str(e))


@app.delete("/dlq")
def dlq_clear():
    """
    Limpia completamente el DLQ.
    
    ⚠️ Operación destructiva: elimina todas las entradas.
    Usar con precaución, típicamente después de analizar y resolver fallos.
    """
    try:
        count = dlq.clear()
        return {"cleared": count, "status": "ok"}
    except Exception as e:
        logger.exception("Failed to clear DLQ")
        raise HTTPException(500, str(e))
