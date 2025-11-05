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

For production, use the published package from PyPI rather than vendoring the entire SDK in the repository. Only keep local copies for development/testing if making modifications to the SDK itself.
