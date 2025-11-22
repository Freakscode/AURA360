# Pipeline de despliegue a Azure

El workflow [`deploy-azure.yml`](../../.github/workflows/deploy-azure.yml) automatiza la validación y el despliegue de la infraestructura de AURA360 en Azure mediante Terraform.

## Eventos soportados

- **push / pull_request** sobre `infra/azure/**` o el propio workflow.
  - Ejecuta `terraform fmt`, `init` y `plan`.
  - Publica el artefacto `tfplan-<entorno>` y comenta en el PR.
- **workflow_dispatch** con inputs:
  - `tf_environment`: etiqueta del entorno (`dev`, `stg`, `prod`).
  - `tfvars_file`: ruta al archivo `.tfvars` a usar.
  - `auto_apply`: si se marca `true`, aplica el plan inmediatamente tras generarlo.

## Requisitos de secretos

| Secreto | Uso |
| --- | --- |
| `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_SUBSCRIPTION_ID` | Autenticación OIDC del Service Principal. |
| `TF_BACKEND_RESOURCE_GROUP`, `TF_BACKEND_STORAGE_ACCOUNT`, `TF_BACKEND_CONTAINER`, `TF_BACKEND_STATE_KEY` | Backend remoto del estado de Terraform. |
| `TF_VAR_admin_object_id` (opcional) | Propaga valores sensibles adicionales a `terraform plan/apply`. |

> 📌 Para AURA360 (prod) usa los valores descritos en `infra/azure/README.md`.

## Flujo

1. **Checkout + Setup**: el workflow descarga el repo y fija Terraform 1.6.6.
2. **Login**: usa `azure/login` para obtener un token federado OIDC.
3. **fmt + init + plan**: valida formato, inicializa el backend remoto y crea `tfplan` usando el tfvars indicado.
4. **Artefactos**: guarda `tfplan` para poder reutilizarlo en `apply` sin volver a generar.
5. **Apply opcional**: cuando se lanza manualmente con `auto_apply=true`, descarga el plan almacenado y ejecuta `terraform apply -auto-approve`.
6. **Notificaciones**: publica comentarios/resúmenes tanto en la ejecución del workflow como en los PR.

## Buenas prácticas

- Mantener un tfvars por entorno (`infra/azure/terraform/envs/<env>.tfvars`).
- Usar entornos protegidos de GitHub para `prod` y requerir aprobaciones antes de `workflow_dispatch`.
- Rotar el Service Principal cada 90 días y limitarlo a los Resource Groups creados por Terraform.
- Añadir un segundo job (futuro) que construya imágenes y dispare despliegues de Helm/ACA después de que la infraestructura esté lista.

## Guía rápida de configuración en GitHub

1. **Secrets**: agrega los 8 secretos obligatorios (`AZURE_*`, `TF_BACKEND_*`) en `Settings → Secrets and variables → Actions` a nivel de repositorio. Si manejas varios entornos, crea secrets por Environment.
2. **Environment `prod`**: crea un Environment y exige aprobación manual para la rama `main`. Posteriormente, desde `Actions → deploy-azure → Run workflow`, selecciona el environment antes de lanzar `workflow_dispatch` con `auto_apply=true`.
3. **Permisos del repo**: asegúrate de que el token de GitHub Actions tenga `contents: read`, `pull-requests: write` e `id-token: write` (ya configurado en el YAML) para poder usar OIDC contra Azure.
4. **Monorepo-friendly**: si deseas que el workflow reaccione a otros directorios (por ejemplo `deploy/azure/helm` cuando exista), añade esas rutas a la sección `on.push.paths` / `on.pull_request.paths`.
