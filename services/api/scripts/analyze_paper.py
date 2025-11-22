#!/usr/bin/env python
from __future__ import annotations
"""
Script para analizar calidad de papers científicos usando Gemini 3 Document Processing.

Uso:
    python analyze_paper.py /path/to/paper.pdf

Retorna JSON con metadata de calidad:
    - evidence_level (1-5)
    - quality_score (1-10)
    - reliability_score (1-10)
    - clinical_relevance (1-10)
    - study_type
    - sample_size
    - key_findings
    - limitations
    - topics

Mejoras:
- Usa Gemini 3 (`gemini-3-pro-preview`) con File API: sube el PDF y aprovecha parsing nativo (texto + imagen).
- Reintentos con backoff ante fallos de Gemini/JSON.
- Fuerza salida JSON (`response_mime_type="application/json"`).
"""

import json
import sys
import os
import time
from pathlib import Path
from typing import Dict, Any

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("⚠️  google-genai no instalado. Instalando...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "google-genai"])
    from google import genai
    from google.genai import types


# Prompt para análisis de calidad
QUALITY_ANALYSIS_PROMPT = """You are a scientific research quality assessment expert. Analyze the following scientific paper and provide a structured quality assessment.

Based on the paper content below, provide a JSON response with the following fields:

1. **evidence_level** (integer 1-5):
   - 5: Systematic review / Meta-analysis
   - 4: Randomized Controlled Trial (RCT)
   - 3: Cohort or Case-Control study
   - 2: Case series
   - 1: Expert opinion / Case report

2. **quality_score** (float 1.0-10.0):
   Overall methodological quality considering:
   - Study design appropriateness
   - Sample size adequacy
   - Statistical methods
   - Control of biases
   - Reproducibility

3. **reliability_score** (float 1.0-10.0):
   Reliability and rigor considering:
   - Data collection methods
   - Measurement validity
   - Conflicts of interest disclosure
   - Peer review quality
   - Journal reputation

4. **clinical_relevance** (float 1.0-10.0):
   Practical clinical relevance:
   - Applicability to clinical practice
   - Real-world implications
   - Population generalizability
   - Actionable recommendations

5. **study_type** (string):
   Specific study design (e.g., "Meta-analysis", "RCT", "Cohort Study", "Cross-sectional", "Review", "Case Study")

6. **sample_size** (integer or null):
   Total number of participants/subjects. If not applicable or not mentioned, return null.

7. **key_findings** (string):
   A concise summary (2-4 sentences) of the main findings and conclusions.

8. **limitations** (string):
   Main limitations of the study (2-3 sentences). If not mentioned, infer based on methodology.

9. **topics** (array of strings):
   List of 3-5 biomedical topics this paper covers. Choose from these categories when applicable:
   - nutrition
   - chrononutrition
   - obesity
   - type2_diabetes
   - metabolism_disorders
   - cardiovascular
   - sleep_health
   - circadian_rhythm
   - gut_microbiome
   - mental_health
   - exercise
   - aging
   - inflammation
   - immune_system
   Or use specific terms if none match.

10. **abstract** (string):
    Extract the paper's abstract if available. If not available, return empty string.

11. **title** (string):
    Extract the paper's title.

12. **authors** (string):
    Extract authors as a comma-separated string. If not available, return "Unknown".

13. **journal** (string):
    Extract journal name. If not available, return empty string.

14. **publication_year** (integer or null):
    Extract publication year. If not available, return null.

**IMPORTANT**: Return ONLY valid JSON. No markdown, no code blocks, no explanations. Just the JSON object.

---

**JSON RESPONSE:**
"""

ANALYSIS_PROMPT_VERSION = "2025-01-24-genai-client"
ANALYSIS_MODEL = os.getenv("ANALYZE_MODEL", "gemini-3-pro-preview")


def wait_for_file_active(client: genai.Client, file_obj, timeout: int = 120, poll: float = 2.0):
    """Espera a que el archivo esté procesado por Gemini File API."""
    start = time.time()
    while time.time() - start < timeout:
        current = client.files.get(name=file_obj.name)
        if current.state.name == "ACTIVE":
            return current
        if current.state.name == "FAILED":
            raise RuntimeError(f"Procesamiento del PDF falló: {current.state}")
        time.sleep(poll)
    raise TimeoutError("Timeout esperando a que Gemini procese el PDF")


def analyze_paper_with_gemini_document(
    pdf_path: str,
    api_key: str,
    model: str = ANALYSIS_MODEL,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    Analiza la calidad de un paper usando Gemini 3 con Document Processing (File API).
    """
    client = genai.Client(api_key=api_key)
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            print("  ☁️  Subiendo PDF a Gemini File API...")
            file_obj = client.files.upload(
                file=Path(pdf_path),
                config={"mime_type": "application/pdf"},
            )
            file_obj = wait_for_file_active(client, file_obj)

            prompt = QUALITY_ANALYSIS_PROMPT
            response = client.models.generate_content(
                model=model,
                contents=[file_obj, prompt],
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=2000,
                    response_mime_type="application/json",
                ),
            )

            result = json.loads(response.text)
            result["_analysis_model"] = model
            result["_analysis_prompt_version"] = ANALYSIS_PROMPT_VERSION
            return result

        except (json.JSONDecodeError, Exception) as e:  # noqa: BLE001
            last_error = e
            if attempt == max_retries:
                break
            sleep_seconds = 2 ** attempt
            print(f"⚠️  Gemini doc falló (intento {attempt}/{max_retries}): {e}. Reintentando en {sleep_seconds}s...")
            time.sleep(sleep_seconds)

    raise Exception(f"Error analizando con Gemini Document API tras {max_retries} reintentos: {last_error}")


def analyze_paper(pdf_path: str, api_key: str) -> Dict[str, Any]:
    """
    Analiza un paper científico completo.

    Args:
        pdf_path: Path al PDF
        api_key: Google API Key

    Returns:
        dict: Metadata completa de calidad
    """
    print(f"📄 Analizando: {pdf_path}")

    # Analizar con Gemini Document Processing
    print("  🤖 Analizando calidad con Gemini (Document Processing)...")
    analysis = analyze_paper_with_gemini_document(pdf_path, api_key)
    print("  ✅ Análisis completado")

    # Agregar metadata adicional
    analysis['_pdf_path'] = pdf_path
    analysis['_pdf_name'] = Path(pdf_path).name

    return analysis


def main():
    """Función principal."""
    if len(sys.argv) < 2:
        print("Uso: python analyze_paper.py <path_to_pdf> [api_key]")
        print("\nEjemplo:")
        print("  python analyze_paper.py paper.pdf")
        print("  python analyze_paper.py paper.pdf AIzaSy...")
        sys.exit(1)

    pdf_path = sys.argv[1]
    api_key = sys.argv[2] if len(sys.argv) > 2 else None

    # Obtener API key de env si no se proporciona
    if not api_key:
        import os
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("❌ Error: GOOGLE_API_KEY no configurada")
            print("   Opción 1: export GOOGLE_API_KEY='tu_api_key'")
            print("   Opción 2: python analyze_paper.py paper.pdf 'tu_api_key'")
            sys.exit(1)

    # Verificar que el archivo existe
    if not Path(pdf_path).exists():
        print(f"❌ Error: El archivo no existe: {pdf_path}")
        sys.exit(1)

    try:
        # Analizar paper
        result = analyze_paper(pdf_path, api_key)

        # Imprimir resultado
        print("\n" + "=" * 70)
        print("  📊 RESULTADOS DEL ANÁLISIS")
        print("=" * 70)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("=" * 70)

        return result

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
