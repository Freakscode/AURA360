# Confluent MCP Server - Setup Completado

**Fecha**: 2025-11-07
**Status**: ✅ Configuración básica completada

---

## ✅ Lo que se ha completado

### 1. Node.js 22 Verificado
- **Versión instalada**: v22.21.1
- **Ubicación**: Sistema global
- ✅ Compatible con @confluentinc/mcp-confluent

### 2. Archivo de Configuración Creado
- **Ubicación**: `~/.config/confluent-mcp/.env`
- **Permisos**: 600 (solo lectura para usuario)
- **Estado**: Template creado, necesita credenciales reales

### 3. Claude Desktop Config Actualizado
- **Archivo creado**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **MCP Server**: confluent configurado
- **Comando**: `npx -y @confluentinc/mcp-confluent`
- **Env file**: Apunta a `~/.config/confluent-mcp/.env`

---

## ⚠️ Pasos pendientes (REQUIERE ACCIÓN MANUAL)

### Paso 1: Obtener Credenciales de Confluent Cloud

Necesitas completar `CONFLUENT_CLOUD_SETUP.md` primero para obtener:

1. **Cloud API Keys** (para gestión de recursos)
2. **Kafka Cluster API Keys** (para producir/consumir)
3. **Bootstrap Servers URL**
4. **Organization ID**
5. **Environment ID**

### Paso 2: Actualizar ~/.config/confluent-mcp/.env

Editar el archivo y reemplazar los placeholders:

```bash
# Editar archivo
nano ~/.config/confluent-mcp/.env

# O con VS Code
code ~/.config/confluent-mcp/.env
```

Reemplazar:
- `your-cloud-api-key-here` → Tu Cloud API Key
- `your-cloud-api-secret-here` → Tu Cloud API Secret
- `pkc-xxxxx.us-east-1.aws.confluent.cloud:9092` → Tu Bootstrap Server real
- `your-kafka-api-key-here` → Tu Kafka API Key
- `your-kafka-api-secret-here` → Tu Kafka API Secret
- `your-org-id-here` → Tu Organization ID
- `env-xxxxx` → Tu Environment ID

### Paso 3: Reiniciar Claude Desktop

```bash
# Cerrar Claude Desktop completamente
# Abrir de nuevo

# O desde terminal (macOS):
killall Claude
open -a Claude
```

### Paso 4: Verificar Instalación

En Claude Desktop, escribir:

```
¿Qué herramientas de Confluent tienes disponibles?
```

**Respuesta esperada** (si todo está bien):
```
Tengo 24 herramientas disponibles para gestionar Confluent Cloud:

Kafka:
- list-topics: Listar todos los topics
- create-topic: Crear un nuevo topic
- describe-topic: Ver configuración detallada
[...]
```

**Si aparece error**:
- Verificar credenciales en `.env`
- Verificar que el path en `claude_desktop_config.json` sea correcto
- Ver sección de Troubleshooting en `MCP_CONFLUENT_SETUP.md`

---

## 🧪 Tests Recomendados Después de Setup

### Test 1: Listar Topics
```
Claude, muéstrame todos los topics en mi cluster
```

### Test 2: Crear Topic de Prueba
```
Claude, crea un topic llamado "test-mcp" con 1 partición y retention de 1 día
```

### Test 3: Ver Consumer Lag
```
Claude, ¿hay algún consumer lag en el topic aura360.user.events?
```

---

## 📁 Archivos Creados

```
~/.config/confluent-mcp/
└── .env                  # Configuración MCP (PENDIENTE: agregar credenciales)

~/Library/Application Support/Claude/
└── claude_desktop_config.json  # Config Claude Desktop (✅ completado)
```

---

## 🔐 Seguridad

### Permisos Configurados
```bash
# Verificar permisos
ls -la ~/.config/confluent-mcp/.env
# Debe mostrar: -rw------- (600)
```

### Recordatorios de Seguridad
- ❌ NUNCA commitear `.env` a Git
- ❌ NUNCA compartir screenshots con API keys visibles
- ❌ NUNCA copiar-pegar credenciales en chats públicos
- ✅ Usar 1Password/Bitwarden para backup de credenciales
- ✅ Regenerar keys si sospechas compromiso

---

## 🔄 Próximos Pasos

### Para Desarrollo Local (sin Confluent Cloud)

Si prefieres probar primero con Kafka local:

1. **Actualizar** `~/.config/confluent-mcp/.env` para usar local:
   ```bash
   KAFKA_BOOTSTRAP_SERVERS=localhost:9092
   KAFKA_API_KEY=
   KAFKA_API_SECRET=
   SCHEMA_REGISTRY_URL=http://localhost:8081
   ```

2. **Levantar Kafka local**:
   ```bash
   cd /Users/freakscode/Proyectos\ 2025/AURA360
   docker compose -f docker-compose.dev.yml up -d kafka zookeeper schema-registry
   ```

3. **Reiniciar Claude Desktop**

**Nota**: MCP con Kafka local tiene funcionalidad limitada (sin métricas de cloud, sin consumer lag avanzado).

### Para Producción (Confluent Cloud)

1. Completar `CONFLUENT_CLOUD_SETUP.md`
2. Obtener credenciales reales
3. Actualizar `~/.config/confluent-mcp/.env`
4. Reiniciar Claude Desktop
5. Verificar con tests

---

## ⚠️ Troubleshooting Común

### Error: "MCP server not found"

**Causa**: Node 22 no está disponible

**Solución**:
```bash
# Verificar Node
node --version

# Si no es v22:
nvm use 22
nvm alias default 22

# Reiniciar Claude Desktop
```

### Error: "Cannot read .env file"

**Causa**: Path incorrecto en `claude_desktop_config.json`

**Solución**:
```bash
# Verificar que el path sea ABSOLUTO
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Debe ser:
"/Users/freakscode/.config/confluent-mcp/.env"

# NO:
"~/.config/confluent-mcp/.env"  # ❌ No funciona con ~
```

### Error: "Authentication failed"

**Causa**: Credenciales incorrectas o expiradas

**Solución**:
1. Verificar credenciales en Confluent Cloud
2. Regenerar API keys si es necesario
3. Asegurarse de copiar el API Secret completo (sin espacios)
4. Verificar que usas Cluster API Key (no Cloud API Key) para KAFKA_API_KEY

---

## 📚 Documentación Relacionada

- **Setup Cloud**: `CONFLUENT_CLOUD_SETUP.md` - Cómo crear cluster y obtener credenciales
- **Guía MCP Original**: `MCP_CONFLUENT_SETUP.md` - Guía detallada paso a paso
- **Plan de Implementación**: `KAFKA_IMPLEMENTATION_PLAN.md` - Roadmap completo

---

## 🎯 Checklist de Estado

- [x] Node.js 22 verificado
- [x] Directorio `~/.config/confluent-mcp/` creado
- [x] Archivo `.env` creado (template)
- [x] Permisos 600 configurados en `.env`
- [x] `claude_desktop_config.json` creado
- [x] MCP server "confluent" configurado
- [ ] **PENDIENTE**: Obtener credenciales de Confluent Cloud
- [ ] **PENDIENTE**: Actualizar `.env` con credenciales reales
- [ ] **PENDIENTE**: Reiniciar Claude Desktop
- [ ] **PENDIENTE**: Verificar con test de listar topics

---

**Estado**: Configuración técnica completa, esperando credenciales de Confluent Cloud.

**Siguiente acción**: Completar `CONFLUENT_CLOUD_SETUP.md` para obtener credenciales.

---

**Creado**: 2025-11-07
**Última actualización**: 2025-11-07
