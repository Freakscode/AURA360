# Configuración de Variables de Entorno de Producción

Este documento te guiará paso a paso para configurar `services/api/.env.production` con tus credenciales reales.

## 📋 Tabla de Contenidos

1. [Django Secret Key](#1-django-secret-key)
2. [Supabase Credentials](#2-supabase-credentials)
3. [Kafka/Confluent Cloud](#3-kafkaconfluent-cloud)
4. [Post-Deploy: URLs de Servicios](#4-post-deploy-urls-de-servicios)
5. [Validación](#5-validación)

---

## 1. Django Secret Key

Genera una nueva SECRET_KEY segura para producción:

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

**Actualiza en `.env.production`:**
```bash
SECRET_KEY=<pega-el-valor-generado-aqui>
```

---

## 2. Supabase Credentials

### Paso 2.1: Acceder a tu proyecto de Supabase

1. Ve a https://app.supabase.com/projects
2. Selecciona tu proyecto de producción
3. Ve a **Settings** > **API**

### Paso 2.2: Obtener Project URL

En la sección **Project URL**, copia el valor:

```
https://abcdefghijklmnop.supabase.co
```

**Actualiza en `.env.production`:**
```bash
SUPABASE_URL=https://TU_PROJECT_REF.supabase.co
SUPABASE_JWKS_URL=https://TU_PROJECT_REF.supabase.co/auth/v1/.well-known/jwks.json
```

### Paso 2.3: Obtener API Keys

En la sección **Project API keys**, encontrarás dos keys:

#### a) **anon/public** (segura para exponer)
```bash
SUPABASE_PUBLISHABLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ey...
```

#### b) **service_role** (⚠️ SECRETA - NO EXPONER AL FRONTEND)
```bash
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ey...
```

### Paso 2.4: Obtener Database Credentials

1. Ve a **Settings** > **Database**
2. Scroll down a **Connection string** > **Connection pooling** (⚠️ Importante: usar pooling para Cloud Run)
3. Copia los valores:

```
Host: aws-0-us-east-1.pooler.supabase.com
Port: 6543
Database: postgres
User: postgres.abcdefghijklmnop
Password: [Click "Reset database password" si no la tienes]
```

**Actualiza en `.env.production`:**
```bash
DB_USER=postgres.TU_PROJECT_REF
DB_PASSWORD=TU_DB_PASSWORD
DB_HOST=aws-0-us-east-1.pooler.supabase.com  # O tu región
DB_PORT=6543
```

---

## 3. Kafka/Confluent Cloud

### Paso 3.1: Acceder a Confluent Cloud

1. Ve a https://confluent.cloud/environments
2. Selecciona tu environment (`aura360-production`)
3. Selecciona tu cluster (`aura360-kafka-prod`)

### Paso 3.2: Obtener Bootstrap Servers

1. En el dashboard del cluster, ve a **Cluster settings**
2. Copia **Bootstrap server**:

```
pkc-xxxxx.us-east-1.aws.confluent.cloud:9092
```

**Actualiza en `.env.production`:**
```bash
KAFKA_BOOTSTRAP_SERVERS=pkc-xxxxx.us-east-1.aws.confluent.cloud:9092
```

### Paso 3.3: Crear API Key

1. En el cluster, ve a **API Keys** (menú lateral)
2. Click en **Add key**
3. Selecciona **Cluster-specific**
4. Scope: **All topics** (o específico si prefieres)
5. **⚠️ IMPORTANTE**: Guarda inmediatamente el **API Secret**, no podrás verlo después

```
API Key: ABCD1234EFGH5678
API Secret: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Actualiza en `.env.production`:**
```bash
KAFKA_API_KEY=TU_API_KEY
KAFKA_API_SECRET=TU_API_SECRET
```

---

## 4. Post-Deploy: URLs de Servicios

Después de desplegar los servicios a Cloud Run, obtendrás URLs automáticas. Actualiza estas variables:

### Paso 4.1: Después del primer deploy del API

El script mostrará algo como:
```
https://aura360-api-abc123xyz-uc.a.run.app
```

**Actualiza en `.env.production`:**
```bash
ALLOWED_HOSTS=aura360-api-abc123xyz-uc.a.run.app
CORS_ALLOWED_ORIGINS=https://aura360-web-HASH-uc.a.run.app,https://storage.googleapis.com
```

### Paso 4.2: URLs de servicios externos

Después de desplegar vectordb y agents:

```bash
VECTOR_DB_BASE_URL=https://aura360-vectordb-HASH-uc.a.run.app
HOLISTIC_AGENT_SERVICE_URL=https://aura360-agents-HASH-uc.a.run.app/api/holistic/v1/run
```

---

## 5. Validación

Una vez completado el archivo `.env.production`, valídalo con:

```bash
./services/api/scripts/validate_production_env.sh services/api/.env.production
```

Si todo está correcto, procede al despliegue:

```bash
export API_ENV_FILE="services/api/.env.production"
export WORKER_ENV_FILE="services/api/.env.production"
./deploy_all_gcloud.sh
```

---

## 🔒 Seguridad

- ✅ **NUNCA** cometas `.env.production` a Git (ya está en `.gitignore`)
- ✅ Usa `.env.production` solo para Cloud Run
- ✅ Rota las credenciales periódicamente (cada 90 días)
- ✅ Usa diferentes proyectos de Supabase para dev/staging/prod
- ✅ Habilita Row Level Security (RLS) en Supabase

---

## ❓ Troubleshooting

### No tengo la password de la base de datos

1. Ve a Supabase > Settings > Database
2. Click en **Reset database password**
3. Guarda la nueva password en un gestor seguro (1Password, Bitwarden, etc.)

### No puedo encontrar el Bootstrap Server de Kafka

1. Asegúrate de haber creado un cluster en Confluent Cloud
2. Ve a Cluster > Settings > Cluster settings
3. El valor está bajo "Bootstrap server"

### Error: "JWKS URL not found"

Verifica que la URL sea exactamente:
```
https://TU_PROJECT_REF.supabase.co/auth/v1/.well-known/jwks.json
```

Prueba accediendo a la URL en el navegador, debe devolver un JSON con las keys públicas.

---

## 📞 Necesitas ayuda?

- **Supabase**: https://supabase.com/docs
- **Confluent Cloud**: https://docs.confluent.io/cloud/current/get-started/index.html
- **Cloud Run**: https://cloud.google.com/run/docs

---

**Última actualización**: 2025-01-13
