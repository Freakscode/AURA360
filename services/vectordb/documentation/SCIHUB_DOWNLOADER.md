# Descargador de Papers desde Sci-Hub (Batch)

## Descripción General

El script `download_scihub_batch.py` permite descargar papers científicos por lotes desde Sci-Hub de manera automatizada y robusta. [[memory:9252075]]

## Características Principales

### 🔍 Identificadores Soportados
- **DOI** (Digital Object Identifier): `10.1038/nature12373`
- **PubMed ID**: `PMID:12345678`
- **URLs de DOI**: `https://doi.org/10.1016/j.cell.2020.04.001`

### 🌐 Múltiples Mirrors
El script intenta automáticamente varios mirrors de Sci-Hub si uno falla:
- `https://sci-hub.se`
- `https://sci-hub.st`
- `https://sci-hub.ru`
- `https://sci-hub.tw`
- `https://sci-hub.wf`

### 🛡️ Manejo Robusto de Errores
- **Reintentos automáticos** con exponential backoff
- **Detección de rate-limiting** con esperas inteligentes
- **Validación de PDFs** (verifica magic bytes `%PDF`)
- **Logs detallados** de éxitos y fallos

### 🔄 Integración con el Sistema
- **Auto-ingesta** opcional al sistema vectorial
- **Metadata personalizable** para cada documento
- **Compatible** con el pipeline de procesamiento existente

## Uso Básico

### 1. Preparar Lista de DOIs

Crea un archivo de texto con un DOI por línea:

```text
# archivo: mis_dois.txt
10.1038/nature12373
doi:10.1126/science.1259855
https://doi.org/10.1016/j.cell.2020.04.001
PMID:12345678
```

### 2. Descargar Papers

#### Descarga Simple
```bash
python scripts/download_scihub_batch.py \
    --dois mis_dois.txt \
    --output-dir downloads/papers
```

#### Descarga con Delay Personalizado
Para evitar ser bloqueado por rate-limiting:
```bash
python scripts/download_scihub_batch.py \
    --dois mis_dois.txt \
    --output-dir downloads/papers \
    --delay 3.0
```

#### Dry Run (sin descargar)
Para ver qué se descargaría sin ejecutar:
```bash
python scripts/download_scihub_batch.py \
    --dois mis_dois.txt \
    --output-dir downloads/papers \
    --dry-run
```

#### Saltar Archivos Existentes
```bash
python scripts/download_scihub_batch.py \
    --dois mis_dois.txt \
    --output-dir downloads/papers \
    --skip-existing
```

### 3. Descargar e Ingestar Automáticamente

Para descargar y automáticamente agregar los papers al sistema vectorial:

```bash
python scripts/download_scihub_batch.py \
    --dois mis_dois.txt \
    --output-dir downloads/papers \
    --auto-ingest \
    --metadata '{"source":"scihub","category":"research_papers"}'
```

### 4. Usar Mirror Específico

Si conoces un mirror que funciona bien:
```bash
python scripts/download_scihub_batch.py \
    --dois mis_dois.txt \
    --output-dir downloads/papers \
    --mirror https://sci-hub.se
```

## Opciones Completas

```
--dois PATH              Archivo con lista de DOIs/PMIDs (REQUERIDO)
--output-dir PATH        Directorio de salida (default: downloads/scihub_papers)
--mirror URL             Mirror específico de Sci-Hub a usar
--timeout SECONDS        Timeout por descarga (default: 30)
--delay SECONDS          Delay entre descargas (default: 2.0)
--auto-ingest            Ingestar automáticamente al sistema vectorial
--api-url URL            URL de la API para auto-ingest (default: http://localhost:8000)
--metadata JSON          Metadata común para todos los documentos
--dry-run                Solo listar sin descargar
--skip-existing          Saltar archivos que ya existen
```

## Funcionamiento Detallado

### 1. Normalización de Identificadores

El script normaliza automáticamente diferentes formatos:

```python
# Ejemplos de normalización:
"10.1038/nature12373"              → tipo: "doi", valor: "10.1038/nature12373"
"doi:10.1126/science.1259855"      → tipo: "doi", valor: "10.1126/science.1259855"
"https://doi.org/10.1016/..."      → tipo: "doi", valor: "10.1016/..."
"PMID:12345678"                    → tipo: "pmid", valor: "12345678"
"12345678" (solo números)          → tipo: "pmid", valor: "12345678"
```

### 2. Proceso de Descarga

Para cada identificador:

1. **Normalización**: Convierte el identificador al formato correcto
2. **Intento en Mirrors**: Prueba cada mirror secuencialmente
3. **Obtención de HTML**: Hace request a Sci-Hub
4. **Extracción de PDF URL**: Busca el link directo al PDF en el HTML usando múltiples patrones regex
5. **Descarga del PDF**: Descarga el archivo desde el link encontrado
6. **Validación**: Verifica que el archivo descargado es un PDF válido
7. **Guardado**: Almacena el PDF con nombre único basado en el identificador

### 3. Generación de Nombres de Archivo

Los archivos se nombran según el tipo de identificador:

- **DOI**: `doi_10.1038_nature12373.pdf` (caracteres especiales reemplazados)
- **PMID**: `pmid_12345678.pdf`
- **URL**: `paper_a1b2c3d4e5f6.pdf` (hash MD5 de la URL)

### 4. Manejo de Errores

El script maneja varios tipos de errores:

```python
# HTTP 404: Paper no encontrado → Pasa al siguiente mirror
# HTTP 429: Rate limit → Espera con exponential backoff
# Timeout: → Reintenta hasta max_retries
# Contenido no-PDF: → Rechaza y reintenta
# Error de red: → Reintenta con siguiente mirror
```

### 5. Logs y Reportes

El script genera:

- **Logs en tiempo real** con `loguru` (INFO, DEBUG, ERROR, SUCCESS)
- **Archivo de fallidos**: `failed_downloads.txt` con lista de DOIs que fallaron
- **Resumen final** con estadísticas:
  - Total de identificadores
  - Descargas exitosas
  - Descargas fallidas
  - Descargas saltadas (skip-existing)

## Integración con el Sistema Vectorial

### Auto-Ingesta

Cuando se usa `--auto-ingest`, el script:

1. **Descarga todos los papers** primero
2. **Importa** el módulo `ingest_batch.py`
3. **Envía cada PDF** al endpoint `/ingest` de la API
4. **Agrega metadata** automáticamente:
   ```json
   {
     "doi": "10.1038/nature12373",
     "source": "scihub",
     "category": "research_papers"  // si se especificó
   }
   ```
5. **Retorna job IDs** para monitorear el progreso

### Metadata Personalizable

Puedes agregar metadata adicional que será incluido en cada documento:

```bash
python scripts/download_scihub_batch.py \
    --dois dois.txt \
    --output-dir papers \
    --auto-ingest \
    --metadata '{
      "source": "scihub",
      "project": "alzheimer_research",
      "reviewed": false,
      "priority": "high"
    }'
```

Este metadata estará disponible durante las búsquedas vectoriales y puede usarse para filtrado.

## Ejemplos de Uso Completos

### Ejemplo 1: Proyecto de Investigación

Descargar papers para un proyecto específico y agregarlos al sistema:

```bash
# 1. Preparar lista de DOIs
cat > alzheimer_papers.txt << EOF
10.1038/s41586-021-03819-2
10.1016/j.neuron.2020.01.012
10.1126/science.abc1234
EOF

# 2. Descargar e ingestar
python scripts/download_scihub_batch.py \
    --dois alzheimer_papers.txt \
    --output-dir research/alzheimer \
    --auto-ingest \
    --api-url http://localhost:8000 \
    --metadata '{"project":"alzheimer","year":2021,"category":"neuroscience"}' \
    --delay 3.0
```

### Ejemplo 2: Recuperar Descargas Fallidas

Si algunas descargas fallaron, puedes reintentar solo esas:

```bash
# 1. Primera ejecución
python scripts/download_scihub_batch.py \
    --dois all_papers.txt \
    --output-dir papers

# 2. Revisar fallidos
cat papers/failed_downloads.txt

# 3. Reintentar solo los fallidos
python scripts/download_scihub_batch.py \
    --dois papers/failed_downloads.txt \
    --output-dir papers \
    --mirror https://sci-hub.st \
    --delay 5.0
```

### Ejemplo 3: Descarga Masiva con Pausa

Para descargas muy grandes, usar delays largos y skip-existing:

```bash
python scripts/download_scihub_batch.py \
    --dois large_list.txt \
    --output-dir papers \
    --skip-existing \
    --delay 5.0 \
    --timeout 60
```

## Consideraciones Importantes

### ⚠️ Aspectos Legales

- **Sci-Hub opera en área legal gris** en muchas jurisdicciones
- **Verifica las leyes locales** antes de usar
- **Respeta los derechos de autor** y usa solo para investigación personal/académica
- **No redistribuyas** papers descargados sin permiso

### 🚦 Rate Limiting

- **Usa delays apropiados** (2-5 segundos recomendado)
- **No ejecutes múltiples instancias** simultáneamente
- **Si eres bloqueado**, aumenta el delay o cambia de mirror

### 🔒 Privacidad

- **Usa VPN o Tor** si te preocupa la privacidad
- **Los mirrors pueden cambiar** sus URLs frecuentemente
- **Actualiza la lista de mirrors** periódicamente si es necesario

### 📊 Monitoreo

Para monitorear el progreso de ingesta después de usar `--auto-ingest`:

```bash
# Importar el módulo ingest_batch y usar su función de monitoreo
python -c "
from scripts.ingest_batch import monitor_jobs
monitor_jobs('http://localhost:8000', ['job_id_1', 'job_id_2'])
"
```

## Solución de Problemas

### Problema: "No PDF link found"

**Causa**: Sci-Hub cambió el formato de su HTML

**Solución**: 
1. Inspecciona manualmente la URL de Sci-Hub
2. Actualiza los `pdf_patterns` en la función `download_from_scihub()`
3. Abre un issue o actualiza el script

### Problema: HTTP 429 (Too Many Requests)

**Causa**: Rate limiting por descargar muy rápido

**Solución**:
```bash
# Aumentar delay
--delay 5.0

# O usar mirror diferente
--mirror https://sci-hub.ru
```

### Problema: Todos los mirrors fallan

**Causa**: Mirrors podrían estar caídos o bloqueados en tu región

**Solución**:
1. Busca mirrors actualizados en Reddit o Twitter
2. Usa VPN para cambiar de región
3. Actualiza la lista `DEFAULT_SCIHUB_MIRRORS`

### Problema: "Downloaded content is not a PDF"

**Causa**: Sci-Hub retornó página de error o CAPTCHA

**Solución**:
- Aumenta el delay
- Intenta con mirror diferente
- Verifica manualmente el DOI/PMID

## Actualización de Mirrors

Los mirrors de Sci-Hub cambian frecuentemente. Para actualizar:

1. **Busca mirrors activos** en:
   - https://sci-hub.now.sh/ (lista actualizada)
   - Reddit: r/scihub
   - Twitter: búsqueda "sci-hub mirror"

2. **Actualiza el script**:
```python
# En download_scihub_batch.py, línea ~43
DEFAULT_SCIHUB_MIRRORS = [
    "https://sci-hub.se",    # Actualiza estas URLs
    "https://sci-hub.st",
    # Agrega nuevos mirrors aquí
]
```

## Referencias

- **Sci-Hub**: https://sci-hub.se (sitio principal, puede cambiar)
- **Wikipedia**: https://en.wikipedia.org/wiki/Sci-Hub
- **Alternativas legales**:
  - PubMed Central (PMC)
  - arXiv
  - bioRxiv
  - ResearchGate (request from authors)

## Contribuciones

Para mejorar este script:

1. Agregar soporte para más fuentes (PMC, arXiv)
2. Mejorar detección de PDF links
3. Agregar soporte para metadata desde Crossref/PubMed API
4. Implementar caché de mirrors activos
5. Agregar GUI para usuarios no técnicos

