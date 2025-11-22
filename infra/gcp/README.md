# Infraestructura GCP para AURA360

Este directorio contiene la configuración de infraestructura para Google Cloud Platform.

## Componentes

### Qdrant Cloud (Vector Database)
- **Tipo**: Managed service con facturación a través de GCP Marketplace
- **Uso**: Base de datos vectorial para RAG y búsqueda semántica
- **Documentación**: [QDRANT_CLOUD_SETUP.md](./QDRANT_CLOUD_SETUP.md)

## Guías Rápidas

### 1. Configurar Qdrant Cloud

```bash
# 1. Suscribirse desde GCP Marketplace
# Ir a: https://console.cloud.google.com/marketplace
# Buscar: "Qdrant Vector Database"

# 2. Crear cluster en Qdrant Cloud Console
# https://cloud.qdrant.io

# 3. Crear colecciones
cd services/vectordb
export QDRANT_URL="https://your-cluster.gcp.cloud.qdrant.io:6333"
export QDRANT_API_KEY="your-api-key"
python scripts/init_qdrant_collections.py

# 4. Verificar integración
cd ../..
./scripts/verify_qdrant_integration.sh
```

### 2. Variables de Entorno Necesarias

#### VectorDB Service (`services/vectordb/.env`)
```bash
QDRANT_URL=https://your-cluster.us-central1-0.gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=your-api-key
VECTOR_COLLECTION_NAME=holistic_memory
PREFER_GRPC=false
```

#### Agents Service (`services/agents/.env`)
```bash
AGENT_SERVICE_QDRANT_URL=https://your-cluster.us-central1-0.gcp.cloud.qdrant.io:6333
AGENT_SERVICE_QDRANT_API_KEY=your-api-key
AGENT_SERVICE_VECTOR_COLLECTION=holistic_agents
AGENT_SERVICE_VECTOR_VERIFY_SSL=true
```

### 3. Seguridad (Producción)

```bash
# Crear secret en Google Secret Manager
gcloud secrets create qdrant-api-key \
  --replication-policy="automatic" \
  --data-file=- <<EOF
your-qdrant-api-key-here
EOF

# Dar permisos a service accounts
gcloud secrets add-iam-policy-binding qdrant-api-key \
  --member="serviceAccount:vectordb@${GCP_PROJECT}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Arquitectura

```
┌─────────────────┐
│  Angular Web    │  apps/web
└────────┬────────┘
         │ HTTP REST
         ↓
┌─────────────────┐
│  Django API     │  services/api:8000
└────────┬────────┘
         │ Kafka
         ↓
┌─────────────────┐
│  Agents Service │  services/agents:8080
└────────┬────────┘
         │ Vector Search
         ↓
┌─────────────────┐
│  VectorDB Svc   │  services/vectordb:8001
└────────┬────────┘
         │ REST/HTTPS
         ↓
┌─────────────────┐
│  Qdrant Cloud   │  https://cluster.gcp.cloud.qdrant.io:6333
└─────────────────┘
```

## Costos Estimados

| Tier | RAM | Storage | Costo/mes | Vectores (~384 dim) |
|------|-----|---------|-----------|---------------------|
| Free | 1 GB | 4 GB | $0 | ~50K |
| Starter | 2 GB | 20 GB | ~$25 | ~100K |
| Standard | 8 GB | 50 GB | ~$100 | ~500K |

Los costos se facturan directamente a tu cuenta de GCP Marketplace.

## Documentación Adicional

- [Configuración Detallada de Qdrant Cloud](./QDRANT_CLOUD_SETUP.md)
- [Guía de Integración Completa](../docs/QDRANT_INTEGRATION_GUIDE.md)
- [Scripts de Verificación](../scripts/verify_qdrant_integration.sh)

## Próximos Pasos

1. ✅ Suscribirse a Qdrant desde GCP Marketplace
2. ✅ Crear cluster en Qdrant Cloud
3. ✅ Configurar variables de entorno
4. ⬜ Crear colecciones necesarias
5. ⬜ Migrar datos existentes (si aplica)
6. ⬜ Configurar Google Secret Manager
7. ⬜ Probar integración end-to-end

## Soporte

- Qdrant Cloud: https://cloud.qdrant.io/support
- Google Cloud: https://cloud.google.com/support
- AURA360 Docs: ../docs/
