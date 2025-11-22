"""Punto de entrada principal para el servicio FastAPI de agentes holísticos."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from agents_service.api.routers.holistic import router as holistic_router
from infra.env import load_environment

# Configurar logging básico ANTES de cargar variables
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Carga variables de entorno al iniciar la aplicación.
logger.info("Iniciando carga de variables de entorno...")
loaded_files = load_environment(override=False)
if loaded_files:
    logger.info(f"Variables cargadas exitosamente desde: {', '.join(str(f) for f in loaded_files)}")
else:
    logger.warning("No se cargaron archivos .env")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Maneja el ciclo de vida de la aplicación FastAPI."""
    # Startup
    logger.info("Servicio de agentes holísticos iniciado.")
    yield
    # Shutdown
    logger.info("Servicio de agentes holísticos detenido.")


app = FastAPI(
    title="AURA360 Agent Service",
    version="1.0.0",
    description="Servicio FastAPI que orquesta agentes holísticos y consultas vectoriales.",
    lifespan=lifespan,
)

app.include_router(holistic_router, prefix="/api/v1/holistic")


@app.get("/readyz")
def readiness_check():
    """Health check endpoint para validar que el servicio está listo."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
