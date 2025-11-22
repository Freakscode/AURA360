# Database Documentation

Este directorio contiene la documentación de la base de datos de AURA365 Mobile.

## Documentos Disponibles

### [database_schema.md](./database_schema.md)
**Esquema Completo de Base de Datos**

Documentación exhaustiva de todas las estructuras de datos, incluyendo:
- Definiciones detalladas de tablas con todos sus campos y restricciones
- Triggers y funciones PL/pgSQL explicados línea por línea
- Vistas y su propósito
- Políticas de Row-Level Security (RLS)
- Mapeo con entidades de dominio en Dart
- Diagramas de flujo de sincronización
- Historial de migraciones aplicadas
- Operaciones comunes y ejemplos de SQL
- Consideraciones futuras y mejoras sugeridas

**Recomendado para**: Desarrolladores que necesitan entender el esquema completo, realizar cambios estructurales, o implementar nuevas features que interactúan con la base de datos.

---

## Resumen Rápido: app_users

### Tabla Principal
- **Tabla**: `public.app_users`
- **Propósito**: Perfil de usuario sincronizado automáticamente con `auth.users` de Supabase
- **Clave Primaria**: `id` (bigserial)
- **Clave Natural**: `auth_user_id` (FK → `auth.users.id`)

### Campos Principales
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | bigserial | ID interno |
| `auth_user_id` | uuid | Vincula con Supabase Auth |
| `email` | text | Email único |
| `full_name` | text | Nombre completo |
| `age` | integer | Edad (≥0) |
| `phone_number` | text | Teléfono opcional |
| `gender` | text | Género (texto libre) |
| `tier` | text | Plan: 'free' o 'premium' |
| `created_at` | timestamptz | Fecha creación |
| `updated_at` | timestamptz | Fecha actualización |

### Sincronización Automática
Los cambios en `auth.users` se propagan automáticamente a `app_users` mediante triggers. Ver [database_schema.md](./database_schema.md#sync_app_user_profile) para detalles completos.

### Acceso desde la App
La entidad `AppUser` en `lib/features/user/domain/entities/app_user.dart` representa este modelo en el código Dart.

---

## Cómo Aplicar Migraciones

```bash
# Entorno local
supabase db push --local

# Entorno remoto (después de link)
supabase db push
```

Para más detalles operacionales, consulta [database_schema.md](./database_schema.md#migraciones-aplicadas).
