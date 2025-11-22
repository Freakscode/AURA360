#!/usr/bin/env python3
from __future__ import annotations

import argparse
from typing import Iterable, List, Optional, Sequence

import numpy as np
from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from vectosvc.config import settings
from vectosvc.core.qdrant_store import store
from vectosvc.core import topics as topic_classifier


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Assign topics to existing documents in Qdrant.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of documents processed.",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Number of documents to skip before processing.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=256,
        help="Number of points fetched per API call.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print assignments without writing back to Qdrant.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Override similarity threshold (defaults to TOPIC_SIM_THRESHOLD or settings).",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Override number of topics per document (defaults to settings).",
    )
    return parser.parse_args()


def iter_doc_ids(client: QdrantClient, batch_size: int) -> Iterable[str]:
    seen: set[str] = set()
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=settings.collection_name,
            offset=offset,
            limit=batch_size,
            with_payload=True,
            with_vectors=False,
        )
        if not points:
            break
        for point in points:
            payload = point.payload or {}
            doc_id = payload.get("doc_id")
            if doc_id and doc_id not in seen:
                seen.add(doc_id)
                yield doc_id
        if offset is None:
            break


def doc_vector(client: QdrantClient, doc_id: str, batch_size: int) -> Optional[np.ndarray]:
    offset = None
    vectors: List[np.ndarray] = []
    condition = qm.FieldCondition(key="doc_id", match=qm.MatchValue(value=doc_id))
    fltr = qm.Filter(must=[condition])
    while True:
        points, offset = client.scroll(
            collection_name=settings.collection_name,
            offset=offset,
            limit=batch_size,
            with_vectors=True,
            with_payload=False,
            scroll_filter=fltr,
        )
        if not points:
            break
        for point in points:
            vec = point.vector
            if vec is None:
                continue
            if isinstance(vec, dict):  # multi-vector collection
                vec = next(iter(vec.values()))
            vectors.append(np.array(vec, dtype=np.float32))
        if offset is None:
            break
    if not vectors:
        return None
    matrix = np.stack(vectors, axis=0)
    mean_vec = np.mean(matrix, axis=0)
    norm = np.linalg.norm(mean_vec)
    if norm == 0:
        return None
    return mean_vec / norm


def main() -> None:
    args = parse_args()

    client = QdrantClient(url=settings.qdrant_url)
    threshold = args.threshold if args.threshold is not None else settings.topic_threshold
    top_k = args.top_k if args.top_k is not None else settings.topic_top_k

    total = 0
    updated = 0

    for idx, doc_id in enumerate(iter_doc_ids(client, args.batch_size)):
        if idx < args.offset:
            continue
        if args.limit is not None and total >= args.limit:
            break
        total += 1
        vector = doc_vector(client, doc_id, args.batch_size)
        if vector is None:
            logger.warning("Skipping doc_id=%s (no vectors)", doc_id)
            continue
        matches = topic_classifier.assign_topics(
            vector,
            top_k=top_k,
            threshold=threshold,
            config_path=settings.topic_config_path,
        )
        if not matches:
            logger.info("doc_id=%s -> no topics (below threshold)", doc_id)
            continue
        topic_ids = [m.topic_id for m in matches]
        score_payload = [
            {"id": m.topic_id, "name": m.name, "score": round(m.score, 4)}
            for m in matches
        ]
        if args.dry_run:
            logger.info("[DRY RUN] doc_id={} topics={}", doc_id, topic_ids)
        else:
            store.set_topics(doc_id, topic_ids, score_payload)
            updated += 1
            logger.info("doc_id={} -> topics={}", doc_id, topic_ids)

    logger.info("Processed {} documents; topics updated for {}", total, updated)


if __name__ == "__main__":
    main()
