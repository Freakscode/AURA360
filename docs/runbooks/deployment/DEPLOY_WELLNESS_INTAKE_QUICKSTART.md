# 🚀 Despliegue Rápido del Formulario Wellness Intake

## Checklist Pre-Despliegue

- [ ] API Django desplegado en Cloud Run
- [ ] Credenciales de Supabase configuradas
- [ ] Variables de entorno del API configuradas (CORS permitiendo Cloud Storage)

## Pasos Rápidos

### 1. Obtener URL del API

```bash
gcloud run services describe aura360-api \
  --project aura-360-471711 \
  --region us-central1 \
  --format 'value(status.url)'
```

### 2. Actualizar environment.ts

Edita `apps/web/src/environments/environment.ts`:

```typescript
apiBaseUrl: 'https://TU_API_URL.run.app/api',  // Reemplaza TU_API_URL
supabase: {
  url: 'https://TU_PROJECT_REF.supabase.co',    // Reemplaza TU_PROJECT_REF
  anonKey: 'TU_ANON_KEY',                       // Reemplaza TU_ANON_KEY
}
```

### 3. Desplegar

```bash
./scripts/deploy_wellness_intake.sh
```

O manualmente:

```bash
export GCP_PROJECT="aura-360-471711"
export GCP_REGION="us-central1"
export WEB_BUCKET="aura360-web-prod"
./scripts/deploy_web_gcloud.sh
```

### 4. Verificar

El formulario estará en:
```
https://storage.googleapis.com/aura360-web-prod/index.html#/public/wellness-intake
```

## ⚠️ Importante: Configurar CORS en el API

Si el formulario no puede enviar datos, actualiza `.env.production` del API:

```
CORS_ALLOWED_ORIGINS=https://storage.googleapis.com
```

Luego re-despliega el API.

