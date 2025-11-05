from __future__ import annotations

from typing import List

import fitz  # PyMuPDF
from langdetect import detect, LangDetectException

from vectosvc.core.schemas import PaperMeta, ParsedDocument, SectionSegment


def extract_plain_text(pdf_bytes: bytes, doc_id: str, source: str | None = None) -> ParsedDocument:
    """Fallback extraction when GROBID is unavailable."""

    text_blocks: List[str] = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
        for page in document:
            page_text = page.get_text("text") or ""
            cleaned = page_text.strip()
            if cleaned:
                text_blocks.append(cleaned)

    meta = PaperMeta(doc_id=doc_id, title=None, authors=[], source=source)

    if text_blocks:
        try:
            meta.lang = detect(" ".join(text_blocks[:3]))
        except LangDetectException:
            meta.lang = None

    segments = [
        SectionSegment(order=i, section_path=f"page_{i+1}", text=block)
        for i, block in enumerate(text_blocks)
    ]

    return ParsedDocument(meta=meta, segments=segments)

