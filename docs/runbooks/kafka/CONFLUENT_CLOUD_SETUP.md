# Confluent Cloud Setup - AURA360

**Propósito**: Guía paso a paso para configurar Confluent Cloud para AURA360 con el beneficio de 1 año gratis.

**Tiempo estimado**: 30-45 minutos

---

## 📋 Pre-requisitos

- ✅ Tarjeta de crédito (no se cobrará durante el año gratis)
- ✅ Email corporativo o personal
- ✅ Código de beneficio del perk (si aplica)

---

## 🚀 Parte 1: Crear Cuenta en Confluent Cloud

### 1.1 Registro Inicial

1. Ir a https://confluent.cloud
2. Click en **Start Free**
3. Llenar el formulario:
   - **Email**: Tu email corporativo/personal
   - **Password**: Contraseña segura
   - **First Name / Last Name**
   - **Company**: AURA360 (o tu empresa)
4. Click **Create Account**
5. **Verificar email**: Revisar inbox y click en el link de verificación

### 1.2 Activar Beneficio de 1 Año Gratis

**Opción A: Si tienes código de perk**
1. Login en Confluent Cloud
2. Click en tu perfil (arriba derecha) → **Billing**
3. Click **Apply Promo Code**
4. Ingresar código del perk
5. Click **Apply**
6. ✅ Deberías ver: "$13,200 promo credit applied (expires in 365 days)"

**Opción B: Si usas free trial estándar**
1. Al crear la cuenta, automáticamente tienes $400 en créditos
2. Suficiente para desarrollo, pero considera el perk para producción

---

## 🏗️ Parte 2: Crear Cluster de Kafka

### 2.1 Crear Environment

1. En el dashboard principal, click **Environments**
2. Click **+ Add cloud environment**
3. Configuración:
   - **Environment name**: `aura360-prod`
   - **Cloud provider**: AWS (recomendado para AURA360)
   - **Region**: us-east-1 (para baja latencia)
4. Click **Create**

### 2.2 Crear Kafka Cluster

1. Dentro del environment `aura360-prod`, click **+ Add cluster**
2. Seleccionar **Basic** cluster:
   - ✅ Más barato (~$150/mes sin créditos)
   - ✅ Suficiente para 99% de casos de uso
   - ✅ Incluye: durabilidad, auto-scaling, monitoring
3. Configuración:
   - **Cluster name**: `aura360-kafka-prod`
   - **Cloud provider**: AWS
   - **Region**: us-east-1 (Virginia)
   - **Availability**: Single Zone (Basic tier)
4. Click **Launch cluster**
5. ⏳ Esperar 5-10 minutos mientras se aprovisiona

---

## 📂 Parte 3: Crear Topics

### 3.1 Topics para AURA360

Una vez que el cluster esté **Ready**, crear los siguientes 6 topics:

#### Topic 1: `aura360.user.events`

1. En el cluster, click **Topics** → **+ Add topic**
2. Configuración:
   - **Topic name**: `aura360.user.events`
   - **Partitions**: 3
   - **Retention time**: 7 days (604800000 ms)
   - **Cleanup policy**: delete
   - **Compression type**: snappy (recomendado)
3. Click **Create**

**Repetir para los otros 5 topics**:

#### Topic 2: `aura360.context.aggregated`
- **Partitions**: 3
- **Retention**: 7 days
- **Compression**: snappy

#### Topic 3: `aura360.context.vectorized`
- **Partitions**: 3
- **Retention**: 7 days
- **Compression**: snappy

#### Topic 4: `aura360.guardian.requests`
- **Partitions**: 3
- **Retention**: 7 days
- **Compression**: snappy

#### Topic 5: `aura360.guardian.responses`
- **Partitions**: 3
- **Retention**: 7 days
- **Compression**: snappy

#### Topic 6: `aura360.vectordb.ingest`
- **Partitions**: 3
- **Retention**: 7 days
- **Compression**: snappy

### 3.2 Verificar Topics

1. En **Topics** tab, deberías ver los 6 topics
2. Click en cada uno para verificar configuración:
   - ✅ Partitions: 3
   - ✅ Replication factor: 3 (automático en Basic tier)
   - ✅ Retention: 604800000 ms (7 días)

---

## 🔑 Parte 4: Generar API Keys

### 4.1 Cluster API Key (para Kafka)

1. En tu cluster `aura360-kafka-prod`, click **API Keys** tab
2. Click **+ Add key**
3. Configuración:
   - **Key type**: Cluster-specific
   - **Description**: "AURA360 Production Services"
   - **Scope**: Cluster-specific
4. Click **Create**
5. ⚠️ **MUY IMPORTANTE**: Copiar y guardar en lugar seguro:
   - **API Key**: Ej. `ABCD1234EFGH5678`
   - **API Secret**: Ej. `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - ⚠️ **NO podrás ver el Secret de nuevo**
6. Guardar en 1Password, Bitwarden, o `.env` local (nunca en Git)

### 4.2 Bootstrap Servers

1. En **Cluster settings** (o **Cluster overview**)
2. Buscar sección **Bootstrap server**
3. Copiar la URL, debería ser algo como:
   ```
   pkc-xxxxx.us-east-1.aws.confluent.cloud:9092
   ```
4. Guardar junto con las API Keys

### 4.3 Cloud API Key (opcional, para MCP Server)

Si vas a usar Claude Desktop con MCP:

1. Click en tu perfil (arriba derecha) → **API Keys**
2. Click **+ Add key**
3. Configuración:
   - **Resource type**: Cloud resource management
   - **Scope**: Organization
   - **Description**: "MCP Server for Claude Desktop"
4. Click **Create**
5. Copiar y guardar:
   - **Cloud API Key**
   - **Cloud API Secret**

### 4.4 Schema Registry API Key (opcional)

Si usas Schema Registry:

1. En el environment, click **Schema Registry** tab
2. Click **API Keys** → **+ Add key**
3. Configuración:
   - **Description**: "AURA360 Schema Registry"
4. Copiar y guardar keys

---

## 🔐 Parte 5: Configurar Seguridad (Opcional para Producción)

### 5.1 ACLs (Access Control Lists)

Para producción, configura ACLs para limitar permisos:

1. En el cluster, click **Access** tab
2. Click **+ Add ACL**
3. Ejemplo para service account `vectordb-consumer`:
   - **Principal**: Service account `sa-xxxxx`
   - **Permission**: Read
   - **Resource**: Topic `aura360.context.aggregated`
   - **Pattern**: Literal
4. Repetir para cada servicio con permisos mínimos necesarios

**Recomendado para producción**:
- Django API: Write a `user.events`
- Vectordb: Read de `user.events`, Write a `context.*`
- Agents: Read de `guardian.requests`, Write a `guardian.responses`

### 5.2 Service Accounts

1. En **Accounts** tab → **+ Add service account**
2. Crear cuentas separadas para cada servicio:
   - `aura360-api-producer`
   - `aura360-vectordb-consumer`
   - `aura360-agents-consumer`
3. Generar API Keys específicas para cada cuenta
4. Aplicar ACLs como en 5.1

---

## 📊 Parte 6: Configurar Monitoring (Opcional pero Recomendado)

### 6.1 Habilitar Metrics

1. En el cluster, click **Metrics** tab
2. Configurar alertas:
   - **Consumer lag** > 1000 mensajes → Email
   - **Produce error rate** > 1% → Email
   - **Cluster health** ≠ Green → Email

### 6.2 Integración con Railway (Producción)

1. Copiar **Cluster ID** del dashboard
2. Configurar en Railway:
   ```bash
   KAFKA_CLUSTER_ID=lkc-xxxxx
   ```
3. Ver logs combinados en Railway + Confluent Cloud

---

## ✅ Verificación Final

### Checklist de Verificación

- [ ] Cuenta de Confluent Cloud creada y verificada
- [ ] Beneficio de 1 año activado (o créditos de free trial)
- [ ] Environment `aura360-prod` creado
- [ ] Cluster `aura360-kafka-prod` en estado **Ready**
- [ ] 6 topics creados con configuración correcta:
  - [ ] `aura360.user.events`
  - [ ] `aura360.context.aggregated`
  - [ ] `aura360.context.vectorized`
  - [ ] `aura360.guardian.requests`
  - [ ] `aura360.guardian.responses`
  - [ ] `aura360.vectordb.ingest`
- [ ] API Key del cluster generada y guardada seguramente
- [ ] Bootstrap Servers URL copiada
- [ ] (Opcional) Cloud API Key para MCP generada
- [ ] (Opcional) Schema Registry configurado
- [ ] (Opcional) ACLs y Service Accounts configurados
- [ ] (Opcional) Alertas configuradas

---

## 🧪 Test de Conectividad

### Opción A: Usando Confluent Cloud Console

1. En un topic, click **Messages** tab
2. Click **Produce a new message**
3. JSON:
   ```json
   {
     "test": "Hello from AURA360",
     "timestamp": "2025-01-07T12:00:00Z"
   }
   ```
4. Click **Produce**
5. ✅ Deberías ver el mensaje en la tabla

### Opción B: Usando Python (desde tu máquina)

```bash
# Crear test script
cat > /tmp/test_confluent.py <<'EOF'
from confluent_kafka import Producer
import json

# Configuración (reemplazar con tus valores)
conf = {
    'bootstrap.servers': 'pkc-xxxxx.us-east-1.aws.confluent.cloud:9092',
    'security.protocol': 'SASL_SSL',
    'sasl.mechanisms': 'PLAIN',
    'sasl.username': 'TU_API_KEY',
    'sasl.password': 'TU_API_SECRET',
}

producer = Producer(conf)

def delivery_report(err, msg):
    if err:
        print(f'❌ Error: {err}')
    else:
        print(f'✅ Message delivered to {msg.topic()} [{msg.partition()}]')

# Enviar mensaje de prueba
topic = 'aura360.user.events'
message = json.dumps({'test': 'Hello from AURA360', 'timestamp': '2025-01-07T12:00:00Z'})
producer.produce(topic, value=message, callback=delivery_report)
producer.flush()
EOF

# Instalar confluent-kafka
pip install confluent-kafka

# Ejecutar test
python /tmp/test_confluent.py
```

**Salida esperada**:
```
✅ Message delivered to aura360.user.events [0]
```

---

## 🎯 Siguiente Paso

Una vez completada esta guía:

1. **Copiar credenciales a `.env` files**:
   - `/services/api/.env`
   - `/services/vectordb/.env`
   - `/services/agents/.env`

2. **Configurar secrets en Railway**:
   ```bash
   railway variables set KAFKA_BOOTSTRAP_SERVERS="pkc-xxxxx.us-east-1.aws.confluent.cloud:9092"
   railway variables set KAFKA_API_KEY="tu-api-key"
   railway variables set KAFKA_API_SECRET="tu-api-secret"
   ```

3. **Continuar con MCP_CONFLUENT_SETUP.md** para integrar con Claude Desktop

---

## 💰 Estimación de Costos (Post Año Gratis)

### Cluster Basic (us-east-1)
- **Costo base**: ~$150/mes
- **Ingestion**: $0.10/GB
- **Storage**: $0.10/GB/mes
- **Egress**: $0.05/GB

### Ejemplo para AURA360 (estimado)
- **Tráfico**: 100 GB/mes ingestion + 50 GB egress = $15
- **Storage**: 50 GB promedio = $5
- **Total**: ~$170/mes

**Recomendación**: En mes 10 del beneficio, evaluar migrar a self-hosted Kafka en Railway si el costo es prohibitivo.

---

## ⚠️ Troubleshooting

### Error: "Invalid API Key"

```bash
# Verificar que estés usando:
# - API Key del CLUSTER (no Cloud API Key)
# - SASL_SSL protocol
# - PLAIN mechanism
```

### Error: "Topic not found"

```bash
# Verificar nombre exacto del topic (case-sensitive)
# Debe ser: aura360.user.events (no aura360_user_events)
```

### Error: "Authentication failed"

```bash
# Regenerar API Key en Confluent Cloud
# Asegurarte de copiar el Secret completo (sin espacios extras)
```

---

## 📚 Recursos

- **Confluent Cloud Docs**: https://docs.confluent.io/cloud/current/
- **Free Trial**: https://www.confluent.io/confluent-cloud/tryfree/
- **Python Client**: https://docs.confluent.io/kafka-clients/python/current/
- **Best Practices**: https://docs.confluent.io/cloud/current/client-apps/best-practices.html

---

**🎉 ¡Listo! Confluent Cloud está configurado y listo para usar.**

**Próximos pasos**:
1. Ver `MCP_CONFLUENT_SETUP.md` para Claude Desktop
2. Ver `QUICKSTART_KAFKA.md` para comenzar a desarrollar
3. Actualizar `.env` files con las credenciales

---

**Última actualización**: 2025-01-07
**Versión**: 1.0
**Contacto**: DevOps Team
