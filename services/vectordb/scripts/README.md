# Scripts de Utilidad - AURA365 Vector DB

Esta carpeta contiene scripts de utilidad para facilitar la gestión e ingesta de documentos en el sistema de base de datos vectorial.

## Scripts Disponibles

### 📥 `download_scihub_batch.py`
**Descarga papers científicos por lotes desde Sci-Hub**

Descarga automáticamente papers usando DOIs, PubMed IDs o URLs, con soporte para múltiples mirrors y auto-ingesta al sistema vectorial.

```bash
# Uso básico
python scripts/download_scihub_batch.py --dois mis_dois.txt --output-dir papers

# Con auto-ingesta
python scripts/download_scihub_batch.py --dois mis_dois.txt --output-dir papers --auto-ingest

# Ver opciones
python scripts/download_scihub_batch.py --help
```

**Documentación completa**: Ver [SCIHUB_DOWNLOADER.md](../documentation/SCIHUB_DOWNLOADER.md)

---

### 📤 `ingest_batch.py`
**Ingesta masiva de PDFs al sistema vectorial**

Procesa múltiples PDFs desde directorio local o URLs y los envía al pipeline de procesamiento.

```bash
# Desde directorio local
python scripts/ingest_batch.py --directory /path/to/pdfs

# Desde lista de URLs
python scripts/ingest_batch.py --urls urls.txt

# Con API remota
python scripts/ingest_batch.py --directory /path/to/pdfs --api-url http://localhost:8000
```

---

### 🏷️ `backfill_topics.py`
**Asigna topics automáticamente a documentos existentes**

Ejecuta clasificación de topics en lote para documentos que no tienen asignación de topics.

```bash
python scripts/backfill_topics.py
```

---

### ☁️ `ingest_gcs_prefix.py`
**Ingesta desde Google Cloud Storage**

Procesa PDFs almacenados en un bucket de GCS por prefijo.

```bash
python scripts/ingest_gcs_prefix.py --bucket my-bucket --prefix research/papers/
```

---

## Workflows Comunes

### Workflow 1: Descargar e Ingestar Papers de Investigación

```bash
# 1. Crear archivo con DOIs
cat > research_papers.txt << EOF
10.1038/s41586-021-03819-2
10.1016/j.neuron.2020.01.012
EOF

# 2. Descargar e ingestar en un solo paso
python scripts/download_scihub_batch.py \
    --dois research_papers.txt \
    --output-dir downloads/research \
    --auto-ingest \
    --metadata '{"project":"neuroscience","priority":"high"}'
```

### Workflow 2: Descargar Primero, Ingestar Después

```bash
# 1. Descargar papers
python scripts/download_scihub_batch.py \
    --dois papers.txt \
    --output-dir downloads/papers

# 2. Revisar/organizar archivos manualmente

# 3. Ingestar cuando esté listo
python scripts/ingest_batch.py \
    --directory downloads/papers \
    --metadata '{"source":"scihub","reviewed":true}'
```

### Workflow 3: Ingesta desde URLs Públicas

```bash
# 1. Crear archivo con URLs
cat > public_urls.txt << EOF
https://arxiv.org/pdf/2301.12345.pdf
https://example.com/research/paper.pdf
EOF

# 2. Ingestar directamente
python scripts/ingest_batch.py --urls public_urls.txt
```

### Workflow 4: Procesamiento de GCS

```bash
# Procesar todos los PDFs en un prefijo de GCS
python scripts/ingest_gcs_prefix.py \
    --bucket research-papers-bucket \
    --prefix 2024/neuroscience/ \
    --metadata '{"year":2024,"field":"neuroscience"}'
```

---

## Consideraciones

### Requisitos
- Python 3.10+
- Dependencias instaladas: `httpx`, `loguru`, `qdrant-client`, etc.
- Servicios activos: API, Qdrant, Redis (para ingesta)

### Variables de Entorno
Ver archivo `.env` en la raíz del proyecto para configuración de:
- URLs de servicios (Qdrant, Redis, Grobid)
- Credenciales de GCS
- Configuración de embeddings

### Monitoreo
Todos los scripts usan `loguru` para logging detallado. Los niveles incluyen:
- `INFO`: Progreso general
- `SUCCESS`: Operaciones completadas
- `WARNING`: Problemas no críticos
- `ERROR`: Errores que requieren atención

---

## Contribuir

Para agregar nuevos scripts:

1. **Nomenclatura**: Usar snake_case, nombres descriptivos
2. **Docstring**: Incluir docstring completo con ejemplos de uso
3. **Argumentos**: Usar `argparse` con help text claro
4. **Logging**: Usar `loguru` con niveles apropiados
5. **Documentación**: Crear archivo MD en `/documentation` si es complejo
6. **Actualizar README**: Agregar entrada en este archivo

---

## Soporte

Para más información:
- Ver documentación completa en `/documentation`
- Revisar tests en `/tests`
- Consultar código fuente en `/vectosvc`

