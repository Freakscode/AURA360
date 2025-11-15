#!/bin/bash
# Test para verificar que los permisos están arreglados

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Verificación de Permisos - AURA360"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

USER=$(whoami)
ERRORS=0

check_service() {
    local service=$1
    local name=$2
    
    echo "📦 $name"
    
    if [ ! -d "services/$service/.venv" ]; then
        echo "  ⚠️  No tiene .venv"
        return
    fi
    
    # Buscar archivos de root
    local root_count=$(find "services/$service/.venv" -user root 2>/dev/null | wc -l | tr -d ' ')
    
    if [ "$root_count" -gt 0 ]; then
        echo "  ❌ PROBLEMA: $root_count archivos de root encontrados"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
    
    # Intentar uv sync
    cd "services/$service"
    if uv sync > /dev/null 2>&1; then
        echo "  ✅ uv sync funciona correctamente"
    else
        echo "  ❌ PROBLEMA: uv sync falló"
        ERRORS=$((ERRORS + 1))
        cd ../..
        return 1
    fi
    cd ../..
    
    echo ""
}

check_service "api" "Backend API (Django)"
check_service "agents" "Servicio de Agentes"
check_service "vectordb" "Servicio Vectorial"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo "✨ ¡Todos los permisos están correctos!"
    echo ""
    echo "🎉 Ya no hay problemas de permisos con UV"
    exit 0
else
    echo "⚠️  Se encontraron $ERRORS problema(s)"
    echo ""
    echo "Ejecuta: ./fix_all_permissions.sh"
    exit 1
fi
