# AURA360 - Guía de Credenciales

Esta guía te ayuda a entender y configurar todas las credenciales necesarias para desplegar AURA360 en Azure.

## Resumen Rápido

Para desplegar AURA360 necesitas:

1. **Supabase Credentials** (4 valores)
   - URL del proyecto
   - Service Role Key
   - JWT Secret
   - Anon Key

2. **Google API Key** (1 valor)
   - API Key con acceso a Generative Language API

## Credenciales Actuales (Desarrollo Local)

Tu proyecto ya tiene credenciales configuradas para **desarrollo local**:

### 🔴 Supabase Local
```bash
URL:              http://127.0.0.1:54321
Service Role Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU
JWT Secret:       c6e7921692a6f3ddcc754210b46d706670c19e38ff275d88c3396f53fa18f166
Anon Key:         sb_publishable_ACJWlzQHlZjBrEguHvfOxg_3BJgxAaH
```

**⚠️ IMPORTANTE**: Estas credenciales son solo para Supabase LOCAL (corriendo en tu máquina). NO funcionan en la nube.

### Google API Key
```bash
API Key: AIzaSyDurj7hebJLQkLqhqcDikRbg17QK1qsW64
```

Esta key ya está en tu archivo `.env` y puede usarse en Azure si:
- Tiene los permisos necesarios habilitados
- No tiene restricciones de IP/dominio que bloqueen Azure

## Opción 1: Testing Rápido (Supabase Local)

**Para testing inicial**, puedes usar las credenciales locales que ya tienes:

```bash
# Script automático
cd infra/azure/helm
./configure-secrets.sh
# Selecciona "s" cuando pregunte si quieres usar credenciales locales
```

**⚠️ Limitaciones**:
- La URL `http://127.0.0.1:54321` NO funcionará desde AKS
- Solo útil para verificar que el despliegue funciona
- Deberás cambiar a Supabase en la nube para funcionalidad real

## Opción 2: Producción (Supabase en la Nube)

### 1. Crear/Configurar Proyecto en Supabase Cloud

#### Si NO tienes un proyecto Supabase en la nube:

1. **Ir a Supabase Dashboard**
   ```
   https://supabase.com/dashboard
   ```

2. **Crear Nuevo Proyecto**
   - Click en "New Project"
   - Nombre: `aura360-prod` (o el que prefieras)
   - Database Password: Guarda esto en lugar seguro
   - Region: Selecciona la más cercana (ej: East US)
   - Pricing: Free tier funciona para testing

3. **Esperar a que se cree** (~2 minutos)

#### Si YA tienes un proyecto Supabase:

1. **Abrir tu proyecto**
   ```
   https://supabase.com/dashboard/project/[tu-project-id]
   ```

### 2. Obtener Credenciales de Supabase

Una vez que tengas el proyecto creado:

1. **Ir a Settings → API**
   ```
   https://supabase.com/dashboard/project/[tu-project-id]/settings/api
   ```

2. **Copiar los siguientes valores**:

   **URL del Proyecto**
   ```
   Sección: Configuration
   Campo: URL
   Ejemplo: https://xxxyyyzzzz.supabase.co
   ```

   **Service Role Key (Secret)**
   ```
   Sección: Project API keys
   Campo: service_role (secret)
   Icono: 🔒 (click para ver)
   Ejemplo: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

   ⚠️  Esta key tiene permisos de ADMIN - mantenla segura
   ```

   **Anon Key (Public)**
   ```
   Sección: Project API keys
   Campo: anon (public)
   Ejemplo: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

   ℹ️  Esta key es segura compartir en frontend
   ```

   **JWT Secret**
   ```
   Sección: JWT Settings
   Campo: JWT Secret
   Ejemplo: una cadena alfanumérica larga

   ⚠️  Este secreto valida los tokens - mantenlo seguro
   ```

### 3. Migrar Schema a Supabase Cloud

Si ya tienes migraciones en `apps/mobile/supabase/migrations/`:

```bash
# Desde apps/mobile/supabase/
cd apps/mobile/supabase

# Link al proyecto remoto
supabase link --project-ref [tu-project-id]

# Aplicar migraciones
supabase db push
```

### 4. Obtener Google API Key

#### Si ya tienes una (verificar permisos):

Tu key actual: `AIzaSyDurj7hebJLQkLqhqcDikRbg17QK1qsW64`

**Verificar que tenga habilitado**:
1. Ir a: https://console.cloud.google.com/apis/library
2. Buscar y habilitar:
   - ✅ **Generative Language API** (Gemini)
   - ✅ **Vertex AI API** (opcional, para modelos avanzados)

**Verificar restricciones**:
1. Ir a: https://console.cloud.google.com/apis/credentials
2. Click en tu API Key
3. En "Application restrictions":
   - ✅ Recomendado: "HTTP referrers" → Agregar dominios de Azure
   - ⚠️ O "None" para testing (menos seguro)

#### Si necesitas crear una nueva:

1. **Ir a Google Cloud Console**
   ```
   https://console.cloud.google.com/apis/credentials
   ```

2. **Crear Proyecto** (si no tienes uno)
   - Click en el dropdown de proyectos (arriba)
   - "New Project"
   - Nombre: `aura360-prod`

3. **Habilitar APIs**
   - Ir a: https://console.cloud.google.com/apis/library
   - Buscar: "Generative Language API"
   - Click "Enable"
   - Repetir para "Vertex AI API" (opcional)

4. **Crear API Key**
   - Ir a: https://console.cloud.google.com/apis/credentials
   - Click "+ CREATE CREDENTIALS"
   - Seleccionar "API key"
   - Copiar la key generada
   - (Opcional) Restringir a APIs específicas

## Configurar Secrets en AKS

### Método 1: Script Automático (Recomendado)

```bash
cd infra/azure/helm
./configure-secrets.sh
```

El script te guiará paso a paso para:
1. Elegir entre credenciales locales o de producción
2. Ingresar cada credencial con validación
3. Confirmar antes de crear los secrets
4. Verificar que se crearon correctamente

### Método 2: Manual con kubectl

```bash
# Conectar a AKS
az aks get-credentials \
  --resource-group aura360-prod-rg \
  --name aura360-prod-aks

# Crear namespace
kubectl create namespace aura360

# Crear secret de Supabase
kubectl create secret generic supabase-credentials \
  --namespace aura360 \
  --from-literal=url='https://xxxyyyzzzz.supabase.co' \
  --from-literal=service_role_key='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  --from-literal=jwt_secret='tu-jwt-secret-aqui' \
  --from-literal=anon_key='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'

# Crear secret de Google API
kubectl create secret generic google-api-credentials \
  --namespace aura360 \
  --from-literal=api_key='AIzaSy...'
```

## Verificar Secrets

```bash
# Listar secrets
kubectl get secrets -n aura360

# Ver estructura del secret (valores en base64)
kubectl get secret supabase-credentials -n aura360 -o yaml

# Decodificar un valor específico
kubectl get secret supabase-credentials -n aura360 \
  -o jsonpath='{.data.url}' | base64 -d && echo

# Decodificar todos los valores
kubectl get secret supabase-credentials -n aura360 -o json | \
  jq -r '.data | to_entries | .[] | "\(.key): \(.value | @base64d)"'
```

## Actualizar Secrets

Si necesitas cambiar alguna credencial:

```bash
# Opción 1: Eliminar y recrear
kubectl delete secret supabase-credentials -n aura360
kubectl create secret generic supabase-credentials \
  --namespace aura360 \
  --from-literal=url='nueva-url' \
  --from-literal=service_role_key='nueva-key' \
  --from-literal=jwt_secret='nuevo-secret' \
  --from-literal=anon_key='nueva-anon-key'

# Opción 2: Editar directamente (valores en base64)
kubectl edit secret supabase-credentials -n aura360

# Opción 3: Patch individual
kubectl patch secret supabase-credentials -n aura360 \
  --type='json' \
  -p='[{"op":"replace","path":"/data/url","value":"'$(echo -n 'nueva-url' | base64)'"}]'
```

**⚠️ IMPORTANTE**: Después de actualizar secrets, reinicia los pods:

```bash
# Reiniciar deployment específico
kubectl rollout restart deployment/api -n aura360

# Reiniciar todos
kubectl rollout restart deployment -n aura360
```

## Troubleshooting

### Error: "Invalid JWT"
- ✅ Verifica que el `JWT_SECRET` sea exactamente el mismo que en Supabase
- ✅ Asegúrate de no tener espacios extra al copiar/pegar

### Error: "Connection refused"
- ✅ Verifica que la `URL` sea la correcta (https, no http para cloud)
- ✅ Asegúrate de incluir el protocolo completo

### Error: "Unauthorized"
- ✅ Verifica que el `SERVICE_ROLE_KEY` sea el correcto
- ✅ Confirma que no haya expirado (las keys de Supabase no expiran, pero pueden ser rotadas)

### Error: "API key not valid"
- ✅ Verifica que la Google API Key esté habilitada
- ✅ Confirma que las APIs necesarias estén activas en el proyecto
- ✅ Revisa las restricciones de la key

### Secrets no se aplican a los pods
```bash
# Los secrets solo se leen al iniciar el pod
# Reinicia después de cambiar secrets:
kubectl rollout restart deployment -n aura360
```

## Seguridad - Mejores Prácticas

### ✅ DO (Hacer):
- Usar diferentes credenciales para dev/staging/prod
- Rotar secrets periódicamente
- Usar Azure Key Vault para gestión centralizada (avanzado)
- Limitar permisos de la Google API Key
- Habilitar Row Level Security (RLS) en Supabase

### ❌ DON'T (No Hacer):
- Commitear secrets a git
- Compartir secrets en canales inseguros
- Usar las mismas credenciales en múltiples ambientes
- Darle el SERVICE_ROLE_KEY al frontend
- Deshabilitar restricciones de API keys en producción

## Próximos Pasos

Una vez configurados los secrets:

1. **Desplegar AURA360**:
   ```bash
   cd infra/azure/helm
   ./deploy.sh dev
   ```

2. **Verificar conectividad**:
   ```bash
   # Ver logs del API
   kubectl logs -n aura360 -l app.kubernetes.io/component=api --tail=50

   # Buscar errores de conexión
   kubectl logs -n aura360 -l app.kubernetes.io/component=api | grep -i "error\|supabase"
   ```

3. **Probar endpoints**:
   ```bash
   # Health check del API
   curl http://<EXTERNAL-IP>/api/v1/health

   # Debe retornar: {"status": "healthy"}
   ```

## Referencias

- **Supabase Docs**: https://supabase.com/docs/guides/api
- **Google Cloud Credentials**: https://cloud.google.com/docs/authentication/api-keys
- **Kubernetes Secrets**: https://kubernetes.io/docs/concepts/configuration/secret/
- **Azure Key Vault Integration**: https://azure.github.io/secrets-store-csi-driver-provider-azure/

## Soporte

Si tienes problemas configurando las credenciales:
1. Revisa esta guía completa
2. Ejecuta el script `./configure-secrets.sh` para validación
3. Verifica los logs de los pods
4. Consulta el archivo `DEPLOYMENT_GUIDE.md` para troubleshooting general
