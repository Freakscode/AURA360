from __future__ import annotations

import logging
from typing import Iterable, List, Tuple

import httpx
from lxml import etree
from langdetect import detect, LangDetectException

from vectosvc.config import settings
from vectosvc.core.schemas import PaperMeta, ParsedDocument, SectionSegment


LOGGER = logging.getLogger(__name__)

NS = {"tei": "http://www.tei-c.org/ns/1.0"}


def fetch_tei(
    pdf_bytes: bytes,
    filename: str | None = None,
    consolidate_citations: bool = True,
    timeout: int | None = None,
) -> str:
    """Call GROBID processFulltextDocument and return TEI XML."""

    url = settings.grobid_url.rstrip("/") + "/api/processFulltextDocument"
    data = {
        "consolidateHeader": 1,
        "consolidateCitations": 1 if consolidate_citations else 0,
        "includeRawAffiliations": 0,
        "teiCoordinates": [],
    }
    req_timeout = timeout or settings.grobid_timeout
    files = {"input": (filename or "document.pdf", pdf_bytes, "application/pdf")}

    with httpx.Client(timeout=req_timeout) as client:
        resp = client.post(url, data=data, files=files)
        resp.raise_for_status()
        return resp.text


def parse_tei(tei_xml: str, doc_id: str, source: str | None = None) -> ParsedDocument:
    """Parse TEI XML into metadata and structured segments."""

    root = etree.fromstring(tei_xml.encode("utf-8"))

    title = _first_text(root.xpath(".//tei:titleStmt/tei:title/text()", namespaces=NS))
    authors = [
        _normalise_spaces(" ".join(author.xpath(".//tei:surname/text() | .//tei:forename/text()", namespaces=NS)))
        for author in root.xpath(".//tei:sourceDesc//tei:author", namespaces=NS)
    ]
    authors = [a for a in authors if a]

    doi = _first_text(root.xpath(".//tei:idno[@type='DOI']/text()", namespaces=NS))
    journal = _first_text(root.xpath(".//tei:monogr/tei:title[@level='j']/text()", namespaces=NS))
    year = _extract_year(root)
    lang = _detect_language(root, title)

    meta = PaperMeta(
        doc_id=doc_id,
        title=title,
        authors=authors,
        doi=doi,
        journal=journal,
        year=year,
        lang=lang,
        topics=[],
        mesh_terms=[],
        source=source,
    )

    segments: List[SectionSegment] = []
    order = 0

    # Abstract paragraphs first
    for paragraph in root.xpath(".//tei:abstract//tei:p", namespaces=NS):
        text = _normalise_spaces("".join(paragraph.itertext()))
        if not text:
            continue
        segments.append(
            SectionSegment(
                order=order,
                section_path="abstract",
                text=text,
                is_abstract=True,
                is_conclusion=False,
            )
        )
        order += 1

    body = root.find(".//tei:text/tei:body", namespaces=NS)
    if body is not None:
        segments.extend(_walk_body(body, order_start=order))

    return ParsedDocument(meta=meta, segments=segments)


def _walk_body(node: etree._Element, order_start: int = 0, parent_path: Iterable[str] | None = None) -> List[SectionSegment]:
    segments: List[SectionSegment] = []
    order = order_start
    parent_path = list(parent_path or [])

    for div in node.xpath("./tei:div", namespaces=NS):
        head = _first_text(div.xpath("./tei:head/text()", namespaces=NS))
        div_type = (div.get("type") or "").lower()
        current_path = parent_path + ([head] if head else [])
        path_label = " > ".join(filter(None, current_path)) or "body"
        is_conclusion = (div_type in {"conclusion", "conclusions"}) or (head and "concl" in head.lower()) if div_type or head else False

        for paragraph in div.xpath("./tei:p", namespaces=NS):
            text = _normalise_spaces("".join(paragraph.itertext()))
            if not text:
                continue
            segments.append(
                SectionSegment(
                    order=order,
                    section_path=path_label,
                    text=text,
                    is_abstract=False,
                    is_conclusion=is_conclusion,
                )
            )
            order += 1

        # Recurse into nested divs
        child_segments = _walk_body(div, order_start=order, parent_path=current_path)
        segments.extend(child_segments)
        order = segments[-1].order + 1 if segments else order

    return segments


def _first_text(items: List[str]) -> str | None:
    for item in items:
        cleaned = _normalise_spaces(item)
        if cleaned:
            return cleaned
    return None


def _normalise_spaces(text: str) -> str:
    return " ".join(text.split())


def _extract_year(root: etree._Element) -> int | None:
    year_text = _first_text(root.xpath(".//tei:monogr//tei:date/@when | .//tei:monogr//tei:date/text()", namespaces=NS))
    if not year_text:
        return None
    for token in year_text.split():
        if token.isdigit() and len(token) == 4:
            return int(token)
    try:
        return int(year_text[:4])
    except (ValueError, TypeError):
        return None


def _detect_language(root: etree._Element, fallback_text: str | None) -> str | None:
    lang_attr = root.get("{http://www.w3.org/XML/1998/namespace}lang")
    if lang_attr:
        return lang_attr.lower()

    sample_text = fallback_text or _first_text(root.xpath(".//tei:p/text()", namespaces=NS))
    if not sample_text:
        return None

    try:
        return detect(sample_text)
    except LangDetectException:
        return None

