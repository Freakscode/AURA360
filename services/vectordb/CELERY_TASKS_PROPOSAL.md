# Propuesta de Nuevas Tareas Celery para AURA360

**Fecha**: 2025-01-20
**Autor**: Backend Developer
**Estado**: 🎯 Propuesta para Implementación

---

## 📋 Resumen Ejecutivo

Basado en las nuevas funcionalidades de **BodyMeasurement** y **NutritionPlan**, se proponen **7 nuevas tareas asíncronas** para Celery que mejorarán la experiencia del usuario y reducirán la carga del servidor.

---

## 🎯 Tareas Propuestas

### 1. **`calculate_body_composition`** - Cálculos Antropométricos

**Propósito**: Calcular automáticamente todos los campos derivados de una medición corporal.

**Input**:
```python
{
    "measurement_id": "uuid",
    "auth_user_id": "uuid",
    "weight_kg": 75.5,
    "height_cm": 175,
    "gender": "M",  # Necesario para fórmulas
    "age": 30,
    # + todos los pliegues, circunferencias, diámetros opcionales
}
```

**Procesamiento**:
1. **IMC**: `weight_kg / (height_cm/100)²`
2. **% Grasa Corporal**:
   - Fórmula Jackson-Pollock (7 pliegues)
   - Fórmula Durning-Womersley (4 pliegues)
   - Fórmula Slaughter (niños/adolescentes)
3. **Masa Grasa y Masa Muscular**:
   - `fat_mass_kg = weight_kg × (body_fat_percentage / 100)`
   - `muscle_mass_kg = weight_kg - fat_mass_kg`
4. **Somatotipo Heath-Carter**:
   - Endomorphy (adiposidad)
   - Mesomorphy (músculo-esqueleto)
   - Ectomorphy (linealidad)
5. **Índices de Salud**:
   - ICC: `waist_circumference / hip_circumference`
   - ICE: `waist_circumference / height_cm`
   - Nivel de Riesgo Cardiovascular

**Output**:
- Actualiza el registro `BodyMeasurement` con todos los campos calculados
- Retorna JSON con resultados y recomendaciones

**Prioridad**: 🔴 **Alta** (crítica para profesionales)

---

### 2. **`vectorize_body_measurement`** - Vectorización para RAG

**Propósito**: Convertir mediciones corporales en embeddings para búsqueda semántica.

**Input**:
```python
{
    "measurement_id": "uuid",
    "auth_user_id": "uuid",
    "protocol": "isak_restricted",
    "patient_type": "athlete"
}
```

**Procesamiento**:
1. Obtener medición completa de la BD
2. Generar texto contextual:
   ```
   Paciente deportista masculino, 30 años.
   Peso: 75.5 kg, Altura: 175 cm, IMC: 24.6 (normal).
   Composición: 12% grasa, 66.2 kg masa muscular.
   Somatotipo: 2.5-5.0-3.0 (mesomorfo balanceado).
   ICC: 0.82 (bajo riesgo cardiovascular).
   Protocolo ISAK Restringido aplicado.
   ```
3. Generar embedding con modelo FastEmbed
4. Almacenar en Qdrant Cloud:
   - Collection: `holistic_memory`
   - Metadata: `user_id`, `measurement_id`, `recorded_at`, `protocol`, `patient_type`

**Output**:
- Embedding almacenado en Qdrant
- ID del vector retornado

**Prioridad**: 🟡 **Media** (útil para agentes IA)

---

### 3. **`analyze_progress_trends`** - Análisis de Tendencias

**Propósito**: Analizar evolución del paciente a lo largo del tiempo.

**Input**:
```python
{
    "auth_user_id": "uuid",
    "period_days": 90,  # Últimos 90 días
    "metrics": ["weight_kg", "body_fat_percentage", "muscle_mass_kg"]
}
```

**Procesamiento**:
1. Obtener todas las mediciones del período
2. Para cada métrica:
   - Calcular tendencia (regresión lineal)
   - Detectar cambios significativos
   - Proyectar valores futuros (7, 14, 30 días)
3. Generar insights:
   - "Pérdida de peso constante: -0.5 kg/semana (saludable)"
   - "Aumento de masa muscular: +0.3 kg/semana (excelente)"
   - "IMC en zona objetivo alcanzado"

**Output**:
```json
{
    "trends": {
        "weight_kg": {
            "change_total": -4.2,
            "change_percentage": -5.3,
            "trend": "decreasing",
            "rate_per_week": -0.5,
            "projection_7d": 74.8,
            "projection_30d": 73.1
        },
        // ... más métricas
    },
    "insights": [...],
    "alerts": [
        {"type": "success", "message": "Objetivo de pérdida de peso en progreso"}
    ]
}
```

**Prioridad**: 🔴 **Alta** (valor para profesionales y pacientes)

---

### 4. **`generate_progress_report_pdf`** - Reporte en PDF

**Propósito**: Generar reporte PDF con visualizaciones y análisis.

**Input**:
```python
{
    "auth_user_id": "uuid",
    "period_days": 90,
    "include_charts": True,
    "include_photos": True,
    "language": "es"
}
```

**Procesamiento**:
1. Llamar a `analyze_progress_trends` para obtener datos
2. Generar gráficos con matplotlib/plotly:
   - Evolución de peso
   - Evolución de composición corporal
   - Somatotipo en 3D
3. Compilar PDF con ReportLab o WeasyPrint:
   - Header con logo y datos del paciente
   - Resumen ejecutivo
   - Gráficos de tendencias
   - Tabla de mediciones
   - Comparación de fotos (antes/después)
   - Recomendaciones

**Output**:
- PDF almacenado en GCS
- URL pública con expiración (7 días)
- Notificación al usuario

**Prioridad**: 🟡 **Media** (nice-to-have para profesionales)

---

### 5. **`vectorize_nutrition_plan`** - Vectorización de Planes

**Propósito**: Indexar planes nutricionales para búsqueda semántica y recomendaciones.

**Input**:
```python
{
    "plan_id": "uuid",
    "auth_user_id": "uuid",
    "is_template": False
}
```

**Procesamiento**:
1. Obtener plan completo de la BD
2. Extraer información clave:
   - Objetivos (pérdida de peso, ganancia muscular, etc.)
   - Restricciones alimentarias
   - Distribución de macros
   - Tipos de comidas
   - Suplementos recomendados
3. Generar texto contextual:
   ```
   Plan Nutricional: "Keto para Deportistas"
   Objetivo: Pérdida de grasa manteniendo músculo
   Macros: 70% grasas, 25% proteínas, 5% carbohidratos
   Restricciones: Sin gluten, sin lactosa
   Comidas: 4 al día (desayuno, almuerzo, snack, cena)
   Duración: 12 semanas
   ```
4. Generar embedding y almacenar en Qdrant:
   - Collection: `holistic_memory`
   - Permite búsquedas como: "planes para pérdida de peso sin gluten"

**Output**:
- Embedding almacenado
- Plan indexado para búsqueda

**Prioridad**: 🟢 **Baja** (optimización futura)

---

### 6. **`analyze_nutrition_adherence`** - Adherencia al Plan

**Propósito**: Medir qué tan bien sigue el paciente su plan nutricional.

**Input**:
```python
{
    "auth_user_id": "uuid",
    "plan_id": "uuid",
    "period_days": 7  # Última semana
}
```

**Procesamiento**:
1. Obtener plan nutricional activo
2. Obtener registros de `NutritionLog` del período
3. Comparar:
   - Calorías target vs. consumidas
   - Macros target vs. consumidos
   - Comidas programadas vs. registradas
   - Restricciones violadas
4. Calcular score de adherencia (0-100%)
5. Generar recomendaciones:
   - "Adherencia excelente al target de proteínas (98%)"
   - "Calorías 15% por encima del target, ajustar porciones"

**Output**:
```json
{
    "adherence_score": 85,
    "calories_adherence": 92,
    "macros_adherence": {
        "protein": 98,
        "carbs": 78,
        "fats": 85
    },
    "meals_logged": 6,
    "meals_expected": 7,
    "restrictions_violations": 0,
    "recommendations": [...]
}
```

**Prioridad**: 🟡 **Media** (valor para profesionales)

---

### 7. **`generate_ai_recommendations`** - Recomendaciones IA

**Propósito**: Usar agentes + RAG para generar recomendaciones personalizadas.

**Input**:
```python
{
    "auth_user_id": "uuid",
    "context": "recent_measurements",  # o "nutrition_adherence", "progress"
    "language": "es"
}
```

**Procesamiento**:
1. Obtener contexto del usuario desde Qdrant (búsqueda semántica)
2. Llamar a agente Guardian/Nutri con contexto:
   - Mediciones recientes
   - Plan nutricional activo
   - Adherencia histórica
   - Objetivos del paciente
3. Generar recomendaciones con Gemini:
   - Ajustes en el plan
   - Tips de adherencia
   - Ejercicios complementarios
   - Alertas de salud

**Output**:
```json
{
    "recommendations": [
        {
            "type": "nutrition",
            "priority": "high",
            "message": "Considera aumentar proteínas post-entreno...",
            "rationale": "Tu masa muscular está aumentando, necesitas..."
        },
        {
            "type": "health_alert",
            "priority": "medium",
            "message": "ICC elevado, monitorear cintura...",
            "rationale": "Tu ICC de 0.92 está en zona de precaución..."
        }
    ],
    "next_actions": [...]
}
```

**Prioridad**: 🟢 **Baja** (experimentación con IA)

---

## 🏗️ Arquitectura Propuesta

```
┌─────────────────────────────────────────────────────────────────┐
│                      DJANGO API (Body App)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  POST /body/measurements/  →  create_measurement()             │
│        ↓                                                        │
│   [SIGNAL: post_save]                                          │
│        ↓                                                        │
│   calculate_body_composition.delay(measurement_id)  ← Celery   │
│        ↓                                                        │
│   vectorize_body_measurement.delay(measurement_id)  ← Celery   │
│                                                                 │
│  POST /body/nutrition-plans/  →  create_plan()                │
│        ↓                                                        │
│   [SIGNAL: post_save]                                          │
│        ↓                                                        │
│   vectorize_nutrition_plan.delay(plan_id)  ← Celery           │
│                                                                 │
│  GET /body/measurements/trends/  →  get_trends()              │
│        ↓                                                        │
│   analyze_progress_trends.delay(user_id)  ← Celery            │
│        ↓                                                        │
│   [Cache resultado en Redis por 1 hora]                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
         │                           │                    │
         ▼                           ▼                    ▼
┌──────────────────┐   ┌──────────────────────┐   ┌──────────────┐
│ Celery Worker    │   │  Qdrant Cloud        │   │  GCS Bucket  │
│ (VectorDB)       │   │  (Embeddings)        │   │  (Reports)   │
│                  │   │                      │   │              │
│ • calculate_*    │   │ • holistic_memory    │   │ • PDFs       │
│ • vectorize_*    │   │ • user_context       │   │ • Photos     │
│ • analyze_*      │   │                      │   │              │
│ • generate_*     │   │                      │   │              │
└──────────────────┘   └──────────────────────┘   └──────────────┘
```

---

## 📦 Estructura de Archivos

```
services/
├── vectordb/
│   └── vectosvc/
│       ├── worker/
│       │   ├── tasks.py  ← Tareas existentes
│       │   └── body_tasks.py  ← 🆕 NUEVAS TAREAS
│       ├── core/
│       │   ├── anthropometry.py  ← 🆕 Fórmulas de cálculo
│       │   ├── reports.py  ← 🆕 Generación de PDFs
│       │   └── trends.py  ← 🆕 Análisis de tendencias
│       └── ...
└── api/
    └── body/
        ├── signals.py  ← 🆕 Post-save signals
        ├── views.py  ← Actualizado con endpoints de trends
        └── ...
```

---

## 🔌 Integración con Django API

### 1. Signals para Procesamiento Automático

```python
# services/api/body/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import BodyMeasurement, NutritionPlan

@receiver(post_save, sender=BodyMeasurement)
def process_new_measurement(sender, instance, created, **kwargs):
    """Procesar nueva medición automáticamente."""
    if created:
        from celery_app import calculate_body_composition
        calculate_body_composition.delay(
            measurement_id=str(instance.id),
            auth_user_id=str(instance.auth_user_id)
        )

@receiver(post_save, sender=NutritionPlan)
def process_new_plan(sender, instance, created, **kwargs):
    """Vectorizar plan nutricional."""
    if created and not instance.is_template:
        from celery_app import vectorize_nutrition_plan
        vectorize_nutrition_plan.delay(
            plan_id=str(instance.id),
            auth_user_id=str(instance.auth_user_id)
        )
```

### 2. Nuevo Endpoint para Tendencias

```python
# services/api/body/views.py
from rest_framework.decorators import action
from rest_framework.response import Response

class BodyMeasurementViewSet(...):

    @action(detail=False, methods=['get'])
    def trends(self, request):
        """
        GET /body/measurements/trends/?period_days=90

        Obtiene análisis de tendencias del usuario autenticado.
        """
        user_id = self._auth_user_id()
        period_days = int(request.query_params.get('period_days', 90))

        # Llamar tarea asíncrona (con result backend para esperar)
        from celery_app import analyze_progress_trends
        result = analyze_progress_trends.apply_async(
            args=[str(user_id), period_days]
        )

        # Esperar resultado (máx 10 segundos)
        try:
            trends_data = result.get(timeout=10)
            return Response(trends_data)
        except TimeoutError:
            return Response(
                {"status": "processing", "task_id": result.id},
                status=202
            )
```

---

## 🧪 Testing

### 1. Test Unitario de Cálculos

```python
# tests/test_anthropometry.py
def test_bmi_calculation():
    result = calculate_bmi(weight_kg=75, height_cm=175)
    assert result == 24.49

def test_body_fat_jackson_pollock():
    # Fórmula de 7 pliegues para hombre de 30 años
    result = calculate_body_fat_jp7(
        chest=10, abdominal=20, thigh=15,
        triceps=12, subscapular=15, suprailiac=18, midaxillary=14,
        age=30, gender='M'
    )
    assert 10 <= result <= 15  # Rango esperado

def test_somatotype_calculation():
    result = calculate_somatotype_heath_carter(
        triceps=12, subscapular=15, suprailiac=18,
        calf_skinfold=10, arm_flexed=32, calf_circ=38,
        femur=9.5, humerus=7.0, height_cm=175, weight_kg=75
    )
    assert 'endomorphy' in result
    assert 'mesomorphy' in result
    assert 'ectomorphy' in result
```

### 2. Test de Integración con Celery

```python
# tests/test_body_tasks.py
@pytest.mark.celery
def test_calculate_body_composition_task():
    # Crear medición de prueba
    measurement = BodyMeasurement.objects.create(
        auth_user_id=uuid4(),
        weight_kg=75.0,
        height_cm=175.0,
        # ... más campos
    )

    # Ejecutar tarea
    result = calculate_body_composition.delay(str(measurement.id))
    result.get(timeout=10)

    # Verificar que se calcularon los campos
    measurement.refresh_from_db()
    assert measurement.bmi is not None
    assert measurement.body_fat_percentage is not None
    assert measurement.somatotype_calculated is True
```

---

## 📅 Plan de Implementación

### Fase 1: Core Calculations (Semana 1) 🔴
- [ ] Crear `vectosvc/core/anthropometry.py` con fórmulas
- [ ] Implementar `calculate_body_composition` task
- [ ] Tests unitarios de cálculos
- [ ] Django signal para auto-procesamiento
- [ ] Documentar fórmulas usadas

### Fase 2: Vectorization (Semana 1-2) 🟡
- [ ] Implementar `vectorize_body_measurement` task
- [ ] Implementar `vectorize_nutrition_plan` task
- [ ] Tests de integración con Qdrant Cloud
- [ ] Verificar embeddings en consola

### Fase 3: Trends & Analytics (Semana 2) 🟡
- [ ] Crear `vectosvc/core/trends.py`
- [ ] Implementar `analyze_progress_trends` task
- [ ] Endpoint `/body/measurements/trends/` en Django
- [ ] Tests de regresión lineal y proyecciones

### Fase 4: Reports (Semana 3) 🟢
- [ ] Crear `vectosvc/core/reports.py`
- [ ] Implementar `generate_progress_report_pdf` task
- [ ] Integración con GCS para almacenamiento
- [ ] Endpoint `/body/measurements/report/` en Django

### Fase 5: AI & Advanced (Semana 4) 🟢
- [ ] Implementar `analyze_nutrition_adherence` task
- [ ] Implementar `generate_ai_recommendations` task
- [ ] Integración con agentes Guardian/Nutri
- [ ] Dashboard de profesional con insights

---

## 🎨 UX Improvements

### Para Profesionales:
1. **Auto-cálculo instantáneo**: Al guardar medición, cálculos aparecen en 2-3 segundos
2. **Dashboard de tendencias**: Gráficos interactivos con progreso de todos los pacientes
3. **Reportes PDF**: Botón "Generar Reporte" → PDF listo en 10 segundos
4. **Alertas automáticas**: "Paciente X tiene ICC elevado, revisar"

### Para Pacientes:
1. **Feedback inmediato**: "Tu composición corporal mejoró 2% este mes"
2. **Visualizaciones claras**: Gráficos de progreso auto-actualizados
3. **Reportes descargables**: PDF con su evolución
4. **Recomendaciones personalizadas**: "Basado en tu progreso, te sugerimos..."

---

## 💰 Costo Estimado

### Recursos Adicionales:
- **Celery Workers**: Ya existentes (sin costo adicional)
- **Redis**: Ya existente (sin costo adicional)
- **Qdrant Cloud**: Free tier suficiente para 100K vectores
- **GCS**: ~$0.02/GB/mes para reportes (estimado: $1-5/mes)
- **Gemini API**: ~$0.001/llamada (si se usa AI recommendations)

**Total estimado**: **$5-10/mes** adicionales

---

## 🚀 Beneficios

1. ✅ **UX mejorada**: Cálculos automáticos sin espera para el usuario
2. ✅ **Valor para profesionales**: Insights y reportes automáticos
3. ✅ **Escalabilidad**: Procesamiento asíncrono evita timeouts
4. ✅ **Inteligencia**: Vectorización habilita búsqueda semántica y agentes IA
5. ✅ **Diferenciación**: Análisis de tendencias y reportes PDF únicos

---

## 🤔 Consideraciones

### Privacidad:
- Embeddings no deben contener datos sensibles directamente
- Reportes PDF con URLs firmadas temporales (7 días)
- Compliance con HIPAA/GDPR para datos de salud

### Performance:
- Cálculos antropométricos: <2 segundos
- Vectorización: <3 segundos
- Análisis de tendencias: <5 segundos
- Generación PDF: <10 segundos

### Fallback:
- Si tarea falla, mostrar error amigable
- Retry automático 3 veces con exponential backoff
- DLQ para tareas fallidas persistentes

---

## 📚 Referencias

### Fórmulas de Composición Corporal:
- Jackson, A.S. & Pollock, M.L. (1978). Generalized equations for predicting body density of men.
- Durnin, J.V.G.A. & Womersley, J. (1974). Body fat assessed from total body density.
- Slaughter et al. (1988). Skinfold equations for estimation of body fatness in children and youth.

### Somatotipo:
- Heath, B.H. & Carter, J.E.L. (1967). A modified somatotype method.

### ISAK:
- International Society for the Advancement of Kinanthropometry (ISAK) Manual (2001).

---

## ✅ Próximos Pasos

1. **Revisar y aprobar** esta propuesta
2. **Priorizar tareas**: ¿Empezar con Fase 1 (cálculos)?
3. **Asignar recursos**: ¿Quién implementará?
4. **Timeline**: ¿4 semanas es razonable?
5. **Feedback**: ¿Algo que agregar/quitar?

¿Te gustaría que empiece con la **Fase 1** (implementación de cálculos antropométricos)?
