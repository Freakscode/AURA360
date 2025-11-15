#!/bin/bash
# Script definitivo para arreglar permisos (REQUIERE SUDO - solo una vez)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER=$(whoami)

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🔧 Arreglo Definitivo de Permisos UV"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Este script requiere sudo para:"
echo "  1. Cambiar la propiedad de archivos de 'root' a '$USER'"
echo "  2. Limpiar entornos virtuales antiguos"
echo ""
echo "⚠️  Se te pedirá tu contraseña de sudo."
echo ""
read -p "¿Continuar? (y/n) " -n 1 -r
echo ""
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelado"
    exit 1
fi

cd "$SCRIPT_DIR"

# Verificar que tenemos sudo
if ! sudo -v; then
    echo "❌ No se pudo obtener permisos sudo"
    exit 1
fi

echo "🔍 Analizando servicios..."
echo ""

# Función para arreglar un servicio
fix_service() {
    local service_path="$1"
    local service_name="$2"

    echo "📁 $service_name ($service_path)"

    if [ -d "$service_path/.venv" ]; then
        # Verificar si hay archivos de root
        local root_files=$(sudo find "$service_path/.venv" -user root 2>/dev/null | wc -l | tr -d ' ')

        if [ "$root_files" -gt 0 ]; then
            echo "  ⚠️  Encontrados $root_files archivos de root"
            echo "  🔄 Cambiando propiedad a $USER:staff..."

            if sudo chown -R "$USER:staff" "$service_path/.venv"; then
                echo "  ✅ Permisos actualizados"
            else
                echo "  ❌ Error al actualizar permisos"
                return 1
            fi
        else
            echo "  ✅ Ya tiene permisos correctos"
        fi
    else
        echo "  ℹ️  No tiene .venv (se creará en próximo 'uv sync')"
    fi

    # Limpiar .venv antiguos
    local old_venvs=$(find "$service_path" -maxdepth 1 -name ".venv-old*" -o -name ".venv.old*" 2>/dev/null)
    if [ ! -z "$old_venvs" ]; then
        echo "  🧹 Limpiando backups antiguos..."
        echo "$old_venvs" | while read -r old_venv; do
            if [ -d "$old_venv" ]; then
                sudo rm -rf "$old_venv"
                echo "     Eliminado: $(basename "$old_venv")"
            fi
        done
    fi

    echo ""
}

# Procesar servicios
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

fix_service "services/api" "Backend API (Django)"
fix_service "services/agents" "Servicio de Agentes"
fix_service "services/vectordb" "Servicio Vectorial"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✨ ¡Permisos arreglados exitosamente!"
echo ""
echo "📝 Próximos pasos:"
echo ""
echo "1. Verificar que funciona:"
echo "   cd services/agents"
echo "   UV_CACHE_DIR=\"\$(pwd)/.uv-cache\" uv sync"
echo ""
echo "2. Ejecutar tests:"
echo "   UV_CACHE_DIR=\"\$(pwd)/.uv-cache\" uv run pytest"
echo ""
echo "3. Para prevenir este problema:"
echo "   • Lee UV_PERMISSIONS_FIX.md"
echo "   • NUNCA uses 'sudo uv' o 'sudo pip'"
echo "   • Configura los aliases de prevención"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
