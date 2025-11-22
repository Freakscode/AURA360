# Migración de Autenticación GCP: De Service Account Files a Métodos Modernos

## Problema Actual

El código está usando **autenticación con archivos** (`GOOGLE_APPLICATION_CREDENTIALS`), que está deprecada:

```yaml
# docker-compose.yml (DEPRECADO)
environment:
  - GOOGLE_APPLICATION_CREDENTIALS=/gcloud/application_default_credentials.json
volumes:
  - ${HOME}/.config/gcloud:/gcloud:ro
```

## Soluciones Modernas

Google recomienda **3 métodos modernos** según el entorno:

---

## 🚀 **Opción 1: Application Default Credentials (ADC)** - RECOMENDADO

### Para Desarrollo Local

**Qué es**: Usa las credenciales de tu `gcloud CLI` automáticamente.

**Ventajas**:
- ✅ No necesitas archivos de credenciales
- ✅ Usa tu propia cuenta de Google
- ✅ Permisos granulares (tu usuario)
- ✅ Fácil rotación (solo `gcloud auth login`)

**Configuración**:

```bash
# 1. Autenticarte con gcloud
gcloud auth application-default login

# 2. Configurar proyecto por defecto
gcloud config set project aura-360-471711

# 3. Verificar credenciales
gcloud auth application-default print-access-token
```

**Actualizar Docker Compose**:

```yaml
# docker-compose.yml (MODERNO)
api:
  environment:
    # Remover GOOGLE_APPLICATION_CREDENTIALS
    - GCS_PROJECT=aura-360-471711
  volumes:
    # Montar solo las credenciales ADC (no todo .config/gcloud)
    - ${HOME}/.config/gcloud/application_default_credentials.json:/tmp/adc.json:ro
    - .:/app:ro
```

**En el código (ya está implementado)**:

```python
# vectosvc/core/repos/gcs.py
# ✅ Ya usa ADC automáticamente
client = storage.Client(project=self._project)
```

---

## ☁️ **Opción 2: Workload Identity (GKE)** - PRODUCCIÓN

### Para Kubernetes en GKE

**Qué es**: Vincula Service Accounts de Kubernetes con Service Accounts de GCP sin credenciales.

**Ventajas**:
- ✅ **Cero credenciales** en pods
- ✅ Rotación automática de tokens
- ✅ Permisos granulares por servicio
- ✅ Auditoría mejorada

**Configuración**:

```bash
# 1. Habilitar Workload Identity en GKE
gcloud container clusters update aura360-cluster \
  --workload-pool=aura-360-471711.svc.id.goog

# 2. Crear Service Account de GCP
gcloud iam service-accounts create vectordb-sa \
  --display-name="VectorDB Service Account"

# 3. Dar permisos al SA
gcloud projects add-iam-policy-binding aura-360-471711 \
  --member="serviceAccount:vectordb-sa@aura-360-471711.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

# 4. Vincular SA de K8s con SA de GCP
gcloud iam service-accounts add-iam-policy-binding \
  vectordb-sa@aura-360-471711.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:aura-360-471711.svc.id.goog[aura360/vectordb]"
```

**Actualizar Helm Values**:

```yaml
# infra/gcp/helm/values.yaml
vectordb:
  serviceAccount:
    create: true
    name: vectordb
    annotations:
      iam.gke.io/gcp-service-account: vectordb-sa@aura-360-471711.iam.gserviceaccount.com

  # NO necesitas GOOGLE_APPLICATION_CREDENTIALS
  env:
    GCS_PROJECT: "aura-360-471711"
```

**Deployment**:

```yaml
# Kubernetes automáticamente inyecta credenciales
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vectordb
spec:
  template:
    spec:
      serviceAccountName: vectordb  # ← Vinculado con GCP SA
      containers:
      - name: vectordb
        env:
        - name: GCS_PROJECT
          value: "aura-360-471711"
        # NO GOOGLE_APPLICATION_CREDENTIALS needed!
```

---

## 🔑 **Opción 3: Service Account Keys (ÚLTIMO RECURSO)**

### Solo si NO puedes usar ADC o Workload Identity

**Cuándo usarlo**:
- Servicios fuera de GCP (AWS, Azure, on-prem)
- CI/CD en plataformas externas

**⚠️ Desventajas**:
- ❌ Credenciales estáticas (riesgo de seguridad)
- ❌ Rotación manual
- ❌ Fácil de filtrar en Git

**Si DEBES usarlo**:

```bash
# 1. Crear SA
gcloud iam service-accounts create vectordb-external \
  --display-name="VectorDB External"

# 2. Crear key (JSON)
gcloud iam service-accounts keys create vectordb-key.json \
  --iam-account=vectordb-external@aura-360-471711.iam.gserviceaccount.com

# 3. IMPORTANTE: Guardar en Secret Manager
gcloud secrets create vectordb-sa-key \
  --data-file=vectordb-key.json

# 4. ELIMINAR archivo local inmediatamente
rm vectordb-key.json
```

**Uso en código**:

```python
# Cargar desde Secret Manager (NO desde archivo)
from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()
secret = client.access_secret_version(
    request={"name": "projects/aura-360-471711/secrets/vectordb-sa-key/versions/latest"}
)
credentials = json.loads(secret.payload.data.decode("UTF-8"))

# Usar credentials
from google.oauth2 import service_account
creds = service_account.Credentials.from_service_account_info(credentials)
storage_client = storage.Client(credentials=creds)
```

---

## 📋 **Plan de Migración Recomendado**

### Fase 1: Desarrollo Local (HOY)

```bash
# 1. Autenticar con ADC
gcloud auth application-default login

# 2. Actualizar docker-compose.yml
# Remover GOOGLE_APPLICATION_CREDENTIALS
# Montar solo ADC credentials
```

**Cambios en `docker-compose.yml`**:

```yaml
api:
  environment:
    # ❌ Remover esta línea
    # - GOOGLE_APPLICATION_CREDENTIALS=/gcloud/application_default_credentials.json

    # ✅ Agregar esto
    - GOOGLE_CLOUD_PROJECT=aura-360-471711
    - GCS_PROJECT=aura-360-471711
  volumes:
    # ❌ Remover esto
    # - ${HOME}/.config/gcloud:/gcloud:ro

    # ✅ Agregar solo ADC (más seguro)
    - ${HOME}/.config/gcloud/application_default_credentials.json:/tmp/adc.json:ro
  # ✅ Opcional: setear env var apuntando a ADC
  environment:
    - GOOGLE_APPLICATION_CREDENTIALS=/tmp/adc.json
```

### Fase 2: Producción en GKE (PRÓXIMAMENTE)

1. ✅ Habilitar Workload Identity en cluster
2. ✅ Crear Service Accounts para cada servicio:
   - `vectordb-sa` (Storage read)
   - `agents-sa` (Vertex AI, Storage)
   - `api-sa` (Firestore, Pub/Sub)
3. ✅ Vincular SAs de K8s con SAs de GCP
4. ✅ Actualizar Helm charts
5. ✅ **NO usar `GOOGLE_APPLICATION_CREDENTIALS`**

---

## ✅ **Verificar que Funciona**

### Test Local

```bash
# Con ADC configurado
cd services/vectordb

# Test de conexión a GCS
uv run python -c "
from google.cloud import storage
client = storage.Client(project='aura-360-471711')
buckets = list(client.list_buckets())
print('✅ Conectado a GCP:', len(buckets), 'buckets')
"
```

### Test en GKE

```bash
# Desde un pod con Workload Identity
kubectl exec -it vectordb-pod -- python -c "
from google.cloud import storage
import os
print('Project:', os.getenv('GCS_PROJECT'))
client = storage.Client()
print('✅ Workload Identity funciona!')
"
```

---

## 🔐 **Mejores Prácticas**

1. ✅ **Desarrollo**: Usa ADC (`gcloud auth application-default login`)
2. ✅ **GKE**: Usa Workload Identity (cero credenciales)
3. ✅ **CI/CD en GCP**: Usa Cloud Build con SA automática
4. ✅ **Externo**: Secret Manager + rotación de keys
5. ❌ **NUNCA**: Comitear archivos `.json` de credenciales en Git
6. ❌ **NUNCA**: Montar todo `~/.config/gcloud` (solo ADC)

---

## 📚 **Referencias**

- [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials)
- [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)
- [Best Practices for Service Account Keys](https://cloud.google.com/iam/docs/best-practices-for-managing-service-account-keys)
- [Migrating from service account keys](https://cloud.google.com/iam/docs/migrating-to-workload-identity)

---

## 🆘 **Troubleshooting**

### Error: "Could not automatically determine credentials"

```bash
# Solución: Autenticarte con ADC
gcloud auth application-default login
```

### Error: "Permission denied" en GCS

```bash
# Verificar permisos de tu usuario
gcloud projects get-iam-policy aura-360-471711 \
  --flatten="bindings[].members" \
  --filter="bindings.members:user:$(gcloud config get-value account)"

# Agregar permiso si falta
gcloud projects add-iam-policy-binding aura-360-471711 \
  --member="user:tu-email@gmail.com" \
  --role="roles/storage.objectViewer"
```

### Error: Workload Identity no funciona

```bash
# Verificar anotación en SA de K8s
kubectl get sa vectordb -n aura360 -o yaml | grep gcp-service-account

# Verificar binding
gcloud iam service-accounts get-iam-policy \
  vectordb-sa@aura-360-471711.iam.gserviceaccount.com
```
