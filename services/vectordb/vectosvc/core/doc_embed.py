from __future__ import annotations

from typing import Iterable, Sequence

from vectosvc.config import service_settings
from vectosvc.core.embeddings import Embeddings
from vectosvc.core.schemas import SectionSegment


def _segment_priority(segment: SectionSegment) -> tuple[int, int]:
    path = (segment.section_path or "").lower()
    if segment.is_abstract or "abstract" in path:
        return (0, segment.order)
    if segment.is_conclusion or "conclusion" in path or "summary" in path:
        return (1, segment.order)
    if "introduction" in path or "background" in path:
        return (2, segment.order)
    if "results" in path or "methods" in path:
        return (3, segment.order)
    return (4, segment.order)


def representative_text(
    segments: Sequence[SectionSegment],
    max_chars: int = 4000,
    min_segments: int = 3,
) -> str:
    """Build a representative text snippet for a document.

    Prefers abstract, conclusion, and introduction segments, but will fall back
    to the first segments available to reach ``max_chars``.
    """

    selected: list[str] = []
    total = 0

    for segment in sorted(segments, key=_segment_priority):
        text = (segment.text or "").strip()
        if not text:
            continue
        if text in selected:
            continue
        selected.append(text)
        total += len(text)
        if total >= max_chars and len(selected) >= min_segments:
            break

    if not selected and segments:
        # Fallback: take the first available segment text
        for segment in segments:
            text = (segment.text or "").strip()
            if text:
                return text[:max_chars]
        return ""

    combined = "\n\n".join(selected)
    return combined[:max_chars]


def document_embedding(texts: Iterable[str]) -> list[float]:
    """Batch embed representative texts and return vectors as plain lists."""

    texts = [t.strip() for t in texts if t and t.strip()]
    if not texts:
        return []
    emb = Embeddings(model_name=service_settings.embedding_model)
    vectors = emb.encode(texts)
    return [vec.tolist() for vec in vectors]


def embedding_for_segments(segments: Sequence[SectionSegment]) -> list[float] | None:
    """Compute a single embedding for a list of document segments."""

    text = representative_text(segments)
    if not text:
        return None
    return document_embedding([text])[0]

