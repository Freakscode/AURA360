#!/bin/bash
# Script para reiniciar entornos virtuales con permisos correctos (SIN SUDO)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔄 Reiniciando entornos virtuales..."
echo ""
echo "⚠️  IMPORTANTE: Este script intentará mover (no eliminar) los .venv problemáticos"
echo "   Si falla, necesitarás ejecutar manualmente:"
echo "   sudo rm -rf services/{api,agents,vectordb}/.venv"
echo ""
read -p "¿Continuar? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelado"
    exit 1
fi

# Función para reiniciar un venv
reset_venv() {
    local service_path="$1"
    local service_name="$2"

    if [ -d "$service_path/.venv" ]; then
        echo "📁 $service_name..."

        # Intentar mover (más seguro que rm)
        if mv "$service_path/.venv" "$service_path/.venv.old.$(date +%s)" 2>/dev/null; then
            echo "  ✅ .venv movido a .venv.old.*"
        else
            echo "  ❌ No se pudo mover (necesitas sudo para eliminar)"
            echo "     Ejecuta: sudo rm -rf $service_path/.venv"
            return 1
        fi

        # Recrear con permisos correctos
        echo "  🔨 Recreando entorno virtual..."
        cd "$service_path"
        if UV_CACHE_DIR="$(pwd)/.uv-cache" uv sync 2>&1 | grep -q "Installed"; then
            echo "  ✅ Entorno recreado exitosamente"
        else
            echo "  ⚠️  Advertencia: La sincronización puede haber tenido problemas"
        fi
        cd "$SCRIPT_DIR"
    else
        echo "  ℹ️  $service_name: no tiene .venv"
    fi

    echo ""
}

# Procesar cada servicio
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
reset_venv "$SCRIPT_DIR/services/api" "Backend API"
reset_venv "$SCRIPT_DIR/services/agents" "Servicio de Agentes"
reset_venv "$SCRIPT_DIR/services/vectordb" "Servicio Vectorial"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Proceso completado!"
echo ""
echo "📝 Para prevenir este problema en el futuro:"
echo ""
echo "1. NUNCA ejecutes estos comandos:"
echo "   ❌ sudo uv sync"
echo "   ❌ sudo pip install"
echo "   ❌ sudo python -m pip ..."
echo ""
echo "2. Si un comando falla por permisos:"
echo "   ✅ Verifica que NO estés en un directorio protegido"
echo "   ✅ Usa: uv sync (sin sudo)"
echo "   ✅ Si el error persiste, ejecuta este script de nuevo"
echo ""
echo "3. Limpieza de .venv.old.* (opcional):"
echo "   sudo rm -rf services/*/.venv.old.*"
