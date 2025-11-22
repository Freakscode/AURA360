# Pipeline Unificado de Validación y Procesamiento de Papers

Pipeline completo que integra validación interactiva, upload a cloud storage (GCS/S3) e ingesta a Qdrant para papers biomédicos categorizados.

## 📋 Tabla de Contenidos

- [Descripción General](#descripción-general)
- [Arquitectura](#arquitectura)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Formato de Datos](#formato-de-datos)
- [Ejemplos](#ejemplos)
- [Troubleshooting](#troubleshooting)

## 🎯 Descripción General

Este pipeline automatiza el flujo completo de procesamiento de papers biomédicos:

1. **Validación:** Revisar categorización generada por Gemini 2.5 Flash (interactiva, automática o skip)
2. **Upload:** Subir PDFs y metadata a Google Cloud Storage o Amazon S3
3. **Ingesta:** Procesar papers en Qdrant usando el servicio vectordb existente
4. **Reportes:** Generar reportes consolidados en Markdown y JSON

## 🏗️ Arquitectura

```
┌─────────────────┐
│  Papers Locales │
│  + JSON de      │
│  Categorización │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FASE 1:       │
│   Validación    │◄─── Modo: Interactive/Auto/Skip
│   Interactiva   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FASE 2:       │
│   Upload a      │◄─── GCS o S3
│   Cloud Storage │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FASE 3:       │
│   Ingesta a     │◄─── Servicio vectordb
│   Qdrant        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FASE 4:       │
│   Generación    │
│   de Reportes   │
└─────────────────┘
```

## 📦 Requisitos

### Python Packages

```bash
# Core dependencies
pydantic>=2.6
pyyaml>=6.0

# Cloud storage
google-cloud-storage>=3.4.0  # Para GCS
boto3>=1.34.0                # Para S3

# HTTP client
httpx>=0.25.0
```

### Servicios Externos

- **Vector DB Service:** Servicio `vectordb` corriendo en `http://localhost:8001` (o URL desplegada)
- **Cloud Storage:** Bucket en GCS o S3 configurado
- **Qdrant:** Cluster de Qdrant (local o cloud)

## 🔧 Instalación

1. **Instalar dependencias:**

```bash
cd scripts
pip install pydantic pyyaml google-cloud-storage httpx
# o con uv:
uv pip install pydantic pyyaml google-cloud-storage httpx
```

2. **Configurar credenciales de GCP (si usas GCS):**

```bash
# Autenticar con gcloud
gcloud auth application-default login

# Configurar proyecto
gcloud config set project aura-360-471711
```

3. **Verificar servicio vectordb:**

```bash
# Asegúrate de que el servicio vectordb esté corriendo
cd services/vectordb
docker compose up -d

# Verificar health check
curl http://localhost:8001/readyz
```

## ⚙️ Configuración

### 1. Copiar configuración de ejemplo

```bash
cd scripts
cp config/pipeline_config.yaml config/my_config.yaml
```

### 2. Editar configuración

```yaml
# config/my_config.yaml

# Paths locales
local_papers_dir: "/Users/freakscode/papers"
categorization_file: "/Users/freakscode/papers/categorization.json"

# Cloud Storage
cloud_provider: "gcs"
gcs_bucket: "aura360-papers"
gcs_project: "aura-360-471711"

# Qdrant
qdrant_url: "${QDRANT_URL}"
qdrant_api_key: "${QDRANT_API_KEY}"
qdrant_collection: "holistic_memory"

# Validación
validation_mode: "interactive"  # interactive, auto, skip
auto_approve_threshold: 0.90
batch_size: 10
```

### 3. Configurar variables de entorno

```bash
# Crear archivo .env (opcional)
export QDRANT_URL="https://your-cluster.qdrant.io"
export QDRANT_API_KEY="your-api-key"
```

## 🚀 Uso

### Modo Interactivo (Por Defecto)

Revisar cada paper manualmente:

```bash
python unified_paper_pipeline.py --config config/my_config.yaml
```

### Modo Auto-aprobación

Aprobar automáticamente papers con alta confianza:

```bash
python unified_paper_pipeline.py \
  --config config/my_config.yaml \
  --validation-mode auto \
  --threshold 0.85
```

### Modo Skip Validación

Confiar en la categorización existente:

```bash
python unified_paper_pipeline.py \
  --config config/my_config.yaml \
  --validation-mode skip
```

### Dry Run (Prueba sin Cambios)

Simular todo el pipeline sin hacer cambios reales:

```bash
python unified_paper_pipeline.py \
  --config config/my_config.yaml \
  --dry-run
```

### Solo Validación (Sin Upload/Ingesta)

```bash
python unified_paper_pipeline.py \
  --config config/my_config.yaml \
  --skip-upload \
  --skip-ingestion
```

## 📄 Formato de Datos

### JSON de Categorización

El archivo JSON debe seguir este esquema:

```json
{
  "papers": [
    {
      "doc_id": "unique_paper_id",
      "filename": "paper.pdf",
      "category": "mente",  // mente, cuerpo, alma
      "topics": ["sleep_health", "cognitive_function"],
      "confidence_score": 0.94,  // Opcional, 0.0-1.0

      // Metadata opcional
      "title": "Paper Title",
      "authors": ["Author 1", "Author 2"],
      "journal": "Journal Name",
      "year": 2023,
      "doi": "10.1234/example",
      "abstract": "Abstract text...",
      "url": "https://...",
      "tags": ["tag1", "tag2"],
      "mesh_terms": ["MeSH term 1", "MeSH term 2"]
    }
  ]
}
```

**Campos requeridos:**
- `doc_id`: ID único del paper
- `filename`: Nombre del archivo PDF (debe existir en `local_papers_dir`)
- `category`: Una de las tres categorías: `mente`, `cuerpo`, `alma`

**Campos opcionales:**
- `topics`: Lista de tópicos biomédicos (ver `services/vectordb/config/topics.yaml`)
- `confidence_score`: Score de confianza (0.0-1.0)
- Metadata: `title`, `authors`, `journal`, `year`, `doi`, `abstract`, `url`, `tags`, `mesh_terms`

Ver ejemplo completo en: `config/categorization_example.json`

## 📊 Reportes Generados

El pipeline genera dos tipos de reportes en `pipeline_reports/`:

### 1. Reporte Markdown (`validation_report_TIMESTAMP.md`)

```markdown
# Reporte de Pipeline - run_20250122_143022_abc123

## Resumen Ejecutivo
- Inicio: 2025-01-22 14:30:22
- Fin: 2025-01-22 15:45:33
- Duración: 4511.2s (75.2min)

## Validación
- Total papers: 47
- Validados manualmente: 35
- Auto-aprobados: 12
...
```

### 2. Reporte JSON (`validation_report_TIMESTAMP.json`)

Formato estructurado con toda la información del run para análisis programático.

## 💡 Ejemplos

### Ejemplo 1: Pipeline Completo Interactivo

```bash
# 1. Preparar papers y categorización
ls /Users/freakscode/papers/
# paper1.pdf, paper2.pdf, ...

# 2. Editar config
vim config/my_config.yaml

# 3. Ejecutar pipeline
python unified_paper_pipeline.py --config config/my_config.yaml

# El sistema mostrará cada paper para validación:
# ────────────────────────────────────────────
# Paper 1/47: sleep_circadian_health.pdf
# ────────────────────────────────────────────
# 📄 Título: Sleep and Circadian Health
# ✍️  Autores: Walker et al.
#
# Categorización actual:
#   🧠 Categoría: mente
#   🏷️  Tópicos: [sleep_health, circadian_rhythm]
#   📊 Confianza: ██████████ 0.94
#
# [V] Validar  [M] Modificar  [R] Rechazar  [A] Auto resto  [Q] Salir
# > v
```

### Ejemplo 2: Auto-aprobación Rápida

```bash
# Para papers ya bien categorizados con alta confianza
python unified_paper_pipeline.py \
  --config config/my_config.yaml \
  --validation-mode auto \
  --threshold 0.90

# Solo mostrará papers con confianza < 0.90 para revisión manual
```

### Ejemplo 3: Testing sin Riesgos

```bash
# Probar todo el flujo sin hacer cambios
python unified_paper_pipeline.py \
  --config config/my_config.yaml \
  --dry-run

# Resultado:
# 🔍 Modo DRY RUN: No se subirán archivos reales
# 🔍 Modo DRY RUN: No se ingestarán papers realmente
```

## 🔧 Troubleshooting

### Error: "Servicio vectordb no disponible"

```bash
# Verificar que vectordb esté corriendo
cd services/vectordb
docker compose up -d

# Verificar health
curl http://localhost:8001/readyz
```

### Error: "google.cloud.storage no instalado"

```bash
pip install google-cloud-storage
```

### Error: "Archivo local no encontrado"

Verificar que:
1. `local_papers_dir` apunte al directorio correcto
2. Los `filename` en el JSON coincidan exactamente con los PDFs
3. Los archivos PDF existan en el directorio

```bash
ls -la /path/to/papers/
```

### Papers en DLQ (Dead Letter Queue)

```bash
# Revisar papers fallidos en Qdrant ingestion
cd services/vectordb
# Ver logs del worker
docker compose logs worker

# Reintentar papers del DLQ
# (implementar script de retry si es necesario)
```

### Modificar Categorización en CLI

Durante validación interactiva, elige `[M] Modificar`:

```
> m

📝 Modificando categorización...

Categoría actual: mente
Nueva categoría [mente/cuerpo/alma] (Enter para mantener):
> cuerpo
✅ Categoría actualizada a: cuerpo

Tópicos actuales: sleep_health, cognitive_function
Nuevos tópicos (separados por coma, Enter para mantener):
> obesity, metabolic_syndrome
✅ Tópicos actualizados: obesity, metabolic_syndrome
```

## 📚 Referencias

- **Tópicos disponibles:** `services/vectordb/config/topics.yaml`
- **API vectordb:** `services/vectordb/README.md`
- **Qdrant docs:** https://qdrant.tech/documentation/
- **GCS docs:** https://cloud.google.com/storage/docs

## 🤝 Soporte

Para problemas o preguntas:
1. Revisar logs en consola y `pipeline_reports/`
2. Verificar configuración en `config/my_config.yaml`
3. Reportar issues con información del reporte JSON generado
