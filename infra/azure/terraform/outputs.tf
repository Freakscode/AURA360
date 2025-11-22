output "resource_group_name" {
  value       = azurerm_resource_group.core.name
  description = "Nombre del resource group principal."
}

output "acr_login_server" {
  value       = azurerm_container_registry.acr.login_server
  description = "Servidor de login del Azure Container Registry."
}

output "aks_name" {
  value       = azurerm_kubernetes_cluster.aks.name
  description = "Nombre del clúster AKS desplegado."
}

output "key_vault_name" {
  value       = azurerm_key_vault.main.name
  description = "Nombre del Key Vault que almacena secretos sensibles."
}

output "storage_account_name" {
  value       = azurerm_storage_account.core.name
  description = "Storage account multiuso (respaldo, blobs, tfstate opcional)."
}

output "log_analytics_workspace_id" {
  value       = azurerm_log_analytics_workspace.main.id
  description = "ID del workspace de Log Analytics para integrar con Azure Monitor."
}
