# Configuración de Qdrant Cloud para AURA360

## Resumen
Esta guía describe cómo configurar Qdrant Cloud (managed service) con facturación a través de GCP Marketplace para AURA360.

## Ventajas de Qdrant Cloud
- ✅ **Zero operaciones**: Completamente gestionado, sin Kubernetes
- ✅ **Facturación consolidada**: A través de tu cuenta GCP Marketplace
- ✅ **Alta disponibilidad**: Backups automáticos y replicación
- ✅ **Free tier**: 1GB RAM gratis para desarrollo
- ✅ **Deployment rápido**: ~2 minutos desde consola

---

## Paso 1: Acceder a Qdrant Cloud desde GCP Marketplace

### 1.1 Buscar Qdrant en GCP Marketplace
1. Ir a [Google Cloud Console](https://console.cloud.google.com)
2. Navegar a **Marketplace** en el menú lateral
3. Buscar: **"Qdrant Vector Database"**
4. Seleccionar el producto oficial de Qdrant

### 1.2 Suscribirse desde GCP Marketplace
1. Click en **"Subscribe"** o **"Enable"**
2. Aceptar los términos de servicio
3. Serás redirigido a **Qdrant Cloud Console** (https://cloud.qdrant.io)
4. **Importante**: La facturación se cargará a tu cuenta GCP automáticamente

---

## Paso 2: Crear un Cluster en Qdrant Cloud

### 2.1 Registrarse/Login en Qdrant Cloud
1. Si vienes desde GCP Marketplace, ya deberías estar autenticado
2. Si no, crear cuenta en: https://cloud.qdrant.io/login
3. Seleccionar **"GCP Marketplace"** como método de pago

### 2.2 Crear Cluster
1. En Qdrant Cloud Console, click **"Create Cluster"**
2. Configuración recomendada para AURA360:

```yaml
Cluster Name: aura360-production
Cloud Provider: Google Cloud Platform (GCP)
Region: us-central1 (Iowa) # O la región más cercana a tus servicios
Configuration:
  - Development (Free Tier): 1 GB RAM, 4 GB Storage
  - Production (Starter): 2 GB RAM, 20 GB Storage
  - Production (Standard): 8 GB RAM, 50 GB Storage
```

3. Click **"Create"**
4. **Esperar ~2 minutos** mientras se aprovisiona el cluster

### 2.3 Obtener Credenciales
Una vez creado el cluster, obtendrás:

```bash
# URL del cluster (ejemplo)
QDRANT_URL=https://abc123-xyz456.us-central1-0.gcp.cloud.qdrant.io:6333

# API Key (clave de autenticación)
QDRANT_API_KEY=your-api-key-here-keep-secret
```

**⚠️ IMPORTANTE**:
- Guarda la **API Key** de forma segura (solo se muestra una vez)
- Usa Google Secret Manager para producción
- **NUNCA** comitees la API key en Git

---

## Paso 3: Crear Colecciones Necesarias

AURA360 necesita las siguientes colecciones en Qdrant:

### 3.1 Colección: `holistic_memory`
Para almacenar embeddings de contexto de usuario y documentos.

```python
# Ejecutar desde services/vectordb
python scripts/create_collections.py
```

O manualmente desde la consola de Qdrant Cloud:

```json
{
  "name": "holistic_memory",
  "vectors": {
    "size": 384,
    "distance": "Cosine"
  }
}
```

### 3.2 Colección: `user_context`
Para almacenar contexto agregado de usuarios.

```json
{
  "name": "user_context",
  "vectors": {
    "size": 384,
    "distance": "Cosine"
  }
}
```

### 3.3 Colección: `holistic_agents` (opcional)
Para el servicio de agents.

```json
{
  "name": "holistic_agents",
  "vectors": {
    "size": 768,
    "distance": "Cosine"
  }
}
```

---

## Paso 4: Configurar Variables de Entorno

### 4.1 Servicio VectorDB (`services/vectordb/.env`)

```bash
# ==============================================================================
# QDRANT CLOUD CONFIGURATION
# ==============================================================================

# Qdrant Cloud URL (desde consola de Qdrant)
QDRANT_URL=https://your-cluster.us-central1-0.gcp.cloud.qdrant.io:6333

# Qdrant API Key (desde consola de Qdrant)
QDRANT_API_KEY=your-qdrant-api-key-here

# NO usar gRPC con Qdrant Cloud (solo REST)
QDRANT_GRPC=
PREFER_GRPC=false

# Collection Configuration
VECTOR_COLLECTION_NAME=holistic_memory
VECTOR_DIMENSION=384
```

### 4.2 Servicio Agents (`services/agents/.env`)

```bash
# ==============================================================================
# QDRANT CLOUD CONFIGURATION
# ==============================================================================

# Qdrant Cloud URL
AGENT_SERVICE_QDRANT_URL=https://your-cluster.us-central1-0.gcp.cloud.qdrant.io:6333

# Qdrant API Key
AGENT_SERVICE_QDRANT_API_KEY=your-qdrant-api-key-here

# Collection name
AGENT_SERVICE_VECTOR_COLLECTION=holistic_agents

# SSL verification (Qdrant Cloud usa HTTPS)
AGENT_SERVICE_VECTOR_VERIFY_SSL=true
```

### 4.3 Helm Values para Kubernetes (`infra/gcp/helm/values.yaml`)

Si más adelante despliegas en GKE, necesitarás:

```yaml
vectordb:
  env:
    QDRANT_URL: "https://your-cluster.us-central1-0.gcp.cloud.qdrant.io:6333"
    QDRANT_API_KEY: # Usar Secret de Kubernetes

agents:
  env:
    AGENT_SERVICE_QDRANT_URL: "https://your-cluster.us-central1-0.gcp.cloud.qdrant.io:6333"
    AGENT_SERVICE_QDRANT_API_KEY: # Usar Secret de Kubernetes
```

---

## Paso 5: Verificar Conectividad

### 5.1 Test desde VectorDB Service

```bash
cd services/vectordb

# Asegúrate de tener las env vars configuradas
source .env

# Test de conexión
python -c "
from qdrant_client import QdrantClient
client = QdrantClient(
    url='${QDRANT_URL}',
    api_key='${QDRANT_API_KEY}'
)
print('Collections:', client.get_collections())
"
```

### 5.2 Test desde Agents Service

```bash
cd services/agents

# Test de conexión
python -c "
from qdrant_client import QdrantClient
import os
client = QdrantClient(
    url=os.getenv('AGENT_SERVICE_QDRANT_URL'),
    api_key=os.getenv('AGENT_SERVICE_QDRANT_API_KEY')
)
print('Connected to Qdrant Cloud:', client.get_collections())
"
```

---

## Paso 6: Seguridad en Producción

### 6.1 Usar Google Secret Manager

```bash
# Crear secret para Qdrant API Key
gcloud secrets create qdrant-api-key \
  --replication-policy="automatic" \
  --data-file=- <<EOF
your-qdrant-api-key-here
EOF

# Dar permisos a las service accounts
gcloud secrets add-iam-policy-binding qdrant-api-key \
  --member="serviceAccount:vectordb@${GCP_PROJECT}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 6.2 Actualizar Kubernetes para usar Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: qdrant-credentials
type: Opaque
stringData:
  api-key: # Se inyecta desde Google Secret Manager
```

---

## Costos Estimados

### Free Tier (Desarrollo)
- **Costo**: $0/mes
- **RAM**: 1 GB
- **Storage**: 4 GB
- **Límites**: Adecuado para desarrollo y testing

### Starter Tier (Producción pequeña)
- **Costo**: ~$25/mes (facturado a GCP)
- **RAM**: 2 GB
- **Storage**: 20 GB
- **Límites**: ~100K vectores de 384 dimensiones

### Standard Tier (Producción media)
- **Costo**: ~$100/mes (facturado a GCP)
- **RAM**: 8 GB
- **Storage**: 50 GB
- **Límites**: ~500K vectores de 384 dimensiones

**Nota**: Los costos se cargan directamente a tu factura de GCP Marketplace.

---

## Migración de Datos (si tienes datos en Qdrant local)

Si ya tienes datos en tu Qdrant local (Docker), necesitas migrarlos:

```bash
cd services/vectordb

# Script de migración (crear)
python scripts/migrate_to_qdrant_cloud.py \
  --source-url http://localhost:6333 \
  --target-url https://your-cluster.gcp.cloud.qdrant.io:6333 \
  --target-api-key your-api-key \
  --collection holistic_memory
```

---

## Troubleshooting

### Error: "Connection refused"
- ✅ Verifica que el cluster esté en estado **"Running"** en Qdrant Console
- ✅ Revisa que la URL incluya el puerto `:6333`
- ✅ Confirma que la API key esté correcta

### Error: "SSL Certificate verification failed"
- ✅ Asegúrate de que `AGENT_SERVICE_VECTOR_VERIFY_SSL=true` en producción
- ✅ Qdrant Cloud usa certificados válidos, no desactives SSL

### Error: "Collection not found"
- ✅ Crea las colecciones primero (Paso 3)
- ✅ Verifica el nombre de la colección en las env vars

---

## Próximos Pasos

1. ✅ Suscribirse a Qdrant desde GCP Marketplace
2. ✅ Crear cluster en Qdrant Cloud
3. ✅ Crear colecciones necesarias
4. ✅ Actualizar variables de entorno en todos los servicios
5. ✅ Migrar datos existentes (si aplica)
6. ✅ Verificar integración completa
7. ✅ Configurar backups automáticos desde Qdrant Console

---

## Referencias

- [Qdrant Cloud Documentation](https://qdrant.tech/documentation/cloud/)
- [Qdrant on GCP Marketplace](https://console.cloud.google.com/marketplace/product/qdrant-public/qdrant)
- [Qdrant Pricing](https://qdrant.tech/pricing/)
- [Google Secret Manager](https://cloud.google.com/secret-manager/docs)
