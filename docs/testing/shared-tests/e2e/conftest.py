"""
Configuración de pytest para pruebas End-to-End.

Este módulo proporciona fixtures compartidas y configuración
para todas las pruebas E2E del proyecto AURA360.
"""

from __future__ import annotations

import os
from typing import Any

import pytest


@pytest.fixture(scope="session")
def test_config() -> dict[str, Any]:
    """
    Configuración global para pruebas E2E.
    Lee variables de entorno y proporciona valores por defecto.
    """
    return {
        "backend_url": os.getenv("BACKEND_URL", "http://localhost:8000"),
        "agents_service_url": os.getenv("AGENTS_SERVICE_URL", "http://localhost:8080"),
        "vectorial_service_url": os.getenv("VECTORIAL_SERVICE_URL", "http://localhost:8001"),
        "service_timeout": int(os.getenv("TEST_SERVICE_TIMEOUT", "5")),
        "request_timeout": int(os.getenv("TEST_REQUEST_TIMEOUT", "120")),
        "test_user_email": os.getenv("TEST_USER_EMAIL", "test@example.com"),
        "test_user_password": os.getenv("TEST_USER_PASSWORD", "testpass123"),
    }


def pytest_configure(config):
    """Configuración de pytest antes de ejecutar tests."""
    # Registrar marcadores personalizados
    config.addinivalue_line(
        "markers", "e2e: marca una prueba como end-to-end (requiere todos los servicios)"
    )
    config.addinivalue_line(
        "markers", "slow: marca una prueba como lenta (puede tardar varios minutos)"
    )
    config.addinivalue_line(
        "markers", "integration: marca una prueba como de integración (requiere servicios externos)"
    )

