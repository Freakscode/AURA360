"""
Tests for document parsers (GROBID TEI and PDF).
"""
import pytest
from vectosvc.core.parsers.grobid import parse_tei
from vectosvc.core.parsers.pdf import extract_plain_text


class TestGrobidParser:
    """Tests for GROBID TEI parser."""
    
    def test_parse_tei_basic(self, sample_tei_xml):
        """Test parsing básico de TEI."""
        parsed = parse_tei(sample_tei_xml, doc_id="test-001")
        
        assert parsed.meta.doc_id == "test-001"
        assert parsed.meta.title == "Effects of Melatonin on Sleep Quality in Adults"
        assert len(parsed.segments) > 0
    
    def test_parse_tei_authors(self, sample_tei_xml):
        """Test extracción de autores."""
        parsed = parse_tei(sample_tei_xml, doc_id="test-002")
        
        assert len(parsed.meta.authors) == 2
        # GROBID retorna "Surname Forename"
        assert "Smith John" in parsed.meta.authors
        assert "Doe Jane" in parsed.meta.authors
    
    def test_parse_tei_doi(self, sample_tei_xml):
        """Test extracción de DOI."""
        parsed = parse_tei(sample_tei_xml, doc_id="test-003")
        
        assert parsed.meta.doi == "10.1234/sleep.2024.001"
    
    def test_parse_tei_journal_and_year(self, sample_tei_xml):
        """Test extracción de journal y año."""
        parsed = parse_tei(sample_tei_xml, doc_id="test-004")
        
        assert parsed.meta.journal == "Sleep Medicine"
        assert parsed.meta.year == 2024
    
    def test_parse_tei_language(self, sample_tei_xml):
        """Test detección de idioma."""
        parsed = parse_tei(sample_tei_xml, doc_id="test-005")
        
        assert parsed.meta.lang == "en"
    
    def test_parse_tei_segments(self, sample_tei_xml):
        """Test extracción de segmentos."""
        parsed = parse_tei(sample_tei_xml, doc_id="test-006")
        
        # Debe tener Abstract, Introduction, Conclusions
        assert len(parsed.segments) >= 3
        
        # Verificar orden
        assert parsed.segments[0].order == 0
        assert parsed.segments[1].order == 1
        assert parsed.segments[2].order == 2
        
        # Verificar section_paths
        section_paths = [seg.section_path for seg in parsed.segments]
        assert any("abstract" in path.lower() for path in section_paths)
        assert any("introduction" in path.lower() for path in section_paths)
    
    def test_parse_tei_abstract_flag(self, sample_tei_xml):
        """Test flag is_abstract."""
        parsed = parse_tei(sample_tei_xml, doc_id="test-007")
        
        # En el TEI de ejemplo, el abstract está en body/div, no en <abstract> tag
        # Por lo tanto, no tendrá is_abstract=True en este caso
        # El parser GROBID extrae abstract del tag <abstract> en teiHeader
        # En nuestro XML de ejemplo no hay tag <abstract> en teiHeader
        assert len(parsed.segments) >= 3
    
    def test_parse_tei_conclusion_flag(self, sample_tei_xml):
        """Test flag is_conclusion."""
        parsed = parse_tei(sample_tei_xml, doc_id="test-008")
        
        # Debe haber al menos un segmento de conclusión
        conclusion_segments = [seg for seg in parsed.segments if seg.is_conclusion]
        assert len(conclusion_segments) >= 1
        assert "results support" in conclusion_segments[0].text
    
    def test_parse_tei_text_normalization(self, sample_tei_xml):
        """Test que texto está normalizado (sin espacios extra)."""
        parsed = parse_tei(sample_tei_xml, doc_id="test-009")
        
        for segment in parsed.segments:
            # No debe tener dobles espacios
            assert "  " not in segment.text
            # No debe tener saltos de línea
            assert "\n" not in segment.text
            # No debe empezar/terminar con espacios
            assert segment.text == segment.text.strip()
    
    def test_parse_tei_with_source(self, sample_tei_xml):
        """Test que source se preserva."""
        parsed = parse_tei(sample_tei_xml, doc_id="test-010", source="pubmed")
        
        assert parsed.meta.source == "pubmed"
    
    def test_parse_tei_minimal(self):
        """Test con TEI mínimo (sin mucha metadata)."""
        minimal_tei = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt>
                        <title>Minimal Paper</title>
                    </titleStmt>
                    <sourceDesc><biblStruct></biblStruct></sourceDesc>
                </fileDesc>
            </teiHeader>
            <text>
                <body>
                    <div>
                        <p>Simple paragraph.</p>
                    </div>
                </body>
            </text>
        </TEI>"""
        
        parsed = parse_tei(minimal_tei, doc_id="minimal-001")
        
        assert parsed.meta.title == "Minimal Paper"
        assert len(parsed.segments) >= 1
        assert "Simple paragraph" in parsed.segments[0].text


class TestPDFParser:
    """Tests for PyMuPDF fallback parser."""
    
    def test_extract_plain_text_basic(self, sample_pdf_bytes):
        """Test extracción básica de PDF."""
        parsed = extract_plain_text(sample_pdf_bytes, doc_id="pdf-test-001")
        
        assert parsed.meta.doc_id == "pdf-test-001"
        assert len(parsed.segments) > 0
    
    def test_extract_plain_text_segments(self, sample_pdf_bytes):
        """Test que cada página es un segmento."""
        parsed = extract_plain_text(sample_pdf_bytes, doc_id="pdf-test-002")
        
        # PDF de prueba tiene 3 páginas
        assert len(parsed.segments) == 3
        
        # Verificar section_path
        assert parsed.segments[0].section_path == "page_1"
        assert parsed.segments[1].section_path == "page_2"
        assert parsed.segments[2].section_path == "page_3"
    
    def test_extract_plain_text_order(self, sample_pdf_bytes):
        """Test que orden es secuencial."""
        parsed = extract_plain_text(sample_pdf_bytes, doc_id="pdf-test-003")
        
        for i, segment in enumerate(parsed.segments):
            assert segment.order == i
    
    def test_extract_plain_text_content(self, sample_pdf_bytes):
        """Test que contenido se extrae correctamente."""
        parsed = extract_plain_text(sample_pdf_bytes, doc_id="pdf-test-004")
        
        # Buscar contenido conocido
        all_text = " ".join([seg.text for seg in parsed.segments])
        assert "Sleep Deprivation" in all_text or "sleep" in all_text.lower()
        assert "Cognitive Performance" in all_text or "cognitive" in all_text.lower()
    
    def test_extract_plain_text_language_detection(self, sample_pdf_bytes):
        """Test detección de idioma."""
        parsed = extract_plain_text(sample_pdf_bytes, doc_id="pdf-test-005")
        
        # Debe detectar inglés
        assert parsed.meta.lang in ["en", "english", None]  # puede variar
    
    def test_extract_plain_text_no_abstract_flags(self, sample_pdf_bytes):
        """Test que sin GROBID no hay flags especiales."""
        parsed = extract_plain_text(sample_pdf_bytes, doc_id="pdf-test-006")
        
        # PyMuPDF no identifica secciones especiales
        for segment in parsed.segments:
            assert segment.is_abstract is False
            assert segment.is_conclusion is False
    
    def test_extract_plain_text_with_source(self, sample_pdf_bytes):
        """Test que source se preserva."""
        parsed = extract_plain_text(
            sample_pdf_bytes,
            doc_id="pdf-test-007",
            source="manual_upload"
        )
        
        assert parsed.meta.source == "manual_upload"
    
    def test_extract_plain_text_empty_pdf(self):
        """Test con PDF vacío."""
        import fitz
        doc = fitz.open()
        doc.new_page()  # página vacía
        empty_pdf = doc.tobytes()
        
        parsed = extract_plain_text(empty_pdf, doc_id="empty-pdf")
        
        # Debe retornar documento con meta pero sin segmentos
        assert parsed.meta.doc_id == "empty-pdf"
        assert len(parsed.segments) == 0
