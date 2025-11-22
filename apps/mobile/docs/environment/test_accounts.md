# Test Environment: Supabase Demo Accounts

This environment includes a curated set of Supabase users to validate B2B, B2C, and B2B2C flows in AURA365 Mobile. Every account shares the same provisional password.

- **Shared password:** `Aura360!`

| Target role | Email | role_global | billing_plan | Notes |
|-------------|-------|-------------|--------------|-------|
| System admin | `admin.sistema@aurademo.com` | `AdminSistema` | `corporate` | Internal superuser with full control |
| Institution admin (non health) | `admin.institucion@aurademo.com` | `AdminInstitucion` | `institution` | Manages a corporate institution |
| Health institution admin | `admin.salud@aurademo.com` | `AdminInstitucionSalud` | `institution` | Oversees a clinic and its professionals |
| Health professional | `pro.salud@aurademo.com` | `ProfesionalSalud` | `b2b2c` | Works in a clinic and maintains an independent practice (`is_independent=true`) |
| Independent patient | `paciente@aurademo.com` | `Paciente` | `individual` | Personal B2C account used to test patient flows |

> All users were created via `POST /auth/v1/admin/users` with the `SUPABASE_SERVICE_ROLE_KEY`. The `sync_app_user_profile()` trigger keeps `role_global`, `billing_plan`, and `is_independent` synchronized in `public.app_users`.
