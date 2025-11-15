#!/bin/bash
# Script para arreglar permisos de entornos virtuales que fueron creados con sudo

set -e

USER=$(whoami)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔧 Arreglando permisos de entornos virtuales..."
echo "Usuario actual: $USER"
echo ""

# Función para arreglar permisos de un servicio
fix_service_venv() {
    local service_path="$1"
    local service_name="$2"

    if [ -d "$service_path/.venv" ]; then
        echo "📁 Procesando $service_name..."
        if sudo chown -R "$USER:staff" "$service_path/.venv" 2>/dev/null; then
            echo "  ✅ Permisos actualizados"
        else
            echo "  ⚠️  No se pudo actualizar (es posible que ya tenga los permisos correctos)"
        fi
    else
        echo "  ℹ️  $service_name: no tiene .venv"
    fi
}

# Arreglar cada servicio
fix_service_venv "$SCRIPT_DIR/services/api" "Backend API"
fix_service_venv "$SCRIPT_DIR/services/agents" "Servicio de Agentes"
fix_service_venv "$SCRIPT_DIR/services/vectordb" "Servicio Vectorial"

echo ""
echo "✨ Proceso completado!"
echo ""
echo "📝 Prevención futura:"
echo "  • NUNCA uses 'sudo uv ...' o 'sudo pip ...'"
echo "  • Si necesitas reinstalar: rm -rf .venv && uv sync"
echo "  • Configura uv para validar permisos (ver abajo)"
