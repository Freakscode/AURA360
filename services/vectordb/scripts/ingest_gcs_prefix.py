#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import math
import os
import re
from typing import Iterable, List, Sequence

import httpx
from google.cloud import storage


PROJECT_ENV_KEYS = (
    "GCS_PROJECT",
    "GOOGLE_CLOUD_PROJECT",
    "GCLOUD_PROJECT",
    "CLOUDSDK_CORE_PROJECT",
)


def _detect_project() -> str | None:
    for key in PROJECT_ENV_KEYS:
        value = os.getenv(key)
        if value:
            return value
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Queue ingestion jobs for all PDFs under a GCS prefix using the vectosvc API.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "prefix",
        help="gs://bucket/path prefix or path within the bucket (use --bucket).",
    )
    parser.add_argument(
        "--bucket",
        help="Bucket name (not required if prefix is gs://bucket/path).",
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="Base URL for vectosvc API (default: http://localhost:8000).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="Number of documents to enqueue per /ingest/batch call (default: 8).",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=900,
        help="Chunk size to pass in each IngestRequest (default: 900).",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=150,
        help="Chunk overlap to pass in each IngestRequest (default: 150).",
    )
    parser.add_argument(
        "--topic",
        dest="topics",
        action="append",
        default=[],
        help="Add one or more topics metadata entries (repeat flag to add).",
    )
    parser.add_argument(
        "--tag",
        dest="tags",
        action="append",
        default=[],
        help="Add one or more tags metadata entries (repeat flag to add).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List documents that would be enqueued without calling the API.",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=None,
        help="Limit the number of documents processed (useful for smoke tests).",
    )
    parser.add_argument(
        "--project",
        help="Override Google Cloud project ID used for Storage API calls.",
    )
    parser.add_argument(
        "--user-project",
        help="Bill requester-pays buckets to this project (sets user_project).",
    )
    return parser.parse_args()


def resolve_bucket_and_prefix(raw_prefix: str, bucket_override: str | None) -> tuple[str, str]:
    if raw_prefix.startswith("gs://"):
        path = raw_prefix[len("gs://") :]
        parts = path.split("/", 1)
        bucket = parts[0]
        prefix = parts[1] if len(parts) > 1 else ""
    else:
        if not bucket_override:
            raise SystemExit("--bucket is required when prefix is not a gs:// URI")
        bucket = bucket_override
        prefix = raw_prefix.lstrip("/")
    return bucket, prefix


def slugify_doc_id(path: str, seen: set[str]) -> str:
    # Use filename without extension as base
    filename = path.rsplit("/", 1)[-1]
    base = filename.rsplit(".", 1)[0]
    slug = re.sub(r"[^0-9a-zA-Z]+", "-", base).strip("-").lower()
    if not slug:
        slug = f"doc-{hashlib.sha1(path.encode('utf-8')).hexdigest()[:10]}"
    if slug in seen:
        suffix = hashlib.sha1(path.encode("utf-8")).hexdigest()[:8]
        slug = f"{slug}-{suffix}"
    seen.add(slug)
    return slug


def build_ingest_request(
    bucket: str,
    blob_name: str,
    doc_id: str,
    chunk_size: int,
    chunk_overlap: int,
    topics: Sequence[str],
    tags: Sequence[str],
) -> dict:
    metadata = {
        "source": "gcs",
        "bucket": bucket,
        "path": blob_name,
    }
    if topics:
        metadata["topics"] = list({t.strip().lower() for t in topics if t})
    if tags:
        metadata["tags"] = list({t.strip().lower() for t in tags if t})

    return {
        "doc_id": doc_id,
        "url": f"gs://{bucket}/{blob_name}",
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "consolidate_citations": True,
        "metadata": metadata,
    }


def chunked(seq: Sequence[dict], size: int) -> Iterable[Sequence[dict]]:
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def main() -> None:
    args = parse_args()
    bucket, prefix = resolve_bucket_and_prefix(args.prefix, args.bucket)

    project = args.project or _detect_project()
    client_kwargs = {}
    if project:
        client_kwargs["project"] = project
    if args.user_project:
        client_kwargs["client_options"] = {"quota_project_id": args.user_project}
    client = storage.Client(**client_kwargs)

    extra_list_kwargs = {}
    if args.user_project:
        extra_list_kwargs["user_project"] = args.user_project

    iterator = client.list_blobs(bucket, prefix=prefix, **extra_list_kwargs)

    requests: List[dict] = []
    seen_ids: set[str] = set()
    total = 0

    for blob in iterator:
        if args.max is not None and total >= args.max:
            break
        if not blob.name.lower().endswith(".pdf"):
            continue
        if blob.size == 0:
            # Skip placeholders (folders)
            continue
        doc_id = slugify_doc_id(blob.name, seen_ids)
        req = build_ingest_request(
            bucket=bucket,
            blob_name=blob.name,
            doc_id=doc_id,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            topics=args.topics,
            tags=args.tags,
        )
        requests.append(req)
        total += 1

    if not requests:
        print("No matching PDF objects found.")
        return

    print(f"Discovered {len(requests)} PDF objects under gs://{bucket}/{prefix}")
    if args.dry_run:
        for req in requests:
            print(f"[DRY RUN] doc_id={req['doc_id']} url={req['url']}")
        return

    batches = list(chunked(requests, args.batch_size))
    print(f"Enqueuing {len(requests)} documents in {len(batches)} batches via {args.api_url}/ingest/batch")

    failures = 0
    with httpx.Client(base_url=args.api_url, timeout=60.0) as http_client:
        for index, batch in enumerate(batches, start=1):
            try:
                response = http_client.post("/ingest/batch", json=batch)
                response.raise_for_status()
                data = response.json()
            except Exception as exc:  # pragma: no cover - CLI utility
                failures += len(batch)
                print(f"Batch {index} failed ({len(batch)} docs): {exc}")
                continue
            job_ids = data.get("job_ids") or []
            print(
                f"Batch {index}/{len(batches)} queued {len(job_ids)} jobs: {', '.join(job_ids)}"
            )

    if failures:
        print(f"Completed with {failures} documents that failed to enqueue")
    else:
        print("All documents enqueued successfully.")


if __name__ == "__main__":
    main()
