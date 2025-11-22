from __future__ import annotations

from typing import Protocol


class BlobRepository(Protocol):
    """Minimal interface for fetching binary objects by URI or path."""

    def read(self, uri: str) -> bytes:
        """Return file bytes for the given URI/path.

        Implementations may support different URI schemes, e.g.,
        - file:///path/to/file or bare local paths
        - https://... or http://...
        - gs://bucket/key for Google Cloud Storage
        """
        ...

