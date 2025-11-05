from __future__ import annotations

import importlib.util
import logging
import os
import pathlib
import sys

from infra.env import load_environment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("diagnostics.agents_service")


def pytest_configure(config) -> None:  # type: ignore[unused-argument]
    """Configura el entorno de pytest antes de ejecutar tests."""

    load_environment(override=False)

    os.environ.setdefault("VECTOR_SERVICE_COLLECTION_NAME", "holistic_agents_test")
    os.environ.setdefault("VECTOR_SERVICE_URL", "http://localhost:6333")
    os.environ.setdefault("VECTOR_SERVICE_TIMEOUT", "15.0")
    os.environ.setdefault("VECTOR_SERVICE_VERIFY_SSL", "false")
    os.environ.setdefault("AGENT_SERVICE_MODEL_VERSION", "1.0.0-test")

    logger.info("Working directory: %s", pathlib.Path.cwd())
    logger.info("sys.path entries:\n%s", "\n".join(sys.path))
    spec_found = importlib.util.find_spec("agents_service") is not None
    logger.info("agents_service importable: %s", spec_found)