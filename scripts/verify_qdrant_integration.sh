#!/bin/bash

###############################################################################
# Script de Verificación de Integración con Qdrant Cloud
#
# Este script verifica que todos los servicios puedan conectarse correctamente
# a Qdrant Cloud.
#
# Uso:
#   ./scripts/verify_qdrant_integration.sh
#
# Requisitos:
#   - QDRANT_URL y QDRANT_API_KEY configurados en cada servicio
#   - Python 3.11+ con uv instalado
###############################################################################

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir encabezados
print_header() {
    echo ""
    echo -e "${BLUE}======================================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}======================================================================${NC}"
    echo ""
}

# Función para imprimir éxito
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Función para imprimir error
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Función para imprimir warning
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Función para imprimir info
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

###############################################################################
# 1. Verificar VectorDB Service
###############################################################################

print_header "Verificando VectorDB Service"

cd services/vectordb

if [ ! -f ".env" ]; then
    print_error ".env no encontrado en services/vectordb"
    print_info "Copia .env.example y configura QDRANT_URL y QDRANT_API_KEY"
    exit 1
fi

# Cargar variables de entorno
source .env

if [ -z "$QDRANT_URL" ]; then
    print_error "QDRANT_URL no está configurada en services/vectordb/.env"
    exit 1
fi

print_info "QDRANT_URL: $QDRANT_URL"

# Verificar conexión
print_info "Probando conexión desde VectorDB Service..."

PYTHONPATH=. uv run python -c "
import os
from qdrant_client import QdrantClient

url = os.getenv('QDRANT_URL')
api_key = os.getenv('QDRANT_API_KEY')

print(f'  Conectando a: {url}')

try:
    client = QdrantClient(url=url, api_key=api_key, timeout=10)
    collections = client.get_collections()
    print(f'  ✅ Conexión exitosa')
    print(f'  📦 Colecciones disponibles: {len(collections.collections)}')
    for col in collections.collections:
        info = client.get_collection(col.name)
        print(f'     • {col.name}: {info.points_count} vectores')
except Exception as e:
    print(f'  ❌ Error: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    print_success "VectorDB Service puede conectarse a Qdrant Cloud"
else
    print_error "VectorDB Service NO puede conectarse a Qdrant Cloud"
    exit 1
fi

cd ../..

###############################################################################
# 2. Verificar Agents Service
###############################################################################

print_header "Verificando Agents Service"

cd services/agents

if [ ! -f ".env" ]; then
    print_warning ".env no encontrado en services/agents"
    print_info "Si planeas usar agents, copia .env.example y configura las variables"
    cd ../..
else
    # Cargar variables de entorno
    source .env

    if [ -z "$AGENT_SERVICE_QDRANT_URL" ]; then
        print_warning "AGENT_SERVICE_QDRANT_URL no está configurada"
        print_info "Configura AGENT_SERVICE_QDRANT_URL en services/agents/.env"
        cd ../..
    else
        print_info "AGENT_SERVICE_QDRANT_URL: $AGENT_SERVICE_QDRANT_URL"

        # Verificar conexión
        print_info "Probando conexión desde Agents Service..."

        PYTHONPATH=. uv run python -c "
import os
from qdrant_client import QdrantClient

url = os.getenv('AGENT_SERVICE_QDRANT_URL')
api_key = os.getenv('AGENT_SERVICE_QDRANT_API_KEY')

print(f'  Conectando a: {url}')

try:
    client = QdrantClient(url=url, api_key=api_key, timeout=10)
    collections = client.get_collections()
    print(f'  ✅ Conexión exitosa')
    print(f'  📦 Colecciones disponibles: {len(collections.collections)}')
    for col in collections.collections:
        info = client.get_collection(col.name)
        print(f'     • {col.name}: {info.points_count} vectores')
except Exception as e:
    print(f'  ❌ Error: {e}')
    exit(1)
"

        if [ $? -eq 0 ]; then
            print_success "Agents Service puede conectarse a Qdrant Cloud"
        else
            print_error "Agents Service NO puede conectarse a Qdrant Cloud"
            exit 1
        fi

        cd ../..
    fi
fi

###############################################################################
# 3. Verificar Colecciones Requeridas
###############################################################################

print_header "Verificando Colecciones Requeridas"

cd services/vectordb
source .env

REQUIRED_COLLECTIONS=("holistic_memory" "user_context")

for collection in "${REQUIRED_COLLECTIONS[@]}"; do
    print_info "Verificando colección: $collection"

    PYTHONPATH=. uv run python -c "
import os
import sys
from qdrant_client import QdrantClient

url = os.getenv('QDRANT_URL')
api_key = os.getenv('QDRANT_API_KEY')
collection_name = '$collection'

try:
    client = QdrantClient(url=url, api_key=api_key, timeout=10)
    info = client.get_collection(collection_name)
    print(f'  ✅ Colección \"{collection_name}\" existe')
    print(f'     Vectores: {info.points_count}')
    print(f'     Dimensión: {info.config.params.vectors.size}')
    print(f'     Distancia: {info.config.params.vectors.distance}')
except Exception as e:
    print(f'  ❌ Colección \"{collection_name}\" NO existe')
    print(f'     Error: {e}')
    print(f'     Ejecuta: python scripts/init_qdrant_collections.py')
    sys.exit(1)
"

    if [ $? -ne 0 ]; then
        print_error "Falta la colección: $collection"
        print_info "Ejecuta: cd services/vectordb && python scripts/init_qdrant_collections.py"
        exit 1
    fi
done

cd ../..

###############################################################################
# Resumen Final
###############################################################################

print_header "✅ Verificación Completada"

print_success "Todos los servicios pueden conectarse a Qdrant Cloud"
print_success "Todas las colecciones requeridas están disponibles"

echo ""
print_info "Próximos pasos:"
echo "  1. Asegúrate de que QDRANT_API_KEY esté en Google Secret Manager para producción"
echo "  2. Actualiza las configuraciones de Helm/K8s con las URLs de Qdrant Cloud"
echo "  3. Prueba la integración end-to-end con: ./scripts/run_user_context_e2e.sh"
echo ""
