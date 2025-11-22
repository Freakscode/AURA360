# Sistema de Gestión de Papers Científicos con Análisis de Calidad

## 📋 Índice

1. [Arquitectura General](#arquitectura-general)
2. [Metadata de Calidad](#metadata-de-calidad)
3. [Scripts de Análisis y Carga](#scripts-de-análisis-y-carga)
4. [Estrategia de Referenciación](#estrategia-de-referenciación)
5. [Integración con Qdrant](#integración-con-qdrant)
6. [Integración con Agente de Recomendaciones](#integración-con-agente-de-recomendaciones)
7. [Uso en Producción](#uso-en-producción)

---

## 🏗️ Arquitectura General

```
┌─────────────────────────────────────────────────────────────────┐
│ FASE 1: INGESTA Y ANÁLISIS                                      │
└─────────────────────────────────────────────────────────────────┘

PDF Local
    ↓
    ├──→ Gemini 2.0 Flash Exp (Análisis de Calidad)
    │    • Evidence Level (1-5)
    │    • Quality Score (1-10)
    │    • Reliability Score (1-10)
    │    • Clinical Relevance (1-10)
    │    • Study Type, Sample Size
    │    • Key Findings, Limitations
    │    • Topics, Abstract extraction
    │
    ├──→ AWS S3 (Almacenamiento)
    │    Key: papers/nutrition/YYYY/author_topic.pdf
    │    Bucket: aura360-clinical-papers
    │    Region: us-east-1
    │
    └──→ PostgreSQL (Metadata)
         Tabla: clinical_papers
         • doc_id (UUID - PRIMARY KEY)
         • s3_key (unique)
         • Quality scores
         • Bibliographic data
         • composite_score (auto-calculated)

┌─────────────────────────────────────────────────────────────────┐
│ FASE 2: ACCESO Y REFERENCIACIÓN                                 │
└─────────────────────────────────────────────────────────────────┘

Agente AI genera recomendaciones
    ↓
Incluye campo "references": [doc_id1, doc_id2, doc_id3]
    ↓
Frontend muestra botón "Ver artículo"
    ↓
Click → GET /api/papers/{doc_id}/download/
    ↓
Backend genera Presigned URL (15 min TTL)
    ↓
Browser descarga directo desde S3 (sin proxy)
```

---

## 📊 Metadata de Calidad

### Campos Analíticos (Generados por Gemini)

#### 1. **evidence_level** (Integer 1-5)
Jerarquía de evidencia científica:
- **5**: Meta-análisis / Systematic Reviews
- **4**: Randomized Controlled Trials (RCT)
- **3**: Estudios de Cohorte / Caso-Control
- **2**: Series de casos
- **1**: Opinión de expertos / Case reports

#### 2. **quality_score** (Decimal 1.0-10.0)
Calidad metodológica general:
- Diseño del estudio
- Tamaño de muestra
- Métodos estadísticos
- Control de sesgos
- Reproducibilidad

#### 3. **reliability_score** (Decimal 1.0-10.0)
Confiabilidad y rigor:
- Métodos de recolección de datos
- Validez de mediciones
- Declaración de conflictos de interés
- Calidad de peer review
- Reputación del journal

#### 4. **clinical_relevance** (Decimal 1.0-10.0)
Relevancia clínica práctica:
- Aplicabilidad a práctica clínica
- Implicaciones en mundo real
- Generalización a población
- Recomendaciones accionables

#### 5. **composite_score** (Decimal - Auto-calculado)
Score compuesto para ranking:
```python
composite_score = (
    (evidence_level / 5.0 * 10.0) * 0.3 +  # 30% peso
    quality_score * 0.4 +                   # 40% peso
    reliability_score * 0.3                 # 30% peso
)
```

**Badges de Calidad**:
- 🟢 **Excelente** (≥8.5): Alta confianza para usar como referencia
- 🟡 **Bueno** (≥7.0): Confiable para recomendaciones generales
- 🟠 **Moderado** (≥5.0): Usar con precaución
- 🔴 **Bajo** (<5.0): No recomendado para referencias directas

### Otros Campos

- **study_type**: Meta-analysis, RCT, Cohort, Review, etc.
- **sample_size**: Número de participantes
- **impact_factor**: Del journal (si disponible)
- **key_findings**: Resumen de hallazgos clave (2-4 oraciones)
- **limitations**: Limitaciones identificadas (2-3 oraciones)
- **topics**: Array de topics biomédicos

---

## 🛠️ Scripts de Análisis y Carga

### 1. **analyze_paper.py** - Análisis Individual

Analiza un PDF con Gemini 3 (File API) y retorna JSON con metadata de calidad.

**Uso**:
```bash
cd services/api

# Usando variable de entorno (recomendado)
export GOOGLE_API_KEY="AIzaSy..."
python scripts/analyze_paper.py "/path/to/paper.pdf"

# Pasando API key como argumento (opcional)
python scripts/analyze_paper.py "/path/to/paper.pdf" "AIzaSy..."
```
Notas:
- Requiere paquete `google-genai` (se instala automáticamente si falta).
- Gemini 3 admite PDFs hasta ~1000 páginas; cada página ~258 tokens según documentación.

**Output** (JSON):
```json
{
  "title": "Effect of Mediterranean Diet on...",
  "authors": "Smith J, García M, et al.",
  "journal": "The Lancet",
  "publication_year": 2024,
  "evidence_level": 4,
  "quality_score": 8.5,
  "reliability_score": 9.0,
  "clinical_relevance": 8.0,
  "study_type": "RCT",
  "sample_size": 1200,
  "key_findings": "Mediterranean diet significantly reduced...",
  "limitations": "Limited to European populations...",
  "topics": ["nutrition", "cardiovascular", "mediterranean_diet"],
  "abstract": "Background: ...",
  "_pdf_path": "/path/to/paper.pdf",
  "_pdf_name": "smith2024_mediterranean.pdf"
}
```

### 2. **batch_upload_papers.py** - Carga Masiva

Procesa carpeta completa: analiza + sube a S3 + crea registros en PostgreSQL.

**Requisitos**:
```bash
# Environment variables
export GOOGLE_API_KEY="AIzaSy..."
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="wJalr..."
export AWS_S3_BUCKET_NAME="aura360-clinical-papers"
export AWS_S3_REGION="us-east-1"

# Database (usa Django settings por defecto)
export DATABASE_URL="postgresql://user:pass@host:port/db"

# Opcional
export ANALYZE_MODEL="gemini-3-pro-preview"  # default ya usa este modelo
# La librería usada es `google-genai`; la API key debe tener acceso a Gemini 3
```

**Uso**:
```bash
cd services/api

# Procesar carpeta de PDFs
python scripts/batch_upload_papers.py "/Users/freakscode/Downloads/PDFs Referencias Nutrición"
```

**Proceso por PDF**:
1. ✅ Verifica si ya existe (evita duplicados)
2. 🤖 Analiza con Gemini (File API, modelo gemini-3-pro-preview)
3. ☁️ Sube a S3
4. 💾 Crea registro en PostgreSQL
5. 📊 Calcula composite_score automáticamente
6. 🔐 S3 con SSE AES256 y metadata (title, year, quality_score, pdf_md5, analysis_model)

**Output**:
```
🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀
  CARGA MASIVA DE PAPERS
🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀

📁 Carpeta: /Users/.../PDFs Referencias Nutrición
📄 PDFs encontrados: 101

[1/101]
======================================================================
📄 Procesando: smith2024_mediterranean.pdf
======================================================================
🤖 Analizando con Gemini...
  📖 Extrayendo texto del PDF...
  ✅ Texto extraído (15234 caracteres)
  🤖 Analizando calidad con Gemini...
  ✅ Análisis completado
📦 S3 Key: papers/nutrition/2024/smith2024_mediterranean.pdf
☁️  Subiendo a S3...
💾 Creando registro en PostgreSQL...
✅ Procesado exitosamente!
   Doc ID: 550e8400-e29b-41d4-a716-446655440000
   Composite Score: 8.32
   Quality Badge: 🟡

...

======================================================================
  📊 RESUMEN DE CARGA
======================================================================
Total de PDFs: 101
✅ Exitosos: 98
⚠️  Omitidos: 2 (duplicados)
❌ Fallidos: 1

📄 Resultados guardados en: upload_results_20250121_143022.json
```

---

## 🔗 Estrategia de Referenciación

### El problema

Necesitamos vincular:
1. **PDF físico** en S3
2. **Metadata** en PostgreSQL
3. **Chunks vectorizados** en Qdrant (opcional)
4. **Referencias** en recomendaciones AI

### La solución: doc_id como UUID canónico

```
┌─────────────────────────────────────────────────────┐
│ MODELO DE DATOS UNIFICADO                           │
└─────────────────────────────────────────────────────┘

ClinicalPaper (PostgreSQL)
├─ doc_id: UUID (PRIMARY KEY) ← IDENTIFICADOR CANÓNICO
├─ s3_key: "papers/nutrition/2024/smith.pdf"
├─ s3_bucket: "aura360-clinical-papers"
├─ s3_region: "us-east-1"
├─ quality_score: 8.5
├─ composite_score: 8.32
└─ topics: ["nutrition", "cardiovascular"]

         ↓ (doc_id se propaga a todos los sistemas)

┌────────────────────────────────────────────────┐
│ Qdrant Chunks (OPCIONAL)                       │
├─ point_id: auto                                │
├─ vector: [0.123, 0.456, ...]                  │
└─ payload:                                      │
    ├─ doc_id: "550e8400..." ← REFERENCIA        │
    ├─ s3_key: "papers/..."                      │
    ├─ quality_score: 8.5                        │
    ├─ chunk_index: 0                            │
    └─ text: "Mediterranean diet..."             │
└────────────────────────────────────────────────┘

         ↓ (Agente busca en Qdrant)

┌────────────────────────────────────────────────┐
│ AI Recommendation                               │
├─ type: "nutrition"                              │
├─ priority: "high"                               │
├─ title: "Adoptar dieta mediterránea"           │
├─ description: "..."                             │
└─ references: [                                  │
    "550e8400-e29b-41d4-a716-446655440000", ← doc_id
    "6ba7b810-9dad-11d1-80b4-00c04fd430c8"        │
   ]                                              │
└────────────────────────────────────────────────┘

         ↓ (Frontend solicita presigned URL)

GET /api/papers/550e8400-e29b-41d4-a716-446655440000/download/

         ↓

Backend:
1. Busca doc_id en PostgreSQL
2. Obtiene s3_key, s3_bucket, s3_region
3. Genera Presigned URL (15 min)
4. Retorna URL al frontend

         ↓

Frontend:
window.open(presigned_url) → S3 directo (sin proxy)
```

### Ventajas de este enfoque

1. **Single Source of Truth**: doc_id es el identificador único
2. **Desacoplamiento**: S3, PostgreSQL y Qdrant son independientes
3. **Performance**: Presigned URLs = descarga directa desde S3
4. **Seguridad**: URLs temporales con TTL
5. **Escalabilidad**: No pasa por tu backend
6. **Trazabilidad**: Puedes auditar accesos vía S3 logs

---

## 🔎 Integración con Qdrant

### Opción A: Ingestar papers completos (Recomendado)

Usa el pipeline existente de `vectordb`:

```bash
# 1. Subir paper a S3 + PostgreSQL (con batch_upload_papers.py)
# 2. Ingestar a Qdrant usando vectordb service

curl -X POST http://localhost:8001/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source_kind": "pdf",
    "source_uri": "s3://aura360-clinical-papers/papers/nutrition/2024/smith.pdf",
    "doc_id": "550e8400-e29b-41d4-a716-446655440000",
    "metadata": {
      "quality_score": 8.5,
      "composite_score": 8.32,
      "evidence_level": 4,
      "topics": ["nutrition", "cardiovascular"]
    }
  }'
```

El pipeline:
1. Descarga PDF desde S3
2. Parsea con Grobid
3. Crea chunks
4. Genera embeddings
5. Upsert a Qdrant con payload:
   ```python
   {
       "doc_id": "550e8400...",
       "s3_key": "papers/nutrition/2024/smith.pdf",
       "chunk_index": 0,
       "text": "Mediterranean diet...",
       "quality_score": 8.5,
       "composite_score": 8.32,
       "evidence_level": 4,
       "topics": ["nutrition", "cardiovascular"]
   }
   ```

### Opción B: Solo metadata (ligero)

Si solo quieres buscar por metadata sin chunks:

```python
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

client = QdrantClient(url="https://qdrant-url", api_key="...")

# Un solo punto por paper (sin chunks)
point = PointStruct(
    id=str(uuid.uuid4()),
    vector=paper_embedding,  # Embedding del abstract
    payload={
        "doc_id": str(paper.doc_id),
        "title": paper.title,
        "abstract": paper.abstract,
        "quality_score": float(paper.quality_score),
        "composite_score": float(paper.composite_score),
        "topics": paper.topics,
    }
)

client.upsert(collection_name="papers_metadata", points=[point])
```

---

## 🤖 Integración con Agente de Recomendaciones

### Modificar el Agente para incluir referencias

El agente debe:
1. Analizar datos del paciente
2. Buscar papers relevantes en Qdrant
3. Filtrar por `composite_score` > umbral
4. Extraer `doc_id` únicos
5. Incluir en recomendaciones

**Ejemplo de búsqueda en Qdrant** (desde el agente):

```python
# services/agents/services/recommendation_agent.py

def search_relevant_papers(self, topics: List[str], quality_threshold: float = 7.0) -> List[str]:
    """
    Busca papers relevantes filtrados por calidad.

    Args:
        topics: Topics de interés
        quality_threshold: Score mínimo de calidad

    Returns:
        list: doc_ids de papers relevantes
    """
    from qdrant_client import QdrantClient, models

    client = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key
    )

    # Buscar por topics + filtro de calidad
    results = client.scroll(
        collection_name="papers_metadata",
        scroll_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="topics",
                    match=models.MatchAny(any=topics)
                ),
                models.FieldCondition(
                    key="composite_score",
                    range=models.Range(gte=quality_threshold)
                )
            ]
        ),
        limit=10,
        with_payload=True
    )

    # Extraer doc_ids únicos
    doc_ids = [point.payload["doc_id"] for point in results[0]]

    # Ordenar por composite_score (descendente)
    doc_ids_sorted = sorted(
        doc_ids,
        key=lambda did: next(
            (p.payload["composite_score"] for p in results[0] if p.payload["doc_id"] == did),
            0
        ),
        reverse=True
    )

    return doc_ids_sorted[:3]  # Top 3
```

**Prompt del agente** (actualizado):

```python
RECOMMENDATION_PROMPT = """
...

Para CADA recomendación, proporciona:
- type: ...
- priority: ...
- title: ...
- description: ...
- rationale: ...
- action_steps: [...]
- references: [<doc_id_1>, <doc_id_2>, ...] ← NUEVO CAMPO

Los doc_ids son UUIDs de papers científicos que respaldan esta recomendación.
Solo incluye papers con alto nivel de evidencia.

...
"""
```

**Respuesta del agente** (ejemplo):

```json
{
  "recommendations": [
    {
      "type": "nutrition",
      "priority": "high",
      "title": "Adoptar dieta mediterránea",
      "description": "La dieta mediterránea ha demostrado reducir...",
      "rationale": "Tu perfil cardiovascular...",
      "action_steps": [
        "Incrementar consumo de aceite de oliva...",
        "Agregar pescado 2-3 veces por semana..."
      ],
      "references": [
        "550e8400-e29b-41d4-a716-446655440000",
        "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
      ]
    }
  ]
}
```

---

## 🚀 Uso en Producción

### 1. Setup Inicial

```bash
# 1. Crear bucket S3
aws s3 mb s3://aura360-clinical-papers --region us-east-1

# 2. Configurar CORS en S3
aws s3api put-bucket-cors \
  --bucket aura360-clinical-papers \
  --cors-configuration file://s3-cors.json

# s3-cors.json:
{
  "CORSRules": [{
    "AllowedOrigins": ["https://app.aura360.com"],
    "AllowedMethods": ["GET"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 3000
  }]
}

# 3. Crear migraciones Django
cd services/api
python manage.py makemigrations papers
python manage.py migrate

# 4. Cargar papers
export GOOGLE_API_KEY="..."
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
python scripts/batch_upload_papers.py "/path/to/pdfs/"
```

### 2. Variables de Entorno

```bash
# .env (producción)
GOOGLE_API_KEY=AIzaSyB7C1_j90uOEDwNh8uBBsqfB-kczZpdAUQ
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=wJalr...
AWS_S3_BUCKET_NAME=aura360-clinical-papers
AWS_S3_REGION=us-east-1
AWS_S3_PRESIGNED_URL_EXPIRATION=900  # 15 minutos
```

### 3. Monitoreo

- **CloudWatch**: Logs de S3 (accesos, errores)
- **PostgreSQL**: Query logs para papers más accedidos
- **Gemini**: Monitoring de uso de API (quotas)

---

## 📚 Ejemplos de Uso

### Frontend: Abrir paper desde recomendación

```typescript
// ai-recommendations-card.component.ts
openPaper(docId: string): void {
  this.papersService.openPaper(docId);
  // → GET /api/papers/{docId}/download/
  // → window.open(presigned_url)
}
```

### Backend: Generar presigned URL

```python
# papers/views.py - ya implementado
@action(detail=True, methods=['get'])
def download(self, request, doc_id=None):
    paper = self.get_object()
    presigned_url = s3_client.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': paper.s3_bucket,
            'Key': paper.s3_key,
        },
        ExpiresIn=900  # 15 min
    )
    return Response({'url': presigned_url, ...})
```

### Qdrant: Buscar papers de alta calidad

```python
from qdrant_client import QdrantClient, models

results = client.search(
    collection_name="papers_metadata",
    query_vector=query_embedding,
    query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="composite_score",
                range=models.Range(gte=8.0)  # Solo excelentes
            )
        ]
    ),
    limit=5
)

doc_ids = [r.payload["doc_id"] for r in results]
```

---

## 🎯 Próximos Pasos

1. ✅ Ejecutar batch upload con los 101 PDFs
2. ✅ Verificar calidad de análisis con muestras
3. 🔄 Ingestar papers seleccionados a Qdrant (opcional)
4. 🔄 Modificar agente para incluir referencias
5. 🔄 Probar flujo completo end-to-end
6. 🔄 Ajustar pesos de composite_score según feedback

---

## 💡 Notas Importantes

1. **Costos**:
   - Gemini: ~$0.001 por análisis (modelo flash)
   - S3: ~$0.023/GB/mes + requests
   - Qdrant Cloud: Según plan

2. **Performance**:
   - Análisis: ~5-10 segundos por paper
   - Upload S3: ~1-3 segundos
   - Presigned URL: <100ms
   - 101 papers: ~15-20 minutos total

3. **Límites**:
   - Gemini API: 15 RPM (requests per minute) en tier gratuito
   - S3 presigned URL: Max 7 días TTL (usamos 15 min)

4. **Backup**:
   - S3 tiene versionado habilitado
   - PostgreSQL backups diarios
   - Scripts idempotentes (no duplican)
