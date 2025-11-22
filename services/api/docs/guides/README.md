# AURA365 Backend API

Backend de la aplicación AURA365 construido con Django y Django REST Framework. Este backend proporciona una API REST completa para gestionar usuarios y servicios, diseñado para integrarse con Supabase Auth y funcionar con múltiples aplicaciones cliente.

## 📋 Tabla de Contenidos

- [Características](#características)
- [Tecnologías](#tecnologías)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Endpoints de la API](#endpoints-de-la-api)
- [Documentación de la API](#documentación-de-la-api)
- [Panel de Administración](#panel-de-administración)

---

## ✨ Características

- **API REST completa** con Django REST Framework
- **Integración con Supabase** (PostgreSQL + Auth)
- **Documentación automática** con OpenAPI/Swagger
- **Sistema de usuarios** con tiers (free/premium)
- **Filtrado, búsqueda y paginación** en todos los endpoints
- **Panel de administración** personalizado
- **CORS configurado** para aplicaciones web/móviles
- **Variables de entorno** para configuración segura

---

## 🛠 Tecnologías

- **Django 5.2.7** - Framework web de Python
- **Django REST Framework 3.16** - Toolkit para APIs REST
- **PostgreSQL** - Base de datos (via Supabase)
- **drf-spectacular** - Generación de esquemas OpenAPI
- **django-cors-headers** - Manejo de CORS
- **python-decouple** - Gestión de variables de entorno
- **uv** - Gestor de paquetes y entornos virtuales

---

## 📁 Estructura del Proyecto

```
backend/
├── config/                 # Configuración principal de Django
│   ├── __init__.py
│   ├── settings.py        # Configuración de la aplicación
│   ├── urls.py            # Routing principal
│   ├── wsgi.py            # Configuración WSGI
│   └── asgi.py            # Configuración ASGI
│
├── users/                  # App de gestión de usuarios
│   ├── migrations/        # Migraciones (vacío, managed=False)
│   ├── __init__.py
│   ├── models.py          # Modelo AppUser
│   ├── serializers.py     # Serializers para la API
│   ├── views.py           # ViewSets y endpoints
│   ├── urls.py            # URLs de la app
│   ├── admin.py           # Configuración del admin
│   └── tests.py           # Tests (próximamente)
│
├── docs/                   # Documentación
│   ├── database_schema.md # Esquema de base de datos
│   └── guides/            # Guías generadas (este archivo, quickstart, etc.)
│
├── scripts/               # Scripts operativos
│   └── test_db_connection.py # Verificación de base de datos
│
├── manage.py              # Script de gestión de Django
├── pyproject.toml         # Dependencias del proyecto
├── uv.lock                # Lock file de dependencias
├── README.md              # Resumen general y enlaces
├── AGENTS.md              # Guía para contribuidores
├── .env                   # Variables de entorno (no en git)
├── .env.example           # Ejemplo de variables de entorno
└── .gitignore             # Archivos ignorados por git
```

---

## 🚀 Instalación

### Prerequisitos

- Python 3.13.7 o superior
- PostgreSQL (o acceso a Supabase)
- `uv` instalado ([instrucciones aquí](https://github.com/astral-sh/uv))

### Pasos

1. **Clonar el repositorio** (o navegar al directorio del backend):

```bash
cd backend
```

2. **Crear el entorno virtual con uv**:

```bash
uv venv
```

3. **Activar el entorno virtual**:

```bash
# En macOS/Linux:
source .venv/bin/activate

# En Windows:
.venv\Scripts\activate
```

4. **Instalar dependencias**:

```bash
uv sync
```

5. **Configurar variables de entorno**:

Copia el archivo `.env.example` a `.env` y ajusta los valores:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales de base de datos.

6. **Inicializar base de datos** (opcional, si no usas Supabase):

```bash
python manage.py migrate
```

> **Nota**: Si usas Supabase, las migraciones son manejadas por Supabase, no por Django. El modelo `AppUser` tiene `managed=False`.

7. **Crear superusuario** para el admin:

```bash
python manage.py createsuperuser
```

También puedes automatizar la creación de cuentas administrativas con:

```bash
python manage.py create_admin_user --email admin@aurademo.com --password "S3guro!" --superuser --first-name Admin --last-name Demo
```

> Usa `--superuser` para permisos completos o quítalo para generar usuarios de staff. Si omites `--password`, el comando solicitará la contraseña de forma segura.

8. **Ejecutar el servidor de desarrollo**:

```bash
python manage.py runserver
```

El servidor estará disponible en `http://localhost:8000`

---

## ⚙️ Configuración

### Variables de Entorno

El archivo `.env` debe contener las siguientes variables:

```ini
# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=54322  # Puerto default de Supabase local

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# API Configuration
API_VERSION=v1

# Supabase Integration
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_API_URL=http://127.0.0.1:54321
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SECRET_KEY=sb_secret_...
SUPABASE_JWT_SECRET=super-secret-jwt-token-with-at-least-32-characters-long
SUPABASE_ALLOW_SERVICE_ROLE_BEARER=true
```

### Conexión con Supabase Local

Si usas Supabase localmente (con `supabase start`), usa estos valores:

```ini
DB_HOST=localhost
DB_PORT=54322
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=postgres
# Obtén el resto de variables con `supabase status -o env`
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_API_URL=http://127.0.0.1:54321
SUPABASE_SERVICE_ROLE_KEY=<SERVICE_ROLE_KEY de supabase status>
SUPABASE_SECRET_KEY=<SECRET_KEY de supabase status>
SUPABASE_JWT_SECRET=<JWT_SECRET de supabase status>
SUPABASE_ALLOW_SERVICE_ROLE_BEARER=true
```

> Ejecuta `supabase status -o env` para copiar estos valores cuando desarrolles con OrbStack/Supabase CLI. Para Supabase Cloud toma las llaves Publishable/Secret y el JWT secret desde Settings → API.

### Conexión con Supabase Remoto

Para conectar con tu proyecto de Supabase en la nube:

1. Ve a tu proyecto en Supabase Dashboard
2. Ve a **Settings > Database**
3. Copia los valores de conexión:

```ini
DB_HOST=db.xxxxxxxxxxxxx.supabase.co
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=tu-password-de-db
DB_NAME=postgres
# Supabase Cloud
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_API_URL=https://<project>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<Service Role Key>
SUPABASE_SECRET_KEY=<Secret Key>
SUPABASE_JWT_SECRET=<JWT Secret>
SUPABASE_ALLOW_SERVICE_ROLE_BEARER=true
SUPABASE_JWT_ALGORITHMS=RS256,HS256
SUPABASE_JWKS_URL=https://<project>.supabase.co/auth/v1/.well-known/jwks.json
```

---

## 💻 Uso

### Servidor de Desarrollo

```bash
# Activar entorno virtual
source .venv/bin/activate

# Iniciar servidor
python manage.py runserver

# Iniciar en un puerto específico
python manage.py runserver 8080
```

### Comandos Útiles

```bash
# Ver estructura de la base de datos
python manage.py inspectdb

# Crear migraciones (si decides hacer managed=True)
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Abrir shell interactivo con Django
python manage.py shell

# Colectar archivos estáticos
python manage.py collectstatic
```

---

## 📡 Endpoints de la API

Todos los endpoints están bajo la ruta base `/dashboard/`.

### Usuarios (`/dashboard/users/`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/dashboard/users/` | Lista todos los usuarios (paginado) |
| `POST` | `/dashboard/users/` | Crea un nuevo usuario |
| `GET` | `/dashboard/users/{id}/` | Obtiene un usuario específico |
| `PUT` | `/dashboard/users/{id}/` | Actualiza un usuario completo |
| `PATCH` | `/dashboard/users/{id}/` | Actualiza parcialmente un usuario |
| `DELETE` | `/dashboard/users/{id}/` | Elimina un usuario |

### Endpoints Adicionales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/dashboard/users/by_auth_id/{uuid}/` | Busca usuario por UUID de Supabase Auth |
| `GET` | `/dashboard/users/premium/` | Lista solo usuarios premium |
| `GET` | `/dashboard/users/free/` | Lista solo usuarios free |
| `GET` | `/dashboard/users/stats/` | Estadísticas agregadas de usuarios |
| `GET` | `/dashboard/users/roles/` | Resumen de usuarios agrupados por rol global |
| `GET` | `/dashboard/users/roles/{rol}/` | Lista usuarios que pertenecen a un rol específico |
| `POST` | `/dashboard/users/{id}/upgrade_to_premium/` | Actualiza usuario a premium |
| `POST` | `/dashboard/users/{id}/downgrade_to_free/` | Actualiza usuario a free |
| `POST` | `/dashboard/users/{id}/set-role/` | Actualiza rol global, independencia o plan (requiere token `service_role`) |
| `POST` | `/dashboard/users/provision/` | Crea usuario directamente en Supabase Auth y sincroniza app_users |

### Vistas HTML de apoyo

- `GET /dashboard/users/roles/manage/` → panel básico para revisar conteos por rol.
- `GET /dashboard/users/roles/manage/<rol>/` → listado filtrado por rol con buscador por nombre/email.

Estas vistas requieren iniciar sesión en el admin de Django y sirven como herramientas operativas mientras se construye la UI definitiva.

### Parámetros de Query

**Filtrado:**
```
GET /dashboard/users/?tier=premium
GET /dashboard/users/?gender=male
GET /dashboard/users/?age=25
GET /dashboard/users/?min_age=18&max_age=65
GET /dashboard/users/?role_global=Paciente
GET /dashboard/users/?billing_plan=individual
```

**Búsqueda:**
```
GET /dashboard/users/?search=Juan
GET /dashboard/users/?search=example@email.com
```

**Ordenamiento:**
```
GET /dashboard/users/?ordering=-created_at
GET /dashboard/users/?ordering=full_name
GET /dashboard/users/?ordering=-age
```

**Paginación:**
```
GET /dashboard/users/?page=2
GET /dashboard/users/?page_size=50
```

### Ejemplos de Respuesta

**Listado de usuarios** (`GET /dashboard/users/`):

```json
{
  "count": 100,
  "next": "http://localhost:8000/dashboard/users/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "auth_user_id": "550e8400-e29b-41d4-a716-446655440000",
      "full_name": "Juan Pérez",
      "email": "juan@example.com",
      "tier": "premium",
      "tier_display": "Premium",
      "created_at": "2025-10-04T10:30:00Z"
    }
  ]
}
```

**Usuario individual** (`GET /dashboard/users/1/`):

```json
{
  "id": 1,
  "auth_user_id": "550e8400-e29b-41d4-a716-446655440000",
  "full_name": "Juan Pérez",
  "age": 30,
  "email": "juan@example.com",
  "phone_number": "+52 1234567890",
  "gender": "male",
  "tier": "premium",
  "tier_display": "Premium",
  "is_premium": true,
  "is_free": false,
  "created_at": "2025-10-04T10:30:00Z",
  "updated_at": "2025-10-04T15:20:00Z"
}
```

**Estadísticas** (`GET /dashboard/users/stats/`):

```json
{
  "total_users": 100,
  "free_users": 80,
  "premium_users": 20,
  "average_age": 32.5
}
```

---

## 📚 Documentación de la API

Django genera automáticamente documentación interactiva de la API:

### Swagger UI (Recomendado)

```
http://localhost:8000/docs/  (alias disponible en /api/docs/)
```

Interfaz interactiva donde puedes:
- Ver todos los endpoints disponibles
- Probar las peticiones directamente
- Ver esquemas de datos
- Descargar el esquema OpenAPI

### ReDoc

```
http://localhost:8000/api/redoc/
```

Documentación alternativa con diseño limpio y enfocado en lectura.

### Esquema OpenAPI (JSON)

```
http://localhost:8000/api/schema/
```

Esquema en formato OpenAPI 3.0 para importar en herramientas como Postman, Insomnia, etc.

---

## 🔧 Panel de Administración

Django incluye un panel de administración completo en:

```
http://localhost:8000/admin/
```

### Características del Admin:

- **Listado de usuarios** con filtros por tier, género y fecha
- **Búsqueda** por nombre, email, teléfono y UUID
- **Badges coloridos** para visualizar tiers
- **Acciones en lote**:
  - Actualizar múltiples usuarios a premium
  - Actualizar múltiples usuarios a free
- **Formularios organizados** con secciones colapsables
- **Campos de solo lectura** para proteger datos críticos

### Credenciales

Usa las credenciales del superusuario que creaste con:

```bash
python manage.py createsuperuser
```

---

## 🗄️ Modelo de Datos

### AppUser

El modelo `AppUser` refleja la tabla `app_users` de Supabase:

```python
class AppUser(models.Model):
    id = models.BigAutoField(primary_key=True)
    auth_user_id = models.UUIDField(unique=True)
    full_name = models.TextField()
    age = models.IntegerField(default=0)
    email = models.TextField(unique=True)
    phone_number = models.TextField(null=True, blank=True)
    gender = models.TextField(null=True, blank=True)
    tier = models.CharField(max_length=20, choices=UserTier.choices)
    role_global = models.CharField(max_length=32, choices=GlobalRole.choices)
    is_independent = models.BooleanField(default=False)
    billing_plan = models.CharField(max_length=16, choices=BillingPlan.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### UserTier (Enum)

```python
class UserTier(models.TextChoices):
    FREE = 'free', 'Free'
    PREMIUM = 'premium', 'Premium'
```

### GlobalRole (Enum)

```python
class GlobalRole(models.TextChoices):
    ADMIN_SISTEMA = 'AdminSistema', 'Admin. Sistema'
    ADMIN_INSTITUCION = 'AdminInstitucion', 'Admin. Institución'
    ADMIN_INSTITUCION_SALUD = 'AdminInstitucionSalud', 'Admin. Institución Salud'
    PROFESIONAL_SALUD = 'ProfesionalSalud', 'Profesional Salud'
    PACIENTE = 'Paciente', 'Paciente'
    INSTITUCION = 'Institucion', 'Institución'
    GENERAL = 'General', 'General'
```

### BillingPlan (Enum)

```python
class BillingPlan(models.TextChoices):
    INDIVIDUAL = 'individual', 'Individual'
    INSTITUTION = 'institution', 'Institution'
    CORPORATE = 'corporate', 'Corporate'
    B2B2C = 'b2b2c', 'B2B2C'
    TRIAL = 'trial', 'Trial'
```

**Importante**: El modelo tiene `managed=False` en el Meta, lo que significa que Django no gestiona las migraciones de esta tabla. Esto es porque Supabase maneja la estructura de la base de datos mediante sus propias migraciones.

Para más detalles sobre el esquema de la base de datos, consulta [`docs/database_schema.md`](../database_schema.md).

---

## 🔐 Autenticación

Actualmente la API acepta:

- **SupabaseJWTAuthentication** (personalizado):
  - Si el header `Authorization: Bearer …` coincide con `SUPABASE_SERVICE_ROLE_KEY` (JWT emitido por Supabase) o `SUPABASE_SECRET_KEY` (la secret key opaca), se confía directamente en la petición.
  - En caso contrario intenta validar el token como JWT HS256 usando `SUPABASE_JWT_SECRET` (o el JWKS si habilitas claves asimétricas).
- **SessionAuthentication / BasicAuthentication**: se mantienen sólo para desarrollo y pruebas manuales.

Variables mínimas para desarrollo local:

```ini
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_API_URL=http://127.0.0.1:54321
SUPABASE_SERVICE_ROLE_KEY=<SERVICE_ROLE_KEY de supabase status>
SUPABASE_SECRET_KEY=<SECRET_KEY de supabase status>
SUPABASE_JWT_SECRET=<JWT_SECRET de supabase status>
SUPABASE_ALLOW_SERVICE_ROLE_BEARER=true
```

> Si migras a JWT Signing Keys, añade `SUPABASE_JWKS_URL=https://<project>.supabase.co/auth/v1/.well-known/jwks.json` y ajusta `SUPABASE_JWT_ALGORITHMS` (p. ej. `RS256,HS256`) para aceptar primero la clave asimétrica.

---

## 🧑‍💻 Provisionar usuarios desde el backend

El endpoint `POST /dashboard/users/provision/` permite crear usuarios directamente en Supabase Auth usando la Supabase Admin API y sincroniza su perfil en `app_users`.

```bash
curl -X POST http://localhost:8000/dashboard/users/provision/ \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "paciente@aurademo.com",
    "password": "Aura360!",
    "email_confirm": true,
    "user_metadata": {
      "full_name": "Paciente Demo",
      "role_global": "Paciente",
      "billing_plan": "individual",
      "tier": "free",
      "is_independent": false,
      "age": 29,
      "gender": "F"
    }
  }'
```

Requisitos:

- Autenticarse con `Authorization: Bearer` usando el `SUPABASE_SERVICE_ROLE_KEY` (JWT) o la `SUPABASE_SECRET_KEY`.
- Tener configuradas `SUPABASE_API_URL`, `SUPABASE_SERVICE_ROLE_KEY` y el `SUPABASE_JWT_SECRET` que entrega `supabase status -o env`.

La respuesta incluye tanto el payload devuelto por Supabase como el registro sincronizado en `app_users`.

---

## 📦 Dependencias Principales

```toml
dependencies = [
    "django>=5.2.7",                    # Framework web
    "djangorestframework>=3.16.1",      # API REST
    "django-filter>=25.1",              # Filtrado avanzado
    "psycopg2-binary>=2.9.10",         # Driver PostgreSQL
    "python-decouple>=3.8",            # Variables de entorno
    "django-cors-headers>=4.6.0",      # CORS
    "drf-spectacular>=0.28.0",         # OpenAPI/Swagger
    "markdown>=3.9",                   # Para DRF browsable API
]
```

---

## 🧪 Testing

(Próximamente)

```bash
# Ejecutar tests
python manage.py test

# Con cobertura
coverage run --source='.' manage.py test
coverage report
```

---

## 🚀 Despliegue

### Variables de Entorno en Producción

Asegúrate de:

1. Cambiar `DEBUG=False`
2. Generar una `SECRET_KEY` segura
3. Configurar `ALLOWED_HOSTS` con tu dominio
4. Usar credenciales seguras de base de datos
5. Configurar `CORS_ALLOWED_ORIGINS` con tus dominios

### Recomendaciones:

- Usar **Gunicorn** como servidor WSGI
- Configurar **Nginx** como proxy inverso
- Usar **PostgreSQL** en producción (ya configurado)
- Habilitar **HTTPS** siempre
- Configurar **rate limiting**
- Implementar **monitoreo** y logs

---

## 📝 Notas Adicionales

### Sincronización con Supabase

La tabla `app_users` se sincroniza automáticamente con `auth.users` de Supabase mediante triggers. Cuando un usuario se registra en Supabase Auth:

1. Se crea el registro en `auth.users`
2. El trigger `trg_sync_app_user_profile_insert` se ejecuta
3. Se crea automáticamente el perfil en `public.app_users`
4. Django lee estos datos via ORM

### Importante

- **No ejecutes migraciones** de Django en la base de datos de Supabase
- **No modifiques** la estructura de `app_users` desde Django
- Todas las migraciones de esquema deben hacerse en Supabase
- Django solo **lee y escribe datos**, no gestiona la estructura

---

## 🤝 Contribuciones

Este es un proyecto privado. Para cambios o sugerencias, contacta al equipo de desarrollo.

---

## 📄 Licencia

Propietario: AURA365  
Todos los derechos reservados.

---

## 📞 Soporte

Para preguntas o problemas, contacta a:
- Email: soporte@aura365.com
- Documentación: `/docs`

---

**Última actualización**: 4 de Octubre, 2025  
**Versión de Django**: 5.2.7  
**Versión de Python**: 3.13.7
