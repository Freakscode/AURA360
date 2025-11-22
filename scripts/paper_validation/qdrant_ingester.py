"""Ingester de papers validados a Qdrant via servicio vectordb."""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import List, Optional

import httpx

from .models import IngestionResult, PaperEntry


class QdrantIngester:
    """Ingester que usa el servicio vectordb existente para procesar papers."""

    def __init__(
        self,
        vectordb_api_url: str = "http://localhost:8001",
        qdrant_collection: str = "holistic_memory",
        batch_size: int = 10,
        dry_run: bool = False,
        timeout: int = 600,
    ):
        self.api_url = vectordb_api_url.rstrip("/")
        self.collection = qdrant_collection
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.timeout = timeout

    async def ingest_papers(self, papers: List[PaperEntry]) -> List[IngestionResult]:
        """Ingesta batch de papers a Qdrant."""
        print(f"\n{'━' * 60}")
        print(f"FASE 3: INGESTA A QDRANT")
        print(f"{'━' * 60}\n")

        if self.dry_run:
            print("🔍 Modo DRY RUN: No se ingestarán papers realmente\n")
            return self._simulate_ingestion(papers)

        # Verificar que vectordb API esté disponible
        if not await self._check_api_health():
            print("❌ Servicio vectordb no disponible. Verifica que esté corriendo.")
            return [
                IngestionResult(
                    doc_id=p.doc_id,
                    success=False,
                    error_message="Servicio vectordb no disponible"
                )
                for p in papers
            ]

        results = []
        success_count = 0
        total = len(papers)

        # Procesar en batches
        for i in range(0, len(papers), self.batch_size):
            batch = papers[i:i + self.batch_size]
            batch_results = await self._ingest_batch(batch, i + 1, total)
            results.extend(batch_results)

            success_count += sum(1 for r in batch_results if r.success)
            self._print_progress(min(i + self.batch_size, total), total, success_count)

            # Pequeña pausa entre batches
            if i + self.batch_size < len(papers):
                await asyncio.sleep(1)

        print(f"\n\n✅ {success_count}/{total} papers ingestados exitosamente")
        if total - success_count > 0:
            print(f"⚠️  {total - success_count} fallidos (revisar DLQ)\n")

        return results

    async def _check_api_health(self) -> bool:
        """Verifica que el servicio vectordb esté disponible."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.api_url}/readyz")
                return response.status_code == 200
        except Exception as e:
            print(f"⚠️  Error conectando con vectordb: {e}")
            return False

    async def _ingest_batch(
        self,
        batch: List[PaperEntry],
        start_idx: int,
        total: int
    ) -> List[IngestionResult]:
        """Ingesta un batch de papers."""
        requests = []

        for paper in batch:
            # Construir request para /ingest endpoint
            ingest_request = {
                "doc_id": paper.doc_id,
                "url": paper.cloud_uri,
                "category": paper.category.value,
                "topics": paper.topics,
                "metadata": {
                    "title": paper.metadata.title,
                    "authors": paper.metadata.authors or [],
                    "journal": paper.metadata.journal,
                    "year": paper.metadata.year,
                    "doi": paper.metadata.doi,
                    "tags": paper.metadata.tags or [],
                    "mesh_terms": paper.metadata.mesh_terms or [],
                    "validated_manually": True,
                    "modified_by_user": paper.modified,
                    "gemini_confidence": paper.confidence_score,
                    "validation_timestamp": paper.validation_timestamp.isoformat() if paper.validation_timestamp else None,
                }
            }
            requests.append((paper, ingest_request))

        results = []

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for paper, request in requests:
                result = await self._submit_single_paper(client, paper, request)
                results.append(result)

        return results

    async def _submit_single_paper(
        self,
        client: httpx.AsyncClient,
        paper: PaperEntry,
        request: dict
    ) -> IngestionResult:
        """Submite un paper individual al servicio vectordb."""
        try:
            # POST a /ingest endpoint
            response = await client.post(
                f"{self.api_url}/ingest",
                json=request
            )

            if response.status_code == 202:
                data = response.json()
                job_id = data.get("job_id")

                # Monitorear el job hasta que complete
                job_result = await self._monitor_job(client, job_id)

                if job_result["status"] == "completed":
                    paper.status = "ingested"
                    paper.ingestion_timestamp = datetime.now()

                    return IngestionResult(
                        doc_id=paper.doc_id,
                        success=True,
                        job_id=job_id,
                        chunks_processed=job_result.get("chunks_processed", 0)
                    )
                else:
                    error_msg = job_result.get("error", "Job failed")
                    return IngestionResult(
                        doc_id=paper.doc_id,
                        success=False,
                        job_id=job_id,
                        error_message=error_msg
                    )

            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                return IngestionResult(
                    doc_id=paper.doc_id,
                    success=False,
                    error_message=error_msg
                )

        except Exception as e:
            error_msg = f"Error ingesting {paper.doc_id}: {str(e)}"
            return IngestionResult(
                doc_id=paper.doc_id,
                success=False,
                error_message=error_msg
            )

    async def _monitor_job(
        self,
        client: httpx.AsyncClient,
        job_id: str,
        max_wait: int = 600
    ) -> dict:
        """Monitorea un job de ingesta hasta que complete o falle."""
        start_time = time.time()
        poll_interval = 5  # segundos

        while time.time() - start_time < max_wait:
            try:
                response = await client.get(f"{self.api_url}/jobs/{job_id}")

                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status")

                    if status in ["completed", "failed"]:
                        return data

                    # Continuar polling
                    await asyncio.sleep(poll_interval)

                else:
                    return {"status": "failed", "error": f"HTTP {response.status_code}"}

            except Exception as e:
                return {"status": "failed", "error": str(e)}

        return {"status": "failed", "error": "Timeout esperando job"}

    def _simulate_ingestion(self, papers: List[PaperEntry]) -> List[IngestionResult]:
        """Simula ingesta en modo dry run."""
        results = []

        for i, paper in enumerate(papers, 1):
            time.sleep(0.1)  # Simular latencia

            result = IngestionResult(
                doc_id=paper.doc_id,
                success=True,
                job_id=f"dry-run-job-{i}",
                chunks_processed=10  # Simular chunks
            )
            results.append(result)

            paper.status = "ingested"
            paper.ingestion_timestamp = datetime.now()

            self._print_progress(i, len(papers), i)

        print("\n")
        return results

    def _print_progress(self, current: int, total: int, success: int) -> None:
        """Imprime barra de progreso."""
        percentage = int((current / total) * 100)
        bar_length = 40
        filled_length = int(bar_length * current // total)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)

        print(f"\r[{bar}] {current}/{total} papers ({percentage}%) | ✅ {success} exitosos", end="", flush=True)

    async def check_dlq(self) -> dict:
        """Verifica el Dead Letter Queue para papers fallidos."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # Asumiendo que existe un endpoint /dlq/stats
                response = await client.get(f"{self.api_url}/dlq/stats")

                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"error": str(e)}


async def run_ingestion(papers: List[PaperEntry], config: dict) -> List[IngestionResult]:
    """Helper function para ejecutar ingesta de forma asíncrona."""
    ingester = QdrantIngester(
        vectordb_api_url=config.get("vectordb_api_url", "http://localhost:8001"),
        qdrant_collection=config.get("qdrant_collection", "holistic_memory"),
        batch_size=config.get("batch_size", 10),
        dry_run=config.get("dry_run", False),
    )

    return await ingester.ingest_papers(papers)
