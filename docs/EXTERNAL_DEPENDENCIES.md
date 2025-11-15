# External Dependencies

## Google ADK Python SDK

The `adk-python` directory contains the Google Agent Development Kit (ADK) Python SDK. This is used by the agents service for building AI agents.

**Note**: This directory can be removed from the monorepo if the agents service uses the published package instead. Consider:

1. Installing via pip/uv:
   ```bash
   uv add google-adk
   ```

2. Or keeping it as a git submodule if you need to make local modifications:
   ```bash
   git submodule add <adk-repo-url> external/adk-python
   ```

## Recommended Approach

- The agents service (`services/agents/pyproject.toml`) ya depende de `google-adk` desde PyPI, por lo que basta con ejecutar `uv sync` para obtener la versión oficial.
- Para producción, usa siempre el paquete publicado en lugar de versionar el SDK completo. Mantén `adk-python/` únicamente cuando necesites parches temporales y documenta el motivo en tu PR.
- Si migras completamente al paquete remoto, puedes eliminar la carpeta `adk-python/` y añadirla al `.gitignore` para evitar futuros commits accidentales.
