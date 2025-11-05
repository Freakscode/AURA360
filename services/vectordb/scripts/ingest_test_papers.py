#!/usr/bin/env python3
"""
Script personalizado para ingestar los papers de test descargados desde Sci-Hub.
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime

from vectosvc.config import service_settings
from vectosvc.core.pipeline import ingest_one
from vectosvc.core.repos.fs import FileSystemRepository
from vectosvc.config import settings
from loguru import logger


def main():
    """Ingesta directa de los PDFs de test sin usar la API."""
    
    # Configuración
    papers_dir = Path("downloads/test_papers")
    pdf_files = list(papers_dir.glob("*.pdf"))
    
    logger.info(f"Found {len(pdf_files)} PDF files in {papers_dir}")
    
    repo = FileSystemRepository()
    
    # Metadata común para todos los documentos
    now_version = datetime.utcnow().strftime("%Y.%m.%d")
    common_metadata = {
        "project": "sleep_obesity",
        "source": "scihub",
        "batch": "test_2025_10_03",
        "manually_verified": True,
        "embedding_model": service_settings.embedding_model,
        "version": service_settings.embedding_version or now_version,
        "category": "mente",  # TODO: Determinar categoría automáticamente según el dominio del documento.
        "locale": "es-CO",  # TODO: Derivar locale real a partir de metadata del documento.
        "source_type": "paper",
    }
    
    successful = 0
    failed = 0
    
    for i, pdf_file in enumerate(pdf_files, 1):
        logger.info(f"[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
        
        try:
            # Leer PDF
            pdf_content = repo.read(str(pdf_file.absolute()))
            
            doc_id = pdf_file.stem  # Nombre sin extensión
            metadata = common_metadata.copy()
            metadata["original_filename"] = pdf_file.name

            payload = {
                "doc_id": doc_id,
                "text": None,
                "url": str(pdf_file.absolute()),
                "filename": pdf_file.name,
                "metadata": metadata,
                "category": metadata["category"],
                "locale": metadata["locale"],
                "source_type": metadata["source_type"],
                "embedding_model": metadata["embedding_model"],
                "version": metadata["version"],
                "valid_from": int(datetime.utcnow().timestamp()),
            }

            chunk_count = ingest_one(payload)

            logger.success(
                "Processed %s: %s chunks stored",
                pdf_file.name,
                chunk_count,
            )
            successful += 1
            
        except Exception as e:
            logger.error(f"Failed to process {pdf_file.name}: {e}")
            failed += 1
    
    # Resumen final
    logger.info("=" * 60)
    logger.info("INGESTION SUMMARY:")
    logger.info(f"  Total PDFs: {len(pdf_files)}")
    logger.info(f"  Successful: {successful}")
    logger.info(f"  Failed: {failed}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
