# Solución al Problema de Permisos con UV

## 🔍 ¿Qué causó el problema?

Los entornos virtuales (`.venv`) fueron creados con `sudo` o por un proceso con privilegios de root. Ahora `uv` no puede modificarlos porque los archivos son propiedad de `root:staff` en lugar de `freakscode:staff`.

## 🚀 Solución Rápida (Recomendada)

### Opción A: Eliminar y recrear manualmente (más control)

```bash
# 1. Eliminar los .venv problemáticos (REQUIERE SUDO - solo una vez)
sudo rm -rf services/api/.venv
sudo rm -rf services/agents/.venv
sudo rm -rf services/vectordb/.venv-old  # Si existe

# 2. Recrear sin sudo
cd services/api && UV_CACHE_DIR="$(pwd)/.uv-cache" uv sync && cd ../..
cd services/agents && UV_CACHE_DIR="$(pwd)/.uv-cache" uv sync && cd ../..
cd services/vectordb && UV_CACHE_DIR="$(pwd)/.uv-cache" uv sync && cd ../..
```

### Opción B: Usar el script automático

```bash
# Este script intenta mover (no eliminar) los .venv
chmod +x reset_venvs.sh
./reset_venvs.sh

# Si falla, usa la Opción A
```

## 🛡️ Prevención Futura

### 1. Regla de Oro: NUNCA uses `sudo` con `uv` o `pip`

❌ **MAL:**
```bash
sudo uv sync
sudo pip install paquete
sudo python -m pip install paquete
```

✅ **BIEN:**
```bash
uv sync
uv pip install paquete
python -m pip install --user paquete  # Si usas pip directamente
```

### 2. Configura tu shell para advertirte

Agrega esto a tu `~/.zshrc` o `~/.bashrc`:

```bash
# Prevenir uso accidental de sudo con uv/pip
alias sudo='_safer_sudo'
_safer_sudo() {
    if [[ "$1" == "uv" ]] || [[ "$1" == "pip" ]] || [[ "$2" == "pip" ]]; then
        echo "⛔ ERROR: No uses 'sudo' con uv/pip!"
        echo "   Ejecuta sin sudo: ${@:2}"
        return 1
    fi
    command sudo "$@"
}
```

Luego recarga tu shell: `source ~/.zshrc`

### 3. Usa variables de entorno consistentes

Agrega a tu `~/.zshrc` o `~/.bashrc`:

```bash
# Configuración de UV
export UV_CACHE_DIR="$HOME/.cache/uv"  # Cache global en tu home
export UV_NO_SYNC_WARNING=1            # Silenciar warnings innecesarios
```

### 4. Git: Ignora archivos temporales

Verifica que tu `.gitignore` tenga:

```gitignore
.venv/
.venv-*/
.venv.old.*/
.uv-cache/
__pycache__/
*.pyc
```

## 🔧 Solución para Servicio de Agentes (problema actual)

```bash
# El servicio de agentes tiene archivos de root, arreglémoslo:
cd services/agents

# Opción 1: Si tienes sudo disponible
sudo rm -rf .venv
UV_CACHE_DIR="$(pwd)/.uv-cache" uv sync

# Opción 2: Si NO puedes usar sudo
# El .venv quedará, pero uv creará uno nuevo si especificas otra ubicación
VIRTUAL_ENV=.venv-new UV_CACHE_DIR="$(pwd)/.uv-cache" uv sync
# Luego renombra manualmente cuando puedas eliminar .venv
```

## 📊 Verificar Permisos

Para ver quién es dueño de los archivos:

```bash
ls -la services/*/‌.venv/lib/python*/site-packages/ | head -5
```

Debe mostrar tu usuario (`freakscode`), no `root`.

## ❓ FAQ

**P: ¿Por qué pasó esto si nunca ejecuté `sudo uv sync`?**

R: Posibles causas:
- Ejecutaste un script que internamente usó sudo
- Un IDE/editor (PyCharm, VS Code) ejecutó pip con privilegios elevados
- Copiaste un .venv de otro proyecto que tenía permisos de root

**P: ¿Puedo simplemente hacer `chmod -R` sin sudo?**

R: No, `chmod` también requiere ser dueño del archivo o tener sudo.

**P: ¿Afecta esto a otros proyectos?**

R: No, es específico a estos directorios. Tus otros proyectos deberían estar bien.

**P: ¿Debo usar virtualenv en lugar de uv?**

R: No, `uv` es excelente. Solo necesitas asegurarte de no usar sudo con él.

## 🎯 Solución Definitiva (una sola vez con sudo)

Si tienes acceso a sudo y quieres arreglarlo de una vez:

```bash
#!/bin/bash
# fix_all_permissions.sh

cd "$(dirname "$0")"

echo "🔧 Arreglando todos los permisos..."

# Arreglar propiedad de .venv
for service in api agents vectordb; do
    if [ -d "services/$service/.venv" ]; then
        echo "  → services/$service/.venv"
        sudo chown -R $(whoami):staff "services/$service/.venv"
    fi
done

# Limpiar .venv antiguos
echo "🧹 Limpiando backups antiguos..."
find services -name ".venv.old.*" -type d -exec sudo rm -rf {} + 2>/dev/null || true

echo "✅ ¡Listo!"
```

Guarda como `fix_all_permissions.sh`, hazlo ejecutable y ejecútalo:

```bash
chmod +x fix_all_permissions.sh
./fix_all_permissions.sh
```

## 📚 Recursos

- [UV Documentation](https://github.com/astral-sh/uv)
- [Python Virtual Environments Best Practices](https://docs.python.org/3/library/venv.html)
- [Understanding Unix Permissions](https://www.redhat.com/sysadmin/linux-file-permissions-explained)
