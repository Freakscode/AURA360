terraform {
  backend "azurerm" {
    resource_group_name  = "rg-tfstate-aura360"
    storage_account_name = "sttfstateaura360"
    container_name       = "tfstate"
    key                  = "aura360-prod.tfstate"
  }
}

# Si prefieres parametrizar el backend desde el pipeline (por ejemplo, con secretos
# en GitHub Actions), elimina estos valores y pasa las banderas correspondientes a
# `terraform init -backend-config=...`. El workflow `deploy-azure.yml` ya demuestra
# cómo hacerlo dinámicamente sin hardcodear credenciales.
