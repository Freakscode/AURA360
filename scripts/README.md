# Scripts de AURA360

Este directorio contiene scripts de utilidad para el proyecto AURA360.

## 📄 Scripts Disponibles

### `run_integration_tests.sh`

Script principal para ejecutar las pruebas de integración del ecosistema completo.

**Uso**:

```bash
# Ejecutar todas las pruebas
./scripts/run_integration_tests.sh

# Solo servicio vectorial
./scripts/run_integration_tests.sh --only-vectorial

# Solo servicio de agentes
./scripts/run_integration_tests.sh --only-agents

# Solo backend
./scripts/run_integration_tests.sh --only-backend

# Solo end-to-end
./scripts/run_integration_tests.sh --only-e2e

# Con cobertura
./scripts/run_integration_tests.sh --coverage

# Verbose
./scripts/run_integration_tests.sh --verbose

# Omitir verificación de servicios
./scripts/run_integration_tests.sh --skip-setup

# Ver ayuda
./scripts/run_integration_tests.sh --help
```

**Prerequisitos**:

- Todos los servicios deben estar corriendo:
  - Servicio Vectorial (puerto 8001)
  - Servicio de Agentes (puerto 8080)
  - Backend Django (puerto 8000)
- Variables de entorno configuradas correctamente
- Python 3.11+ y pytest instalados

**Output**:

Los reportes de pruebas se guardan en `test-reports/TIMESTAMP/`:

```
test-reports/
└── 20251027_143022/
    ├── Servicio_Vectorial.xml
    ├── Servicio_de_Agentes.xml
    ├── Backend_Django.xml
    └── End-to-End.xml
```

---

## 📚 Documentación Adicional

- [Guía Completa de Pruebas de Integración](../docs/INTEGRATION_TESTING.md)
- [Documentación del Backend](../backend/docs/)
- [Documentación del Servicio de Agentes](../agents-service/README.md)
- [Documentación del Servicio Vectorial](../vectorial_db/documentation/INDEX.md)

---

## 🔧 Desarrollo

### Agregar Nuevos Scripts

1. Crear el script en este directorio
2. Darle permisos de ejecución: `chmod +x scripts/nuevo_script.sh`
3. Documentarlo en este README
4. Seguir las convenciones del proyecto

### Convenciones

- Usar `#!/bin/bash` como shebang
- Incluir comentarios descriptivos
- Usar `set -e` para salir en errores
- Validar prerequisitos antes de ejecutar
- Proporcionar mensajes de error claros
- Usar colores para output (ver `run_integration_tests.sh` como ejemplo)

---

**Última actualización**: Octubre 2025

