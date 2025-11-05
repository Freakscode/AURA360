# Quickstart - Módulo de Planes Nutricionales

## Pasos Rápidos para Empezar

### 1️⃣ Ejecutar Migración de Base de Datos

```bash
cd aura_mobile/supabase
supabase migration up
```

**Verificar que se aplicó correctamente**:

```bash
supabase migration list
```

Deberías ver `20251028_create_nutrition_plans_table` en estado `Applied`.

---

### 2️⃣ Verificar Tabla en Base de Datos

```sql
-- Conectarse a la base de datos
supabase db reset  # Solo si es necesario

-- Verificar tabla
SELECT * FROM nutrition_plans;

-- Verificar políticas RLS
SELECT * FROM pg_policies WHERE tablename = 'nutrition_plans';
```

---

### 3️⃣ Reiniciar Backend Django

```bash
cd backend
source .venv/bin/activate  # Si usas venv
# o
uv sync  # Si usas uv

# Reiniciar servidor
uv run python manage.py runserver 0.0.0.0:8000
```

**Verificar que el endpoint está disponible**:

```bash
# Deberías ver /dashboard/body/nutrition-plans/ en la lista
curl http://localhost:8000/dashboard/ -H "Authorization: Bearer <token>"
```

---

### 4️⃣ Probar API con Ejemplo

#### a) Obtener Token JWT

Primero necesitas un token de Supabase Auth:

```bash
# Login en la app móvil o usa el siguiente comando si tienes credenciales
curl -X POST https://<tu-proyecto>.supabase.co/auth/v1/token?grant_type=password \
  -H "apikey: <tu-anon-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "tu@email.com",
    "password": "tu-password"
  }'
```

Guarda el `access_token` que te devuelve.

#### b) Crear un Plan de Prueba

```bash
export TOKEN="<tu-access-token-aqui>"

curl -X POST http://localhost:8000/dashboard/body/nutrition-plans/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @docs/nutrition_plan_example.json
```

Si todo funciona correctamente, deberías recibir una respuesta con el plan creado, incluyendo su `id`.

#### c) Listar Tus Planes

```bash
curl http://localhost:8000/dashboard/body/nutrition-plans/ \
  -H "Authorization: Bearer $TOKEN"
```

#### d) Filtrar Solo Planes Activos

```bash
curl "http://localhost:8000/dashboard/body/nutrition-plans/?active=true" \
  -H "Authorization: Bearer $TOKEN"
```

#### e) Obtener Plan Específico

```bash
# Reemplaza {id} con el ID del plan
curl http://localhost:8000/dashboard/body/nutrition-plans/{id}/ \
  -H "Authorization: Bearer $TOKEN"
```

---

### 5️⃣ Integrar en Flutter

#### a) Registrar Repositorio en DI

Si usas Riverpod para dependency injection, registra el repositorio:

```dart
// lib/app/providers.dart (o donde tengas tus providers)

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:aura_mobile/features/body/domain/repositories/nutrition_plan_repository.dart';
import 'package:aura_mobile/features/body/infrastructure/repositories/http_nutrition_plan_repository.dart';

final nutritionPlanRepositoryProvider = Provider<NutritionPlanRepository>((ref) {
  final dio = ref.watch(dioProvider); // Tu provider de Dio existente
  return HttpNutritionPlanRepository(dio: dio);
});
```

#### b) Usar en un Controller o State

```dart
// Ejemplo: Controller para planes nutricionales

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:aura_mobile/features/body/domain/entities/nutrition_plan.dart';
import 'package:aura_mobile/features/body/domain/repositories/nutrition_plan_repository.dart';

class NutritionPlanController extends StateNotifier<AsyncValue<List<NutritionPlan>>> {
  NutritionPlanController(this._repository) : super(const AsyncValue.loading()) {
    loadPlans();
  }

  final NutritionPlanRepository _repository;

  Future<void> loadPlans({bool? activeOnly}) async {
    state = const AsyncValue.loading();
    try {
      final plans = await _repository.getPlans(activeOnly: activeOnly);
      state = AsyncValue.data(plans);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<NutritionPlan?> getActivePlan() async {
    try {
      return await _repository.getActivePlan();
    } catch (e) {
      return null;
    }
  }
}

// Provider del controller
final nutritionPlanControllerProvider = 
    StateNotifierProvider<NutritionPlanController, AsyncValue<List<NutritionPlan>>>((ref) {
  final repository = ref.watch(nutritionPlanRepositoryProvider);
  return NutritionPlanController(repository);
});
```

#### c) Usar en UI

```dart
// Ejemplo: Página para mostrar planes

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class NutritionPlansPage extends ConsumerWidget {
  const NutritionPlansPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final plansState = ref.watch(nutritionPlanControllerProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Mis Planes Nutricionales'),
      ),
      body: plansState.when(
        data: (plans) => plans.isEmpty
            ? const Center(child: Text('No tienes planes aún'))
            : ListView.builder(
                itemCount: plans.length,
                itemBuilder: (context, index) {
                  final plan = plans[index];
                  return ListTile(
                    title: Text(plan.title),
                    subtitle: Text(
                      'Vigente hasta: ${plan.validUntil?.toString() ?? "Sin fecha"}',
                    ),
                    trailing: Icon(
                      plan.isValid ? Icons.check_circle : Icons.cancel,
                      color: plan.isValid ? Colors.green : Colors.red,
                    ),
                    onTap: () {
                      // Navegar a detalle del plan
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => PlanDetailPage(plan: plan),
                        ),
                      );
                    },
                  );
                },
              ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(child: Text('Error: $error')),
      ),
    );
  }
}
```

---

## 🧪 Verificación Final

### Checklist de Funcionamiento

- [ ] Migración ejecutada sin errores
- [ ] Tabla `nutrition_plans` existe en Supabase
- [ ] Políticas RLS están activas
- [ ] Backend responde en `/dashboard/body/nutrition-plans/`
- [ ] Puedes crear un plan con el ejemplo JSON
- [ ] Puedes listar tus planes
- [ ] Puedes obtener un plan específico
- [ ] Flutter puede llamar al endpoint

---

## 🐛 Troubleshooting

### Error: "relation 'nutrition_plans' does not exist"

**Solución**: La migración no se aplicó. Ejecuta:

```bash
cd aura_mobile/supabase
supabase migration up
```

### Error: "JWT token is invalid"

**Solución**: Tu token expiró o es inválido. Genera uno nuevo:

```bash
# Desde la app móvil, haz login y copia el token
# O usa el endpoint de Supabase Auth
```

### Error: "Faltan campos requeridos en plan_data"

**Solución**: Revisa que tu JSON tenga al menos:
- `plan` con `source` y `language`
- `subject`
- `directives` con `meals`

Usa el ejemplo en `docs/nutrition_plan_example.json` como referencia.

### Error: "Row Level Security policy violation"

**Solución**: Asegúrate de que:
1. Estás usando un token JWT válido de Supabase
2. El token corresponde a un usuario existente
3. Las políticas RLS se aplicaron correctamente

Verifica políticas:

```sql
SELECT * FROM pg_policies WHERE tablename = 'nutrition_plans';
```

### Flutter: "Failed host lookup"

**Solución**: Verifica que el backend está corriendo y accesible:

```bash
# Si usas emulador Android
http://10.0.2.2:8000

# Si usas dispositivo físico
http://<tu-ip-local>:8000

# Si usas iOS simulator
http://localhost:8000
```

Actualiza `BACKEND_URL` en tu `env/local.env`.

---

## 📚 Recursos Adicionales

- **Documentación Completa**: `docs/NUTRITION_PLANS_MODULE.md`
- **Resumen de Implementación**: `docs/NUTRITION_PLANS_IMPLEMENTATION_SUMMARY.md`
- **Ejemplo JSON**: `docs/nutrition_plan_example.json`
- **Esquema de BD**: `aura_mobile/supabase/migrations/20251028_create_nutrition_plans_table.sql`

---

## 🚀 Próximos Pasos

Una vez que todo funcione:

1. **Crear UI en Flutter** para visualizar planes
2. **Implementar páginas de detalle** de cada plan
3. **Agregar navegación** desde la sección de nutrición
4. **Mostrar comidas del día** basadas en el plan activo
5. **Comparar registros** vs. plan prescrito

---

**¡Listo para empezar! 🎉**

Si tienes algún problema, revisa la sección de troubleshooting o consulta la documentación completa.

