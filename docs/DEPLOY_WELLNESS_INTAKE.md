# Despliegue del Formulario Wellness Intake

Esta guía explica cómo desplegar el formulario de wellness intake (encuesta holística) a Google Cloud Platform.

## 📋 Prerequisitos

1. **API Django desplegado** en Cloud Run
   - El formulario necesita el API para enviar las respuestas
   - Verifica que el endpoint `/api/holistic/intake-submissions/` esté disponible

2. **Credenciales de Supabase** configuradas
   - URL del proyecto
   - Anon key (clave pública)

3. **gcloud CLI** configurado y autenticado

## 🚀 Proceso de Despliegue

### Paso 1: Obtener URL del API

Primero, obtén la URL del API desplegado:

```bash
gcloud run services describe aura360-api \
  --project aura-360-471711 \
  --region us-central1 \
  --format 'value(status.url)'
```

Deberías obtener algo como: `https://aura360-api-xxxxx-uc.a.run.app`

### Paso 2: Configurar Variables de Entorno del Frontend

Edita `apps/web/src/environments/environment.ts`:

```typescript
export const environment: Aura360Environment = {
  production: true,
  // Reemplaza con la URL de tu API desplegado
  apiBaseUrl: 'https://aura360-api-xxxxx-uc.a.run.app/api',
  supabase: {
    // Reemplaza con tu URL de Supabase de producción
    url: 'https://TU_PROJECT_REF.supabase.co',
    // Reemplaza con tu anon key de Supabase
    anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
  },
};
```

**Obtener credenciales de Supabase:**
1. Ve a: https://app.supabase.com/project/YOUR_PROJECT/settings/api
2. Copia el "Project URL"
3. Copia el "anon/public" key (NO uses la service_role key)

### Paso 3: Desplegar el Frontend

#### Opción A: Script Automático (Recomendado)

```bash
./scripts/deploy_wellness_intake.sh
```

Este script:
- Detecta automáticamente la URL del API
- Actualiza la configuración temporalmente
- Despliega el frontend
- Restaura la configuración original

#### Opción B: Despliegue Manual

```bash
# Configurar variables
export GCP_PROJECT="aura-360-471711"
export GCP_REGION="us-central1"
export WEB_BUCKET="aura360-web-prod"

# Desplegar
./scripts/deploy_web_gcloud.sh
```

### Paso 4: Verificar el Despliegue

El formulario estará disponible en:

```
https://storage.googleapis.com/aura360-web-prod/index.html#/public/wellness-intake
```

**Nota importante:** Cloud Storage sirve archivos estáticos. Para que las rutas de Angular funcionen correctamente:

1. El bucket ya está configurado con `index.html` como página de error
2. Esto permite que Angular Router maneje las rutas del lado del cliente
3. La ruta completa del formulario es: `/public/wellness-intake`

## 🔍 Verificación Post-Despliegue

### 1. Verificar que el formulario carga

```bash
curl -I https://storage.googleapis.com/aura360-web-prod/index.html
```

Deberías recibir un `200 OK`.

### 2. Verificar que el API responde

```bash
# Obtener URL del API
API_URL=$(gcloud run services describe aura360-api \
  --project aura-360-471711 \
  --region us-central1 \
  --format 'value(status.url)')

# Verificar endpoint de intake
curl "${API_URL}/api/holistic/intake-submissions/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Probar el formulario completo

1. Abre el formulario en el navegador
2. Completa todas las secciones (Físico, Mental, Espiritual)
3. Envía el formulario
4. Verifica que se muestre el estado de procesamiento
5. Verifica en los logs del API que se recibió la submission

## 🐛 Troubleshooting

### Error: "API Base URL not configured"

**Causa:** El `apiBaseUrl` en `environment.ts` no está configurado correctamente.

**Solución:**
1. Verifica que la URL del API sea correcta
2. Asegúrate de incluir `/api` al final: `https://api-url.run.app/api`
3. Re-despliega el frontend

### Error: "CORS blocked"

**Causa:** El API no tiene configurado `CORS_ALLOWED_ORIGINS` para incluir Cloud Storage.

**Solución:**
1. Actualiza `.env.production` del API:
   ```
   CORS_ALLOWED_ORIGINS=https://storage.googleapis.com
   ```
2. Re-despliega el API:
   ```bash
   export API_ENV_FILE="services/api/.env.production"
   ./scripts/deploy_api_gcloud.sh
   ```

### Error: "Supabase not configured"

**Causa:** Las credenciales de Supabase en `environment.ts` son placeholders.

**Solución:**
1. Obtén las credenciales reales desde Supabase Dashboard
2. Actualiza `environment.ts`
3. Re-despliega el frontend

### El formulario no carga (404)

**Causa:** Cloud Storage no está configurado para servir rutas SPA.

**Solución:**
```bash
gcloud storage buckets update gs://aura360-web-prod \
  --web-main-page-suffix index.html \
  --web-error-page index.html
```

### El formulario carga pero no puede enviar datos

**Causa:** El API no está accesible o requiere autenticación.

**Solución:**
1. Verifica que el API esté desplegado y funcionando
2. Verifica que el endpoint `/api/holistic/intake-submissions/` permita POST sin autenticación (o con token)
3. Revisa los logs del API:
   ```bash
   gcloud run services logs read aura360-api \
     --project aura-360-471711 \
     --region us-central1 \
     --limit 50
   ```

## 📝 Notas Importantes

1. **Rutas públicas:** El formulario está en `/public/wellness-intake` y NO requiere autenticación
2. **CORS:** Asegúrate de que el API permita requests desde `storage.googleapis.com`
3. **Variables de entorno:** El `environment.ts` se compila en el bundle, así que actualízalo antes de hacer build
4. **Cache:** Cloud Storage tiene cache configurado. Si haces cambios, puede tomar unos minutos en reflejarse

## 🔄 Actualizar el Formulario

Para actualizar el formulario después de cambios:

```bash
# 1. Asegúrate de que environment.ts tenga la configuración correcta
# 2. Despliega
./scripts/deploy_wellness_intake.sh

# O manualmente:
./scripts/deploy_web_gcloud.sh
```

## 📚 Referencias

- [DEPLOYMENT_GCLOUD.md](../DEPLOYMENT_GCLOUD.md) - Documentación general de despliegue
- [PRODUCTION_ENV_SETUP.md](./runbooks/deployment/PRODUCTION_ENV_SETUP.md) - Configuración de variables de entorno
- [Wellness Intake Component](../../apps/web/src/app/features/public/wellness-intake/) - Código del formulario

