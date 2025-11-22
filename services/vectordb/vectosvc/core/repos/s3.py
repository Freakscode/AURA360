from __future__ import annotations

import os
import re
from typing import Optional

from loguru import logger

from .base import BlobRepository


_S3_RE = re.compile(r"^s3://(?P<bucket>[^/]+)/(?P<key>.+)$")


class S3Repository(BlobRepository):
    def __init__(self, region: Optional[str] = None):
        self._region = region or self._detect_region_from_env()

    @staticmethod
    def _parse(uri: str) -> tuple[str, str]:
        m = _S3_RE.match(uri)
        if not m:
            raise ValueError(f"Invalid S3 URI (expected s3://bucket/key): {uri}")
        return m.group("bucket"), m.group("key")

    def read(self, uri: str) -> bytes:
        try:
            import boto3  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dep
            raise RuntimeError(
                "boto3 is not installed. Install with: pip install boto3"
            ) from exc

        bucket_name, key = self._parse(uri)
        try:
            if self._region:
                s3 = boto3.client('s3', region_name=self._region)
            else:
                s3 = boto3.client('s3')
        except Exception as exc:  # pragma: no cover - surface config issues
            raise RuntimeError(
                "Failed to initialise S3 client. Configure AWS credentials."
            ) from exc

        logger.debug("Downloading from S3 bucket={} key={}", bucket_name, key)
        response = s3.get_object(Bucket=bucket_name, Key=key)
        return response['Body'].read()

    @staticmethod
    def _detect_region_from_env() -> Optional[str]:
        env_keys = (
            "AWS_REGION",
            "AWS_DEFAULT_REGION",
        )
        for key in env_keys:
            value = os.getenv(key)
            if value:
                return value
        return None
