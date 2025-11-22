# Confluent MCP Server - Setup para AURA360

**Propósito**: Gestionar Confluent Cloud desde Claude Desktop usando lenguaje natural.

---

## 📋 Pre-requisitos

- ✅ Confluent Cloud activado (ya tienes esto)
- ✅ Claude Desktop instalado (https://claude.ai/download)
- ✅ Node.js 22+ instalado

---

## 🚀 Setup Paso a Paso

### 1. Instalar Node.js 22

```bash
# Instalar NVM si no lo tienes
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Instalar Node 22
nvm install 22
nvm use 22

# Verificar
node --version  # Debería mostrar v22.x.x
```

---

### 2. Crear archivo de configuración

Crear `~/.config/confluent-mcp/.env`:

```bash
# Crear directorio
mkdir -p ~/.config/confluent-mcp

# Crear archivo .env
cat > ~/.config/confluent-mcp/.env <<'EOF'
# ============================================================================
# AURA360 - Confluent Cloud Configuration for MCP
# ============================================================================

# Confluent Cloud API Keys (obtener en: https://confluent.cloud/settings/api-keys)
CONFLUENT_CLOUD_API_KEY=your-cloud-api-key
CONFLUENT_CLOUD_API_SECRET=your-cloud-api-secret

# Kafka Cluster (obtener en: Confluent Cloud → Environment → Cluster → Settings)
KAFKA_BOOTSTRAP_SERVERS=pkc-xxxxx.us-east-1.aws.confluent.cloud:9092
KAFKA_API_KEY=your-kafka-api-key
KAFKA_API_SECRET=your-kafka-api-secret

# Schema Registry (opcional)
SCHEMA_REGISTRY_URL=https://psrc-xxxxx.us-east-1.aws.confluent.cloud
SCHEMA_REGISTRY_API_KEY=your-sr-api-key
SCHEMA_REGISTRY_API_SECRET=your-sr-api-secret

# Flink (opcional, si usas Flink SQL)
FLINK_REST_ENDPOINT=https://flink.us-east-1.aws.confluent.cloud
FLINK_API_KEY=your-flink-api-key
FLINK_API_SECRET=your-flink-api-secret

# Organization ID (obtener en: Confluent Cloud → Settings → Organization)
CONFLUENT_ORGANIZATION_ID=your-org-id

# Environment ID (obtener en: Confluent Cloud → Environments)
CONFLUENT_ENVIRONMENT_ID=env-xxxxx
EOF
```

**⚠️ IMPORTANTE**: Actualizar los valores con tus credenciales reales.

---

### 3. Obtener Credenciales de Confluent Cloud

#### 3.1 API Keys (Cloud-level)

1. Ir a https://confluent.cloud
2. Click en tu perfil (arriba derecha) → **API Keys**
3. Click **+ Add key** → **Cloud resource management**
4. Scope: Organization
5. Description: "MCP Server for AURA360"
6. Copiar **API Key** y **API Secret**
7. Pegar en `.env`:
   ```
   CONFLUENT_CLOUD_API_KEY=<tu-api-key>
   CONFLUENT_CLOUD_API_SECRET=<tu-api-secret>
   ```

#### 3.2 Kafka Cluster Keys

1. Ir a tu cluster: **aura360-kafka-prod**
2. Click **API Keys** tab
3. Click **+ Add key**
4. Scope: Cluster-specific
5. Description: "MCP Server Kafka Access"
6. Copiar keys y pegar en `.env`:
   ```
   KAFKA_API_KEY=<tu-kafka-key>
   KAFKA_API_SECRET=<tu-kafka-secret>
   ```

#### 3.3 Bootstrap Servers

1. En tu cluster → **Cluster settings**
2. Copiar **Bootstrap server**:
   ```
   KAFKA_BOOTSTRAP_SERVERS=pkc-xxxxx.us-east-1.aws.confluent.cloud:9092
   ```

#### 3.4 Schema Registry (si aplica)

1. Ir a **Schema Registry** tab
2. Click **API Keys** → **+ Add key**
3. Copiar keys y URL

#### 3.5 Organization & Environment IDs

```bash
# Organization ID: En Settings → Organization → copiar el ID
CONFLUENT_ORGANIZATION_ID=abc123-def456-...

# Environment ID: En Environments → click en tu env → copiar el ID de la URL
CONFLUENT_ENVIRONMENT_ID=env-xxxxx
```

---

### 4. Configurar Claude Desktop

#### 4.1 Ubicar archivo de configuración

```bash
# macOS
CLAUDE_CONFIG=~/Library/Application\ Support/Claude/claude_desktop_config.json

# Linux
CLAUDE_CONFIG=~/.config/Claude/claude_desktop_config.json

# Windows
CLAUDE_CONFIG=%APPDATA%\Claude\claude_desktop_config.json
```

#### 4.2 Editar configuración

```bash
# macOS/Linux
code "$CLAUDE_CONFIG"

# O abrir con cualquier editor
open -a TextEdit "$CLAUDE_CONFIG"
```

#### 4.3 Agregar servidor MCP

Agregar esta sección a `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "confluent": {
      "command": "npx",
      "args": [
        "-y",
        "@confluentinc/mcp-confluent",
        "--env-file",
        "/Users/YOUR_USERNAME/.config/confluent-mcp/.env"
      ]
    }
  }
}
```

**⚠️ Reemplazar** `/Users/YOUR_USERNAME/` con tu home directory real:

```bash
# Ver tu home directory
echo ~

# Ejemplo de configuración completa:
{
  "mcpServers": {
    "confluent": {
      "command": "npx",
      "args": [
        "-y",
        "@confluentinc/mcp-confluent",
        "--env-file",
        "/Users/freakscode/.config/confluent-mcp/.env"
      ]
    }
  }
}
```

---

### 5. Reiniciar Claude Desktop

```bash
# Cerrar Claude Desktop completamente
# Abrir de nuevo
```

---

### 6. Verificar Instalación

En Claude Desktop, escribir:

```
¿Qué herramientas de Confluent tienes disponibles?
```

**Respuesta esperada**:
```
Tengo 24 herramientas disponibles para gestionar Confluent Cloud:

Kafka:
- list-topics: Listar todos los topics
- create-topic: Crear un nuevo topic
- describe-topic: Ver configuración detallada de un topic
- delete-topic: Eliminar un topic
- list-consumer-groups: Ver grupos de consumers
- describe-consumer-group: Ver detalles y lag de un consumer group

Schema Registry:
- list-schemas: Listar schemas registrados
- get-schema: Obtener un schema específico
[...]
```

---

## 🧪 Pruebas Básicas

### Test 1: Listar Topics

```
Claude, muéstrame todos los topics en mi cluster aura360-kafka-prod
```

**Esperado**:
```
Estos son los topics en tu cluster:

1. aura360.user.events
   - Partitions: 3
   - Replication factor: 3
   - Retention: 7 days

2. aura360.context.aggregated
   - Partitions: 3
   - Replication factor: 3
   - Retention: 7 days

[... resto de topics ...]
```

---

### Test 2: Ver Consumer Lag

```
Claude, ¿cuál es el consumer lag del grupo "vectordb-context-aggregator"?
```

**Esperado**:
```
Consumer Group: vectordb-context-aggregator

Topic: aura360.user.events
- Partition 0: 12 mensajes de lag
- Partition 1: 5 mensajes de lag
- Partition 2: 0 mensajes de lag

Total lag: 17 mensajes
Lag aproximado en tiempo: ~0.5 segundos
```

---

### Test 3: Crear Topic de Prueba

```
Claude, crea un topic llamado "test-mcp" con 1 partición y retention de 1 día
```

**Esperado**:
```
✅ Topic creado exitosamente:

Name: test-mcp
Partitions: 1
Replication factor: 3 (default)
Retention: 1 day (86400000 ms)

¿Quieres que verifique que el topic está disponible?
```

---

### Test 4: Debugging

```
Claude, ayúdame a debuggear por qué mi consumer "vectordb-vectorization"
no está procesando mensajes del topic aura360.context.aggregated
```

**Esperado** (Claude ejecuta varios tools automáticamente):
```
Voy a investigar. Déjame revisar...

1. ✅ Topic aura360.context.aggregated existe
   - 3 particiones
   - 156 mensajes en total

2. ✅ Consumer group "vectordb-vectorization" está registrado
   - Estado: STABLE
   - 1 miembro activo

3. ⚠️  Consumer lag:
   - Partition 0: 52 mensajes (aumentando)
   - Partition 1: 51 mensajes (aumentando)
   - Partition 2: 53 mensajes (aumentando)

4. ❌ Problema identificado:
   - Consumer está leyendo pero NO committeando offsets
   - Offsets se quedaron estancados hace 5 minutos

Posibles causas:
1. enable.auto.commit está en false y no estás haciendo commit manual
2. Consumer crasheó pero Kafka aún lo ve como "activo"
3. Procesamiento muy lento y max.poll.interval.ms expiró

¿Quieres que revise los logs del consumer o la configuración?
```

---

## 🎯 Casos de Uso Comunes

### Monitoreo Diario

```
Claude, dame un health check de mi infraestructura Kafka
```

### Crear Recursos

```
Claude, crea un topic para notificaciones push con:
- 3 particiones
- Retention de 3 días
- Compresión snappy
```

### Troubleshooting

```
Claude, mi aplicación reporta errores de timeout.
¿Puedes revisar si hay problemas en los consumers?
```

### Analytics

```
Claude, muéstrame qué topics tienen más throughput en las últimas 24 horas
```

---

## ⚠️ Troubleshooting

### Error: "MCP server not found"

```bash
# Verificar que Node 22 esté activo
node --version

# Si no es v22:
nvm use 22

# Reiniciar Claude Desktop
```

### Error: "Authentication failed"

```bash
# Verificar credenciales en .env
cat ~/.config/confluent-mcp/.env

# Regenerar API keys en Confluent Cloud si es necesario
```

### Error: "Cannot read .env file"

```bash
# Verificar path en claude_desktop_config.json
# Debe ser ruta ABSOLUTA, no relativa

# ❌ Mal:
"--env-file", "~/.config/confluent-mcp/.env"

# ✅ Bien:
"--env-file", "/Users/freakscode/.config/confluent-mcp/.env"
```

---

## 🔒 Seguridad

### Permisos de API Keys

- ✅ Cloud API Key: Solo permisos de lectura si es posible
- ✅ Kafka API Key: Read + Write (necesario para debugging)
- ✅ Archivo `.env`: Permisos 600 (solo tu usuario)

```bash
# Asegurar permisos
chmod 600 ~/.config/confluent-mcp/.env
```

### NO compartir

- ❌ NO commitear `.env` a Git
- ❌ NO compartir screenshots con API keys visibles
- ❌ NO copiar-pegar el `.env` en Claude conversations (Claude no lo verá de todas formas, pero por seguridad)

---

## 📚 Recursos

- **GitHub**: https://github.com/confluentinc/mcp-confluent
- **Confluent Docs**: https://docs.confluent.io/cloud/current/
- **Model Context Protocol**: https://modelcontextprotocol.io/

---

## ✅ Checklist de Verificación

- [ ] Node.js 22 instalado
- [ ] Archivo `.env` creado con credenciales reales
- [ ] `claude_desktop_config.json` actualizado
- [ ] Claude Desktop reiniciado
- [ ] Test 1 (listar topics) funciona
- [ ] Test 2 (ver consumer lag) funciona
- [ ] Permisos de `.env` configurados (600)

---

**🎉 ¡Listo! Ahora puedes gestionar Confluent Cloud conversando con Claude.**

**Próximo paso**: Ver ejemplos avanzados en CLAUDE.md o empezar a usar en tu workflow diario.
