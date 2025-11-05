#!/usr/bin/env python3
"""Script para verificar que las variables de entorno se cargan correctamente."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path para imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Test 1: Cargar variables con infra.env
logger.info("=" * 80)
logger.info("TEST 1: Cargando variables con infra.env.load_environment()")
logger.info("=" * 80)

from infra.env import load_environment

loaded_files = load_environment(override=False)
logger.info(f"Archivos cargados: {loaded_files}")

# Test 2: Verificar variables críticas
logger.info("\n" + "=" * 80)
logger.info("TEST 2: Verificando variables de entorno críticas")
logger.info("=" * 80)

critical_vars = [
    "GOOGLE_API_KEY",
    "AGENT_SERVICE_QDRANT_URL",
    "AGENT_SERVICE_VECTOR_COLLECTION",
    "AGENT_DEFAULT_EMBEDDING_MODEL",
    "AGENT_SERVICE_EMBEDDING_BACKEND",
]

for var in critical_vars:
    value = os.getenv(var)
    if value:
        # Ocultar parcialmente API keys
        if "KEY" in var or "SECRET" in var:
            display_value = f"{value[:10]}..." if len(value) > 10 else "***"
        else:
            display_value = value
        logger.info(f"✓ {var} = {display_value}")
    else:
        logger.warning(f"✗ {var} no está definida")

# Test 3: Cargar ServiceSettings
logger.info("\n" + "=" * 80)
logger.info("TEST 3: Cargando ServiceSettings (pydantic-settings)")
logger.info("=" * 80)

from infra.settings import get_settings

settings = get_settings()

logger.info(f"✓ vector_service_url: {settings.vector_service_url}")
logger.info(f"✓ vector_collection_name: {settings.vector_collection_name}")
logger.info(f"✓ embedding_model: {settings.embedding_model}")
logger.info(f"✓ embedding_backend: {settings.embedding_backend}")

api_key = settings.resolved_embedding_api_key
if api_key:
    logger.info(f"✓ resolved_embedding_api_key: {api_key[:10]}...")
else:
    logger.warning("✗ resolved_embedding_api_key no está disponible")

# Test 4: Verificar ruta del .env
logger.info("\n" + "=" * 80)
logger.info("TEST 4: Verificando ubicación del archivo .env")
logger.info("=" * 80)

env_file = project_root / ".env"
if env_file.exists():
    logger.info(f"✓ Archivo .env existe: {env_file}")
    logger.info(f"  Tamaño: {env_file.stat().st_size} bytes")
else:
    logger.error(f"✗ Archivo .env NO existe: {env_file}")

# Resumen final
logger.info("\n" + "=" * 80)
logger.info("RESUMEN")
logger.info("=" * 80)

if loaded_files and api_key:
    logger.info("✓ Variables de entorno cargadas correctamente")
    logger.info("✓ El servicio debería funcionar sin necesidad de 'export' manual")
else:
    logger.error("✗ Hay problemas con la carga de variables")
    logger.error("  Revisa que el archivo .env existe y contiene las variables necesarias")
