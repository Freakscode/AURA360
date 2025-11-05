from __future__ import annotations

from urllib.parse import urlparse

from .base import BlobRepository
from .fs import LocalFSRepository
from .http import HTTPRepository


def repository_for(uri: str) -> BlobRepository:
    """Return a repository implementation based on URI scheme.

    - gs://... -> GCSRepository (requires optional dependency)
    - http(s)://... -> HTTPRepository
    - file:///... or bare path -> LocalFSRepository
    """
    parsed = urlparse(uri)
    scheme = parsed.scheme.lower()
    if scheme in ("http", "https"):
        return HTTPRepository()
    if scheme in ("file", ""):
        return LocalFSRepository()
    if scheme in ("gs", "gcs"):
        from .gcs import GCSRepository
        # lazily import to keep dependency optional
        from vectosvc.config import settings

        return GCSRepository(
            project=getattr(settings, "gcs_project", None),
            user_project=getattr(settings, "gcs_user_project", None),
        )
    raise ValueError(f"Unsupported URI scheme for repository: {scheme or 'file'}")

__all__ = ["BlobRepository", "repository_for"]

