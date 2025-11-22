# 🚀 Guía de Inicio Rápido - AURA365 Backend

Esta guía te ayudará a poner en marcha el backend de AURA365 en menos de 5 minutos.

## ⚡ Inicio Rápido

### 1. Configurar Entorno

```bash
# Activar entorno virtual
source .venv/bin/activate

# Verificar que las dependencias estén instaladas
uv sync
```

### 2. Configurar Variables de Entorno

Crea el archivo `.env` (si no existe):

```bash
cp .env.example .env
```

Para **desarrollo local con Supabase**, ajusta los valores con lo que devuelve `supabase status -o env`:

```ini
DB_HOST=localhost
DB_PORT=54322
DB_USER=postgres
DB_PASSWORD=postgres
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_API_URL=http://127.0.0.1:54321
SUPABASE_SERVICE_ROLE_KEY=<SERVICE_ROLE_KEY>
SUPABASE_SECRET_KEY=<SECRET_KEY>
SUPABASE_JWT_SECRET=<JWT_SECRET>
SUPABASE_ALLOW_SERVICE_ROLE_BEARER=true
```

> 💡 Todos estos valores se pueden copiar ejecutando `supabase status -o env` en tu proyecto local. Si trabajas con Supabase Cloud, toma las llaves desde Settings → API.

#### 📄 Ingesta automática de planes nutricionales (PDF)

Completa también las variables que coordinarán al backend con el servicio vectorial para extraer planes desde PDFs:

```ini
# Ubicación del bucket en Supabase Storage donde se guardarán los PDFs
NUTRITION_PLAN_STORAGE_BUCKET=nutrition-plans
NUTRITION_PLAN_STORAGE_PREFIX=nutrition-plans
NUTRITION_PLAN_STORAGE_PUBLIC_URL=https://<tu-proyecto>.supabase.co/storage/v1/object/public/nutrition-plans

# Límite y tipos de archivo aceptados para la carga vía dashboard
NUTRITION_PLAN_MAX_UPLOAD_MB=10
NUTRITION_PLAN_ALLOWED_FILE_TYPES=application/pdf

# Endpoint y token del microservicio vectorial (FastAPI + Celery)
NUTRITION_PLAN_INGESTION_URL=http://localhost:8001/api/ingest/nutrition-plan
NUTRITION_PLAN_INGESTION_TOKEN=vector-service-token

# URL pública donde el vector service devolverá el plan estructurado
NUTRITION_PLAN_CALLBACK_URL=http://localhost:8000/dashboard/internal/nutrition-plans/ingest-callback/
NUTRITION_PLAN_CALLBACK_TOKEN=backend-callback-secret
```

> Ajusta los valores según tu despliegue (ej. dominios productivos, tokens en 1Password, etc.).

### 3. Iniciar Supabase (si usas Supabase local)

```bash
# En otra terminal, navega a tu proyecto de Supabase
cd ../supabase  # o donde esté tu proyecto de Supabase

# Inicia Supabase
supabase start
```

Esto iniciará:
- PostgreSQL en el puerto `54322`
- Supabase Studio en `http://localhost:54323`

### 4. Verificar Conexión

```bash
# Regresa al directorio del backend
cd backend

# Ejecuta el script de prueba
python scripts/test_db_connection.py
```

Deberías ver:
```
✅ Conexión exitosa con PostgreSQL
✅ Tabla app_users accesible
```

### 5. Crear Superusuario

```bash
python manage.py createsuperuser
```

Ingresa:
- Username: `admin`
- Email: `admin@aura365.com`
- Password: (tu elección)

### 6. Iniciar Servidor

```bash
python manage.py runserver
```

El servidor estará disponible en `http://localhost:8000`

### (Opcional) Crear administradores adicionales

Para generar cuentas de staff/superuser sin el asistente interactivo:

```bash
python manage.py create_admin_user --email admin@aurademo.com --password "S3guro!" --superuser --first-name Admin --last-name Demo
```

- Omitir `--superuser` crea un usuario solo con permiso de staff.
- Si no proporcionas `--password`, el comando te pedirá la contraseña dos veces.

---

## 🎯 Verificar Instalación

Abre estos URLs en tu navegador:

### 1. Documentación de la API (Swagger)
```
http://localhost:8000/docs/
```

### 2. Panel de Administración
```
http://localhost:8000/admin/
```
- Usuario: `admin`
- Password: (el que configuraste)

### 3. API de Usuarios
```
http://localhost:8000/dashboard/users/
```

### 4. Estadísticas
```
http://localhost:8000/dashboard/users/stats/
```

---

## 📝 Comandos Útiles

### Ver todos los usuarios
```bash
python manage.py shell
>>> from users.models import AppUser
>>> AppUser.objects.all()
```

### Ver estadísticas rápidas
```bash
python manage.py shell
>>> from users.models import AppUser
>>> print(f"Total: {AppUser.objects.count()}")
>>> print(f"Premium: {AppUser.objects.filter(tier='premium').count()}")
```

### Verificar configuración
```bash
python manage.py check
```

### Ver rutas de la API
```bash
python manage.py show_urls  # Si tienes django-extensions
```

---

## 🧪 Probar la API con curl

### Obtener lista de usuarios
```bash
curl http://localhost:8000/dashboard/users/
```

### Buscar usuario por email
```bash
curl "http://localhost:8000/dashboard/users/?search=juan"
```

### Filtrar usuarios premium
```bash
curl http://localhost:8000/dashboard/users/premium/
```

### Obtener estadísticas
```bash
curl http://localhost:8000/dashboard/users/stats/
```

### Resumen por roles
```bash
curl http://localhost:8000/dashboard/users/roles/
curl http://localhost:8000/dashboard/users/roles/paciente/
```

### Crear un usuario (requiere autenticación)
```bash
curl -X POST http://localhost:8000/dashboard/users/provision/ \
  -H "Content-Type: application/json" \
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

> El endpoint `POST /dashboard/users/provision/` usa la Supabase Admin API para crear el usuario en `auth.users` y sincronizar su perfil en `app_users`. Puedes enviar en el header `Authorization` la `SUPABASE_SERVICE_ROLE_KEY` (JWT) o la `SUPABASE_SECRET_KEY`.

### Actualizar rol global de un usuario (requiere token service_role)
```bash
curl -X POST http://localhost:8000/dashboard/users/123/set-role/ \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "role_global": "ProfesionalSalud",
    "billing_plan": "institution",
    "is_independent": false
  }'
```

---

## 🔧 Solución de Problemas

### Error: "could not connect to server"

**Causa**: La base de datos no está iniciada.

**Solución**:
```bash
# Si usas Supabase local
supabase start

# O verifica que PostgreSQL esté corriendo
```

### Error: "relation app_users does not exist"

**Causa**: La tabla no existe en la base de datos.

**Solución**:
```bash
# Aplica las migraciones en Supabase
cd ../supabase
supabase db push
```

### Error: "No module named 'decouple'"

**Causa**: Dependencias no instaladas.

**Solución**:
```bash
uv sync
```

### Puerto 8000 ya en uso

**Solución**: Usa otro puerto
```bash
python manage.py runserver 8080
```

---

## 📚 Próximos Pasos

1. ✅ Servidor corriendo
2. ✅ Base de datos conectada
3. ✅ Admin configurado

Ahora puedes:

- **Explorar la API**: `http://localhost:8000/docs/`
- **Gestionar usuarios**: `http://localhost:8000/admin/`
- **Integrar con tu frontend**: Usa los endpoints en `/dashboard/`
- **Añadir nuevos endpoints**: Crea nuevos ViewSets en `users/views.py`
- **Añadir más apps**: `python manage.py startapp nombre_app`

---

## 🎓 Recursos

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Supabase Documentation](https://supabase.com/docs)
- [README.md del Proyecto](./README.md)
- [Esquema de Base de Datos](../database_schema.md)

---

## 🆘 Ayuda

Si tienes problemas:

1. Verifica el archivo `.env`
2. Ejecuta `python scripts/test_db_connection.py`
3. Revisa los logs del servidor
4. Consulta la documentación completa en `docs/guides/README.md`

---

**¡Listo!** 🎉 Ahora tienes un backend Django completamente funcional integrado con Supabase.
