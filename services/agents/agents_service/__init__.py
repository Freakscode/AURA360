"""Compatibilidad de namespace para exponer los módulos existentes como `agents_service.*`.

Este paquete evita refactorizaciones extensas al registrar los submódulos actuales
(`api`, `infra`, `services`, etc.) bajo el namespace `agents_service`, permitiendo
imports consistentes desde las pruebas y el backend.
"""
from __future__ import annotations

import importlib
import sys
from typing import Dict

# IMPORTANTE: Cargar variables de entorno ANTES de cualquier otro import
# Esto garantiza que los módulos que se importan después tengan acceso a las variables
from infra.env import load_environment

load_environment(override=False)

_SUBMODULE_MAP: Dict[str, str] = {
    "api": "api",
    "infra": "infra",
    "services": "services",
    "holistic_agent": "holistic_agent",
    "nutritional_agent": "nutritional_agent",
}


def _wire_submodules() -> None:
    """Carga los paquetes originales y los expone bajo `agents_service.*`."""
    for alias, target in _SUBMODULE_MAP.items():
        module = importlib.import_module(target)
        sys.modules[f"{__name__}.{alias}"] = module
        globals()[alias] = module


_wire_submodules()

__all__ = sorted(_SUBMODULE_MAP)