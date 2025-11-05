#!/usr/bin/env python3
"""
Script para descargar estudios científicos por lotes desde Sci-Hub.

Este script permite descargar papers usando DOIs, PubMed IDs o URLs directas,
con soporte para múltiples mirrors de Sci-Hub y manejo robusto de errores.

Uso:
    # Descargar desde archivo de DOIs
    python scripts/download_scihub_batch.py --dois dois.txt --output-dir downloads/papers

    # Descargar y luego ingestar automáticamente
    python scripts/download_scihub_batch.py --dois dois.txt --output-dir downloads/papers --auto-ingest

    # Con metadata personalizado
    python scripts/download_scihub_batch.py --dois dois.txt --output-dir downloads/papers --metadata '{"source":"scihub","category":"research"}'

    # Usando un mirror específico
    python scripts/download_scihub_batch.py --dois dois.txt --output-dir downloads/papers --mirror https://sci-hub.se

Formato del archivo de DOIs:
    - Un DOI por línea
    - Las líneas que comienzan con # son comentarios
    - Soporta DOIs con o sin prefijo "doi:" o "https://doi.org/"
    
Ejemplo:
    10.1016/j.cell.2020.04.001
    doi:10.1038/nature12345
    https://doi.org/10.1126/science.abc1234
    # Este es un comentario
    PMID:12345678
"""
import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import quote, urlparse

import httpx
from loguru import logger

# Mirrors de Sci-Hub (se pueden actualizar según disponibilidad)
DEFAULT_SCIHUB_MIRRORS = [
    "https://sci-hub.se",
    "https://sci-hub.st",
    "https://sci-hub.ru",
    "https://sci-hub.tw",
    "https://sci-hub.wf",
]


def normalize_identifier(identifier: str) -> Tuple[str, str]:
    """
    Normaliza un identificador (DOI, PMID, URL) a formato estándar.
    
    Args:
        identifier: DOI, PMID o URL del paper
    
    Returns:
        Tuple de (tipo, valor_normalizado)
        tipo puede ser: 'doi', 'pmid', 'url'
    """
    identifier = identifier.strip()
    
    # Verificar si es PMID
    if identifier.lower().startswith("pmid:"):
        pmid = identifier[5:].strip()
        return ("pmid", pmid)
    
    # Verificar si es un PMID sin prefijo (solo números)
    if identifier.isdigit() and len(identifier) >= 6:
        return ("pmid", identifier)
    
    # Verificar si es una URL completa de DOI
    if identifier.startswith("https://doi.org/"):
        doi = identifier.replace("https://doi.org/", "")
        return ("doi", doi)
    
    if identifier.startswith("http://doi.org/"):
        doi = identifier.replace("http://doi.org/", "")
        return ("doi", doi)
    
    # Verificar si tiene prefijo "doi:"
    if identifier.lower().startswith("doi:"):
        doi = identifier[4:].strip()
        return ("doi", doi)
    
    # Si contiene "/" probablemente es un DOI
    if "/" in identifier:
        return ("doi", identifier)
    
    # Por defecto, asumir que es una URL
    return ("url", identifier)


def read_identifiers_from_file(file_path: Path) -> List[str]:
    """
    Lee identificadores desde un archivo de texto (uno por línea).
    Ignora líneas vacías y comentarios (líneas que comienzan con #).
    """
    identifiers = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Ignorar líneas vacías y comentarios
            if not line or line.startswith("#"):
                continue
            
            identifiers.append(line)
            logger.debug(f"Line {line_num}: {line}")
    
    return identifiers


def generate_filename_from_identifier(identifier: str, id_type: str) -> str:
    """
    Genera un nombre de archivo único basado en el identificador.
    Usa el DOI/PMID si está disponible, o un hash de la URL.
    """
    if id_type == "doi":
        # Reemplazar caracteres no válidos para nombres de archivo
        safe_name = re.sub(r'[^\w\-.]', '_', identifier)
        return f"doi_{safe_name}.pdf"
    elif id_type == "pmid":
        return f"pmid_{identifier}.pdf"
    else:
        # Para URLs, usar hash MD5
        hash_val = hashlib.md5(identifier.encode()).hexdigest()[:12]
        return f"paper_{hash_val}.pdf"


def download_from_scihub(
    identifier: str,
    mirrors: List[str],
    timeout: int = 30,
    max_retries: int = 3,
) -> Optional[bytes]:
    """
    Intenta descargar un paper desde Sci-Hub usando múltiples mirrors.
    
    Args:
        identifier: DOI, PMID o URL del paper
        mirrors: Lista de URLs de mirrors de Sci-Hub
        timeout: Timeout para cada request en segundos
        max_retries: Número máximo de reintentos por mirror
    
    Returns:
        Contenido del PDF en bytes, o None si falla
    """
    id_type, normalized_id = normalize_identifier(identifier)
    
    logger.info(f"Attempting to download {id_type}: {normalized_id}")
    
    # Construir la URL de búsqueda para Sci-Hub
    if id_type == "doi":
        search_query = normalized_id
    elif id_type == "pmid":
        search_query = f"PMID:{normalized_id}"
    else:
        search_query = normalized_id
    
    for mirror in mirrors:
        logger.debug(f"Trying mirror: {mirror}")
        
        for attempt in range(max_retries):
            try:
                # Sci-Hub usa el formato: https://sci-hub.se/{doi_or_identifier}
                scihub_url = f"{mirror}/{quote(search_query, safe='')}"
                
                logger.debug(f"Request URL: {scihub_url} (attempt {attempt + 1}/{max_retries})")
                
                with httpx.Client(
                    timeout=timeout,
                    follow_redirects=True,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                ) as client:
                    # Primera request: obtener la página de Sci-Hub
                    response = client.get(scihub_url)
                    response.raise_for_status()
                    
                    # Buscar el link directo al PDF en el HTML
                    html_content = response.text
                    
                    # Sci-Hub típicamente incluye el PDF en un iframe o link directo
                    # Patrones comunes:
                    # <iframe src="...pdf...">
                    # <embed src="...pdf...">
                    # <a href="...pdf...">
                    pdf_patterns = [
                        r'<iframe[^>]+src=["\'](https?://[^"\']+\.pdf[^"\']*)["\']',
                        r'<embed[^>]+src=["\'](https?://[^"\']+\.pdf[^"\']*)["\']',
                        r'<button[^>]+onclick=["\']location\.href=["\']([^"\']+\.pdf[^"\']*)["\']',
                        r'<a[^>]+href=["\'](https?://[^"\']+\.pdf[^"\']*)["\']',
                        r'src=["\'](//[^"\']+\.pdf[^"\']*)["\']',
                    ]
                    
                    pdf_url = None
                    for pattern in pdf_patterns:
                        match = re.search(pattern, html_content, re.IGNORECASE)
                        if match:
                            pdf_url = match.group(1)
                            # Si la URL es relativa (comienza con //), agregar protocolo
                            if pdf_url.startswith("//"):
                                pdf_url = "https:" + pdf_url
                            logger.debug(f"Found PDF URL: {pdf_url}")
                            break
                    
                    if not pdf_url:
                        logger.warning(f"No PDF link found in Sci-Hub response from {mirror}")
                        continue
                    
                    # Descargar el PDF
                    logger.debug(f"Downloading PDF from: {pdf_url}")
                    pdf_response = client.get(pdf_url)
                    pdf_response.raise_for_status()
                    
                    # Verificar que el contenido es un PDF
                    content_type = pdf_response.headers.get("content-type", "")
                    content = pdf_response.content
                    
                    if not content:
                        logger.warning(f"Empty response from {mirror}")
                        continue
                    
                    # Verificar magic bytes del PDF
                    if not content.startswith(b"%PDF"):
                        logger.warning(
                            f"Downloaded content is not a PDF (Content-Type: {content_type})"
                        )
                        continue
                    
                    logger.success(
                        f"Successfully downloaded from {mirror} ({len(content) / 1024:.1f} KB)"
                    )
                    return content
            
            except httpx.HTTPStatusError as e:
                logger.warning(
                    f"HTTP error on {mirror} (attempt {attempt + 1}): {e.response.status_code}"
                )
                if e.response.status_code == 404:
                    # Paper no encontrado, no tiene sentido reintentar en este mirror
                    break
                if e.response.status_code == 429:
                    # Rate limit, esperar antes de reintentar
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Rate limited, waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
            
            except httpx.TimeoutException:
                logger.warning(f"Timeout on {mirror} (attempt {attempt + 1})")
                time.sleep(1)
            
            except Exception as e:
                logger.warning(f"Error on {mirror} (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
        
        # Pequeña pausa entre mirrors
        time.sleep(0.5)
    
    logger.error(f"Failed to download {identifier} from all mirrors")
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Descarga por lotes de papers científicos desde Sci-Hub",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    parser.add_argument(
        "--dois",
        type=Path,
        required=True,
        help="Archivo con lista de DOIs, PMIDs o URLs (uno por línea)",
    )
    
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("downloads/scihub_papers"),
        help="Directorio de salida para PDFs descargados (default: downloads/scihub_papers)",
    )
    
    parser.add_argument(
        "--mirror",
        type=str,
        help="Mirror específico de Sci-Hub a usar (ej: https://sci-hub.se)",
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout en segundos para cada descarga (default: 30)",
    )
    
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay en segundos entre descargas para evitar rate-limiting (default: 2.0)",
    )
    
    parser.add_argument(
        "--auto-ingest",
        action="store_true",
        help="Ingestar automáticamente los PDFs descargados al sistema vectorial",
    )
    
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="URL de la API para auto-ingest (default: http://localhost:8000)",
    )
    
    parser.add_argument(
        "--metadata",
        type=str,
        help="Metadata JSON común para todos los documentos (ej: '{\"source\":\"scihub\"}')",
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo listar identificadores sin descargar",
    )
    
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Saltar descargas si el archivo ya existe",
    )
    
    args = parser.parse_args()
    
    # Validar archivo de entrada
    if not args.dois.exists():
        logger.error(f"Input file not found: {args.dois}")
        sys.exit(1)
    
    # Crear directorio de salida
    args.output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {args.output_dir}")
    
    # Leer identificadores
    identifiers = read_identifiers_from_file(args.dois)
    logger.info(f"Loaded {len(identifiers)} identifiers from {args.dois}")
    
    if not identifiers:
        logger.warning("No identifiers found in input file")
        sys.exit(0)
    
    # Determinar mirrors a usar
    mirrors = [args.mirror] if args.mirror else DEFAULT_SCIHUB_MIRRORS
    logger.info(f"Using {len(mirrors)} Sci-Hub mirror(s)")
    
    # Parse metadata
    common_metadata = {}
    if args.metadata:
        try:
            common_metadata = json.loads(args.metadata)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid metadata JSON: {e}")
            sys.exit(1)
    
    if args.dry_run:
        logger.info("DRY RUN - would download:")
        for i, identifier in enumerate(identifiers, 1):
            id_type, normalized = normalize_identifier(identifier)
            filename = generate_filename_from_identifier(normalized, id_type)
            logger.info(f"  [{i}/{len(identifiers)}] {id_type}: {normalized} → {filename}")
        sys.exit(0)
    
    # Descargar papers
    successful_downloads = []
    failed_downloads = []
    skipped_downloads = []
    
    logger.info("=" * 60)
    logger.info("Starting batch download...")
    logger.info("=" * 60)
    
    for i, identifier in enumerate(identifiers, 1):
        id_type, normalized = normalize_identifier(identifier)
        filename = generate_filename_from_identifier(normalized, id_type)
        output_path = args.output_dir / filename
        
        logger.info(f"[{i}/{len(identifiers)}] Processing: {normalized}")
        
        # Verificar si ya existe
        if args.skip_existing and output_path.exists():
            logger.info(f"Skipping (already exists): {output_path}")
            skipped_downloads.append((identifier, output_path))
            continue
        
        # Descargar
        pdf_content = download_from_scihub(
            identifier,
            mirrors=mirrors,
            timeout=args.timeout,
        )
        
        if pdf_content:
            # Guardar PDF
            try:
                with open(output_path, "wb") as f:
                    f.write(pdf_content)
                logger.success(f"Saved: {output_path}")
                successful_downloads.append((identifier, output_path))
            except Exception as e:
                logger.error(f"Failed to save file {output_path}: {e}")
                failed_downloads.append(identifier)
        else:
            failed_downloads.append(identifier)
        
        # Delay entre descargas (excepto en la última)
        if i < len(identifiers):
            time.sleep(args.delay)
    
    # Resumen de descargas
    logger.info("=" * 60)
    logger.info("DOWNLOAD SUMMARY:")
    logger.info(f"  Total identifiers: {len(identifiers)}")
    logger.info(f"  Successful: {len(successful_downloads)}")
    logger.info(f"  Failed: {len(failed_downloads)}")
    logger.info(f"  Skipped: {len(skipped_downloads)}")
    logger.info("=" * 60)
    
    # Guardar log de fallidos
    if failed_downloads:
        failed_log = args.output_dir / "failed_downloads.txt"
        with open(failed_log, "w") as f:
            for identifier in failed_downloads:
                f.write(f"{identifier}\n")
        logger.warning(f"Failed downloads logged to: {failed_log}")
    
    # Auto-ingest si se solicitó
    if args.auto_ingest and successful_downloads:
        logger.info("=" * 60)
        logger.info("Starting auto-ingestion...")
        logger.info("=" * 60)
        
        try:
            # Importar el módulo de ingesta
            sys.path.insert(0, str(Path(__file__).parent))
            from ingest_batch import ingest_local_file
            
            job_ids = []
            for identifier, file_path in successful_downloads:
                try:
                    # Agregar identificador al metadata
                    metadata = common_metadata.copy()
                    id_type, normalized = normalize_identifier(identifier)
                    metadata[id_type] = normalized
                    metadata["source"] = "scihub"
                    
                    result = ingest_local_file(args.api_url, file_path, metadata)
                    job_id = result.get("job_id")
                    job_ids.append(job_id)
                    logger.info(f"Submitted for ingestion: {file_path.name} → {job_id}")
                except Exception as e:
                    logger.error(f"Failed to submit {file_path.name}: {e}")
            
            logger.info(f"Auto-ingestion complete: {len(job_ids)} jobs submitted")
            logger.info("Use ingest_batch.py with --no-monitor to track job progress")
        
        except ImportError as e:
            logger.error(f"Failed to import ingest_batch module: {e}")
            logger.error("Auto-ingestion skipped")
    
    logger.info("=" * 60)
    logger.info("Batch download complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

