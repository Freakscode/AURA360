# Esquema del Módulo Body (Salud Física)

## Resumen

Este documento detalla el modelo de datos completo del módulo **Body**, que permite a los usuarios registrar y consultar información sobre:

- **Actividad Física**: Sesiones de ejercicio con tipo, duración e intensidad
- **Nutrición**: Registros de comidas con macronutrientes
- **Sueño**: Ciclos de descanso con calidad percibida

---

## Arquitectura de 3 Capas

### 1. Base de Datos (Supabase PostgreSQL)

**Tablas creadas**: `body_activities`, `body_nutrition_logs`, `body_sleep_logs`

**Migración**: `aura_mobile/supabase/migrations/20251028031900_create_body_tables.sql`

**Características**:
- UUIDs como primary keys
- Foreign keys a `auth.users(id)` con `ON DELETE CASCADE`
- Timestamps automáticos (`created_at`, `updated_at`)
- Row Level Security (RLS) habilitado
- Políticas que limitan acceso por `auth.uid()`
- Índices optimizados para queries por usuario y fecha

---

### 2. Backend (Django REST Framework)

**Modelos**: `BodyActivity`, `NutritionLog`, `SleepLog`

**Ubicación**: `backend/body/models.py`

**Configuración**:
```python
class Meta:
    managed = False  # Django NO gestiona migraciones
    db_table = 'body_activities'  # Nombre exacto en Supabase
```

**Endpoints API**:

| Ruta | Métodos | Descripción |
|------|---------|-------------|
| `/dashboard/body/dashboard/` | GET | Snapshot consolidado (activities + nutrition + sleep) |
| `/dashboard/body/activities/` | GET, POST, PATCH, DELETE | CRUD de actividades físicas |
| `/dashboard/body/nutrition/` | GET, POST, PATCH, DELETE | CRUD de registros nutricionales |
| `/dashboard/body/sleep/` | GET, POST, PATCH, DELETE | CRUD de registros de sueño |

**Seguridad**:
- Requiere token JWT de Supabase
- Filtra automáticamente por `auth_user_id` del usuario autenticado
- ViewSets usan `SupabaseJWTRequiredPermission`

---

### 3. App Mobile (Flutter)

**Entidades**: `ActivitySession`, `NutritionLogEntry`, `SleepLog`, `BodyDashboardSnapshot`

**Ubicación**: `aura_mobile/lib/features/body/domain/entities/`

**Repositorio**:
- **Interfaz**: `BodyRepository` (`domain/repositories/body_repository.dart`)
- **Implementaciones**:
  - `InMemoryBodyRepository` - Datos simulados para desarrollo
  - `HttpBodyRepository` - Conecta con backend Django

**Controller**: `BodyDashboardController` (Riverpod StateNotifier)

**Mapper**: `BodyApiMapper` convierte entre JSON del backend y entidades Dart

---

## Esquema de Tablas

### body_activities

| Columna | Tipo | Constraints | Descripción |
|---------|------|-------------|-------------|
| `id` | uuid | PK | Identificador único |
| `auth_user_id` | uuid | FK, NOT NULL, indexed | Usuario propietario |
| `activity_type` | text | CHECK (enum), NOT NULL | `cardio`, `strength`, `flexibility`, `mindfulness` |
| `intensity` | text | CHECK (enum), DEFAULT 'moderate' | `low`, `moderate`, `high` |
| `duration_minutes` | int | CHECK > 0, NOT NULL | Duración en minutos |
| `session_date` | date | DEFAULT CURRENT_DATE | Fecha de la sesión |
| `notes` | text | NULL | Notas opcionales |
| `created_at` | timestamptz | DEFAULT now() | Timestamp de creación |
| `updated_at` | timestamptz | DEFAULT now() | Timestamp de última actualización |

**Índices**:
- `idx_body_activities_user` ON (`auth_user_id`)
- `idx_body_activities_date` ON (`session_date` DESC)
- `idx_body_activities_type` ON (`activity_type`)

---

### body_nutrition_logs

| Columna | Tipo | Constraints | Descripción |
|---------|------|-------------|-------------|
| `id` | uuid | PK | Identificador único |
| `auth_user_id` | uuid | FK, NOT NULL, indexed | Usuario propietario |
| `meal_type` | text | CHECK (enum), NOT NULL | `breakfast`, `lunch`, `dinner`, `snack` |
| `timestamp` | timestamptz | DEFAULT now() | Fecha/hora de la comida |
| `items` | jsonb | DEFAULT '[]' | Array de alimentos |
| `calories` | int | CHECK >= 0, NULL | Calorías estimadas |
| `protein` | decimal(6,2) | CHECK >= 0, NULL | Proteínas (g) |
| `carbs` | decimal(6,2) | CHECK >= 0, NULL | Carbohidratos (g) |
| `fats` | decimal(6,2) | CHECK >= 0, NULL | Grasas (g) |
| `notes` | text | NULL | Notas opcionales |
| `created_at` | timestamptz | DEFAULT now() | Timestamp de creación |
| `updated_at` | timestamptz | DEFAULT now() | Timestamp de última actualización |

**Índices**:
- `idx_body_nutrition_user` ON (`auth_user_id`)
- `idx_body_nutrition_timestamp` ON (`timestamp` DESC)
- `idx_body_nutrition_meal_type` ON (`meal_type`)

---

### body_sleep_logs

| Columna | Tipo | Constraints | Descripción |
|---------|------|-------------|-------------|
| `id` | uuid | PK | Identificador único |
| `auth_user_id` | uuid | FK, NOT NULL, indexed | Usuario propietario |
| `bedtime` | timestamptz | NOT NULL | Hora de acostarse |
| `wake_time` | timestamptz | NOT NULL | Hora de despertar |
| `duration_hours` | decimal(4,1) | CHECK (> 0 AND <= 24), NOT NULL | Duración en horas |
| `quality` | text | CHECK (enum), DEFAULT 'good' | `poor`, `fair`, `good`, `excellent` |
| `notes` | text | NULL | Notas opcionales |
| `created_at` | timestamptz | DEFAULT now() | Timestamp de creación |
| `updated_at` | timestamptz | DEFAULT now() | Timestamp de última actualización |

**Índices**:
- `idx_body_sleep_user` ON (`auth_user_id`)
- `idx_body_sleep_wake_time` ON (`wake_time` DESC)
- `idx_body_sleep_bedtime` ON (`bedtime` DESC)

---

## Políticas RLS (Row Level Security)

Todas las tablas tienen las siguientes políticas:

### Para usuarios autenticados:
- **SELECT**: Solo sus propios registros (`auth_user_id = auth.uid()`)
- **INSERT**: Solo pueden crear registros con su propio `auth_user_id`
- **UPDATE**: Solo sus propios registros
- **DELETE**: Solo sus propios registros

### Para service_role:
- **ALL**: Acceso completo sin restricciones

---

## Mapeo de Campos entre Capas

### Actividad Física

| Flutter (Dart) | Django (Python) | Supabase (SQL) |
|----------------|-----------------|----------------|
| `id` | `id` | `id` |
| - | `auth_user_id` | `auth_user_id` |
| `type` (enum) | `activity_type` | `activity_type` |
| `intensity` (enum) | `intensity` | `intensity` |
| `durationMinutes` | `duration_minutes` | `duration_minutes` |
| `date` | `session_date` | `session_date` |
| `notes` | `notes` | `notes` |
| - | `created_at` | `created_at` |
| - | `updated_at` | `updated_at` |

**Enums**:
```dart
// Flutter
enum ActivityType { cardio, strength, flexibility, mindfulness }
enum ActivityIntensity { low, moderate, high }
```

```python
# Django
ActivityType = ['cardio', 'strength', 'flexibility', 'mindfulness']
ActivityIntensity = ['low', 'moderate', 'high']
```

---

### Nutrición

| Flutter (Dart) | Django (Python) | Supabase (SQL) |
|----------------|-----------------|----------------|
| `id` | `id` | `id` |
| - | `auth_user_id` | `auth_user_id` |
| `mealType` (enum) | `meal_type` | `meal_type` |
| `timestamp` | `timestamp` | `timestamp` |
| `items` (List<String>) | `items` (JSONField) | `items` (jsonb) |
| `calories` | `calories` | `calories` |
| `protein` | `protein` | `protein` |
| `carbs` | `carbs` | `carbs` |
| `fats` | `fats` | `fats` |
| `notes` | `notes` | `notes` |
| - | `created_at` | `created_at` |
| - | `updated_at` | `updated_at` |

**Enums**:
```dart
// Flutter
enum MealType { breakfast, lunch, dinner, snack }
```

```python
# Django
MealType = ['breakfast', 'lunch', 'dinner', 'snack']
```

---

### Sueño

| Flutter (Dart) | Django (Python) | Supabase (SQL) |
|----------------|-----------------|----------------|
| `id` | `id` | `id` |
| - | `auth_user_id` | `auth_user_id` |
| `bedtime` | `bedtime` | `bedtime` |
| `wakeTime` | `wake_time` | `wake_time` |
| `durationHours` | `duration_hours` | `duration_hours` |
| `quality` (enum) | `quality` | `quality` |
| `notes` | `notes` | `notes` |
| - | `created_at` | `created_at` |
| - | `updated_at` | `updated_at` |

**Enums**:
```dart
// Flutter
enum SleepQuality { poor, fair, good, excellent }
```

```python
# Django
SleepQuality = ['poor', 'fair', 'good', 'excellent']
```

---

## Flujo de Datos Completo

```
┌────────────────────────────────────────────────────────────────┐
│ 1. Usuario registra actividad (ExerciseRegisterPage)          │
└──────────────────────────┬─────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────────┐
              │ BodyDashboardController     │
              │   .addActivity()            │
              └──────────┬─────────────────┘
                         │
                         ▼
            ┌────────────────────────────────┐
            │  HttpBodyRepository             │
            │    .saveActivity()              │
            └──────────┬─────────────────────┘
                       │
                       ▼ POST /dashboard/body/activities/
            ┌────────────────────────────────┐
            │  Django BodyActivityViewSet     │
            │    .create()                    │
            │  - Valida JWT                   │
            │  - Extrae auth_user_id          │
            │  - Guarda en Supabase           │
            └──────────┬─────────────────────┘
                       │
                       ▼ INSERT INTO body_activities
            ┌────────────────────────────────┐
            │  Supabase PostgreSQL            │
            │  - RLS verifica auth_user_id    │
            │  - Trigger actualiza updated_at │
            │  - Retorna registro creado      │
            └──────────┬─────────────────────┘
                       │
                       ▼ Response 201 + JSON
            ┌────────────────────────────────┐
            │  Controller refresca dashboard  │
            │    .refresh()                   │
            └──────────┬─────────────────────┘
                       │
                       ▼ GET /dashboard/body/dashboard/
            ┌────────────────────────────────┐
            │  Backend devuelve snapshot      │
            │  (activities, nutrition, sleep) │
            └──────────┬─────────────────────┘
                       │
                       ▼
            ┌────────────────────────────────┐
            │  UI actualiza con nuevos datos │
            └────────────────────────────────┘
```

---

## Testing

### Backend (Django)

```bash
cd backend
uv run python manage.py test body
```

**Casos de prueba** (`body/tests/test_body_api.py`):
- Creación de actividades, comidas y sueño
- Carga de dashboard consolidado
- Validación de permisos por usuario

### Mobile (Flutter)

```bash
cd aura_mobile
flutter test test/features/body/
```

**Casos de prueba**:
- Mappers (JSON ↔ Entidades)
- Repositorios (in-memory e HTTP)
- Controller (estado y métodos)

---

## Configuración para Conectar Todo

### 1. Backend Django

En `backend/.env`:
```env
# Usar las mismas credenciales que Supabase
DATABASE_URL=postgresql://postgres:[PASSWORD]@[SUPABASE_HOST]:5432/postgres
SUPABASE_JWT_SECRET=[TU_JWT_SECRET]
```

### 2. App Mobile

En `aura_mobile/env/local.env`:
```env
# URL del backend Django
BASE_URL=http://localhost:8000/dashboard
# O tu servidor real
# BASE_URL=https://api.tudominio.com/dashboard
```

El `bodyRepositoryProvider` automáticamente usa `HttpBodyRepository` cuando detecta una URL válida.

---

## Queries SQL Útiles

### Ver actividades de un usuario

```sql
SELECT * FROM public.body_activities
WHERE auth_user_id = '[UUID]'
ORDER BY session_date DESC
LIMIT 10;
```

### Resumen de nutrición de la última semana

```sql
SELECT
  DATE(timestamp) as fecha,
  COUNT(*) as num_comidas,
  SUM(calories) as total_calorias,
  AVG(protein) as prom_proteina
FROM public.body_nutrition_logs
WHERE auth_user_id = '[UUID]'
  AND timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(timestamp)
ORDER BY fecha DESC;
```

### Promedio de sueño del mes

```sql
SELECT
  AVG(duration_hours) as promedio_horas,
  COUNT(*) as total_registros
FROM public.body_sleep_logs
WHERE auth_user_id = '[UUID]'
  AND wake_time >= DATE_TRUNC('month', CURRENT_DATE);
```

---

## Próximos Pasos

### Funcionalidades Pendientes

1. **Gráficas y Estadísticas**:
   - Implementar `ExerciseMetricsPage` con gráficas reales
   - Implementar `NutritionQualityPage` con análisis de macros
   - Implementar `SleepMetricsPage` con tendencias

2. **Mejoras en Entidades**:
   - Agregar campos calculados (ej: calorías quemadas estimadas)
   - Soporte para rutinas de ejercicio predefinidas
   - Base de datos de alimentos común

3. **Notificaciones**:
   - Recordatorios para registrar comidas
   - Alertas de objetivos cumplidos
   - Sugerencias basadas en patrones

4. **Integración con Dispositivos**:
   - Importar datos de smartwatches
   - Sincronización con apps de fitness
   - APIs de terceros (Google Fit, Apple Health)

---

## Contacto y Soporte

Para preguntas o mejoras:
- Revisa la documentación general en `backend/docs/`
- Consulta `aura_mobile/docs/` para guías de Flutter
- Reporta issues específicos del módulo Body

---

**Última actualización**: 2025-10-28  
**Versión del schema**: 1.0  
**Compatibilidad**: Supabase CLI >= 2.51, Django >= 5.0, Flutter >= 3.24

