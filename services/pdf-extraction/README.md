# PDF Extraction Service

Microservicio de extracción de datos estructurados de PDFs de planes nutricionales usando Google Gemini 2.0 Flash.

## Características

- **Extracción con Gemini 2.0**: Usa Google Gemini 2.0 Flash para entender y extraer información estructurada
- **Structured Outputs**: Gemini devuelve datos en formato JSON estructurado garantizado mediante Pydantic models
- **Procesamiento nativo de PDF**: Gemini procesa PDFs directamente, incluyendo texto, imágenes y tablas
- **API FastAPI**: Endpoint RESTful para integración con backend
- **Validación de datos**: Estructura de datos tipo-safe con Pydantic
- **Logging robusto**: Trazabilidad completa del proceso de extracción

## Requisitos

- Python 3.13+
- Google AI API Key (Gemini)

## Instalación

```bash
cd pdf-extraction-service

# Instalar dependencias con uv
uv sync

# O con pip
pip install -e .
```

## Configuración

El servicio se configura mediante variables de entorno con el prefijo `PDF_EXTRACTION_`:

```bash
# Configuración de Gemini
PDF_EXTRACTION_GEMINI_API_KEY=your-api-key-here
PDF_EXTRACTION_GEMINI_MODEL=gemini-2.0-flash-exp
PDF_EXTRACTION_GEMINI_TIMEOUT=300

# Configuración del servicio
PDF_EXTRACTION_SERVICE_PORT=8002
PDF_EXTRACTION_LOG_LEVEL=INFO

# Configuración de PDFs
PDF_EXTRACTION_MAX_PDF_SIZE_MB=10
PDF_EXTRACTION_PDF_MAX_PAGES=50
```

## Uso

### Iniciar el servicio

```bash
# Con uv
uv run python -m app.main

# O con uvicorn directamente
uv run uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

### API Endpoints

#### Health Check
```bash
GET /health
```

Respuesta:
```json
{
  "status": "ok",
  "service": "pdf-extraction-service"
}
```

#### Extraer datos de PDF
```bash
POST /extract
Content-Type: multipart/form-data

{
  "file": <PDF file>
}
```

**Respuesta exitosa (200):**
```json
{
  "success": true,
  "data": {
    "metadata": {
      "patient_name": "GABRIEL CARDONA",
      "nutritionist_name": "Angie martinez",
      "issue_date": "2025-08-01",
      "valid_until": "2025-10-01",
      "daily_calories": 2000
    },
    "body_composition": {
      "weight_kg": 75.5,
      "height_cm": 175,
      "bmi": 24.6,
      "body_fat_percentage": 31.5
    },
    "exchange_tables": [
      {
        "category": "Harinas",
        "items": [
          {
            "food": "ARROZ BLANCO",
            "portion": "1/2 taza",
            "grams": "90"
          }
        ]
      }
    ],
    "meals": [
      {
        "name": "Desayuno",
        "time": "07:00",
        "exchanges": {
          "harinas": 2,
          "carnes": 1,
          "grasas": 1,
          "verduras": 0,
          "lacteos": 1,
          "frutas": 1,
          "azucares": 0
        },
        "notes": null
      }
    ],
    "daily_exchanges": {
      "harinas": 8,
      "carnes": 5,
      "grasas": 4,
      "verduras": 2,
      "lacteos": 2,
      "frutas": 3,
      "azucares": 0
    },
    "notes": null
  },
  "metadata": {
    "filename": "plan.pdf",
    "size_bytes": 754000
  }
}
```

**Respuesta de error:**
```json
{
  "detail": "Failed to extract structured data: <error message>"
}
```

## Integración con Backend

El backend Django puede consumir este servicio para extraer datos de PDFs:

```python
import requests

response = requests.post(
    "http://localhost:8002/extract",
    files={"file": ("plan.pdf", pdf_bytes, "application/pdf")}
)

if response.status_code == 200:
    result = response.json()
    if result["success"]:
        extracted_data = result["data"]
        # Usar datos extraídos...
```

## Desarrollo

### Ejecutar tests
```bash
uv run pytest
```

### Formato de código
```bash
uv run black app/
uv run ruff check app/
```

## Arquitectura

```
pdf-extraction-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configuración
│   ├── models/
│   │   ├── __init__.py
│   │   └── nutrition_plan.py   # Pydantic models para structured outputs
│   └── services/
│       ├── __init__.py
│       └── llm_service.py   # Extracción con Gemini
├── pyproject.toml
└── README.md
```

## Ventajas de Gemini 2.0 Flash

- **Procesamiento nativo de PDF**: No requiere extracción previa de texto con PyMuPDF
- **Comprensión de imágenes**: Puede procesar PDFs basados en imágenes y tablas complejas
- **Structured Outputs**: Garantiza respuestas en formato JSON válido siguiendo el schema Pydantic
- **Rapidez**: Modelo optimizado para latencia (Flash)
- **Precisión**: Mejor comprensión de documentos complejos en español

## Notas

- El modelo Gemini 2.0 Flash es gratuito hasta 1,500 requests/día
- Cada extracción toma aproximadamente 20-30 segundos
- El timeout por defecto es 5 minutos (configurable)
- Los archivos PDF se suben temporalmente a la API de Gemini y se eliminan después del procesamiento
- Soporta PDFs con texto, imágenes y tablas
