# Azure Infrastructure Stack

Este directorio contiene la propuesta inicial para operar AURA360 en Azure empleando Terraform y un pipeline automatizado de GitHub Actions.

## 🧱 Componentes

| Recurso | Propósito |
| --- | --- |
| Resource Group | Contenedor lógico de toda la infraestructura del entorno. |
| Azure Container Registry (ACR) | Almacena las imágenes Docker generadas por los servicios (api, workers, agents, pdf, web). |
| Azure Kubernetes Service (AKS) | Ejecuta los microservicios de AURA360 y expone ingress HTTP(S). |
| Virtual Network + Subnets | Segmenta el tráfico entre AKS, servicios administrados y endpoints privados. |
| Log Analytics Workspace | Base para Azure Monitor Container Insights y alertas. |
| Key Vault | Custodia secretos equivalentes a `services/api/.env.production`. |
| Storage Account | Respaldos (PDFs, assets) y backend remoto de Terraform (opcional). |

## 📂 Estructura

```
infra/azure/
├── README.md              # Este archivo
└── terraform/
    ├── main.tf           # Recursos principales
    ├── providers.tf      # Definición de providers
    ├── variables.tf      # Variables de entrada
    ├── outputs.tf        # Valores exportados
    ├── backend.tf        # Config remota (rellenar antes de `init`)
    └── envs/
        └── prod.tfvars   # Ejemplo de variables para producción
```

## ✅ Prerrequisitos

1. Terraform >= 1.6.0
2. Azure CLI >= 2.60.0 y permisos de `Contributor` + `AcrPush` sobre la suscripción.
3. Service Principal dedicado con permisos mínimos y variables de entorno configuradas en CI:
   - `AZURE_TENANT_ID`
   - `AZURE_CLIENT_ID`
   - `AZURE_CLIENT_SECRET`
   - `AZURE_SUBSCRIPTION_ID`
4. Backend remoto (Blob Storage) operativo. Para AURA360 ya se aprovisionó:
   - Resource Group: `rg-tfstate-aura360`
   - Storage Account: `sttfstateaura360`
   - Container: `tfstate`
   - Blob/key sugerido: `aura360-prod.tfstate`

> ⚠️ Si cambias los nombres anteriores, actualiza `infra/azure/terraform/backend.tf` o pasa los valores mediante `terraform init -backend-config` como hace el workflow.

## 📝 Variables por entorno

El archivo `infra/azure/terraform/envs/prod.tfvars` incluye los parámetros recomendados para producción. Ajusta los campos marcados con comentarios:

1. `key_vault_admin_object_id`: Object ID del equipo que administrará secretos (actualmente usa tu usuario `429f59bd-e94f-44cc-a39e-0561144662f8`). Sustituye por un grupo si lo deseas.
2. `allowed_ip_ranges`: reemplaza los CIDR de ejemplo (`203.0.113.0/24`, `198.51.100.10/32`) por las IPs corporativas reales.
3. `aks_vm_size`, `aks_node_count`: adapta a la carga esperada por entorno.
4. `tags`: agrega `owner`, `cost_center`, etc., según políticas internas.

## 🚀 Uso Local

```bash
cd infra/azure/terraform
terraform init -backend-config="resource_group_name=rg-tfstate" \
               -backend-config="storage_account_name=sttfstate" \
               -backend-config="container_name=tfstate" \
               -backend-config="key=aura360-prod.tfstate"
terraform plan -var-file=envs/prod.tfvars
terraform apply -var-file=envs/prod.tfvars
```

> 💡 Ajusta `prod.tfvars` para cada entorno (`stg`, `dev`).

## 🧪 Checklist previo al primer `apply`

1. Ejecuta `az account show` para confirmar la suscripción activa `9a376aee-130b-4d76-8847-63877b872859`.
2. Comprueba acceso al backend: `az storage account show -n sttfstateaura360` y `az storage container list -o table`.
3. Verifica que el Service Principal `sp-aura360-terraform` sigue teniendo el rol **Contributor** + **AcrPush**. Si se rotó el secreto, actualiza los secretos en GitHub antes de continuar.

## 🔁 Pipeline Automatizado

El workflow `.github/workflows/deploy-azure.yml` ejecuta Terraform en dos fases:

1. **Plan** (cualquier push/PR que toque `infra/azure/**`):
   - Formatea (`terraform fmt -check`).
   - Ejecuta `terraform init` usando los secretos del repositorio (`AZURE_*`, `TF_BACKEND_*`).
   - Publica el plan como artefacto y comentario en el PR.

2. **Apply** (solo `workflow_dispatch` con `auto_apply=true`):
   - Reutiliza el plan generado.
   - Llama `terraform apply -auto-approve` usando el mismo tfvars (`ENVIRONMENT`, `TFVARS_FILE`).
   - En caso de éxito, actualiza el comentario del PR con las salidas clave (URLs, nombres de recursos).

### Secretos necesarios en GitHub

| Secreto | Descripción |
| --- | --- |
| `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_SUBSCRIPTION_ID` | Credenciales del Service Principal. |
| `TF_BACKEND_RESOURCE_GROUP`, `TF_BACKEND_STORAGE_ACCOUNT`, `TF_BACKEND_CONTAINER`, `TF_BACKEND_STATE_KEY` | Configuración del backend remoto de Terraform. |
| `TF_VAR_admin_object_id` | Object ID que debe recibir acceso en Key Vault (ej. equipo DevOps). |

### Variables de entorno en el workflow

- `TF_ENVIRONMENT`: `prod`, `stg`, etc. Se usa para seleccionar el archivo tfvars.
- `TFVARS_FILE`: Ruta relativa (`infra/azure/terraform/envs/prod.tfvars`).

Consulta el propio workflow para más detalles de pasos, comandos y artefactos.

### Cómo configurarlo (paso a paso)

1. **Crear secretos globales** (`Settings → Secrets and variables → Actions → New repository secret`):
   - `AZURE_TENANT_ID` = `7279e21a-502b-41bf-9070-f45e0020de36`
   - `AZURE_SUBSCRIPTION_ID` = `9a376aee-130b-4d76-8847-63877b872859`
   - `AZURE_CLIENT_ID` = `dff5ca41-d72b-49a5-b2cb-35427b944c67`
   - `AZURE_CLIENT_SECRET` = valor del password del SP (rota cada vez que se regenere)
   - `TF_BACKEND_RESOURCE_GROUP` = `rg-tfstate-aura360`
   - `TF_BACKEND_STORAGE_ACCOUNT` = `sttfstateaura360`
   - `TF_BACKEND_CONTAINER` = `tfstate`
   - `TF_BACKEND_STATE_KEY` = `aura360-prod.tfstate`
2. **Variables opcionales** (como `TF_VAR_admin_object_id`) pueden definirse como secretos o `env` según el entorno.
3. **Environments protegidos**: crea un Environment `prod` e impón aprobación manual antes de ejecutar `workflow_dispatch` con `auto_apply=true`. Desde el dispatch selecciona `tf_environment=prod` y `tfvars_file=infra/azure/terraform/envs/prod.tfvars`.
4. **Monorepo awareness**: el workflow se dispara únicamente si cambian archivos dentro de `infra/azure/**` o el propio YAML, por lo que no molestará a otros equipos del monorepo.
5. **Reutilizar planes**: después de un PR, descarga el artefacto `tfplan-prod` si necesitas aplicarlo localmente (`terraform apply tfplan`).

## 📌 Próximos Pasos

1. Añadir módulos específicos (p.ej. `modules/aks`, `modules/networking`) si la infraestructura crece.
2. Conectar el clúster AKS con Azure Container Registry mediante Managed Identity y `az role assignment`.
3. Crear charts Helm (o manifests Kustomize) bajo `deploy/azure/` y referenciarlos desde el pipeline.
4. Integrar Azure Monitor Managed Prometheus o Grafana para métricas de Qdrant/Celery.
