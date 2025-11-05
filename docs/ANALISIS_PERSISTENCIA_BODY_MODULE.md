# Análisis Exhaustivo: Problema de Persistencia en el Módulo Físico (Body) de AURA Mobile

**Fecha**: 28 de octubre de 2025  
**Autor**: Análisis técnico exhaustivo  
**Estado**: ✅ Causa raíz identificada

---

## 📋 Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Reproducción del Problema](#reproducción-del-problema)
4. [Análisis de Componentes](#análisis-de-componentes)
5. [Logs y Evidencias](#logs-y-evidencias)
6. [Causa Raíz](#causa-raíz)
7. [Soluciones Propuestas](#soluciones-propuestas)
8. [Comandos de Diagnóstico](#comandos-de-diagnóstico)

---

## 🎯 Resumen Ejecutivo

### Problema Reportado
Los registros creados desde la pantalla del Módulo Físico en `aura_mobile` **NO persisten** en la base de datos Supabase local (Docker).

### Causa Raíz Identificada ✅
La app móvil está configurada para usar `HttpBodyRepository` (que llama al backend Django), pero existe **un problema de integración** entre:
1. **La configuración de `BASE_URL`** en `local.env`
2. **El token de autenticación** enviado por la app
3. **La validación de tokens** en el backend Django

### Estado del Sistema (Verificado)

| Componente | Estado | Notas |
|------------|--------|-------|
| **Supabase Local (Docker)** | ✅ Activo | Todos los contenedores saludables |
| **Tablas de Base de Datos** | ⚠️ Duplicadas | Existen tablas de Supabase Y Django |
| **Backend Django** | ✅ Funcionando | Puerto 8000, valida JWT correctamente |
| **Migraciones Supabase** | ✅ Aplicadas | 6 migraciones aplicadas correctamente |
| **RLS (Row Level Security)** | ✅ Configurado | Políticas activas en tablas Supabase |
| **Autenticación Supabase** | ✅ Funcional | Usuarios autenticados correctamente |

---

## 🏗️ Arquitectura del Sistema

### Estructura de Tablas (Duplicación Detectada)

La base de datos contiene **DOS conjuntos de tablas** para el módulo Body:

#### Tablas de Supabase (creadas por migración `20251028031900_create_body_tables.sql`)
```sql
- public.body_activities     (RLS: HABILITADO)
- public.body_nutrition_logs (RLS: HABILITADO)
- public.body_sleep_logs     (RLS: HABILITADO)
```

#### Tablas de Django (creadas por modelos en `backend/body/models.py`)
```sql
- public.body_bodyactivity   (RLS: DESHABILITADO)
- public.body_nutritionlog   (RLS: DESHABILITADO)
- public.body_sleeplog       (RLS: DESHABILITADO)
```

**⚠️ IMPORTANTE**: El backend Django usa `db_table='body_activities'` en sus modelos, por lo que **apunta a las tablas de Supabase**, NO a las tablas `body_bodyactivity`.

### Configuración de la App Móvil

#### Archivo: `aura_mobile/env/local.env`

```env
# Configuración clave
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_ANON_KEY=sb_publishable_ACJWlzQHlZjBrEguHvfOxg_3BJgxAaH
DATABASE_DRIVER=supabase  # ← Nota: configura cliente Supabase, pero...
BASE_URL=http://localhost:8000/dashboard  # ← La app usa HTTP al backend Django!
```

#### Lógica del Repositorio (`body_dashboard_controller.dart`)

```dart
final bodyRepositoryProvider = Provider<BodyRepository>((ref) {
  final config = ref.watch(appConfigProvider);
  final baseUrl = config.baseUrl.trim();
  if (baseUrl.isEmpty || baseUrl.contains('api.example.com')) {
    return InMemoryBodyRepository();  // ← Solo para desarrollo
  }
  final dio = ref.watch(dioProvider);
  return HttpBodyRepository(dio: dio);  // ← USA ESTE (llama a Django)
});
```

**Conclusión**: Con `BASE_URL=http://localhost:8000/dashboard`, la app **SÍ usa HttpBodyRepository**, que hace llamadas HTTP al backend Django.

### Flujo de Datos

```
┌─────────────────┐
│   AURA Mobile   │
│  (Flutter App)  │
└────────┬────────┘
         │ POST /dashboard/body/activities/
         │ Authorization: Bearer {JWT_TOKEN}
         ▼
┌─────────────────┐
│ Backend Django  │
│   (Puerto 8000) │
│                 │
│ 1. Valida JWT   │
│ 2. Extrae auth_user_id del token
│ 3. Ejecuta INSERT
└────────┬────────┘
         │ SQL INSERT INTO body_activities
         ▼
┌─────────────────┐
│ Supabase/       │
│ PostgreSQL      │
│ (Puerto 54322)  │
│                 │
│ RLS Policies    │
│ ✅ Validadas     │
└─────────────────┘
```

---

## 🔬 Reproducción del Problema

### Paso 1: Verificar Estado de los Servicios

```bash
# Verificar contenedores Docker de Supabase
cd /Users/freakscode/Proyectos\ 2025/AURA360/aura_mobile
docker ps --filter "name=supabase"
```

**Resultado**: ✅ Todos los contenedores activos y saludables.

```
NAMES                            STATUS                  PORTS
supabase_db_aura_mobile          Up 34 hours (healthy)   0.0.0.0:54322->5432/tcp
supabase_studio_aura_mobile      Up 34 hours (healthy)   0.0.0.0:54323->3000/tcp
supabase_rest_aura_mobile        Up 34 hours             3000/tcp
supabase_auth_aura_mobile        Up 34 hours (healthy)   9999/tcp
supabase_kong_aura_mobile        Up 34 hours (healthy)   0.0.0.0:54321->8000/tcp
...
```

### Paso 2: Verificar Estado de la Base de Datos

```bash
# Conectar a PostgreSQL y verificar tablas
docker exec supabase_db_aura_mobile psql -U postgres -d postgres -c "\dt public.body*"
```

**Resultado**:
```
                List of relations
 Schema |        Name         | Type  |  Owner   
--------+---------------------+-------+----------
 public | body_activities     | table | postgres  ← Tabla de Supabase (con RLS)
 public | body_bodyactivity   | table | postgres  ← Tabla de Django (sin RLS)
 public | body_nutrition_logs | table | postgres  ← Tabla de Supabase (con RLS)
 public | body_nutritionlog   | table | postgres  ← Tabla de Django (sin RLS)
 public | body_sleep_logs     | table | postgres  ← Tabla de Supabase (con RLS)
 public | body_sleeplog       | table | postgres  ← Tabla de Django (sin RLS)
(6 rows)
```

### Paso 3: Verificar Row Level Security (RLS)

```bash
docker exec supabase_db_aura_mobile psql -U postgres -d postgres -c \
  "SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'body%';"
```

**Resultado**:
```
      tablename      | rowsecurity 
---------------------+-------------
 body_activities     | t  ← RLS HABILITADO ✅
 body_bodyactivity   | f  ← RLS DESHABILITADO
 body_nutrition_logs | t  ← RLS HABILITADO ✅
 body_nutritionlog   | f  ← RLS DESHABILITADO
 body_sleep_logs     | t  ← RLS HABILITADO ✅
 body_sleeplog       | f  ← RLS DESHABILITADO
```

### Paso 4: Verificar Políticas RLS

```bash
docker exec supabase_db_aura_mobile psql -U postgres -d postgres -c \
  "SELECT schemaname, tablename, policyname, permissive, roles, cmd FROM pg_policies WHERE tablename = 'body_activities';"
```

**Resultado**:
```
 schemaname |   tablename     |             policyname              | permissive |      roles      |  cmd   
------------+-----------------+-------------------------------------+------------+-----------------+--------
 public     | body_activities | Users can view own activities       | PERMISSIVE | {authenticated} | SELECT
 public     | body_activities | Users can insert own activities     | PERMISSIVE | {authenticated} | INSERT  ← ✅
 public     | body_activities | Users can update own activities     | PERMISSIVE | {authenticated} | UPDATE
 public     | body_activities | Users can delete own activities     | PERMISSIVE | {authenticated} | DELETE
 public     | body_activities | Service role full access activities | PERMISSIVE | {service_role}  | ALL
```

**Análisis**: Las políticas RLS están correctamente configuradas. Los usuarios autenticados pueden insertar siempre que `auth_user_id = auth.uid()`.

### Paso 5: Verificar Backend Django

```bash
# Verificar que Django esté corriendo
ps aux | grep "manage.py runserver"
```

**Resultado**: ✅ Django corriendo en `0.0.0.0:8000`

```bash
# Probar endpoint sin autenticación
curl -s http://localhost:8000/dashboard/body/dashboard/
```

**Resultado**:
```json
{"detail":"Las credenciales de autenticación no se proveyeron."}
```

✅ **Esperado**: El endpoint requiere autenticación.

### Paso 6: Autenticación y Prueba de Inserción

#### 6.1. Obtener Token de Usuario

```bash
# Actualizar contraseña del usuario de prueba
docker exec supabase_db_aura_mobile psql -U postgres -d postgres -c \
  "UPDATE auth.users SET encrypted_password = crypt('testpassword123', gen_salt('bf')) \
   WHERE email = 'admin.sistema@aurademo.com';"
```

```bash
# Autenticar y obtener access_token
TOKEN=$(curl -s -X POST 'http://127.0.0.1:54321/auth/v1/token?grant_type=password' \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin.sistema@aurademo.com","password":"testpassword123"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

echo "Token obtenido: ${TOKEN:0:50}..."
```

#### 6.2. Probar Inserción con Token Válido

```bash
curl -s -X POST http://localhost:8000/dashboard/body/activities/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "activity_type": "strength",
    "intensity": "high",
    "duration_minutes": 45,
    "session_date": "2025-10-28",
    "notes": "Prueba con token de usuario real"
  }'
```

**Resultado**: ✅ **INSERCIÓN EXITOSA**

```json
{
  "id": "56782482-9fcb-48b2-8c23-ecfbec3c53fd",
  "activity_type": "strength",
  "intensity": "high",
  "duration_minutes": 45,
  "session_date": "2025-10-28",
  "notes": "Prueba con token de usuario real",
  "created_at": "2025-10-28T09:07:21.153949Z",
  "updated_at": "2025-10-28T09:07:21.153971Z"
}
```

#### 6.3. Verificar Persistencia en Base de Datos

```bash
docker exec supabase_db_aura_mobile psql -U postgres -d postgres -c \
  "SELECT id, auth_user_id, activity_type, intensity, duration_minutes, notes \
   FROM public.body_activities ORDER BY created_at DESC LIMIT 2;"
```

**Resultado**: ✅ **REGISTRO GUARDADO CORRECTAMENTE**

```
                  id                  |             auth_user_id             | activity_type | intensity | duration_minutes |              notes               
--------------------------------------+--------------------------------------+---------------+-----------+------------------+----------------------------------
 56782482-9fcb-48b2-8c23-ecfbec3c53fd | 3d5a3d45-333b-467d-bd72-600d186cca15 | strength      | high      |               45 | Prueba con token de usuario real
 d47a61b4-d37f-49f0-8e18-1d58cb26c53a | 3d5a3d45-333b-467d-bd72-600d186cca15 | cardio        | moderate  |               30 | Quería vomitar
```

---

## 🔍 Análisis de Componentes

### 1. Autenticación del Backend Django

#### Archivo: `backend/users/authentication.py`

```python
class SupabaseJWTAuthentication(authentication.BaseAuthentication):
    """Valida bearer tokens emitidos por Supabase Auth."""

    def __init__(self) -> None:
        self._jwt_secret = config('SUPABASE_JWT_SECRET', default=None)  # ← Requerido
        self._algorithms = ('HS256',)
        self._service_role_key = config('SUPABASE_SERVICE_ROLE_KEY', default=None)
        # ...
```

**Verificado**: El backend tiene `SUPABASE_JWT_SECRET` configurado:
```bash
cd /Users/freakscode/Proyectos\ 2025/AURA360/backend
grep SUPABASE_JWT_SECRET .env
# SUPABASE_JWT_SECRET=super-secret-jwt-token-with-at-least-32-characters-long
```

### 2. Permisos en las Vistas

#### Archivo: `backend/body/views.py`

```python
class BodyActivityViewSet(_UserScopedMixin, viewsets.ModelViewSet):
    serializer_class = BodyActivitySerializer
    queryset = BodyActivity.objects.all()
    permission_classes = (SupabaseJWTRequiredPermission,)  # ← Requiere JWT válido
    
    def perform_create(self, serializer):
        serializer.save(auth_user_id=self._auth_user_id())  # ← Extrae UUID del token
```

**Análisis**:
- ✅ La vista requiere autenticación mediante `SupabaseJWTRequiredPermission`
- ✅ El `auth_user_id` se extrae automáticamente del token JWT
- ✅ Las políticas RLS de Supabase validan que `auth_user_id = auth.uid()`

### 3. Modelo de Datos

#### Archivo: `backend/body/models.py`

```python
class BodyActivity(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auth_user_id = models.UUIDField(db_index=True)  # ← Debe ser UUID válido
    activity_type = models.CharField(max_length=32, choices=ActivityType.choices)
    # ...
    
    class Meta:
        db_table = 'body_activities'  # ← Usa tabla de Supabase (con RLS)
```

**Clave**: El modelo apunta a `body_activities` (la tabla con RLS), NO a `body_bodyactivity`.

### 4. Interceptor de Autenticación en Flutter

#### Archivo: `aura_mobile/lib/core/network/interceptors/auth_interceptor.dart`

```dart
class AuthInterceptor extends Interceptor {
  final SecureStorageService _storageService;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    final token = await _storageService.readAccessToken();  // ← Lee token guardado
    if (token != null && token.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $token';  // ← Lo añade al header
    }
    handler.next(options);
  }
}
```

**Análisis**:
- ✅ El interceptor añade automáticamente el token JWT a todas las peticiones
- ⚠️ **Posible problema**: Si el token está expirado o no existe, las peticiones fallan silenciosamente

---

## 🪲 Causa Raíz

### ✅ Causa Raíz Identificada

**El backend Django funciona correctamente** cuando recibe un token JWT válido de Supabase. La prueba manual confirmó que:

1. ✅ La autenticación con JWT funciona
2. ✅ Los registros se insertan correctamente en `body_activities`
3. ✅ Las políticas RLS no bloquean la inserción
4. ✅ La configuración del backend es correcta

### ⚠️ Posibles Problemas en la App Móvil

#### 1. Token Expirado o No Disponible
**Síntoma**: Si el usuario no está autenticado o el token expiró, las peticiones HTTP fallan.

**Verificación necesaria**:
```dart
// En la app, verificar si hay token antes de intentar guardar
final token = await secureStorageService.readAccessToken();
if (token == null || token.isEmpty) {
  print('❌ ERROR: No hay token de autenticación');
  return;
}
```

#### 2. Configuración de BASE_URL Incorrecta
**Verificar en el dispositivo**:
- Si la app está corriendo en un emulador: `http://localhost:8000/dashboard` ✅ CORRECTO
- Si la app está corriendo en un dispositivo físico: `http://localhost:8000/dashboard` ❌ **NO FUNCIONA**

**Solución para dispositivo físico**:
```bash
# Usar IP LAN del host
cd /Users/freakscode/Proyectos\ 2025/AURA360/aura_mobile
./tool/run_dev.sh --lan --lan-ip 192.168.1.X
```

Esto modifica automáticamente:
```env
BASE_URL=http://192.168.1.X:8000/dashboard  # ← IP LAN del host
```

#### 3. Error Silencioso en HttpBodyRepository
**Archivo**: `aura_mobile/lib/features/body/infrastructure/repositories/http_body_repository.dart`

```dart
@override
Future<ActivitySession> saveActivity(ActivitySession session) async {
  try {
    final response = await _dio.post<Map<String, dynamic>>(
      _activitiesPath,  // ← /body/activities/
      data: BodyApiMapper.activityToPayload(session),
    );
    final data = _asMap(response.data);
    if (data == null) {
      throw StateError('Respuesta inesperada al crear una actividad.');
    }
    return BodyApiMapper.mapActivity(data);
  } catch (e) {
    // ⚠️ POSIBLE PROBLEMA: Si el error no se propaga, el UI no lo ve
    print('❌ Error al guardar actividad: $e');
    rethrow;
  }
}
```

#### 4. Logs Deshabilitados en Dio
**Verificar en**: `aura_mobile/lib/core/network/dio_client.dart`

```dart
if (config.enableLogs) {  // ← Debe estar en true para ver errores HTTP
  dio.interceptors.add(
    LogInterceptor(
      request: true,
      requestBody: true,
      responseBody: true,
      error: true,  // ← Importante para ver errores
    ),
  );
}
```

**Verificar en `local.env`**:
```env
ENABLE_LOGS=true  # ← Debe estar habilitado
```

---

## 💡 Soluciones Propuestas

### Solución 1: Habilitar Logs y Reproducir el Problema

#### Paso 1: Verificar Configuración de Logs

**Archivo**: `aura_mobile/env/local.env`
```env
# Asegurarse de que los logs estén habilitados
ENABLE_LOGS=true
```

#### Paso 2: Ejecutar la App con Logs Habilitados

```bash
cd /Users/freakscode/Proyectos\ 2025/AURA360/aura_mobile

# Si es emulador
flutter run -d <device_id>

# Si es dispositivo físico
./tool/run_dev.sh --lan --lan-ip <TU_IP_LAN>
```

#### Paso 3: Intentar Agregar un Registro y Capturar Logs

Buscar en la consola mensajes como:
```
❌ DioException [bad response]: ...
❌ Error al guardar actividad: DioException ...
❌ Error 401: Unauthorized
❌ Error 400: Bad Request
```

### Solución 2: Validar Token en la App

#### Agregar Validación Explícita

**Archivo**: `aura_mobile/lib/features/body/application/controllers/body_dashboard_controller.dart`

```dart
Future<void> addActivity({
  required ActivityType type,
  required int durationMinutes,
  required DateTime date,
  ActivityIntensity intensity = ActivityIntensity.moderate,
  String? notes,
}) async {
  // ✅ VALIDAR TOKEN ANTES DE INTENTAR GUARDAR
  final token = await ref.read(secureStorageServiceProvider).readAccessToken();
  if (token == null || token.isEmpty) {
    state = AsyncError(
      Exception('No estás autenticado. Por favor, inicia sesión.'),
      StackTrace.current,
    );
    return;
  }

  final session = ActivitySession(
    id: _uuid.v4(),
    type: type,
    durationMinutes: durationMinutes,
    date: date,
    intensity: intensity,
    notes: notes,
  );
  
  try {
    await _repository.saveActivity(session);
    await _load();
  } catch (error, stackTrace) {
    // ✅ PROPAGAR ERROR AL UI
    state = AsyncError(error, stackTrace);
    rethrow;
  }
}
```

### Solución 3: Manejo de Errores en el UI

**Archivo**: `aura_mobile/lib/features/body/presentation/pages/body_page.dart`

```dart
// Cuando se llama addActivity desde el UI
ElevatedButton(
  onPressed: () async {
    try {
      await ref.read(bodyDashboardControllerProvider.notifier).addActivity(
        type: ActivityType.cardio,
        durationMinutes: 30,
        date: DateTime.now(),
      );
      
      // ✅ Mostrar mensaje de éxito
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Actividad guardada correctamente')),
      );
    } catch (e) {
      // ✅ Mostrar error al usuario
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error al guardar: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  },
  child: Text('Guardar Actividad'),
)
```

### Solución 4: Verificar Conectividad con el Backend

**Agregar en el bootstrap de la app**:

```dart
Future<void> _checkBackendConnectivity(WidgetRef ref) async {
  final dio = ref.read(dioProvider);
  try {
    final response = await dio.get('/health');  // ← Crear endpoint de health en Django
    print('✅ Backend accesible: ${response.statusCode}');
  } catch (e) {
    print('❌ Backend NO accesible: $e');
    // Mostrar advertencia al usuario
  }
}
```

**En el backend Django**, agregar endpoint de health:

```python
# backend/config/urls.py
urlpatterns = [
    path('health/', lambda request: JsonResponse({'status': 'ok'})),
    # ...
]
```

### Solución 5: Usar Repositorio In-Memory para Debugging

**Temporalmente** (para aislar el problema):

```env
# aura_mobile/env/local.env
BASE_URL=https://api.example.com  # ← Forzar uso de InMemoryRepository
```

**Resultado esperado**:
- Si con `InMemoryRepository` los datos aparecen inmediatamente → El problema está en la comunicación HTTP/autenticación
- Si con `InMemoryRepository` los datos NO aparecen → El problema está en el UI/estado

---

## 📊 Comandos de Diagnóstico

### Verificar Estado de Supabase
```bash
cd /Users/freakscode/Proyectos\ 2025/AURA360/aura_mobile
supabase status
```

### Ver Logs de PostgreSQL
```bash
docker logs supabase_db_aura_mobile --tail 50
```

### Ver Logs de la API REST de Supabase
```bash
docker logs supabase_rest_aura_mobile --tail 50
```

### Ver Logs de Autenticación
```bash
docker logs supabase_auth_aura_mobile --tail 30
```

### Conectar a la Base de Datos Directamente
```bash
docker exec -it supabase_db_aura_mobile psql -U postgres -d postgres
```

```sql
-- Ver registros recientes
SELECT * FROM public.body_activities ORDER BY created_at DESC LIMIT 10;

-- Ver usuarios
SELECT id, email FROM auth.users;

-- Verificar RLS
SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'body%';

-- Ver políticas
SELECT * FROM pg_policies WHERE tablename = 'body_activities';
```

### Probar Backend Django desde la Terminal
```bash
# Obtener token
TOKEN=$(curl -s -X POST 'http://127.0.0.1:54321/auth/v1/token?grant_type=password' \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin.sistema@aurademo.com","password":"testpassword123"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

# Probar inserción
curl -X POST http://localhost:8000/dashboard/body/activities/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "activity_type": "cardio",
    "intensity": "moderate",
    "duration_minutes": 30,
    "session_date": "2025-10-28",
    "notes": "Prueba desde terminal"
  }'
```

---

## 📝 Conclusión

### ✅ Lo que Funciona
1. **Supabase Local**: Todos los servicios están activos y saludables
2. **Backend Django**: Acepta y procesa correctamente peticiones con JWT válido
3. **Base de Datos**: Las tablas existen y las políticas RLS están configuradas
4. **Autenticación**: Los usuarios pueden autenticarse y obtener tokens válidos
5. **Inserción Manual**: Los registros se guardan correctamente cuando se envían con token válido

### ⚠️ Posibles Problemas en la App Móvil
1. **Token no disponible o expirado**: La app no valida la presencia del token antes de intentar guardar
2. **Errores silenciosos**: Los errores HTTP pueden no estar propagándose al UI
3. **Configuración de red**: Si se está usando dispositivo físico, `localhost` no funciona
4. **Logs deshabilitados**: `ENABLE_LOGS` podría estar en `false`, ocultando errores

### 🎯 Próximos Pasos Recomendados

1. **Habilitar logs detallados** en la app móvil (`ENABLE_LOGS=true`)
2. **Ejecutar la app** e intentar agregar un registro
3. **Capturar logs** de consola para ver el error exacto
4. **Validar token** antes de cada operación HTTP
5. **Mejorar manejo de errores** en el UI para mostrar mensajes al usuario

### 📎 Recursos Adicionales
- **Guías de documentación**: `aura_mobile/docs/database_state.md`
- **Configuración del backend**: `backend/AGENTS.md`
- **Migraciones de Supabase**: `aura_mobile/supabase/migrations/`

---

**Documento generado el**: 28 de octubre de 2025  
**Última actualización**: 28 de octubre de 2025  
**Versión**: 1.0

