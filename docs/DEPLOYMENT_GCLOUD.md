# Deployment con gcloud CLI (Cloud Run + Cloud Storage)

Esta guía describe cómo desplegar los nuevos componentes (API Django, worker de Celery y
formulario Angular) usando **Google Cloud Run** y **Cloud Storage** exclusivamente con la CLI
`gcloud`. La autenticación ya está configurada, por lo que solo debes exportar las variables
indicadas antes de ejecutar los scripts incluidos en `scripts/`.

## 1. Requisitos previos

- `gcloud` 490+ y `gsutil` instalados.
- Proyecto de GCP activo con los APIs habilitados:
  - Cloud Build
  - Artifact Registry (o Container Registry)
  - Cloud Run
  - Cloud Storage
- Redis gestionado (MemoryStore o Upstash) accesible para Celery.
- Supabase / Postgres ya operativos.

## 2. Variables de entorno comunes

```
export GCP_PROJECT=aura360-prod
export GCP_REGION=us-central1
```

### API Django (Cloud Run)

Variables opcionales:

```
export API_SERVICE_NAME=aura360-api
export API_IMAGE_NAME=aura360-api
export API_MIN_INSTANCES=1
export API_MAX_INSTANCES=4
export API_MEMORY=1Gi
export API_CPU=1
export API_SERVICE_ACCOUNT=aura360-api@aura360-prod.iam.gserviceaccount.com
export API_ENV_FILE=deploy/api.env   # Archivo KEY=VALUE usado por --set-env-vars
```

Ejemplo de `deploy/api.env` (sin comillas ni espacios):

```
SECRET_KEY=super-secret
DEBUG=False
ALLOWED_HOSTS=api.aura360.app
DB_HOST=aws-0-us-east-1.pooler.supabase.com
DB_PORT=6543
DB_NAME=postgres
DB_USER=postgres.xxxxxx
DB_PASSWORD=********
SUPABASE_SERVICE_ROLE_KEY=********
VECTOR_DB_BASE_URL=https://vectordb.aura360.app
HOLISTIC_AGENT_SERVICE_URL=https://agents.aura360.app/api/holistic/v1/run
CELERY_BROKER_URL=redis://:password@redis-host:6379/0
CELERY_RESULT_BACKEND=redis://:password@redis-host:6379/1
HOLISTIC_REPORT_SERVICE_URL=https://reports.aura360.app/render
HOLISTIC_REPORT_SERVICE_TOKEN=********
```

### Worker de Celery (Cloud Run)

Comparte casi las mismas variables que la API, pero puedes especificar:

```
export WORKER_SERVICE_NAME=aura360-celery
export WORKER_MIN_INSTANCES=1
export WORKER_MAX_INSTANCES=1
export CELERY_QUEUE=holistic_snapshots
export CELERY_CONCURRENCY=2
export WORKER_ENV_FILE=deploy/api.env   # Puedes reutilizar el mismo archivo
```

### Frontend Angular (Cloud Storage + opcional CDN)

```
export WEB_BUCKET=aura360-web-static
export WEB_DIR=apps/web
# Personaliza el comando si usas bun/pnpm
export WEB_INSTALL_COMMAND="npm ci"
export WEB_BUILD_COMMAND="npm run build"
export WEB_CACHE_CONTROL="public,max-age=300"
```

## 3. Scripts disponibles

Los scripts están en `scripts/` y son auto-documentados por consola.

### 3.1 API Django

```
./scripts/deploy_api_gcloud.sh
```

Pasos realizados:
1. `gcloud builds submit services/api --tag gcr.io/$PROJECT/$IMAGE_NAME:$TAG`
2. `gcloud run deploy $API_SERVICE_NAME ... --set-env-vars` (lee `API_ENV_FILE` y añade
   `DJANGO_SETTINGS_MODULE=config.settings`).
3. Muestra la URL pública del servicio.

### 3.2 Worker de Celery

```
./scripts/deploy_worker_gcloud.sh
```

- Construye la misma imagen que la API (puedes cambiar `WORKER_IMAGE_NAME`).
- Despliega un servicio privado de Cloud Run que ejecuta
  `/app/scripts/start_celery_worker.sh`. Este script inicia el worker y levanta un HTTP server
  mínimo (`python -m http.server`) para satisfacer los health checks de Cloud Run.
- Asegúrate de que la VPC o el Redis usado por Celery sea accesible desde este servicio.

### 3.3 Frontend Angular

```
./scripts/deploy_web_gcloud.sh
```

Acciones:
1. Ejecuta `npm ci` + `npm run build` (puedes sobrescribir comandos).
2. Crea el bucket si no existe y configura `index.html` como documento principal.
3. `gcloud storage rsync` del contenido `dist/aura360-front/browser` al bucket.
4. Aplica `Cache-Control` homogéneo usando `gsutil -m setmeta`.

> **Opcional CDN:** crea un backend bucket y HTTP(S) Load Balancer para servir el bucket con
> Cloud CDN. El script imprime la URL `https://storage.googleapis.com/<bucket>/index.html` que
> funciona inmediatamente.

## 4. Celery worker y colas

- El script `services/api/scripts/start_celery_worker.sh` se copia dentro de la imagen Docker y
  se usa como entrypoint para Cloud Run. Ajusta `CELERY_QUEUE` y `CELERY_CONCURRENCY` vía env vars.
- Si necesitas varias colas (ej. `holistic_snapshots`, `vectorize_pending`), despliega múltiples
  servicios Worker con distintos valores de `CELERY_QUEUE`.

## 5. Checklist post-despliegue

1. Verifica la URL del API (`gcloud run services describe aura360-api ...`).
2. Confirma que el worker aparece como "Ready" en Cloud Run y que el log muestra "Booting worker".
3. Habilita CORS en Django (`CORS_ALLOWED_ORIGINS`) para incluir la URL del bucket o del CDN.
4. Actualiza `environment.ts`/CI para que `apiBaseUrl` apunte al dominio de Cloud Run.
5. (Opcional) Configura un load balancer con dominio personalizado y certificado administrado
   (`gcloud compute ssl-certificates create ...`).

Con estos scripts puedes repetir el deployment desde la CLI en minutos y sin depender de la UI de
Google Cloud.
