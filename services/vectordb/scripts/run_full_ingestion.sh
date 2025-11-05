#!/bin/bash
# Script para ejecutar el proceso completo de ingesta
# Uso: ./scripts/run_full_ingestion.sh

set -e  # Salir si hay error

echo "=================================="
echo "  AURA365 - Full Ingestion Flow"
echo "=================================="
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Paso 1: Iniciar servicios
echo -e "${YELLOW}[1/5] Iniciando servicios con Docker Compose...${NC}"
docker-compose up -d

# Paso 2: Esperar a que los servicios estén listos
echo -e "${YELLOW}[2/5] Esperando a que los servicios estén listos...${NC}"
sleep 10

# Verificar Qdrant
echo -n "  - Verificando Qdrant... "
if curl -s http://localhost:6333/collections > /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Error: Qdrant no está respondiendo"
    exit 1
fi

# Verificar Redis
echo -n "  - Verificando Redis... "
if docker exec vectorial_db-redis-1 redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Error: Redis no está respondiendo"
    exit 1
fi

# Verificar Grobid
echo -n "  - Verificando Grobid... "
if curl -s http://localhost:8070/api/version > /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Error: Grobid no está respondiendo"
    exit 1
fi

# Verificar API
echo -n "  - Verificando API... "
sleep 5  # Dar tiempo extra a la API
if curl -s http://localhost:8000/docs > /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Warning: API podría no estar completamente lista, continuando..."
fi

# Paso 3: Contar PDFs
echo -e "${YELLOW}[3/5] Contando PDFs en downloads/test_papers...${NC}"
PDF_COUNT=$(ls -1 downloads/test_papers/*.pdf 2>/dev/null | wc -l | tr -d ' ')
echo -e "  Encontrados: ${GREEN}${PDF_COUNT} PDFs${NC}"

if [ "$PDF_COUNT" -eq 0 ]; then
    echo -e "${RED}Error: No se encontraron PDFs para ingestar${NC}"
    exit 1
fi

# Paso 4: Ejecutar ingesta
echo -e "${YELLOW}[4/5] Iniciando ingesta de PDFs...${NC}"
python3 scripts/ingest_batch.py \
    --directory downloads/test_papers \
    --api-url http://localhost:8000 \
    --metadata '{"project":"sleep_obesity","source":"scihub","batch":"test_oct_2025","ingestion_date":"'$(date +%Y-%m-%d)'","category":"mente","locale":"es-CO","source_type":"paper","embedding_model":"'"${DEFAULT_EMBEDDING_MODEL:-text-embedding-3-small}"'","version":"'"${EMBEDDING_VERSION:-'$(date +%Y.%m.%d)'}"'"}'

# Paso 5: Resumen
echo ""
echo -e "${GREEN}=================================="
echo "  Ingesta Completada ✓"
echo "==================================${NC}"
echo ""
echo "Próximos pasos:"
echo "  1. Ver logs de procesamiento:"
echo "     docker-compose logs -f worker"
echo ""
echo "  2. Verificar colección en Qdrant:"
echo "     curl http://localhost:6333/collections/docs"
echo ""
echo "  3. Hacer búsquedas de prueba en la API"
echo ""
