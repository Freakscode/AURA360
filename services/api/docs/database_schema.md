# Esquema de Base de Datos - AURA365 Mobile

Este documento detalla todas las estructuras de datos definidas en el entorno local de Supabase para AURA365 Mobile, incluyendo tablas, triggers, funciones, vistas y políticas RLS.

---

## Índice

1. [Tablas](#tablas)
   - [app_users](#app_users)
2. [Vistas](#vistas)
   - [vw_app_users](#vw_app_users)
3. [Funciones y Triggers](#funciones-y-triggers)
   - [set_current_timestamp_updated_at](#set_current_timestamp_updated_at)
   - [sync_app_user_profile](#sync_app_user_profile)
4. [Row-Level Security (RLS)](#row-level-security-rls)
5. [Entidades de Dominio (Dart)](#entidades-de-dominio-dart)
6. [Flujo de Sincronización](#flujo-de-sincronización)
7. [Migraciones Aplicadas](#migraciones-aplicadas)

---

## Tablas

### app_users

**Tabla**: `public.app_users`

**Propósito**: Almacena los perfiles de usuario de la aplicación, sincronizados automáticamente con `auth.users` de Supabase. Esta tabla actúa como una capa de aplicación que extiende los datos de autenticación básicos con información específica del dominio.

**Clave Primaria**: `id` (bigserial)

**Clave Natural**: `auth_user_id` (FK → `auth.users.id`)

#### Columnas

| Columna | Tipo | Requerido | Default | Restricciones | Descripción |
|---------|------|-----------|---------|---------------|-------------|
| `id` | `bigserial` | Sí | Auto-increment | PK | Clave sustituta para joins internos |
| `auth_user_id` | `uuid` | Sí | - | UNIQUE, FK | Vincula con `auth.users.id` para autenticación |
| `full_name` | `text` | Sí | - | - | Nombre completo legal mostrado en la app |
| `age` | `integer` | Sí | `0` | `age >= 0` | Edad en años, debe ser no negativa |
| `email` | `text` | Sí | - | UNIQUE (case-insensitive) | Email principal de contacto |
| `phone_number` | `text` | No | `NULL` | - | Teléfono de contacto opcional (formato E.164 preferido) |
| `gender` | `text` | No | `NULL` | - | Descriptor de género auto-identificado (texto libre) |
| `tier` | `text` | Sí | `'free'` | `IN ('free', 'premium')` | Plan de membresía del usuario |
| `role_global` | `text` | Sí | `'General'` | `IN ('AdminSistema','AdminInstitucion','AdminInstitucionSalud','ProfesionalSalud','Paciente','Institucion','General')` | Rol primario del usuario dentro del ecosistema AURA365 |
| `is_independent` | `boolean` | Sí | `false` | - | `true` cuando el usuario opera fuera de instituciones (B2C) |
| `billing_plan` | `text` | Sí | `'individual'` | `IN ('individual','institution','corporate','b2b2c','trial')` | Código del plan comercial asignado |
| `created_at` | `timestamptz` | Sí | `timezone('utc', now())` | - | Timestamp de creación del registro |
| `updated_at` | `timestamptz` | Sí | `timezone('utc', now())` | - | Timestamp de última actualización |

#### Índices

```sql
-- Índice único para email (case-insensitive)
CREATE UNIQUE INDEX app_users_email_key 
  ON public.app_users (lower(email));

-- Índice único para auth_user_id
CREATE UNIQUE INDEX app_users_auth_user_id_key 
  ON public.app_users (auth_user_id);

CREATE INDEX app_users_role_global_idx
  ON public.app_users (role_global);

CREATE INDEX app_users_billing_plan_idx
  ON public.app_users (billing_plan);
```

#### Restricciones de Integridad

```sql
-- Edad no negativa
ALTER TABLE public.app_users 
  ADD CHECK (age >= 0);

-- Tier limitado a valores enumerados (plan actual)
ALTER TABLE public.app_users 
  ADD CONSTRAINT app_users_tier_check 
  CHECK (tier IN ('free', 'premium'));

ALTER TABLE public.app_users
  ADD CONSTRAINT app_users_role_global_check
  CHECK (role_global IN (
    'AdminSistema',
    'AdminInstitucion',
    'AdminInstitucionSalud',
    'ProfesionalSalud',
    'Paciente',
    'Institucion',
    'General'
  ));

ALTER TABLE public.app_users
  ADD CONSTRAINT app_users_billing_plan_check
  CHECK (billing_plan IN (
    'individual',
    'institution',
    'corporate',
    'b2b2c',
    'trial'
  ));
```

#### Comentarios de Columnas

Los comentarios de columna están documentados en la migración para facilitar la comprensión del esquema:

- `full_name`: "Full legal name displayed across the app."
- `age`: "Age in years; must be >= 0."
- `email`: "Primary contact email. Must be unique."
- `phone_number`: "Optional phone contact."
- `gender`: "Optional self-identified gender descriptor."
- `auth_user_id`: "Foreign key to auth.users.id for login linkage."
- `tier`: "Membership plan for the user (free o premium)."
- `role_global`: "Rol primario a nivel sistema utilizado para accesos rápidos."
- `is_independent`: "Identifica si el usuario opera fuera de instituciones (modelo B2C)."
- `billing_plan`: "Código del plan comercial asignado (individual, corporate, etc.)."

---

## Vistas

### vw_app_users

**Vista**: `public.vw_app_users`

**Propósito**: Proporciona una proyección de la tabla `app_users` donde el `auth_user_id` se expone como `id`, facilitando las consultas y joins desde la aplicación cuando se trabaja directamente con el ID de autenticación.

#### Definición

```sql
CREATE OR REPLACE VIEW public.vw_app_users AS
SELECT
  auth_user_id AS id,
  full_name,
  age,
  email,
  phone_number,
  gender,
  tier,
  role_global,
  is_independent,
  billing_plan,
  created_at,
  updated_at
FROM public.app_users;
```

#### Uso

Esta vista es útil cuando las consultas de la aplicación necesitan trabajar directamente con el UUID de autenticación como identificador principal, eliminando la necesidad de joins adicionales.

**Ejemplo de uso**:
```sql
-- Obtener usuario por su ID de auth
SELECT * FROM public.vw_app_users WHERE id = 'uuid-del-usuario';
```

---

## Funciones y Triggers

### set_current_timestamp_updated_at

**Función**: `public.set_current_timestamp_updated_at()`

**Tipo**: Trigger Function (PL/pgSQL)

**Propósito**: Actualiza automáticamente la columna `updated_at` con el timestamp actual en UTC cada vez que se modifica un registro.

#### Definición

```sql
CREATE OR REPLACE FUNCTION public.set_current_timestamp_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc', now());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

#### Trigger Asociado

```sql
CREATE TRIGGER set_app_users_updated_at
  BEFORE UPDATE ON public.app_users
  FOR EACH ROW
  EXECUTE PROCEDURE public.set_current_timestamp_updated_at();
```

**Comportamiento**: Se ejecuta **antes** de cada UPDATE en `app_users`, garantizando que `updated_at` siempre refleje la última modificación del registro.

---

### sync_app_user_profile

**Función**: `public.sync_app_user_profile()`

**Tipo**: Trigger Function (PL/pgSQL)

**Propósito**: Sincroniza automáticamente los datos de `auth.users` hacia `public.app_users`, creando o actualizando perfiles cuando cambian los datos de autenticación o metadata del usuario.

#### Definición Completa

```sql
CREATE OR REPLACE FUNCTION public.sync_app_user_profile()
RETURNS TRIGGER AS $$
DECLARE
  meta jsonb := NEW.raw_user_meta_data;
  full_name text := coalesce(meta ->> 'full_name', NEW.email, 'Unknown User');
  tier text := coalesce(meta ->> 'tier', 'free');
  raw_age text := meta ->> 'age';
  age_value integer;
  gender text := nullif(meta ->> 'gender', '');
  phone text := coalesce(nullif(NEW.phone, ''), nullif(meta ->> 'phone', ''));
BEGIN
  -- Parsear edad de manera segura
  BEGIN
    IF raw_age IS NOT NULL AND raw_age ~ '^\d+$' THEN
      age_value := raw_age::integer;
    END IF;
  EXCEPTION WHEN OTHERS THEN
    age_value := NULL;
  END;

  -- Validar tier
  IF tier NOT IN ('free', 'premium') THEN
    tier := 'free';
  END IF;

  -- Upsert en app_users
  INSERT INTO public.app_users (
    auth_user_id,
    email,
    full_name,
    age,
    phone_number,
    gender,
    tier
  ) VALUES (
    NEW.id,
    coalesce(NEW.email, ''),
    full_name,
    coalesce(age_value, 0),
    phone,
    gender,
    tier
  )
  ON CONFLICT (auth_user_id) DO UPDATE SET
    email = EXCLUDED.email,
    full_name = EXCLUDED.full_name,
    phone_number = EXCLUDED.phone_number,
    gender = EXCLUDED.gender,
    tier = EXCLUDED.tier,
    age = CASE
      WHEN EXCLUDED.age IS DISTINCT FROM public.app_users.age 
        AND EXCLUDED.age <> 0 
      THEN EXCLUDED.age
      ELSE public.app_users.age
    END,
    updated_at = timezone('utc', now());

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

#### Lógica de Sincronización

1. **Extracción de Metadata**: Lee `raw_user_meta_data` de `auth.users` para obtener:
   - `full_name`: Nombre completo (fallback: email o "Unknown User")
   - `tier`: Plan del usuario (fallback: 'free')
   - `age`: Edad (valida que sea numérico, fallback: 0)
   - `gender`: Género (nullable)
   - `phone`: Teléfono (prioriza `auth.users.phone` sobre metadata)

2. **Validación**:
   - La edad debe ser un entero válido o se establece como NULL
   - El tier debe ser 'free' o 'premium', de lo contrario se fuerza a 'free'
   - Los campos opcionales se limpian de strings vacíos a NULL

3. **Upsert**:
   - Si no existe registro con ese `auth_user_id`, lo crea
   - Si existe, actualiza todos los campos excepto `age` (que solo se actualiza si hay un valor nuevo válido y diferente de 0)

#### Triggers Asociados

```sql
-- Trigger para INSERT en auth.users
DROP TRIGGER IF EXISTS trg_sync_app_user_profile_insert ON auth.users;
CREATE TRIGGER trg_sync_app_user_profile_insert
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.sync_app_user_profile();

-- Trigger para UPDATE en auth.users
DROP TRIGGER IF EXISTS trg_sync_app_user_profile_update ON auth.users;
CREATE TRIGGER trg_sync_app_user_profile_update
  AFTER UPDATE ON auth.users
  FOR EACH ROW
  WHEN (
    NEW.email IS DISTINCT FROM OLD.email OR
    NEW.phone IS DISTINCT FROM OLD.phone OR
    coalesce(NEW.raw_user_meta_data, '{}'::jsonb) IS DISTINCT FROM 
      coalesce(OLD.raw_user_meta_data, '{}'::jsonb)
  )
  EXECUTE FUNCTION public.sync_app_user_profile();
```

**Comportamiento**:
- El trigger de INSERT se ejecuta **después** de cada nuevo registro en `auth.users`
- El trigger de UPDATE solo se ejecuta cuando cambian: email, phone o raw_user_meta_data
- Ambos garantizan que `app_users` esté siempre sincronizado con `auth.users`

#### Backfill Inicial

La migración incluye un script de backfill que crea perfiles para todos los usuarios existentes en `auth.users` que no tienen un registro correspondiente en `app_users`:

```sql
INSERT INTO public.app_users (
  auth_user_id,
  email,
  full_name,
  age,
  phone_number,
  gender,
  tier
)
SELECT
  u.id,
  coalesce(u.email, ''),
  coalesce(u.raw_user_meta_data ->> 'full_name', u.email, 'Unknown User'),
  coalesce(
    CASE
      WHEN (u.raw_user_meta_data ->> 'age') ~ '^\d+$'
        THEN (u.raw_user_meta_data ->> 'age')::integer
    END,
    0
  ),
  nullif(coalesce(u.phone, u.raw_user_meta_data ->> 'phone'), ''),
  nullif(u.raw_user_meta_data ->> 'gender', ''),
  CASE
    WHEN (u.raw_user_meta_data ->> 'tier') IN ('free', 'premium')
      THEN u.raw_user_meta_data ->> 'tier'
    ELSE 'free'
  END
FROM auth.users u
WHERE NOT EXISTS (
  SELECT 1 FROM public.app_users a WHERE a.auth_user_id = u.id
);
```

---

## Row-Level Security (RLS)

La tabla `app_users` tiene RLS habilitado para garantizar la seguridad de los datos.

### Políticas Activas

#### 1. Allow read for authenticated

```sql
CREATE POLICY "Allow read for authenticated" 
  ON public.app_users
  FOR SELECT
  TO authenticated
  USING (true);
```

**Alcance**: Cualquier usuario autenticado puede leer **todos** los registros de `app_users`.

**Consideración**: Esta es una política permisiva. Si necesitas restricciones más granulares (ej: que cada usuario solo vea su propio perfil), esta política debería modificarse.

#### 2. Allow insert for authenticated

```sql
CREATE POLICY "Allow insert for authenticated" 
  ON public.app_users
  FOR INSERT
  TO authenticated
  WITH CHECK (true);
```

**Alcance**: Cualquier usuario autenticado puede insertar registros en `app_users`.

**Nota**: En la práctica, los triggers de sincronización suelen manejar las inserciones, por lo que esta política raramente se invoca desde la aplicación cliente.

#### 3. Service role full access

```sql
CREATE POLICY "Service role full access" 
  ON public.app_users
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);
```

**Alcance**: El `service_role` de Supabase tiene acceso completo sin restricciones (SELECT, INSERT, UPDATE, DELETE).

**Uso**: Operaciones administrativas, migraciones y triggers del sistema.

### Consideraciones de Seguridad

- **READ**: Actualmente todos los usuarios autenticados pueden ver todos los perfiles. Evalúa si esto es apropiado para tu caso de uso.
- **WRITE**: No hay políticas explícitas para UPDATE o DELETE desde roles autenticados, lo que significa que estos están bloqueados por defecto.
- **Recomendación**: Considera añadir políticas para que los usuarios solo puedan actualizar su propio perfil:

```sql
-- Ejemplo de política más restrictiva (no aplicada actualmente)
CREATE POLICY "Users can update own profile" 
  ON public.app_users
  FOR UPDATE
  TO authenticated
  USING (auth_user_id = auth.uid())
  WITH CHECK (auth_user_id = auth.uid());
```

---

## Entidades de Dominio (Dart)

Las estructuras de base de datos se mapean a las siguientes entidades en el código Dart de la aplicación.

### AppUser

**Archivo**: `lib/features/user/domain/entities/app_user.dart`

```dart
class AppUser {
  final String id;           // Mapea a auth_user_id
  final String email;        // Mapea a email
  final UserTier tier;       // Mapea a tier (enum)
  final DateTime? createdAt; // Mapea a created_at

  const AppUser({
    required this.id,
    required this.email,
    required this.tier,
    this.createdAt,
  });

  // Helpers de conveniencia
  bool get isPremium => tier.isPremium;
  bool get isFree => tier.isFree;

  // Método copyWith para inmutabilidad
  AppUser copyWith({
    String? email, 
    UserTier? tier, 
    DateTime? createdAt
  }) {
    return AppUser(
      id: id,
      email: email ?? this.email,
      tier: tier ?? this.tier,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}
```

**Notas**:
- El `id` en Dart corresponde a `auth_user_id` en la base de datos
- Esta entidad es una versión simplificada; no incluye todos los campos de `app_users` (age, phone, gender, etc.)
- La entidad actual está optimizada para las necesidades de autenticación y control de acceso

### UserTier

**Archivo**: `lib/features/user/domain/entities/user_tier.dart`

```dart
enum UserTier { 
  free, 
  premium 
}

extension UserTierX on UserTier {
  // Parser desde string
  static UserTier parse(String raw) {
    switch (raw.toLowerCase()) {
      case 'premium':
        return UserTier.premium;
      case 'free':
      default:
        return UserTier.free;
    }
  }

  // Serialización a string
  String get label => switch (this) {
    UserTier.free => 'free',
    UserTier.premium => 'premium',
  };

  // Helpers de conveniencia
  bool get isPremium => this == UserTier.premium;
  bool get isFree => this == UserTier.free;
}
```

**Notas**:
- El enum coincide exactamente con los valores permitidos en la restricción CHECK de la base de datos
- El parser tiene un fallback seguro a `free` para valores inválidos

### AuthSession

**Archivo**: `lib/features/auth/domain/entities/auth_session.dart`

```dart
class AuthSession {
  final String accessToken;
  final String? refreshToken;
  final DateTime? expiresAt;
  final String userId;  // Corresponde a auth.users.id

  const AuthSession({
    required this.accessToken,
    this.refreshToken,
    this.expiresAt,
    required this.userId,
  });
}
```

**Notas**:
- Esta entidad representa la sesión de Supabase Auth
- `userId` corresponde a `auth.users.id`, que se vincula con `app_users.auth_user_id`
- Gestiona los tokens de acceso y renovación para mantener la sesión activa

---

## Flujo de Sincronización

### Diagrama de Flujo

```
┌─────────────────────────────────────────────────────────────────┐
│                      Usuario se registra                         │
│                    (Supabase Auth UI/API)                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   auth.users.INSERT   │
                │  (Supabase Auth)      │
                └───────────┬───────────┘
                            │
                            ▼
        ┌───────────────────────────────────────────┐
        │ trg_sync_app_user_profile_insert          │
        │ AFTER INSERT ON auth.users                │
        └───────────┬───────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────────────────────────┐
        │ public.sync_app_user_profile()            │
        │                                           │
        │ 1. Lee raw_user_meta_data                 │
        │ 2. Extrae: full_name, age, gender,        │
        │    phone, tier                            │
        │ 3. Valida y limpia datos                  │
        │ 4. INSERT ... ON CONFLICT DO UPDATE       │
        └───────────┬───────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────────────────────────┐
        │      public.app_users (UPSERTED)          │
        └───────────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────────────────────────┐
        │   App consulta via UserRemoteDataSource   │
        │   y obtiene perfil completo               │
        └───────────────────────────────────────────┘
```

### Proceso de Actualización

```
┌─────────────────────────────────────────────────────────────────┐
│       Usuario actualiza perfil (metadata)                       │
│       Supabase.auth.updateUser()                                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   auth.users.UPDATE   │
                │  (email/phone/meta)   │
                └───────────┬───────────┘
                            │
                            ▼
        ┌───────────────────────────────────────────┐
        │ trg_sync_app_user_profile_update          │
        │ AFTER UPDATE ON auth.users                │
        │ (solo si cambió email, phone o metadata)  │
        └───────────┬───────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────────────────────────┐
        │ public.sync_app_user_profile()            │
        │ (misma lógica de sincronización)          │
        └───────────┬───────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────────────────────────┐
        │  public.app_users (UPDATED)               │
        │  + trigger actualiza updated_at           │
        └───────────────────────────────────────────┘
```

### Puntos Clave del Flujo

1. **Automatización Total**: No se requiere intervención manual; los triggers gestionan toda la sincronización.

2. **Fuente de Verdad**: `auth.users` es la fuente de verdad. Los cambios siempre fluyen de auth → app_users.

3. **Metadata como Configuración**: La aplicación debe almacenar datos extendidos en `raw_user_meta_data` durante el registro:
   ```dart
   await supabase.auth.signUp(
     email: email,
     password: password,
     data: {
       'full_name': fullName,
       'age': age.toString(),
       'gender': gender,
       'tier': 'free',
     },
   );
   ```

4. **Protección de Edad**: La edad solo se actualiza si el nuevo valor es válido y diferente de 0, evitando sobrescribir edades reales con valores por defecto.

5. **Backfill Automático**: La migración garantiza que usuarios existentes reciban un perfil sin intervención manual.

---

## Migraciones Aplicadas

### Historial de Migraciones

| Timestamp | Archivo | Descripción |
|-----------|---------|-------------|
| `20250923173416` | `create_users_table.sql` | Creación inicial de la tabla `app_users` con columnas básicas (id, full_name, age, email, phone_number, gender, timestamps). Configura RLS y trigger para `updated_at`. |
| `20250923220023` | `add_user_tier_and_auth_id.sql` | Añade `auth_user_id` y `tier` a `app_users`. Establece `tier` como NOT NULL con default 'free' y constraint CHECK. Vincula registros existentes con `auth.users` por email. Crea vista `vw_app_users`. |
| `20250924043000` | `auto_sync_app_users.sql` | Implementa sincronización automática entre `auth.users` y `app_users` mediante la función `sync_app_user_profile()` y triggers en INSERT/UPDATE. Incluye backfill de usuarios existentes. |

### Cómo Aplicar Migraciones

#### Entorno Local

```bash
# Iniciar Supabase local
supabase start

# Aplicar todas las migraciones
supabase db push --local

# Ver estado de migraciones
supabase migration list --local
```

#### Entorno Remoto

```bash
# Vincular proyecto (solo primera vez)
supabase link --project-ref <tu-project-ref>

# Aplicar migraciones
supabase db push

# Verificar en el dashboard
supabase db remote status
```

### Crear Nueva Migración

```bash
# Crear archivo de migración
supabase migration new nombre_descriptivo

# Editar el archivo generado en supabase/migrations/
# Luego aplicar con db push
```

---

## Operaciones Comunes

### Consultar Usuario por Auth ID

```sql
-- Usando la tabla principal
SELECT * FROM public.app_users 
WHERE auth_user_id = '<uuid>';

-- Usando la vista
SELECT * FROM public.vw_app_users 
WHERE id = '<uuid>';
```

### Actualizar Tier de Usuario

```sql
-- Opción 1: Actualizar directamente en app_users
UPDATE public.app_users 
SET tier = 'premium' 
WHERE auth_user_id = '<uuid>';

-- Opción 2: Actualizar en auth.users metadata (recomendado)
-- Esto mantiene auth.users como fuente de verdad
UPDATE auth.users 
SET raw_user_meta_data = 
  jsonb_set(
    coalesce(raw_user_meta_data, '{}'::jsonb), 
    '{tier}', 
    '"premium"'
  )
WHERE id = '<uuid>';
-- El trigger sincronizará automáticamente a app_users
```

### Obtener Estadísticas de Usuarios

```sql
-- Contar usuarios por tier
SELECT tier, COUNT(*) as total
FROM public.app_users
GROUP BY tier;

-- Edad promedio por tier
SELECT tier, AVG(age) as edad_promedio
FROM public.app_users
WHERE age > 0
GROUP BY tier;

-- Usuarios sin teléfono
SELECT COUNT(*) as sin_telefono
FROM public.app_users
WHERE phone_number IS NULL;
```

### Forzar Re-sincronización

```sql
-- Útil si los datos se desincronizaron manualmente
-- Esto fuerza la ejecución del trigger para todos los usuarios
UPDATE auth.users 
SET raw_user_meta_data = coalesce(raw_user_meta_data, '{}'::jsonb)
WHERE id IN (
  SELECT auth_user_id FROM public.app_users
);
```

---

## Consideraciones Futuras

### Mejoras Sugeridas

1. **Validación Más Estricta de Gender**:
   - Actualmente es texto libre
   - Considerar un enum: `('male', 'female', 'non-binary', 'other', 'prefer-not-to-say')`

2. **Edad Nullable**:
   - Permitir `NULL` para casos donde la edad es desconocida o no proporcionada
   - Actualmente se fuerza a 0, lo cual puede ser confuso

3. **Auditoría de Cambios de Tier**:
   - Crear tabla `tier_history` para trackear cambios de plan
   - Útil para analytics y compliance

4. **Notificaciones de Cambio de Tier**:
   - Implementar un sistema de eventos (queue/task) para notificar a la app móvil cuando el tier cambia

5. **Soft Deletes**:
   - Añadir columna `deleted_at` para soft deletes
   - Modificar políticas RLS para excluir registros eliminados

6. **Testing Automatizado**:
   - Tests para triggers de sincronización
   - Tests para lógica de validación
   - Tests de integración con repositorios

7. **Perfil Completo en AppUser**:
   - Extender la entidad `AppUser` en Dart para incluir `full_name`, `age`, `phone`, `gender`
   - Actualmente solo expone `id`, `email`, `tier`, `createdAt`

8. **Políticas RLS Granulares**:
   - Implementar políticas que permitan a usuarios solo ver/editar su propio perfil
   - Roles de administrador para acceso completo

---

## Referencias

- **Documentación Oficial de Supabase**: https://supabase.com/docs
- **PostgreSQL Row Level Security**: https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- **PostgreSQL Triggers**: https://www.postgresql.org/docs/current/sql-createtrigger.html
- **Repositorio del Proyecto**: Consultar `AGENTS.md` para guías de desarrollo

---

## Notas de Versión

- **Versión 1.0**: Esquema inicial con tabla `app_users`, sincronización automática y RLS básico.
- **Última Actualización**: 2025-09-24
- **Compatibilidad**: Supabase CLI >= 1.0, PostgreSQL >= 14

---

## Contacto y Soporte

Para preguntas sobre el esquema o modificaciones necesarias, consulta:
- El directorio `docs/` para guías específicas
- `docs/database_state.md` para configuración de Supabase
- El código fuente en `lib/features/user/` para implementación de repositorios
