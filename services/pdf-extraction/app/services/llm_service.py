"""LLM service using Google Gemini for structured data extraction."""

import logging
import tempfile
from pathlib import Path

from google import genai
from google.genai import types

from ..models.nutrition_plan import NutritionPlan

logger = logging.getLogger(__name__)


class LLMExtractionError(Exception):
    """Error during LLM extraction."""


class LLMService:
    """Service for extracting structured data using Gemini."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp", timeout: int = 300):
        """Initialize LLM service.

        Args:
            api_key: Google AI API key
            model: Gemini model name
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.client = genai.Client(api_key=api_key)

    def extract_nutrition_plan(self, pdf_bytes: bytes) -> NutritionPlan:
        """Extract structured nutrition plan data from PDF using Gemini.

        Args:
            pdf_bytes: Raw PDF file bytes

        Returns:
            Structured nutrition plan data as NutritionPlan model

        Raises:
            LLMExtractionError: If extraction fails
        """
        try:
            # Save PDF to temporary file for upload
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                temp_file.write(pdf_bytes)
                temp_path = temp_file.name

            logger.info(f"Uploading PDF to Gemini (model: {self.model})")

            # Upload PDF file
            uploaded_file = self.client.files.upload(file=temp_path)
            logger.info(f"File uploaded: {uploaded_file.name}")

            # Build extraction prompt
            prompt = self._build_extraction_prompt()

            logger.info("Sending extraction request to Gemini")

            # Call Gemini with structured output
            response = self.client.models.generate_content(
                model=self.model,
                contents=[prompt, uploaded_file],
                config=types.GenerateContentConfig(
                    temperature=0.1,  # Low temperature for consistency
                    response_mime_type="application/json",
                    response_schema=NutritionPlan,  # Gemini will follow this schema
                )
            )

            # Clean up temporary file
            Path(temp_path).unlink()

            # Clean up uploaded file
            self.client.files.delete(name=uploaded_file.name)
            logger.info("Cleaned up temporary and uploaded files")

            # Parse the structured response
            if not response.parsed:
                raise LLMExtractionError("Gemini returned no parsed data")

            logger.info("Successfully extracted nutrition plan data")
            return response.parsed

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}", exc_info=True)
            # Clean up on error
            if 'temp_path' in locals():
                try:
                    Path(temp_path).unlink()
                except:
                    pass
            if 'uploaded_file' in locals():
                try:
                    self.client.files.delete(name=uploaded_file.name)
                except:
                    pass
            raise LLMExtractionError(f"Failed to extract data with Gemini: {e}") from e

    def _build_extraction_prompt(self) -> str:
        """Build extraction prompt for Gemini.

        Returns:
            Extraction prompt text
        """
        return """Eres un asistente experto en extraer información estructurada de planes nutricionales en español.

Tu tarea es analizar el PDF del plan nutricional y extraer toda la información relevante en el formato JSON estructurado especificado.

**INSTRUCCIONES:**
1. Extrae TODA la información presente en el documento
2. Para los metadatos: busca nombre del paciente, nutricionista, fechas y calorías diarias
3. Para la composición corporal: identifica peso, talla, IMC, porcentajes, masa muscular, etc.
4. Para las tablas de intercambio: identifica cada categoría (Harinas, Carnes, Grasas, Verduras, Lácteos, Frutas, Azúcares) con sus alimentos, porciones y gramos
5. Para las comidas: identifica el nombre (Desayuno, Media Mañana, Almuerzo, Merienda, Cena), horario y cantidades de intercambios por categoría
6. Para intercambios diarios: suma los intercambios totales de todas las comidas
7. Si un campo no está presente en el documento, usa null o 0 según corresponda
8. Asegúrate de capturar TODOS los alimentos de las tablas de intercambio

**IMPORTANTE:**
- Lee el documento completo cuidadosamente
- No inventes información que no esté presente
- Extrae todos los detalles disponibles
- Sigue exactamente el formato del schema proporcionado"""
