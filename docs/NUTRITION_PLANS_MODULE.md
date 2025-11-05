# Módulo de Planes Nutricionales

## Resumen

El módulo de **Planes Nutricionales** permite a los usuarios gestionar planes alimentarios estructurados y completos. Este módulo implementa un esquema JSON robusto que captura:

- **Metadatos del plan**: Título, versión, vigencia, idioma, unidades, fuente de origen
- **Información del sujeto**: Datos demográficos del usuario
- **Evaluación nutricional**: Serie temporal de métricas corporales, diagnósticos, objetivos
- **Directivas del plan**: Comidas estructuradas con componentes, restricciones alimentarias, tablas de sustituciones
- **Suplementos**: Recomendaciones de suplementación con dosis y timing
- **Recomendaciones generales**: Guías de actividad física y notas adicionales
- **Texto libre**: Bloques no estructurados para trazabilidad

---

## Arquitectura de 3 Capas

### 1. Base de Datos (Supabase PostgreSQL)

**Tabla**: `nutrition_plans`

**Migración**: `aura_mobile/supabase/migrations/20251028_create_nutrition_plans_table.sql`

#### Campos Principales

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | Identificador único (PK) |
| `auth_user_id` | UUID | ID del usuario en Supabase Auth (FK a auth.users) |
| `title` | VARCHAR(255) | Título del plan |
| `language` | VARCHAR(10) | Código de idioma ISO 639-1 (default: 'es') |
| `issued_at` | DATE | Fecha de emisión del plan |
| `valid_until` | DATE | Fecha de expiración |
| `is_active` | BOOLEAN | Indica si el plan está activo |
| `plan_data` | JSONB | Estructura completa del plan en JSON |
| `source_kind` | VARCHAR(32) | Tipo de fuente: pdf, image, text, web |
| `source_uri` | TEXT | URI del documento fuente |
| `extracted_at` | TIMESTAMPTZ | Timestamp de extracción |
| `extractor` | VARCHAR(128) | Sistema que extrajo el plan |
| `created_at` | TIMESTAMPTZ | Timestamp de creación |
| `updated_at` | TIMESTAMPTZ | Timestamp de última actualización |

#### Índices

- `idx_nutrition_plans_user_active`: Índice compuesto en `(auth_user_id, is_active)`
- `idx_nutrition_plans_user_validity`: Índice compuesto en `(auth_user_id, valid_until)`
- `idx_nutrition_plans_user_issued`: Índice en `(auth_user_id, issued_at DESC)`
- `idx_nutrition_plans_data_gin`: Índice GIN para búsquedas en `plan_data`

#### Row Level Security (RLS)

- **SELECT**: Los usuarios solo pueden ver sus propios planes
- **INSERT**: Los usuarios solo pueden crear planes para sí mismos
- **UPDATE**: Los usuarios solo pueden actualizar sus propios planes
- **DELETE**: Los usuarios solo pueden eliminar sus propios planes

#### Triggers

- `trigger_update_nutrition_plans_updated_at`: Actualiza automáticamente `updated_at` en cada modificación

---

### 2. Backend (Django REST Framework)

**Modelo**: `NutritionPlan`

**Ubicación**: `backend/body/models.py`

#### Características del Modelo

- Utiliza `JSONField` para almacenar la estructura completa del plan en `plan_data`
- Extrae campos clave (`title`, `language`, `issued_at`, `valid_until`, `is_active`) para facilitar consultas
- Incluye métodos helper para acceder a secciones específicas del plan:
  - `get_meals()`: Extrae las comidas del plan
  - `get_restrictions()`: Extrae restricciones alimentarias
  - `get_substitutions()`: Extrae tablas de intercambio
  - `get_supplements()`: Extrae suplementos
  - `get_goals()`: Extrae objetivos nutricionales
- Propiedad computada `is_valid`: Verifica si el plan está vigente

#### Serializer: `NutritionPlanSerializer`

**Ubicación**: `backend/body/serializers.py`

**Funcionalidades**:

- Validación completa de la estructura `plan_data` contra el esquema JSON
- Verifica campos requeridos: `plan`, `subject`, `directives`
- Valida estructura de `plan.source` (debe incluir `kind`)
- Valida estructura de `directives.meals` (cada comida debe tener `name` y `components`)
- Sincronización automática entre campos extraídos y `plan_data`
- Campos computados: `is_valid`, `meals`, `restrictions`, `goals`

#### ViewSet: `NutritionPlanViewSet`

**Ubicación**: `backend/body/views.py`

**Endpoints API**:

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/dashboard/body/nutrition-plans/` | Lista todos los planes del usuario |
| GET | `/dashboard/body/nutrition-plans/?active=true` | Filtra solo planes activos |
| GET | `/dashboard/body/nutrition-plans/?valid=true` | Filtra solo planes vigentes |
| GET | `/dashboard/body/nutrition-plans/{id}/` | Detalle de un plan específico |
| POST | `/dashboard/body/nutrition-plans/` | Crear nuevo plan |
| PATCH | `/dashboard/body/nutrition-plans/{id}/` | Actualizar plan |
| DELETE | `/dashboard/body/nutrition-plans/{id}/` | Eliminar plan |

**Seguridad**:
- Requiere token JWT de Supabase (`SupabaseJWTRequiredPermission`)
- Filtra automáticamente por `auth_user_id` del usuario autenticado
- Solo permite operaciones sobre planes propios del usuario

#### Configuración de URLs

**Archivo**: `backend/body/urls.py`

```python
router.register(
    r'body/nutrition-plans', 
    NutritionPlanViewSet, 
    basename='nutrition-plans'
)
```

---

### 3. App Mobile (Flutter)

#### Entidades del Dominio

**Ubicación**: `aura_mobile/lib/features/body/domain/entities/nutrition_plan.dart`

**Clases Principales**:

1. **NutritionPlan**: Entidad raíz del plan completo
2. **PlanMetadata**: Metadatos (versión, idioma, unidades, fuente)
3. **PlanSource**: Información de la fuente (tipo, URI, páginas)
4. **PlanSubject**: Información del usuario (demografía)
5. **Assessment**: Evaluación nutricional (métricas, diagnósticos, objetivos)
   - `MetricTimeseries`: Serie temporal de métricas corporales
   - `BodyMetrics`: BMI, % grasa, masa muscular, etc.
   - `Diagnosis`: Diagnósticos nutricionales
   - `NutritionalGoal`: Objetivos con valores target
6. **PlanDirectives**: Directivas del plan
   - `Meal`: Comida con componentes
   - `MealComponent`: Componente de comida (grupo alimenticio + cantidad)
   - `ComponentQuantity`: Cantidad en porciones o valor+unidad
   - `Restriction`: Restricción alimentaria (forbidden/limited/free)
   - `SubstitutionGroup`: Tabla de intercambios por grupo
   - `WeeklyFrequency`: Frecuencia semanal recomendada
   - `ConditionalAllowance`: Permisos condicionales (cheat meals)
7. **Supplement**: Suplemento con dosis y timing
8. **FreeText**: Texto libre no estructurado

**Enums**:
- `SourceKind`: pdf, image, text, web
- `MassUnit`: kg, lb
- `VolumeUnit`: ml, l, cup
- `EnergyUnit`: kcal, kj
- `RestrictionRule`: forbidden, limited, free

#### Mappers

**Ubicación**: `aura_mobile/lib/features/body/infrastructure/mappers/nutrition_plan_mapper.dart`

**Clase**: `NutritionPlanMapper`

**Métodos**:
- `fromJson(Map<String, dynamic>)`: Convierte JSON de API a entidad Dart
- `toJson(NutritionPlan)`: Convierte entidad Dart a JSON para API
- Métodos privados para mapeo de sub-estructuras (metadata, subject, assessment, directives, etc.)
- Helpers para conversión de enums

#### Repositorio

**Interfaz**: `aura_mobile/lib/features/body/domain/repositories/nutrition_plan_repository.dart`

**Implementación HTTP**: `aura_mobile/lib/features/body/infrastructure/repositories/http_nutrition_plan_repository.dart`

**Métodos**:

```dart
Future<List<NutritionPlan>> getPlans({bool? activeOnly, bool? validOnly})
Future<NutritionPlan> getPlan(String id)
Future<NutritionPlan> createPlan(NutritionPlan plan)
Future<NutritionPlan> updatePlan(String id, NutritionPlan plan)
Future<void> deletePlan(String id)
Future<NutritionPlan?> getActivePlan()
```

---

## Esquema JSON del Plan

El campo `plan_data` en la base de datos sigue esta estructura:

```json
{
  "plan": {
    "title": "Plan Nutricional Personalizado",
    "version": "1.0",
    "issued_at": "2025-10-28",
    "valid_until": "2026-01-28",
    "language": "es",
    "units": {
      "mass": "kg",
      "volume": "ml",
      "energy": "kcal"
    },
    "source": {
      "kind": "pdf",
      "uri": "s3://plans/usuario123/plan_oct2025.pdf",
      "pages": [
        {"page": 1, "section_hint": "Diagnóstico"},
        {"page": 2, "section_hint": "Plan de comidas"}
      ],
      "extracted_at": "2025-10-28T10:30:00Z",
      "extractor": "nutrition-ai-v2"
    }
  },
  "subject": {
    "user_id": "uuid-del-usuario",
    "name": "Juan Pérez",
    "demographics": {
      "sex": "M",
      "age_years": 32,
      "height_cm": 175,
      "weight_kg": 78
    }
  },
  "assessment": {
    "timeseries": [
      {
        "date": "2025-10-28",
        "metrics": {
          "bmi": 25.5,
          "fat_percent": 18.5,
          "muscle_mass_kg": 35.2,
          "bone_mass_kg": 3.8,
          "residual_mass_kg": 12.1
        },
        "method_notes": "Bioimpedancia eléctrica"
      }
    ],
    "diagnoses": [
      {
        "label": "Sobrepeso leve",
        "severity": "moderado",
        "notes": "IMC entre 25-27"
      }
    ],
    "goals": [
      {
        "target": "peso_kg",
        "value": 72,
        "unit": "kg",
        "due_date": "2026-01-28"
      },
      {
        "target": "grasa_corporal",
        "value": 15,
        "unit": "%",
        "due_date": "2026-01-28"
      }
    ]
  },
  "directives": {
    "weekly_frequency": {
      "min_days_per_week": 6,
      "notes": "Seguir el plan al menos 6 días por semana"
    },
    "conditional_allowances": [
      {
        "name": "cheat_meal",
        "allowed": true,
        "frequency": "1 por semana",
        "conditions": "Si cumples 100% los otros 6 días"
      }
    ],
    "restrictions": [
      {
        "target": "azúcares añadidos",
        "rule": "forbidden",
        "details": "Evitar completamente azúcares refinados"
      },
      {
        "target": "sodio",
        "rule": "limited",
        "details": "Máximo 2300mg al día"
      }
    ],
    "meals": [
      {
        "name": "Desayuno",
        "time_window": "7:00-9:00",
        "components": [
          {
            "group": "Harinas",
            "quantity": {
              "portions": 2,
              "notes": "Preferir integrales"
            },
            "must_present": true
          },
          {
            "group": "Proteína",
            "quantity": {
              "portions": 1
            },
            "must_present": true
          },
          {
            "group": "Fruta",
            "quantity": {
              "portions": 1
            },
            "must_present": false
          }
        ],
        "notes": "Desayuno balanceado con carbohidratos complejos"
      },
      {
        "name": "Media Mañana",
        "time_window": "10:00-11:00",
        "components": [
          {
            "group": "Fruta",
            "quantity": {
              "portions": 1
            }
          }
        ]
      }
    ],
    "substitutions": [
      {
        "group": "Harinas",
        "items": [
          {"name": "Pan integral", "grams": 60, "portion_equiv": 1},
          {"name": "Avena", "grams": 40, "portion_equiv": 1},
          {"name": "Tortilla de maíz", "grams": 50, "portion_equiv": 1}
        ]
      },
      {
        "group": "Proteína",
        "items": [
          {"name": "Pechuga de pollo", "grams": 90, "portion_equiv": 1},
          {"name": "Huevo entero", "grams": 60, "portion_equiv": 1, "notes": "1 pieza"},
          {"name": "Atún en agua", "grams": 75, "portion_equiv": 1}
        ]
      }
    ]
  },
  "supplements": [
    {
      "name": "Omega-3",
      "dose": "1000mg",
      "timing": "Con almuerzo",
      "notes": "Aceite de pescado de alta calidad"
    },
    {
      "name": "Vitamina D3",
      "dose": "2000 UI",
      "timing": "Por la mañana"
    }
  ],
  "recommendations": [
    "Mantener hidratación adecuada: 2-3 litros de agua al día",
    "Realizar actividad física moderada 4-5 días por semana",
    "Dormir 7-8 horas diarias",
    "Evitar alcohol durante el plan"
  ],
  "activity_guidance": "Combinar cardio (3x semana, 30-40 min) con entrenamiento de fuerza (2x semana). Caminar al menos 10,000 pasos diarios.",
  "free_text": {
    "diagnosis_raw": "Texto completo del diagnóstico original del nutriólogo...",
    "instructions_raw": "Instrucciones detalladas originales del plan...",
    "notes_raw": "Notas adicionales del profesional..."
  }
}
```

---

## Flujo de Uso

### Crear un Plan Nutricional

**Backend (API REST)**:

```bash
POST /dashboard/body/nutrition-plans/
Authorization: Bearer <supabase-jwt-token>
Content-Type: application/json

{
  "title": "Plan de Reducción de Grasa",
  "language": "es",
  "issued_at": "2025-10-28",
  "valid_until": "2026-01-28",
  "is_active": true,
  "plan_data": {
    "plan": { ... },
    "subject": { ... },
    "directives": { ... }
  }
}
```

**Flutter**:

```dart
final repository = HttpNutritionPlanRepository(dio: dio);

final newPlan = NutritionPlan(
  id: '',  // Se generará en el servidor
  title: 'Plan de Reducción de Grasa',
  language: 'es',
  isActive: true,
  isValid: true,
  planMetadata: PlanMetadata(...),
  subject: PlanSubject(...),
  directives: PlanDirectives(...),
  // ...
);

final created = await repository.createPlan(newPlan);
```

### Obtener el Plan Activo

**Backend**:
```bash
GET /dashboard/body/nutrition-plans/?active=true&valid=true
Authorization: Bearer <supabase-jwt-token>
```

**Flutter**:
```dart
final activePlan = await repository.getActivePlan();
if (activePlan != null) {
  print('Plan activo: ${activePlan.title}');
  print('Comidas: ${activePlan.directives.meals.length}');
}
```

### Actualizar un Plan

**Backend**:
```bash
PATCH /dashboard/body/nutrition-plans/{id}/
Authorization: Bearer <supabase-jwt-token>
Content-Type: application/json

{
  "is_active": false,
  "plan_data": { ... }
}
```

**Flutter**:
```dart
final updated = plan.copyWith(isActive: false);
await repository.updatePlan(plan.id, updated);
```

---

## Validaciones

### Validaciones del Backend

El serializer `NutritionPlanSerializer` valida:

1. ✅ `plan_data` debe ser un objeto JSON
2. ✅ Campos requeridos de nivel superior: `plan`, `subject`, `directives`
3. ✅ `plan` debe contener: `source`, `language`
4. ✅ `plan.source` debe contener: `kind` (pdf|image|text|web)
5. ✅ `directives` debe contener: `meals`
6. ✅ Cada comida debe tener: `name`, `components`
7. ✅ `components` debe ser una lista
8. ✅ Sincroniza automáticamente campos extraídos con `plan_data`

### Validaciones de Base de Datos

1. ✅ `auth_user_id` debe existir en `auth.users` (FK constraint)
2. ✅ `plan_data` debe ser JSON válido (tipo JSONB)
3. ✅ RLS asegura que solo el propietario acceda a sus planes

---

## Pruebas

### Ejecutar Migración

```bash
cd aura_mobile/supabase
supabase migration up
```

### Verificar Tabla

```sql
SELECT * FROM nutrition_plans WHERE auth_user_id = '<user-uuid>';
```

### Probar API

```bash
# Crear plan
curl -X POST http://localhost:8000/dashboard/body/nutrition-plans/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d @plan_example.json

# Listar planes activos
curl http://localhost:8000/dashboard/body/nutrition-plans/?active=true \
  -H "Authorization: Bearer <token>"

# Obtener plan específico
curl http://localhost:8000/dashboard/body/nutrition-plans/<plan-id>/ \
  -H "Authorization: Bearer <token>"
```

---

## Casos de Uso

### 1. Profesional de Nutrición Crea Plan

Un nutriólogo crea un plan estructurado para un paciente:

1. Realiza evaluación nutricional (métricas corporales, análisis de composición)
2. Define objetivos específicos (peso target, % grasa, etc.)
3. Diseña plan de comidas con porciones y sustituciones
4. Establece restricciones alimentarias
5. Recomienda suplementos si es necesario
6. Sube el plan al sistema

### 2. Usuario Consulta su Plan Activo

El usuario desde la app móvil:

1. Abre la sección de nutrición
2. Ve su plan activo vigente
3. Consulta las comidas del día
4. Revisa las tablas de intercambio
5. Verifica restricciones antes de elegir alimentos

### 3. Sistema de IA Extrae Plan desde PDF

Un agente de IA procesa un plan en PDF:

1. Extrae texto y estructura del documento
2. Identifica secciones: diagnóstico, plan de comidas, restricciones
3. Parsea comidas y componentes
4. Genera estructura JSON conforme al esquema
5. Crea plan en el sistema con metadata de fuente

### 4. Usuario Actualiza Progreso

El usuario actualiza su evolución:

1. Registra nuevas métricas corporales
2. El sistema añade entrada en `assessment.timeseries`
3. Compara con objetivos definidos
4. Muestra progreso visual

---

## Extensiones Futuras

### 1. Análisis de Adherencia

- Calcular % de adherencia al plan basado en registros de `NutritionLog`
- Comparar comidas registradas vs. plan prescrito
- Generar reportes de cumplimiento

### 2. Recomendaciones Inteligentes

- Sugerir sustituciones automáticas basadas en disponibilidad
- Ajustar porciones según progreso hacia objetivos
- Alertar sobre desviaciones del plan

### 3. Integración con Servicios Externos

- Importar planes desde servicios de nutriólogos
- Exportar planes a apps de tracking (MyFitnessPal, etc.)
- Sincronizar con wearables para ajustar calorías

### 4. Versionado de Planes

- Mantener historial de versiones de cada plan
- Permitir rollback a versiones anteriores
- Comparar evolución entre versiones

---

## Mantenimiento

### Actualizar Esquema JSON

Si se necesita agregar campos al esquema:

1. Actualizar modelos Dart en `nutrition_plan.dart`
2. Actualizar mappers en `nutrition_plan_mapper.dart`
3. Documentar cambios en validaciones del serializer
4. Actualizar esta documentación

### Migrar Datos Existentes

Para migrar planes antiguos a nueva estructura:

```sql
UPDATE nutrition_plans
SET plan_data = plan_data || '{"nuevo_campo": "valor_default"}'::jsonb
WHERE plan_data ->> 'nuevo_campo' IS NULL;
```

---

## Soporte

Para dudas o problemas con el módulo de planes nutricionales:

1. Revisar logs de Django para errores de validación
2. Verificar estructura JSON contra esquema documentado
3. Consultar tests de integración en `backend/body/tests/`
4. Revisar documentación de API en `/dashboard/docs/` (Swagger/ReDoc)

---

## Referencias

- **Esquema JSON**: `nutrition-plan.schema.json` (proporcionado por el usuario)
- **Modelos Django**: `backend/body/models.py`
- **Serializers**: `backend/body/serializers.py`
- **ViewSets**: `backend/body/views.py`
- **Modelos Dart**: `aura_mobile/lib/features/body/domain/entities/nutrition_plan.dart`
- **Mappers**: `aura_mobile/lib/features/body/infrastructure/mappers/nutrition_plan_mapper.dart`
- **Repositorio**: `aura_mobile/lib/features/body/infrastructure/repositories/http_nutrition_plan_repository.dart`

