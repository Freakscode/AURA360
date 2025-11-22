"""
Pytest configuration and shared fixtures.
"""
from __future__ import annotations

import pytest
import fitz  # PyMuPDF
from qdrant_client import QdrantClient

from vectosvc.config import settings
from vectosvc.core.qdrant_store import QdrantStore


@pytest.fixture(scope="session")
def test_qdrant_client():
    """Cliente Qdrant para tests (usa colección temporal)."""
    client = QdrantClient(url=settings.qdrant_url)
    yield client
    # Cleanup: intentar eliminar colecciones de prueba
    try:
        collections = client.get_collections().collections
        for collection in collections:
            if collection.name.startswith("test_"):
                client.delete_collection(collection.name)
    except Exception:
        pass


@pytest.fixture
def test_store(test_qdrant_client):
    """Store con colección temporal."""
    original_name = settings.collection_name
    test_collection = f"test_collection_{id(test_qdrant_client)}"
    settings.collection_name = test_collection
    
    store = QdrantStore(client=test_qdrant_client)
    
    yield store
    
    # Cleanup
    settings.collection_name = original_name
    try:
        test_qdrant_client.delete_collection(test_collection)
    except Exception:
        pass


@pytest.fixture
def sample_pdf_bytes():
    """PDF de prueba mínimo con contenido estructurado."""
    doc = fitz.open()
    
    # Página 1 - Abstract
    page1 = doc.new_page(width=595, height=842)  # A4
    page1.insert_text(
        (72, 100),
        "Sleep Deprivation and Cognitive Performance",
        fontsize=16,
    )
    page1.insert_text(
        (72, 150),
        "Abstract: This study examines the effects of sleep deprivation on cognitive "
        "performance in healthy adults. Results indicate significant impairment in "
        "attention and memory tasks after 24 hours of sleep deprivation.",
        fontsize=11,
    )
    
    # Página 2 - Introduction
    page2 = doc.new_page(width=595, height=842)
    page2.insert_text((72, 100), "Introduction", fontsize=14)
    page2.insert_text(
        (72, 130),
        "Sleep is essential for cognitive function. Previous research has shown that "
        "sleep deprivation affects various cognitive domains including attention, "
        "working memory, and executive function.",
        fontsize=11,
    )
    
    # Página 3 - Conclusion
    page3 = doc.new_page(width=595, height=842)
    page3.insert_text((72, 100), "Conclusion", fontsize=14)
    page3.insert_text(
        (72, 130),
        "Our findings confirm that acute sleep deprivation has measurable negative "
        "effects on cognitive performance. Future studies should examine chronic "
        "sleep restriction.",
        fontsize=11,
    )
    
    return doc.tobytes()


@pytest.fixture
def sample_tei_xml():
    """TEI XML de ejemplo (salida típica de GROBID)."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <teiHeader>
        <fileDesc>
            <titleStmt>
                <title>Effects of Melatonin on Sleep Quality in Adults</title>
            </titleStmt>
            <sourceDesc>
                <biblStruct>
                    <analytic>
                        <author>
                            <persName>
                                <surname>Smith</surname>
                                <forename>John</forename>
                            </persName>
                        </author>
                        <author>
                            <persName>
                                <surname>Doe</surname>
                                <forename>Jane</forename>
                            </persName>
                        </author>
                        <idno type="DOI">10.1234/sleep.2024.001</idno>
                    </analytic>
                    <monogr>
                        <title level="j">Sleep Medicine</title>
                        <imprint>
                            <date when="2024">2024</date>
                        </imprint>
                    </monogr>
                </biblStruct>
            </sourceDesc>
        </fileDesc>
    </teiHeader>
    <text xml:lang="en">
        <body>
            <div>
                <head>Abstract</head>
                <p>Melatonin supplementation significantly improved sleep onset latency and total sleep time in our study cohort of 150 adults.</p>
            </div>
            <div>
                <head>Introduction</head>
                <p>Sleep disorders affect millions of adults worldwide. Melatonin is a hormone that regulates circadian rhythms.</p>
            </div>
            <div type="conclusion">
                <head>Conclusions</head>
                <p>Our results support the use of melatonin supplementation for improving sleep quality in adults with insomnia.</p>
            </div>
        </body>
    </text>
</TEI>"""


@pytest.fixture
def sample_ingest_request():
    """IngestRequest de ejemplo para tests."""
    return {
        "doc_id": "test-doc-001",
        "text": "This is a test document about sleep deprivation and cognitive performance. " * 20,
        "chunk_size": 300,
        "chunk_overlap": 50,
        "category": "mente",
        "locale": "es-co",
        "source_type": "paper",
        "embedding_model": "test-embedding-model",
        "version": "2025.10.27",
        "valid_from": int(__import__("time").time()),
        "metadata": {
            "topics": ["sleep_health", "cognitive_function"],
            "year": 2024,
            "journal": "Test Journal",
            "source": "test",
        },
    }
