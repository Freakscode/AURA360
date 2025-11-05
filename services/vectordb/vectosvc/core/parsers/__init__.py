"""Parser utilities for PDF ingestion."""

from .grobid import fetch_tei, parse_tei
from .pdf import extract_plain_text

__all__ = [
    "fetch_tei",
    "parse_tei",
    "extract_plain_text",
]

