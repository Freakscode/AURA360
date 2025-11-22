from __future__ import annotations

import httpx

from vectosvc.config import settings
from .base import BlobRepository


class HTTPRepository(BlobRepository):
    def read(self, uri: str) -> bytes:
        timeout = getattr(settings, "grobid_timeout", 60)
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(uri)
            resp.raise_for_status()
            return resp.content

