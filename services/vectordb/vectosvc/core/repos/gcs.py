from __future__ import annotations

import os
import re
from typing import Optional

from loguru import logger

from vectosvc.config import settings
from .base import BlobRepository


_GS_RE = re.compile(r"^gs://(?P<bucket>[^/]+)/(?P<key>.+)$")


class GCSRepository(BlobRepository):
    def __init__(self, project: Optional[str] = None, user_project: Optional[str] = None):
        self._project = project or self._detect_project_from_env()
        self._user_project = user_project

    @staticmethod
    def _parse(uri: str) -> tuple[str, str]:
        m = _GS_RE.match(uri)
        if not m:
            raise ValueError(f"Invalid GCS URI (expected gs://bucket/key): {uri}")
        return m.group("bucket"), m.group("key")

    def read(self, uri: str) -> bytes:
        try:
            from google.cloud import storage  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dep
            raise RuntimeError(
                "google-cloud-storage is not installed. Install extras 'gcs'"
            ) from exc

        bucket_name, key = self._parse(uri)
        try:
            client = storage.Client(project=self._project) if self._project else storage.Client()
        except Exception as exc:  # pragma: no cover - surface config issues
            raise RuntimeError(
                "Failed to initialise GCS client. Set GCS_PROJECT or GOOGLE_CLOUD_PROJECT environment variable."
            ) from exc
        bucket = storage.Bucket(client, name=bucket_name, user_project=self._user_project)
        blob = storage.Blob(name=key, bucket=bucket)
        logger.debug("Downloading from GCS bucket={} key={}", bucket_name, key)
        return blob.download_as_bytes()

    @staticmethod
    def _detect_project_from_env() -> Optional[str]:
        env_keys = (
            "GCS_PROJECT",
            "GOOGLE_CLOUD_PROJECT",
            "GCLOUD_PROJECT",
            "CLOUDSDK_CORE_PROJECT",
        )
        for key in env_keys:
            value = os.getenv(key)
            if value:
                return value
        return None
