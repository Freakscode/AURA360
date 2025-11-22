#!/usr/bin/env python3
"""
Script de utilidad para ingesta masiva de PDFs desde directorio local o URLs.

Uso:
    # Ingestar desde directorio local
    python scripts/ingest_batch.py --directory /path/to/pdfs

    # Ingestar desde lista de URLs
    python scripts/ingest_batch.py --urls urls.txt

    # Usar API remota
    python scripts/ingest_batch.py --directory /path/to/pdfs --api-url http://localhost:8000
"""
import argparse
import json
import sys
import time
from pathlib import Path
from typing import List

import httpx
from loguru import logger


def read_urls_from_file(file_path: Path) -> List[str]:
    """Lee URLs desde un archivo de texto (una por línea)."""
    with open(file_path, "r") as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return urls


def find_pdfs_in_directory(directory: Path) -> List[Path]:
    """Encuentra todos los PDFs en un directorio (recursivo)."""
    return list(directory.rglob("*.pdf"))


def ingest_url(api_url: str, url: str, metadata: dict = None) -> dict:
    """
    Envía una solicitud de ingesta para una URL.
    
    Returns:
        Response dict con job_id
    """
    payload = {
        "doc_id": f"url_{hash(url)}",  # Generar doc_id desde URL
        "url": url,
        "metadata": metadata or {},
    }
    
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(f"{api_url}/ingest", json=payload)
        resp.raise_for_status()
        return resp.json()


def ingest_local_file(api_url: str, file_path: Path, metadata: dict = None) -> dict:
    """
    Envía una solicitud de ingesta para un archivo local usando file:// URL.
    
    Returns:
        Response dict con job_id
    """
    # Use relative path from current directory for Docker compatibility
    # The worker container has the project mounted at /app
    import os
    cwd = Path(os.getcwd())
    abs_file_path = file_path.absolute()
    
    try:
        # Try to get relative path from current working directory
        rel_path = abs_file_path.relative_to(cwd)
        # Use plain relative path without file:// prefix for Docker compat
        file_url = str(rel_path)
    except ValueError:
        # If file is outside cwd, use absolute path
        file_url = abs_file_path.as_uri()
    
    payload = {
        "doc_id": file_path.stem,  # Usar nombre del archivo sin extensión
        "url": file_url,
        "filename": file_path.name,
        "metadata": metadata or {},
    }
    
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(f"{api_url}/ingest", json=payload)
        resp.raise_for_status()
        return resp.json()


def monitor_jobs(api_url: str, job_ids: List[str], poll_interval: int = 5):
    """
    Monitorea el progreso de una lista de jobs.
    
    Args:
        api_url: URL base de la API
        job_ids: Lista de job IDs a monitorear
        poll_interval: Intervalo en segundos entre polls
    """
    pending = set(job_ids)
    completed = []
    failed = []
    
    logger.info(f"Monitoring {len(job_ids)} jobs...")
    
    with httpx.Client(timeout=10.0) as client:
        while pending:
            time.sleep(poll_interval)
            
            for job_id in list(pending):
                try:
                    resp = client.get(f"{api_url}/jobs/{job_id}")
                    resp.raise_for_status()
                    job_data = resp.json()
                    
                    status = job_data.get("status")
                    
                    if status == "completed":
                        completed.append(job_id)
                        pending.remove(job_id)
                        logger.success(
                            f"Job {job_id} completed: {job_data.get('processed_chunks', 0)} chunks"
                        )
                    
                    elif status == "failed":
                        failed.append(job_id)
                        pending.remove(job_id)
                        logger.error(
                            f"Job {job_id} failed: {job_data.get('error', 'unknown error')}"
                        )
                
                except Exception as e:
                    logger.warning(f"Failed to check job {job_id}: {e}")
            
            if pending:
                logger.info(
                    f"Progress: {len(completed)} completed, {len(failed)} failed, {len(pending)} pending"
                )
    
    return {
        "completed": completed,
        "failed": failed,
        "total": len(job_ids),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Ingesta masiva de PDFs a vectosvc"
    )
    parser.add_argument(
        "--directory",
        type=Path,
        help="Directorio con PDFs (búsqueda recursiva)",
    )
    parser.add_argument(
        "--urls",
        type=Path,
        help="Archivo con lista de URLs (una por línea)",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="URL base de la API (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--metadata",
        type=str,
        help="Metadata JSON común para todos los documentos (ej: '{\"source\":\"manual\"}')",
    )
    parser.add_argument(
        "--no-monitor",
        action="store_true",
        help="No monitorear progreso de jobs",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo listar archivos/URLs sin ingestar",
    )
    
    args = parser.parse_args()
    
    if not args.directory and not args.urls:
        parser.error("Debe especificar --directory o --urls")
    
    # Parse metadata común
    common_metadata = {}
    if args.metadata:
        try:
            common_metadata = json.loads(args.metadata)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid metadata JSON: {e}")
            sys.exit(1)
    
    # Recolectar items a ingestar
    items = []
    
    if args.directory:
        if not args.directory.exists():
            logger.error(f"Directory not found: {args.directory}")
            sys.exit(1)
        
        pdf_files = find_pdfs_in_directory(args.directory)
        logger.info(f"Found {len(pdf_files)} PDF files in {args.directory}")
        items.extend(("file", f) for f in pdf_files)
    
    if args.urls:
        if not args.urls.exists():
            logger.error(f"URLs file not found: {args.urls}")
            sys.exit(1)
        
        urls = read_urls_from_file(args.urls)
        logger.info(f"Loaded {len(urls)} URLs from {args.urls}")
        items.extend(("url", u) for u in urls)
    
    if not items:
        logger.warning("No items to ingest")
        sys.exit(0)
    
    if args.dry_run:
        logger.info("DRY RUN - would ingest:")
        for item_type, item in items:
            logger.info(f"  [{item_type}] {item}")
        sys.exit(0)
    
    # Ingestar items
    job_ids = []
    failed_submissions = 0
    
    logger.info(f"Starting ingestion of {len(items)} items...")
    
    for i, (item_type, item) in enumerate(items, 1):
        try:
            if item_type == "file":
                result = ingest_local_file(args.api_url, item, common_metadata)
            else:  # url
                result = ingest_url(args.api_url, item, common_metadata)
            
            job_id = result.get("job_id")
            job_ids.append(job_id)
            logger.info(f"[{i}/{len(items)}] Submitted {item_type}: {item} → {job_id}")
        
        except Exception as e:
            failed_submissions += 1
            logger.error(f"[{i}/{len(items)}] Failed to submit {item_type} {item}: {e}")
    
    logger.info(
        f"Submission complete: {len(job_ids)} submitted, {failed_submissions} failed"
    )
    
    # Monitorear jobs
    if not args.no_monitor and job_ids:
        summary = monitor_jobs(args.api_url, job_ids, poll_interval=5)
        
        logger.info("=" * 60)
        logger.info("FINAL SUMMARY:")
        logger.info(f"  Total submitted: {summary['total']}")
        logger.info(f"  Completed: {len(summary['completed'])}")
        logger.info(f"  Failed: {len(summary['failed'])}")
        logger.info(f"  Submission failures: {failed_submissions}")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()

