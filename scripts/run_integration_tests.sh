#!/bin/bash

###############################################################################
# Script de Orquestación de Pruebas de Integración - AURA360
#
# Este script ejecuta las pruebas de integración en el orden correcto,
# verificando prerequisitos y generando reportes.
#
# Uso:
#   ./scripts/run_integration_tests.sh [opciones]
#
# Opciones:
#   --skip-setup          Omite la verificación de servicios
#   --only-vectorial      Solo ejecuta pruebas del servicio vectorial
#   --only-agents         Solo ejecuta pruebas del servicio de agentes
#   --only-backend        Solo ejecuta pruebas del backend
#   --only-e2e            Solo ejecuta pruebas end-to-end
#   --coverage            Genera reporte de cobertura
#   --verbose             Output verboso
#   --help                Muestra esta ayuda
#
###############################################################################

set -e  # Exit on error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables de configuración
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_DIR="${PROJECT_ROOT}/test-reports/${TIMESTAMP}"

# Flags
SKIP_SETUP=false
ONLY_VECTORIAL=false
ONLY_AGENTS=false
ONLY_BACKEND=false
ONLY_E2E=false
WITH_COVERAGE=false
VERBOSE=false

# Parse argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-setup)
            SKIP_SETUP=true
            shift
            ;;
        --only-vectorial)
            ONLY_VECTORIAL=true
            shift
            ;;
        --only-agents)
            ONLY_AGENTS=true
            shift
            ;;
        --only-backend)
            ONLY_BACKEND=true
            shift
            ;;
        --only-e2e)
            ONLY_E2E=true
            shift
            ;;
        --coverage)
            WITH_COVERAGE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            grep '^#' "$0" | grep -v '#!/bin/bash' | sed 's/^# //'
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Opción desconocida: $1${NC}"
            echo "Usa --help para ver las opciones disponibles."
            exit 1
            ;;
    esac
done

# Funciones auxiliares

print_header() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

check_service() {
    local url=$1
    local name=$2
    local max_attempts=3
    
    for i in $(seq 1 $max_attempts); do
        if curl -s --max-time 5 "$url" > /dev/null 2>&1; then
            print_success "$name está disponible en $url"
            return 0
        fi
        if [ $i -lt $max_attempts ]; then
            sleep 2
        fi
    done
    
    print_error "$name NO está disponible en $url"
    return 1
}

# Inicio del script
print_header "AURA360 - Suite de Pruebas de Integración"

print_info "Directorio del proyecto: $PROJECT_ROOT"
print_info "Directorio de reportes: $REPORT_DIR"

# Crear directorio de reportes
mkdir -p "$REPORT_DIR"

# Verificación de prerequisitos
if [ "$SKIP_SETUP" = false ]; then
    print_header "Verificando Prerequisitos"
    
    # Verificar que Python está instalado
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 no está instalado"
        exit 1
    fi
    print_success "Python 3 está instalado: $(python3 --version)"
    
    # Verificar que uv está instalado
    if ! command -v uv &> /dev/null; then
        print_warning "uv no está instalado (recomendado para gestión de dependencias)"
    else
        print_success "uv está instalado: $(uv --version)"
    fi
    
    # Verificar que pytest está instalado
    if ! command -v pytest &> /dev/null && ! python3 -m pytest --version &> /dev/null; then
        print_error "pytest no está instalado"
        exit 1
    fi
    print_success "pytest está instalado"
    
    # Verificar servicios
    print_header "Verificando Servicios"
    
    SERVICES_OK=true
    
    # Servicio Vectorial
    if ! check_service "http://localhost:8001/readyz" "Servicio Vectorial"; then
        print_warning "Para iniciar: cd vectorial_db && docker compose up -d"
        SERVICES_OK=false
    fi
    
    # Servicio de Agentes
    if ! check_service "http://localhost:8080/readyz" "Servicio de Agentes"; then
        print_warning "Para iniciar: cd agents-service && uv run uvicorn main:app --reload --port 8080"
        SERVICES_OK=false
    fi
    
    # Backend Django
    if ! check_service "http://localhost:8000/api/health" "Backend Django"; then
        print_warning "Para iniciar: cd backend && uv run python manage.py runserver"
        SERVICES_OK=false
    fi
    
    if [ "$SERVICES_OK" = false ]; then
        print_error "Algunos servicios no están disponibles"
        print_info "Ejecuta con --skip-setup para omitir esta verificación"
        exit 1
    fi
    
    print_success "Todos los servicios están disponibles"
fi

# Función para ejecutar pruebas
run_tests() {
    local test_path=$1
    local test_name=$2
    local working_dir=$3
    
    print_header "Ejecutando: $test_name"
    
    cd "$working_dir"
    
    local pytest_args="-v"
    [ "$VERBOSE" = true ] && pytest_args="$pytest_args -s"
    [ "$WITH_COVERAGE" = true ] && pytest_args="$pytest_args --cov --cov-report=html --cov-report=term"
    
    local report_file="${REPORT_DIR}/${test_name// /_}.xml"
    pytest_args="$pytest_args --junitxml=\"$report_file\""
    
    if eval "pytest $pytest_args \"$test_path\""; then
        print_success "$test_name: PASSED"
        return 0
    else
        print_error "$test_name: FAILED"
        return 1
    fi
}

# Ejecutar pruebas según flags
FAILED_TESTS=()

# Pruebas del Servicio Vectorial
if [ "$ONLY_VECTORIAL" = true ] || [ "$ONLY_AGENTS" = false ] && [ "$ONLY_BACKEND" = false ] && [ "$ONLY_E2E" = false ]; then
    if ! run_tests \
        "tests/integration/test_vectorial_service_integration.py" \
        "Servicio Vectorial" \
        "$PROJECT_ROOT/vectorial_db"; then
        FAILED_TESTS+=("Servicio Vectorial")
    fi
fi

# Pruebas del Servicio de Agentes
if [ "$ONLY_AGENTS" = true ] || [ "$ONLY_VECTORIAL" = false ] && [ "$ONLY_BACKEND" = false ] && [ "$ONLY_E2E" = false ]; then
    if ! run_tests \
        "tests/integration/test_agents_service_integration.py" \
        "Servicio de Agentes" \
        "$PROJECT_ROOT/agents-service"; then
        FAILED_TESTS+=("Servicio de Agentes")
    fi
fi

# Pruebas del Backend
if [ "$ONLY_BACKEND" = true ] || [ "$ONLY_VECTORIAL" = false ] && [ "$ONLY_AGENTS" = false ] && [ "$ONLY_E2E" = false ]; then
    if ! run_tests \
        "holistic/tests/test_backend_integration.py" \
        "Backend Django" \
        "$PROJECT_ROOT/backend"; then
        FAILED_TESTS+=("Backend Django")
    fi
fi

# Pruebas End-to-End
if [ "$ONLY_E2E" = true ] || [ "$ONLY_VECTORIAL" = false ] && [ "$ONLY_AGENTS" = false ] && [ "$ONLY_BACKEND" = false ]; then
    if ! run_tests \
        "tests/e2e/test_full_integration_flow.py" \
        "End-to-End" \
        "$PROJECT_ROOT"; then
        FAILED_TESTS+=("End-to-End")
    fi
fi

# Resumen final
print_header "Resumen de Pruebas"

if [ ${#FAILED_TESTS[@]} -eq 0 ]; then
    print_success "Todas las pruebas pasaron exitosamente ✓"
    echo ""
    print_info "Reportes guardados en: $REPORT_DIR"
    exit 0
else
    print_error "Las siguientes pruebas fallaron:"
    for test in "${FAILED_TESTS[@]}"; do
        echo "  - $test"
    done
    echo ""
    print_info "Reportes guardados en: $REPORT_DIR"
    exit 1
fi

