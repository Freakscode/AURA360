# Tests - vectosvc

Este directorio contiene los tests unitarios e de integración para el servicio de base de datos vectorial.

## Estructura

```
tests/
├── conftest.py              # Fixtures compartidos
├── unit/                    # Tests unitarios (rápidos, sin servicios externos)
│   ├── test_schemas.py      # Validación de Pydantic schemas
│   ├── test_pipeline.py     # Funciones de chunking, hashing, normalización
│   ├── test_qdrant_store.py # Operaciones de Qdrant store
│   └── test_parsers.py      # Parsers GROBID y PDF
└── integration/             # Tests de integración (requieren servicios)
    ├── test_ingestion_flow.py  # Flujo completo de ingesta
    └── test_search.py          # Búsqueda semántica end-to-end
```

## Ejecutar Tests

### Prerequisitos

1. **Servicios Docker corriendo**:
   ```bash
   docker compose up -d
   ```

2. **Dependencias instaladas**:
   ```bash
   pip install -e '.[dev]'
   ```

### Comandos

#### Todos los tests
```bash
pytest tests/ -v
```

#### Solo tests unitarios (rápidos, ~10s)
```bash
pytest tests/unit/ -v
```

#### Solo tests de integración (lentos, ~40s)
```bash
pytest tests/integration/ -v
```

#### Con cobertura
```bash
pytest tests/ --cov=vectosvc --cov-report=html
open htmlcov/index.html  # Ver reporte en navegador
```

#### Modo silencioso
```bash
pytest tests/ -q
```

#### Detener en primer fallo
```bash
pytest tests/ -x
```

## Fixtures Disponibles

### `test_qdrant_client` (session)
Cliente Qdrant compartido para todos los tests unitarios.

### `test_store` (function)
Store de Qdrant con colección temporal, se elimina después de cada test.

### `sample_pdf_bytes` (function)
PDF de prueba generado con PyMuPDF con 3 páginas (Abstract, Introduction, Conclusion).

### `sample_tei_xml` (function)
XML TEI de ejemplo simulando salida de GROBID.

### `sample_ingest_request` (function)
Diccionario con IngestRequest de prueba.

## Tests Importantes

### Unitarios

- **`test_split_text_*`**: Validan el chunking de texto con diferentes tamaños y overlaps
- **`test_hash_id_deterministic`**: Verifica idempotencia de hashes
- **`test_build_filter_*`**: Validanfiltros de Qdrant (must/should)
- **`test_parse_tei_*`**: Extracción de metadata de TEI XML

### Integración

- **`test_ingest_text_end_to_end`**: Flujo completo text → chunks → embeddings → Qdrant
- **`test_ingest_idempotent`**: Re-ingestar no duplica chunks
- **`test_search_basic`**: Búsqueda semántica funciona correctamente
- **`test_search_with_filters`**: Filtros por metadata funcionan

## Notas

- Los tests de integración usan la colección real `docs` definida en `.env`
- FastEmbed descarga modelos la primera vez (~2 minutos)
- Algunos tests pueden fallar si hay datos residuales en Qdrant (normal en desarrollo)

## CI/CD

Los tests se ejecutan automáticamente en GitHub Actions en cada push/PR.
Ver `.github/workflows/test.yml` para la configuración completa.
