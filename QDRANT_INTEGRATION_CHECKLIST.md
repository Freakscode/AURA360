# ✅ Checklist: Integración de Qdrant Cloud con AURA360

Esta checklist te guía paso a paso para integrar Qdrant Cloud (desde GCP Marketplace) con AURA360.

---

## 📋 Pre-requisitos

- [ ] Cuenta de Google Cloud Platform activa
- [ ] Facturación habilitada en GCP
- [ ] Acceso al proyecto GCP de AURA360
- [ ] Python 3.11+ con `uv` instalado localmente
- [ ] Servicios de AURA360 clonados localmente

---

## 🚀 Fase 1: Configurar Qdrant Cloud

### Paso 1.1: Suscribirse desde GCP Marketplace
- [ ] Ir a [Google Cloud Console - Marketplace](https://console.cloud.google.com/marketplace)
- [ ] Buscar: **"Qdrant Vector Database"**
- [ ] Click en **"Subscribe"** o **"Enable"**
- [ ] Aceptar términos de servicio
- [ ] Serás redirigido a Qdrant Cloud Console (https://cloud.qdrant.io)

**Documentación**: `infra/gcp/QDRANT_CLOUD_SETUP.md` (Paso 1)

---

### Paso 1.2: Crear Cluster en Qdrant Cloud
- [ ] Login en [Qdrant Cloud Console](https://cloud.qdrant.io)
- [ ] Click en **"Create Cluster"**
- [ ] Configurar:
  ```yaml
  Cluster Name: aura360-production
  Cloud Provider: Google Cloud Platform (GCP)
  Region: us-central1 (o la más cercana a tus servicios)
  Configuration: Development (Free Tier) o Starter ($25/mes)
  ```
- [ ] Click **"Create"**
- [ ] Esperar ~2 minutos hasta que el cluster esté en estado **"Running"**

**Documentación**: `infra/gcp/QDRANT_CLOUD_SETUP.md` (Paso 2)

---

### Paso 1.3: Guardar Credenciales
Una vez creado el cluster, **guarda las credenciales**:

- [ ] **Cluster URL**: `https://abc-xyz.us-central1-0.gcp.cloud.qdrant.io:6333`
- [ ] **API Key**: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

⚠️ **IMPORTANTE**: La API Key solo se muestra una vez. Guárdala de forma segura.

**Sugerencia**: Usa un gestor de contraseñas o crea el secret inmediatamente en Google Secret Manager.

---

## 🔧 Fase 2: Configurar Servicios Locales

### Paso 2.1: Configurar VectorDB Service
- [ ] Ir a `services/vectordb/`
- [ ] Copiar `.env.example` a `.env`:
  ```bash
  cd services/vectordb
  cp .env.example .env
  ```
- [ ] Editar `.env` y configurar:
  ```bash
  QDRANT_URL=https://tu-cluster-id.us-central1-0.gcp.cloud.qdrant.io:6333
  QDRANT_API_KEY=tu-api-key-aqui
  VECTOR_COLLECTION_NAME=holistic_memory
  PREFER_GRPC=false
  ```

**Archivos modificados**:
- `services/vectordb/.env`

---

### Paso 2.2: Configurar Agents Service
- [ ] Ir a `services/agents/`
- [ ] Copiar `.env.example` a `.env` (si no existe):
  ```bash
  cd services/agents
  cp .env.example .env
  ```
- [ ] Editar `.env` y configurar:
  ```bash
  AGENT_SERVICE_QDRANT_URL=https://tu-cluster-id.us-central1-0.gcp.cloud.qdrant.io:6333
  AGENT_SERVICE_QDRANT_API_KEY=tu-api-key-aqui
  AGENT_SERVICE_VECTOR_COLLECTION=holistic_agents
  AGENT_SERVICE_VECTOR_VERIFY_SSL=true
  ```

**Archivos modificados**:
- `services/agents/.env`

---

## 🗄️ Fase 3: Crear Colecciones en Qdrant

### Paso 3.1: Inicializar Colecciones
- [ ] Ejecutar script de inicialización:
  ```bash
  cd services/vectordb
  source .env
  python scripts/init_qdrant_collections.py
  ```

- [ ] Verificar que se crearon las colecciones:
  - `holistic_memory` (384 dim, Cosine)
  - `user_context` (384 dim, Cosine)
  - `holistic_agents` (768 dim, Cosine)

**Archivos relevantes**:
- `services/vectordb/scripts/init_qdrant_collections.py`

**Documentación**: `infra/gcp/QDRANT_CLOUD_SETUP.md` (Paso 3)

---

## ✅ Fase 4: Verificar Integración

### Paso 4.1: Ejecutar Script de Verificación
- [ ] Ejecutar desde la raíz del proyecto:
  ```bash
  ./scripts/verify_qdrant_integration.sh
  ```

- [ ] Verificar que todos los checks pasen:
  - ✅ VectorDB Service puede conectarse a Qdrant Cloud
  - ✅ Agents Service puede conectarse a Qdrant Cloud
  - ✅ Todas las colecciones requeridas existen

**Archivos relevantes**:
- `scripts/verify_qdrant_integration.sh`

---

### Paso 4.2: Test Manual de Conexión (Opcional)
Desde `services/vectordb`:
```bash
cd services/vectordb
source .env

python -c "
from qdrant_client import QdrantClient
import os

client = QdrantClient(
    url=os.getenv('QDRANT_URL'),
    api_key=os.getenv('QDRANT_API_KEY')
)

collections = client.get_collections()
print('✅ Conexión exitosa')
print(f'📦 Colecciones: {[c.name for c in collections.collections]}')
"
```

- [ ] Verificar que el output muestre las colecciones creadas

---

## 🔐 Fase 5: Seguridad (Producción)

### Paso 5.1: Crear Secret en Google Secret Manager
- [ ] Ejecutar:
  ```bash
  gcloud secrets create qdrant-api-key \
    --replication-policy="automatic" \
    --data-file=- <<EOF
  tu-qdrant-api-key-aqui
  EOF
  ```

- [ ] Dar permisos a service accounts:
  ```bash
  # VectorDB Service
  gcloud secrets add-iam-policy-binding qdrant-api-key \
    --member="serviceAccount:vectordb@${GCP_PROJECT}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

  # Agents Service
  gcloud secrets add-iam-policy-binding qdrant-api-key \
    --member="serviceAccount:agents@${GCP_PROJECT}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
  ```

**Documentación**: `infra/gcp/QDRANT_CLOUD_SETUP.md` (Paso 6)

---

### Paso 5.2: Actualizar Kubernetes Secrets (si usas GKE)
- [ ] Crear secret en Kubernetes:
  ```bash
  kubectl create secret generic qdrant-credentials \
    --from-literal=api-key=tu-api-key \
    --namespace=aura360
  ```

- [ ] Verificar:
  ```bash
  kubectl get secrets -n aura360 | grep qdrant
  ```

---

## 🧪 Fase 6: Testing End-to-End

### Paso 6.1: Test de Integración Completa
- [ ] Ejecutar test end-to-end:
  ```bash
  ./scripts/run_user_context_e2e.sh
  ```

- [ ] Verificar que el test pase sin errores

---

### Paso 6.2: Test Manual desde Frontend
- [ ] Levantar servicios:
  ```bash
  # Terminal 1: Django API
  cd services/api
  uv run python manage.py runserver 0.0.0.0:8000

  # Terminal 2: Agents Service
  cd services/agents
  uv run uvicorn main:app --reload --port 8080

  # Terminal 3: VectorDB Service
  cd services/vectordb
  docker compose up -d  # Solo qdrant local si lo necesitas
  uv run uvicorn vectosvc.api.http:app --reload --port 8001

  # Terminal 4: Frontend
  cd apps/web
  ng serve
  ```

- [ ] Abrir navegador en `http://localhost:4200`
- [ ] Login en la aplicación
- [ ] Navegar a "Dashboard" → "Consejo Holístico"
- [ ] Ingresar una pregunta (ej: "¿Qué ejercicios debo hacer?")
- [ ] Verificar que se reciba una respuesta

---

## 📊 Fase 7: Monitoreo

### Paso 7.1: Verificar Métricas en Qdrant Console
- [ ] Ir a [Qdrant Cloud Console](https://cloud.qdrant.io)
- [ ] Seleccionar tu cluster
- [ ] Revisar:
  - **Storage**: Uso de disco
  - **RAM**: Uso de memoria
  - **Requests**: Requests por segundo
  - **Latency**: P50, P95, P99

---

### Paso 7.2: Configurar Alertas (Opcional)
- [ ] Configurar alertas en Qdrant Cloud para:
  - Uso de RAM > 80%
  - Latencia P95 > 200ms
  - Errores > 1%

---

## 📝 Fase 8: Documentación

### Paso 8.1: Actualizar Documentación Interna
- [ ] Agregar URLs y credenciales a tu gestor de contraseñas
- [ ] Documentar región del cluster en wiki/confluence
- [ ] Compartir acceso a Qdrant Console con equipo (si aplica)

---

### Paso 8.2: Actualizar Runbooks
- [ ] Agregar procedimiento de backup de Qdrant a runbooks
- [ ] Documentar proceso de escalado (upgrade de tier)
- [ ] Agregar troubleshooting común

---

## 🎉 Completado

- [ ] ✅ Qdrant Cloud configurado y corriendo
- [ ] ✅ Todos los servicios conectados exitosamente
- [ ] ✅ Colecciones creadas y verificadas
- [ ] ✅ Seguridad configurada (Secret Manager)
- [ ] ✅ Tests pasando
- [ ] ✅ Documentación actualizada

---

## 📚 Referencias

- [Guía de Setup de Qdrant Cloud](infra/gcp/QDRANT_CLOUD_SETUP.md)
- [Guía de Integración Completa](docs/QDRANT_INTEGRATION_GUIDE.md)
- [Script de Verificación](scripts/verify_qdrant_integration.sh)
- [Script de Inicialización de Colecciones](services/vectordb/scripts/init_qdrant_collections.py)
- [Qdrant Cloud Documentation](https://qdrant.tech/documentation/cloud/)

---

## 🆘 Troubleshooting

Si encuentras problemas, consulta:
1. `docs/QDRANT_INTEGRATION_GUIDE.md` (Sección 7: Troubleshooting)
2. Logs de servicios: `kubectl logs -n aura360 -l app=vectordb`
3. Qdrant Cloud Console: Sección "Monitoring" → "Logs"

---

## 💰 Costos

| Tier | Costo/mes | Uso Recomendado |
|------|-----------|-----------------|
| Free | $0 | Desarrollo/Testing |
| Starter | ~$25 | Producción pequeña (<100K vectores) |
| Standard | ~$100 | Producción media (<500K vectores) |

Los costos se facturan directamente a tu cuenta de GCP Marketplace.

---

**Última actualización**: 2025-01-20
