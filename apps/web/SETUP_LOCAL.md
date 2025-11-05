# Guía de Configuración Local - AURA360 Angular

## 📋 Requisitos Previos

- Node.js 18+ y npm
- Angular CLI 20+
- Supabase CLI instalado
- Proyecto Supabase local iniciado (o instancia en la nube)

## 🚀 Iniciar la Aplicación

### 1. Instalar Dependencias

```bash
cd /Users/freakscode/Proyectos\ 2025/AURA360/aura360-front
npm install
```

### 2. Iniciar Supabase Local (Opción A - Recomendado para testing)

Si tienes Supabase local configurado:

```bash
# En el directorio del backend o donde tengas supabase configurado
cd /Users/freakscode/Proyectos\ 2025/AURA360/backend
# o cd /Users/freakscode/Proyectos\ 2025/AURA360/aura_mobile

supabase start
```

Esto iniciará Supabase en `http://127.0.0.1:54321`

**Obtener las credenciales:**
```bash
supabase status
```

Busca:
- `API URL`: http://127.0.0.1:54321
- `anon key`: La clave anon que debes usar

### 3. Verificar Configuración de Environment

El archivo `src/environments/environment.development.ts` debe tener:

```typescript
{
  production: false,
  supabase: {
    url: 'http://127.0.0.1:54321',
    anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' // La clave de supabase status
  }
}
```

### 4. Iniciar la Aplicación Angular

```bash
# Modo desarrollo (usa environment.development.ts)
npm start
# o
ng serve

# La app estará disponible en http://localhost:4200
```

### 5. Iniciar el Backend Django (Opcional)

Si necesitas endpoints del backend:

```bash
cd /Users/freakscode/Proyectos\ 2025/AURA360/backend
uv run python manage.py runserver 0.0.0.0:8000
```

---

## 👥 Usuarios de Prueba

### Script SQL para Crear Usuarios de Prueba

Ejecuta estos comandos en Supabase SQL Editor o usando `psql`:

```sql
-- ============================================
-- CREAR USUARIOS DE PRUEBA - AURA360
-- ============================================

-- IMPORTANTE: Primero debes crear los usuarios en Supabase Auth
-- Luego este script sincronizará los datos en app_users

-- 1. ADMIN SISTEMA
-- Email: admin@aura360.com
-- Password: Admin123!
INSERT INTO auth.users (
  instance_id,
  id,
  aud,
  role,
  email,
  encrypted_password,
  email_confirmed_at,
  raw_app_meta_data,
  raw_user_meta_data,
  created_at,
  updated_at,
  confirmation_token,
  recovery_token
) VALUES (
  '00000000-0000-0000-0000-000000000000',
  gen_random_uuid(),
  'authenticated',
  'authenticated',
  'admin@aura360.com',
  crypt('Admin123!', gen_salt('bf')),
  NOW(),
  '{"provider":"email","providers":["email"],"role_global":"AdminSistema","tier":"premium","billing_plan":"corporate"}',
  '{"full_name":"Admin Sistema","role_global":"AdminSistema","tier":"premium"}',
  NOW(),
  NOW(),
  '',
  ''
) ON CONFLICT (email) DO NOTHING;

-- 2. ADMIN INSTITUCIÓN
-- Email: admin.institucion@aura360.com
-- Password: Admin123!
INSERT INTO auth.users (
  instance_id,
  id,
  aud,
  role,
  email,
  encrypted_password,
  email_confirmed_at,
  raw_app_meta_data,
  raw_user_meta_data,
  created_at,
  updated_at,
  confirmation_token,
  recovery_token
) VALUES (
  '00000000-0000-0000-0000-000000000000',
  gen_random_uuid(),
  'authenticated',
  'authenticated',
  'admin.institucion@aura360.com',
  crypt('Admin123!', gen_salt('bf')),
  NOW(),
  '{"provider":"email","providers":["email"],"role_global":"AdminInstitucion","tier":"premium","billing_plan":"institution"}',
  '{"full_name":"Admin Institución","role_global":"AdminInstitucion","tier":"premium"}',
  NOW(),
  NOW(),
  '',
  ''
) ON CONFLICT (email) DO NOTHING;

-- 3. ADMIN INSTITUCIÓN SALUD
-- Email: admin.salud@aura360.com
-- Password: Admin123!
INSERT INTO auth.users (
  instance_id,
  id,
  aud,
  role,
  email,
  encrypted_password,
  email_confirmed_at,
  raw_app_meta_data,
  raw_user_meta_data,
  created_at,
  updated_at,
  confirmation_token,
  recovery_token
) VALUES (
  '00000000-0000-0000-0000-000000000000',
  gen_random_uuid(),
  'authenticated',
  'authenticated',
  'admin.salud@aura360.com',
  crypt('Admin123!', gen_salt('bf')),
  NOW(),
  '{"provider":"email","providers":["email"],"role_global":"AdminInstitucionSalud","tier":"premium","billing_plan":"institution"}',
  '{"full_name":"Admin Salud","role_global":"AdminInstitucionSalud","tier":"premium"}',
  NOW(),
  NOW(),
  '',
  ''
) ON CONFLICT (email) DO NOTHING;

-- 4. PROFESIONAL DE SALUD
-- Email: profesional@aura360.com
-- Password: Prof123!
INSERT INTO auth.users (
  instance_id,
  id,
  aud,
  role,
  email,
  encrypted_password,
  email_confirmed_at,
  raw_app_meta_data,
  raw_user_meta_data,
  created_at,
  updated_at,
  confirmation_token,
  recovery_token
) VALUES (
  '00000000-0000-0000-0000-000000000000',
  gen_random_uuid(),
  'authenticated',
  'authenticated',
  'profesional@aura360.com',
  crypt('Prof123!', gen_salt('bf')),
  NOW(),
  '{"provider":"email","providers":["email"],"role_global":"ProfesionalSalud","tier":"premium","billing_plan":"individual","is_independent":true}',
  '{"full_name":"Dr. Juan Pérez","role_global":"ProfesionalSalud","tier":"premium"}',
  NOW(),
  NOW(),
  '',
  ''
) ON CONFLICT (email) DO NOTHING;

-- 5. PACIENTE
-- Email: paciente@aura360.com
-- Password: Pac123!
INSERT INTO auth.users (
  instance_id,
  id,
  aud,
  role,
  email,
  encrypted_password,
  email_confirmed_at,
  raw_app_meta_data,
  raw_user_meta_data,
  created_at,
  updated_at,
  confirmation_token,
  recovery_token
) VALUES (
  '00000000-0000-0000-0000-000000000000',
  gen_random_uuid(),
  'authenticated',
  'authenticated',
  'paciente@aura360.com',
  crypt('Pac123!', gen_salt('bf')),
  NOW(),
  '{"provider":"email","providers":["email"],"role_global":"Paciente","tier":"premium","billing_plan":"individual"}',
  '{"full_name":"María García","role_global":"Paciente","tier":"premium"}',
  NOW(),
  NOW(),
  '',
  ''
) ON CONFLICT (email) DO NOTHING;

-- 6. USUARIO GENERAL (Free)
-- Email: usuario@aura360.com
-- Password: User123!
INSERT INTO auth.users (
  instance_id,
  id,
  aud,
  role,
  email,
  encrypted_password,
  email_confirmed_at,
  raw_app_meta_data,
  raw_user_meta_data,
  created_at,
  updated_at,
  confirmation_token,
  recovery_token
) VALUES (
  '00000000-0000-0000-0000-000000000000',
  gen_random_uuid(),
  'authenticated',
  'authenticated',
  'usuario@aura360.com',
  crypt('User123!', gen_salt('bf')),
  NOW(),
  '{"provider":"email","providers":["email"],"role_global":"General","tier":"free","billing_plan":"trial"}',
  '{"full_name":"Usuario Prueba","role_global":"General","tier":"free"}',
  NOW(),
  NOW(),
  '',
  ''
) ON CONFLICT (email) DO NOTHING;

-- Verificar que se crearon los usuarios
SELECT
  email,
  raw_app_meta_data->>'role_global' as role,
  raw_app_meta_data->>'tier' as tier
FROM auth.users
WHERE email LIKE '%@aura360.com'
ORDER BY email;
```

### Alternativa: Crear Usuarios Manualmente (Recomendado)

Si prefieres crear usuarios manualmente a través de Supabase Dashboard:

1. Ve a `Authentication` → `Users` → `Add user`
2. Usa los siguientes datos:

**NOTA IMPORTANTE**: Los usuarios a continuación son ejemplos para crear manualmente. Los usuarios que **actualmente existen** en la base de datos local tienen credenciales diferentes (ver tabla de "Resumen de Credenciales" más abajo).

#### 1️⃣ Admin Sistema
```
Email: admin.sistema@aurademo.com
Password: Aura360!
User Metadata:
{
  "full_name": "Admin Sistema",
  "role_global": "AdminSistema",
  "tier": "premium",
  "billing_plan": "corporate"
}
```

#### 2️⃣ Admin Institución
```
Email: admin.institucion@aurademo.com
Password: Aura360!
User Metadata:
{
  "full_name": "Admin Institución",
  "role_global": "AdminInstitucion",
  "tier": "premium",
  "billing_plan": "institution"
}
```

#### 3️⃣ Admin Institución Salud
```
Email: admin.salud@aurademo.com
Password: Aura360!
User Metadata:
{
  "full_name": "Admin Salud",
  "role_global": "AdminInstitucionSalud",
  "tier": "premium",
  "billing_plan": "institution"
}
```

#### 4️⃣ Profesional de Salud
```
Email: pro.salud@aurademo.com
Password: Aura360!
User Metadata:
{
  "full_name": "Dr. Juan Pérez",
  "role_global": "ProfesionalSalud",
  "tier": "premium",
  "billing_plan": "individual",
  "is_independent": true
}
```

#### 5️⃣ Paciente
```
Email: paciente@aurademo.com
Password: Aura360!
User Metadata:
{
  "full_name": "María García",
  "role_global": "Paciente",
  "tier": "premium",
  "billing_plan": "individual"
}
```

#### 6️⃣ Paciente 2
```
Email: paciente2@aurademo.com
Password: Aura360!
User Metadata:
{
  "full_name": "Carlos Rodríguez",
  "role_global": "Paciente",
  "tier": "premium",
  "billing_plan": "individual"
}
```

---

## 📝 Resumen de Credenciales

**NOTA**: Estos son los usuarios que actualmente existen en la base de datos local de Supabase.

| Rol | Email | Password | Dashboard URL | Notas |
|-----|-------|----------|---------------|-------|
| **Admin Sistema** | admin.sistema@aurademo.com | Aura360! | /admin-sistema | - |
| **Admin Institución** | admin.institucion@aurademo.com | Aura360! | /admin-institucion | - |
| **Admin Salud** | admin.salud@aurademo.com | Aura360! | /admin-salud | - |
| **Profesional Salud** | pro.salud@aurademo.com | Aura360! | /profesional | - |
| **Nutricionista Independiente** | angie.martinez@aurademo.com | Aura360! | /profesional | Profesional independiente, sin institución. **Tiene 2 pacientes asignados** |
| **Paciente** | paciente@aurademo.com | Aura360! | /paciente | - |
| **Paciente 2** | paciente2@aurademo.com | Aura360! | /paciente | - |
| **Gabriel Cardona** | gacardona@aura.com | Aura360! | /general | Paciente de Angie Martinez |
| **Ana** | ana@aura.com | Aura360! | /general | Paciente de Angie Martinez |

---

## 🧪 Flujo de Prueba

### 1. Probar Login Básico

1. Abre http://localhost:4200
2. Deberías ser redirigido a `/auth/login`
3. Ingresa credenciales de cualquier usuario (ejemplo: `admin.sistema@aurademo.com` / `Aura360!`)
4. Deberías ver la carga de contextos en la consola del navegador
5. Serás redirigido al dashboard correspondiente

### 2. Probar Context Switcher

1. Login como `pro.salud@aurademo.com` / `Aura360!`
2. Verifica que el Context Switcher aparece en el header
3. Debería mostrar "Práctica Independiente" (si `is_independent: true` en metadata)

### 3. Probar Navegación por Rol

1. Login como cada usuario
2. Verifica que el menú lateral muestra opciones específicas del rol
3. Intenta acceder a una ruta de otro rol directamente (ej: `/admin-sistema` como paciente)
4. Deberías ser redirigido por los guards

### 4. Probar Dashboard de Profesional con Pacientes

1. Login como `angie.martinez@aurademo.com` / `Aura360!`
2. Verifica que en el dashboard aparece "2" en el card de "Mis Pacientes"
3. Debería aparecer una sección "Pacientes Recientes" con:
   - GABRIEL CARDONA (gacardona@aura.com)
   - ANA (ana@aura.com)
4. Click en el botón "Mis Pacientes" o en "Ver todos los pacientes"
5. Deberías ver la lista completa con:
   - Nombre, email, teléfono, edad, género
   - Contexto (Independiente)
   - Estado (Activo)
   - Fecha de inicio

### 5. Probar Búsqueda y Filtros de Pacientes

1. En la lista de pacientes (`/profesional/pacientes`):
2. **Búsqueda**:
   - Escribe "gabriel" en el campo de búsqueda
   - Deberías ver solo a Gabriel Cardona
   - Limpia la búsqueda con el botón "✕"
3. **Filtros por Estado**:
   - Selecciona "Activos" en el dropdown
   - Deberías ver solo pacientes activos
   - Cambia a "Todos" para ver todos
4. **Ordenamiento**:
   - Click en "Nombre" para ordenar alfabéticamente
   - Click nuevamente para invertir el orden (↑↓)
   - Click en "Fecha" para ordenar por fecha de inicio
5. Verifica el contador "Mostrando" que refleja los filtros aplicados

### 6. Probar Detalle del Paciente

1. En la lista de pacientes, click en cualquier fila (las filas son clickeables)
2. Deberías ver la página de detalle con:
   - **Información Personal**: Nombre, email, teléfono, edad, género
   - **Relación de Cuidado**: Contexto, fecha de inicio, notas
   - **Historial de Consultas**: Placeholder con opción de agregar consultas
   - **Plan Nutricional**: Placeholder con opción de crear plan
3. Prueba el botón "Finalizar Relación" (solo visible si está activa)
4. Usa "← Volver a la Lista" para regresar

### 7. Probar Asignación de Nuevos Pacientes

1. En la lista de pacientes, click en "+ Asignar Paciente"
2. Se abre un modal de asignación
3. **Buscar usuario**:
   - Escribe al menos 3 caracteres (ej: "pac")
   - Deberías ver sugerencias de usuarios disponibles
   - Los profesionales de salud NO aparecen en los resultados
4. **Seleccionar paciente**:
   - Click en un usuario de los resultados
   - El usuario se marca con un check verde
5. **Configurar relación**:
   - Selecciona "Práctica Independiente" o "Institucional"
   - Agrega notas opcionales
6. Click en "Asignar Paciente"
7. Verifica que el paciente aparece en la lista

### 8. Probar Logout

1. Click en el avatar del usuario (esquina superior derecha)
2. Click en "Cerrar Sesión"
3. Deberías ser redirigido a `/auth/login`
4. Los contextos deben limpiarse

---

## 🐛 Troubleshooting

### Error: "No active context"

**Problema**: Los guards bloquean el acceso porque no hay contexto activo.

**Solución**:
1. Verifica que el usuario tenga `role_global` en `user_metadata`
2. Revisa la consola del navegador para ver errores en la carga de contextos
3. Verifica que existe el usuario en `auth.users`

### Error: "Failed to fetch user contexts"

**Problema**: No se pueden cargar las membresías institucionales.

**Solución**:
1. Verifica que las tablas existen:
   - `public.app_users`
   - `public.institutions`
   - `public.institution_memberships`
2. El usuario puede no tener membresías (está OK para práctica independiente)

### Context Switcher no aparece

**Problema**: No hay contextos disponibles.

**Solución**:
1. Para usuarios con práctica independiente, agrega `"is_independent": true` en metadata
2. Para usuarios institucionales, crea registros en `institution_memberships`

### Menú lateral vacío

**Problema**: El NavigationMenuService no reconoce el rol.

**Solución**:
1. Verifica que `role_global` está en `user_metadata` con un valor válido
2. Chequea la consola para ver qué rol se está detectando
3. Los valores válidos son: AdminSistema, AdminInstitucion, AdminInstitucionSalud, ProfesionalSalud, Paciente, General

---

## 📚 Comandos Útiles

```bash
# Instalar dependencias
npm install

# Iniciar en modo desarrollo
npm start
# o
ng serve

# Iniciar en modo production (preview)
ng serve --configuration=production

# Build para producción
ng build

# Run tests
ng test

# Linting
ng lint

# Ver estado de Supabase local
supabase status

# Ver logs de Supabase
supabase logs

# Reset Supabase (borra todos los datos)
supabase db reset

# Generar nuevos tipos de TypeScript desde Supabase
supabase gen types typescript --local > src/app/core/models/database.types.ts
```

---

## 🧑‍⚕️ Relaciones de Cuidado (Care Relationships)

La aplicación ahora soporta relaciones entre profesionales de salud y pacientes. Estas relaciones se gestionan en la tabla `care_relationships`.

### Relaciones Existentes en la Base de Datos Local

- **Angie Martinez** (Nutricionista Independiente) tiene 2 pacientes asignados:
  - Gabriel Cardona (gacardona@aura.com)
  - Ana (ana@aura.com)

### Crear Nuevas Relaciones

Para asignar pacientes a un profesional, ejecuta en la consola de Supabase:

```sql
-- Obtener IDs
SELECT id, email, full_name, role_global FROM app_users
WHERE email IN ('profesional@email.com', 'paciente@email.com');

-- Crear relación (reemplaza los IDs)
INSERT INTO care_relationships (
  professional_user_id,
  patient_user_id,
  context_type,
  status,
  notes
) VALUES (
  19,  -- ID del profesional
  13,  -- ID del paciente
  'independent',  -- o 'institutional'
  'active',
  'Descripción de la relación'
);
```

### Contextos de Relación

- **independent**: Profesional independiente sin institución
- **institutional**: Profesional asociado a una institución

### Estados de Relación

- **active**: Relación activa (aparece en dashboard)
- **inactive**: Relación inactiva (no aparece en conteo activo)
- **ended**: Relación finalizada

## 🔗 URLs Importantes

- **App Angular**: http://localhost:4200
- **Supabase Studio (local)**: http://127.0.0.1:54323
- **Backend Django**: http://localhost:8000
- **Supabase API (local)**: http://127.0.0.1:54321
- **Dashboard Profesional**: http://localhost:4200/profesional
- **Lista de Pacientes**: http://localhost:4200/profesional/pacientes
- **Detalle de Paciente**: http://localhost:4200/profesional/pacientes/:id

## 🎯 Funcionalidades Implementadas para Profesionales

### Gestión de Pacientes

1. **Dashboard con Resumen**
   - Contador de pacientes activos en tiempo real
   - Vista previa de pacientes recientes
   - Navegación rápida a la lista completa

2. **Lista de Pacientes con Filtros**
   - **Búsqueda en tiempo real**: Por nombre o email
   - **Filtros por estado**: Todos, Activos, Inactivos
   - **Ordenamiento**: Por nombre o fecha de inicio (ascendente/descendente)
   - **Contador dinámico**: Muestra cuántos pacientes se están visualizando

3. **Detalle del Paciente**
   - **Información Personal**: Perfil completo del paciente
   - **Relación de Cuidado**: Contexto, estado, fechas, notas
   - **Historial de Consultas**: (Placeholder - listo para implementar)
   - **Plan Nutricional**: (Placeholder - listo para implementar)
   - **Acciones**: Finalizar relación, volver a la lista

4. **Asignación de Nuevos Pacientes**
   - **Modal interactivo** con búsqueda en tiempo real
   - **Búsqueda inteligente**: Encuentra usuarios por nombre o email
   - **Filtrado automático**: Excluye profesionales de salud
   - **Selección visual**: UI clara con feedback visual
   - **Configuración de contexto**: Independiente o institucional
   - **Notas opcionales**: Para documentar la relación

### Características Técnicas

- ✅ **Reactive UI** con Angular Signals
- ✅ **Computed values** para filtrado y ordenamiento eficiente
- ✅ **Debounce** en búsquedas para optimizar rendimiento
- ✅ **Lazy loading** de rutas
- ✅ **Navegación fluida** con RouterLink
- ✅ **Validaciones** en asignación de pacientes
- ✅ **Error handling** con mensajes descriptivos

---

## ✅ Checklist de Verificación

Antes de reportar un problema, verifica:

- [ ] Supabase local está corriendo (`supabase status`)
- [ ] npm install ejecutado correctamente
- [ ] Environment development tiene las credenciales correctas
- [ ] Usuario existe en `auth.users` con `user_metadata` correcto
- [ ] No hay errores en la consola del navegador
- [ ] No hay errores en la consola de Angular CLI

---

¡Listo! Ahora puedes probar la aplicación con diferentes roles. 🎉
