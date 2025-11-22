"""Bootstrap de variables de entorno para el servicio de agentes.

Centraliza la carga de archivos ``.env`` usando ``python-dotenv`` para evitar
duplicar lógica en scripts, pruebas y la aplicación principal.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_DEFAULT_ENV_FILES: tuple[str, ...] = (".env", ".env.local")
_ENV_ALREADY_LOADED = False


def _resolve_path(path: str | Path, base_dir: Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = base_dir / candidate
    return candidate


def load_environment(
    *, override: bool = False, extra_paths: Iterable[str | Path] | None = None
) -> list[Path]:
    """Carga archivos ``.env`` del proyecto.

    Args:
        override: Si es ``True`` re-escribe variables ya definidas en el entorno.
        extra_paths: Rutas adicionales (absolutas o relativas al raíz del
            proyecto) que se intentarán cargar.

    Returns:
        Lista con las rutas efectivamente cargadas.
    """

    global _ENV_ALREADY_LOADED

    base_dir = Path(__file__).resolve().parent.parent
    candidates: List[str | Path] = list(_DEFAULT_ENV_FILES)
    if extra_paths:
        candidates.extend(extra_paths)

    loaded_paths: list[Path] = []

    # Si ya se cargaron los envs y no nos solicitaron override explícito ni
    # rutas adicionales, evitamos recargar.
    if _ENV_ALREADY_LOADED and not override and not extra_paths:
        logger.debug("Variables de entorno ya cargadas anteriormente, saltando recarga")
        return loaded_paths

    logger.info(f"Buscando archivos .env en: {base_dir}")

    for candidate in candidates:
        dotenv_path = _resolve_path(candidate, base_dir)
        if not dotenv_path.exists():
            logger.debug(f"Archivo no encontrado: {dotenv_path}")
            continue

        logger.info(f"✓ Cargando variables desde: {dotenv_path}")
        load_dotenv(dotenv_path=dotenv_path, override=override)
        loaded_paths.append(dotenv_path)

    if loaded_paths:
        _ENV_ALREADY_LOADED = True
        logger.info(f"Variables cargadas desde {len(loaded_paths)} archivo(s)")
    else:
        logger.warning(f"No se encontraron archivos .env en {base_dir}")

    return loaded_paths


__all__ = ["load_environment"]


