"""
Vectosvc API package.

Exports the FastAPI application lazily to avoid circular imports when worker
modules import `vectosvc.api.schemas`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .http import app as _app_type

__all__ = ["app"]


def __getattr__(name: str):
    if name == "app":
        from .http import app as fastapi_app

        return fastapi_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")