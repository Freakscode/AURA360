# Supabase Database - Guía de Configuración para Producción

**AURA360 - Deployment Guide**

---

## 📊 Resumen

AURA360 usa **Supabase PostgreSQL** como base de datos principal con una arquitectura híbrida:
- **Supabase Auth**: Maneja autenticación de usuarios (tablas en schema `auth`)
- **Django ORM**: Maneja tablas de aplicación (schema `public`)

---

## 🗄️ Arquitectura de Database

### **Schema Organization**

```
Supabase Database (PostgreSQL 15)
├── auth.* (Supabase-managed)
│   ├── users             ← Supabase Auth users
│   ├── sessions          ← JWT sessions
│   └── refresh_tokens    ← Auth tokens
│
└── public.* (Django-managed)
    ├── app_users                      ← Perfil extendido (managed=False)
    ├── mood_entries                   ← Mind module
    ├── user_context_snapshots         ← User context system
    ├── user_profile_extended          ← IKIGAI + psychosocial
    ├── body_activities                ← Body module
    ├── nutrition_logs                 ← Nutrition tracking
    ├── sleep_logs                     ← Sleep tracking
    └── nutrition_plans                ← PDF nutrition plans
```

### **Tabla Crítica: app_users**

```python
# services/api/users/models.py
class AppUser(models.Model):
    id = models.UUIDField(primary_key=True)
    email = models.EmailField()
    full_name = models.CharField()
    # ...

    class Meta:
        managed = False  # ← IMPORTANTE: Django NO crea esta tabla
        db_table = 'app_users'
```

**Por qué `managed=False`**:
- Tabla existe en Supabase (creada via SQL migrations)
- Django solo la LEE, no la modifica
- Schema changes van via Supabase Dashboard → SQL Editor

---

## 🔧 Configuración para Producción

### **1. Obtener Connection String**

#### Paso 1: Ir a Supabase Dashboard
```
https://supabase.com/dashboard/project/<your-project-id>
```

#### Paso 2: Settings → Database

Verás 2 connection strings:

**A) Connection Pooling (Supavisor)** ✅ **USAR ESTE**
```
Host: aws-0-us-east-1.pooler.supabase.com
Database: postgres
Port: 6543
User: postgres.[project-ref]
Password: [your-password]

Connection string:
postgresql://postgres.[project-ref]:[password]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

**B) Direct Connection** ❌ **NO USAR en Railway**
```
Host: db.[project-ref].supabase.co
Port: 5432
```

#### Paso 3: Reset Password (si es necesario)
```
Settings → Database → Database Password → Reset
```

**⚠️ IMPORTANTE**: Guarda el password inmediatamente (no se puede recuperar después).

---

### **2. Configurar Railway Variables**

Tienes 2 opciones:

#### **Opción A: Variables Separadas** (actual)
```bash
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
DB_USER=postgres.abcdefghijklmnop
DB_PASSWORD=<your-password>
DB_HOST=aws-0-us-east-1.pooler.supabase.com
DB_PORT=6543
CONN_MAX_AGE=600
```

#### **Opción B: Single DATABASE_URL** (recomendado)
```bash
DATABASE_URL=postgresql://postgres.[ref]:<password>@aws-0-us-east-1.pooler.supabase.com:6543/postgres
CONN_MAX_AGE=600
```

**Para Opción B**, actualizar `settings.py`:
```python
# Agregar esta dependencia a pyproject.toml:
# "dj-database-url>=2.1.0"

import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=int(config('CONN_MAX_AGE', default=600)),
        conn_health_checks=True,
    )
}
```

**Recomendación**: Usar Opción A por ahora (ya configurado), migrar a Opción B después si prefieres.

---

### **3. Verificar Tables en Supabase**

#### SQL Query para verificar:
```sql
-- En Supabase SQL Editor
SELECT
    table_schema,
    table_name,
    pg_size_pretty(pg_total_relation_size(quote_ident(table_schema) || '.' || quote_ident(table_name))) AS size
FROM information_schema.tables
WHERE table_schema IN ('public', 'auth')
ORDER BY table_schema, table_name;
```

**Expected Output**:
```
auth     | users                      | 128 kB
public   | app_users                  | 64 kB
public   | mood_entries               | 32 kB
public   | user_context_snapshots     | 16 kB
... etc
```

#### Si faltan tablas Django:
```bash
# Ejecutar migraciones localmente PRIMERO (para validar)
cd services/api
uv run python manage.py migrate --database default

# Luego Railway las ejecutará automáticamente en deploy
```

### 4. Provisionar Usuarios de Prueba

Para evitar violaciones de FK cuando registres actividades o snapshots, crea usuarios reales en Supabase usando el nuevo comando:

```bash
# Desde la raíz del repo
cd services/api
uv run python manage.py bootstrap_supabase_user \
  --email paciente.demo+1@aura360.dev \
  --full-name "Paciente Demo" \
  --role Paciente
```

El comando invoca la Admin API de Supabase (requiere `SUPABASE_SERVICE_ROLE_KEY`) y sincroniza `app_users`. El password generado se imprime al final.

### 5. Auditoría RLS

Verifica qué tablas tienen Row Level Security activo y qué políticas están publicadas:

```bash
cd services/api
uv run python manage.py check_rls --tables body_activities body_nutrition_logs user_context_snapshots
```

Úsalo antes/después de cambios para confirmar que las políticas cumplen con el modelo multi-tenant.

---

## 🔐 Security Configuration

### **1. Row Level Security (RLS)**

**⚠️ IMPORTANTE**: Verificar RLS en tablas Django

```sql
-- Ver políticas RLS actuales
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies
WHERE schemaname = 'public';
```

**Para tablas Django** (mood_entries, body_activities, etc.):

#### Opción A: Disable RLS (más simple)
```sql
ALTER TABLE public.mood_entries DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_context_snapshots DISABLE ROW LEVEL SECURITY;
-- Repetir para cada tabla Django
```

**Cuándo usar**: Django API maneja autorización (DRF permissions)

#### Opción B: Enable RLS con Service Role bypass
```sql
ALTER TABLE public.mood_entries ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role bypass" ON public.mood_entries
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
```

**Cuándo usar**: Quieres RLS para acceso directo (PostgREST API) pero bypass desde Django.

**Recomendación**: Usar **Opción A** (disable RLS) para simplicidad.

---

### **2. Database Roles**

**Service Role** (Django usa este):
```sql
-- Verificar permisos
SELECT grantee, privilege_type
FROM information_schema.role_table_grants
WHERE grantee = 'service_role' AND table_schema = 'public';
```

**Expected**: `service_role` tiene `ALL PRIVILEGES` en schema `public`.

---

## 🚀 Migration Strategy

### **Django Migrations**

**QUÉ se migra automáticamente** (en Railway deploy):
```bash
# Start Command en Railway:
python manage.py migrate --noinput && gunicorn ...

# Ejecuta:
users.0001_initial
users.0002_...
body.0001_initial
body.0002_alter_table_names
holistic.0001_initial
holistic.0002_userprofileextended_moodentry_usercontextsnapshot
```

**QUÉ NO se migra** (managed=False):
- `app_users` table (Supabase-managed)
- Schema `auth.*` (Supabase Auth)

### **Supabase Migrations**

Para cambios en `app_users` o `auth.*`:

```sql
-- En Supabase SQL Editor
ALTER TABLE public.app_users ADD COLUMN IF NOT EXISTS new_field TEXT;
```

**O vía Supabase CLI** (avanzado):
```bash
supabase migration new add_field_to_app_users
# Editar SQL file generado
supabase db push
```

---

## 📊 Connection Pooling Details

### **Por qué usar Supavisor (port 6543)**

**Problema sin pooler**:
```
Railway → 10 containers × 2 workers = 20 connections
Supabase Free: Max 100 connections
Con múltiples services: Fácilmente excedes límite
```

**Con pooler**:
```
Railway → 20 connections → Supavisor → 5 connections reales a Postgres
Supavisor maneja pool interno
Django CONN_MAX_AGE reutiliza conexiones
```

### **Connection Limits por Plan**

| Supabase Plan | Direct Connections | Pooler Connections |
|---------------|-------------------|--------------------|
| Free          | 60                | 200                |
| Pro           | 120               | 400                |
| Team          | 240               | 800                |

**Recomendación**: Usar **Pooler** siempre (puerto 6543).

---

## ✅ Pre-Deployment Checklist

### **Verificar antes de deployar**:

- [ ] **Connection String obtenida** (con pooler port 6543)
- [ ] **Password guardada** en password manager
- [ ] **Tablas verificadas**:
  ```sql
  SELECT COUNT(*) FROM app_users;  -- Debe funcionar
  SELECT COUNT(*) FROM auth.users; -- Debe funcionar
  ```
- [ ] **RLS configurada** (disabled o service_role bypass)
- [ ] **Migrations ejecutadas localmente** (sin errores)
- [ ] **Service Role permissions OK**:
  ```sql
  SELECT has_table_privilege('service_role', 'public.mood_entries', 'INSERT');
  -- Esperado: true
  ```

---

## 🐛 Troubleshooting

### **Error: "remaining connection slots reserved"**

**Causa**: Excediste connection limit
**Solución**:
1. Verificar estás usando **puerto 6543** (pooler)
2. Verificar `CONN_MAX_AGE=600` está configurado
3. Reducir Railway workers: `WEB_CONCURRENCY=2` (no más de 4)

---

### **Error: "permission denied for schema public"**

**Causa**: `service_role` no tiene permisos
**Solución**:
```sql
GRANT ALL ON SCHEMA public TO service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO service_role;
```

---

### **Error: "relation app_users does not exist"**

**Causa**: Tabla no existe en Supabase
**Solución**: Crear tabla via SQL Editor:
```sql
CREATE TABLE IF NOT EXISTS public.app_users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    phone_number TEXT,
    timezone TEXT DEFAULT 'UTC',
    locale TEXT DEFAULT 'es-CO',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index para performance
CREATE INDEX IF NOT EXISTS idx_app_users_email ON public.app_users(email);

-- Trigger para updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_app_users_updated_at
    BEFORE UPDATE ON public.app_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

### **Error: "row-level security policy violation"**

**Causa**: RLS está habilitada y bloqueando Django
**Solución**: Disable RLS o agregar policy para service_role (ver sección Security).

---

## 📊 Monitoring

### **Supabase Dashboard**

**Database → Connection Pooler**:
- Active connections
- Connection pool usage
- Query performance

**Database → Logs**:
- Slow queries
- Connection errors
- Schema changes

**Database → Reports**:
- Database size
- Query statistics
- Table sizes

---

## 🔄 Backup Strategy

**Supabase maneja backups automáticamente**:

| Plan  | Point-in-Time Recovery | Manual Backups |
|-------|------------------------|----------------|
| Free  | 7 días                 | No             |
| Pro   | 7 días                 | Ilimitados     |
| Team  | 14 días                | Ilimitados     |

**Backup manual (opcional)**:
```bash
# Via Supabase CLI
supabase db dump > backup.sql

# Via pg_dump
pg_dump -h aws-0-us-east-1.pooler.supabase.com \
        -U postgres.[ref] \
        -p 6543 \
        -d postgres \
        > backup_$(date +%Y%m%d).sql
```

---

## 🚀 Production Checklist

**Antes de deploy a Railway**:
- [ ] Connection string obtenida (pooler port 6543)
- [ ] Variables configuradas en Railway
- [ ] Migrations tested localmente
- [ ] RLS configurada correctamente
- [ ] Service role permissions verificados
- [ ] Backup manual creado (opcional)

**Después de deploy**:
- [ ] Verificar migraciones se ejecutaron: `railway logs --service api | grep migrate`
- [ ] Test health check: `curl https://api.railway.app/api/v1/health`
- [ ] Verificar conexión DB: `railway run python manage.py dbshell`
- [ ] Monitor connection pooler en Supabase Dashboard

---

## 📞 Support

- **Supabase Docs**: https://supabase.com/docs/guides/database
- **Connection Pooling**: https://supabase.com/docs/guides/database/connection-pooling
- **Migrations**: https://supabase.com/docs/guides/cli/local-development#database-migrations

---

**Última actualización**: 2025-11-05
