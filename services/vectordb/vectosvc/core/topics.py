from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np
import yaml

from vectosvc.config import settings
from vectosvc.core.embeddings import Embeddings


def _default_config_path() -> Path:
    env_path = os.getenv("TOPIC_CONFIG_PATH")
    if env_path:
        return Path(env_path)
    return Path(__file__).resolve().parents[2] / "config" / "topics.yaml"


@dataclass(frozen=True)
class TopicDefinition:
    topic_id: str
    name: str
    phrases: Tuple[str, ...]


@dataclass
class TopicMatch:
    topic_id: str
    name: str
    score: float


class TopicCatalogue:
    def __init__(
        self,
        topics: Sequence[TopicDefinition],
        vectors: np.ndarray,
    ) -> None:
        self.topics = list(topics)
        self.vectors = vectors
        self.topic_index = {topic.topic_id: idx for idx, topic in enumerate(self.topics)}

    def to_dict(self) -> Dict[str, Dict[str, Sequence[str]]]:
        return {
            topic.topic_id: {
                "name": topic.name,
                "phrases": list(topic.phrases),
            }
            for topic in self.topics
        }


def _load_config(path: Path) -> List[TopicDefinition]:
    if not path.exists():
        raise FileNotFoundError(f"Topic config not found at {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    topics_section = data.get("topics") or {}
    topics: List[TopicDefinition] = []
    for topic_id, entry in topics_section.items():
        name = entry.get("name") or topic_id.replace("_", " ").title()
        synonyms = entry.get("synonyms") or []
        phrases = [name] + [s for s in synonyms if s]
        clean_phrases = tuple({p.strip().lower() for p in phrases if p and p.strip()})
        if not clean_phrases:
            continue
        topics.append(TopicDefinition(topic_id=topic_id, name=name, phrases=clean_phrases))
    if not topics:
        raise ValueError("No topics defined in config")
    return topics


def _topic_vectors(topics: Sequence[TopicDefinition]) -> np.ndarray:
    texts: List[str] = []
    topic_ids: List[str] = []
    for topic in topics:
        for phrase in topic.phrases:
            texts.append(phrase)
            topic_ids.append(topic.topic_id)
    emb = Embeddings()
    all_vecs = emb.encode(texts)
    # Aggregate embeddings per topic (mean pooling)
    topic_vectors: Dict[str, List[np.ndarray]] = {}
    for idx, topic_id in enumerate(topic_ids):
        topic_vectors.setdefault(topic_id, []).append(all_vecs[idx])
    pooled: List[np.ndarray] = []
    for topic in topics:
        vecs = topic_vectors[topic.topic_id]
        mean_vec = np.mean(np.stack(vecs, axis=0), axis=0)
        # normalize to unit length
        norm = np.linalg.norm(mean_vec) + 1e-12
        pooled.append(mean_vec / norm)
    return np.stack(pooled, axis=0)


@lru_cache(maxsize=1)
def load_catalogue(config_path: str | None = None) -> TopicCatalogue:
    path = Path(config_path) if config_path else _default_config_path().resolve()
    topics = _load_config(path)
    vectors = _topic_vectors(topics)
    return TopicCatalogue(topics=topics, vectors=vectors)


def assign_topics(
    vector: Sequence[float] | np.ndarray,
    top_k: int = 3,
    threshold: float | None = None,
    config_path: str | None = None,
) -> List[TopicMatch]:
    if threshold is None:
        threshold = float(os.getenv("TOPIC_SIM_THRESHOLD", "0.34"))
    catalogue = load_catalogue(config_path)
    vec = np.array(vector, dtype=np.float32)
    norm = np.linalg.norm(vec)
    if norm == 0:
        return []
    vec = vec / norm
    scores = catalogue.vectors @ vec
    order = np.argsort(scores)[::-1]
    matches: List[TopicMatch] = []
    for idx in order[:top_k]:
        score = float(scores[idx])
        if score < threshold:
            continue
        topic = catalogue.topics[idx]
        matches.append(TopicMatch(topic_id=topic.topic_id, name=topic.name, score=score))
    return matches


def export_catalogue(config_path: str | None = None) -> str:
    catalogue = load_catalogue(config_path)
    return json.dumps(catalogue.to_dict(), indent=2)
