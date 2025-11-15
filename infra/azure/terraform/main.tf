locals {
  name_prefix = "${var.project_name}-${var.environment}"
  tags = merge({
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
  }, var.tags)
}

resource "azurerm_resource_group" "core" {
  name     = "${local.name_prefix}-rg"
  location = var.location
  tags     = local.tags
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "${local.name_prefix}-law"
  location            = azurerm_resource_group.core.location
  resource_group_name = azurerm_resource_group.core.name
  sku                 = var.log_analytics_sku
  retention_in_days   = 30
  tags                = local.tags
}

resource "azurerm_storage_account" "core" {
  name                     = replace("${local.name_prefix}core", "-", "")
  resource_group_name      = azurerm_resource_group.core.name
  location                 = azurerm_resource_group.core.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"
  allow_nested_items_to_be_public = false
  tags                     = local.tags
}

resource "azurerm_container_registry" "acr" {
  name                = substr(replace("${local.name_prefix}acr", "-", ""), 0, 50)
  resource_group_name = azurerm_resource_group.core.name
  location            = azurerm_resource_group.core.location
  sku                 = var.acr_sku
  admin_enabled       = false
  tags                = local.tags
}

resource "azurerm_virtual_network" "core" {
  name                = "${local.name_prefix}-vnet"
  address_space       = var.address_space
  location            = azurerm_resource_group.core.location
  resource_group_name = azurerm_resource_group.core.name
  tags                = local.tags
}

resource "azurerm_subnet" "aks" {
  name                 = "${local.name_prefix}-aks"
  resource_group_name  = azurerm_resource_group.core.name
  virtual_network_name = azurerm_virtual_network.core.name
  address_prefixes     = [var.aks_subnet_cidr]

  delegations {
    name = "aks-delegation"
    service_delegation {
      name = "Microsoft.ContainerService/managedClusters"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action",
        "Microsoft.Network/virtualNetworks/subnets/prepareNetworkPolicies/action"
      ]
    }
  }
}

resource "azurerm_subnet" "services" {
  name                 = "${local.name_prefix}-services"
  resource_group_name  = azurerm_resource_group.core.name
  virtual_network_name = azurerm_virtual_network.core.name
  address_prefixes     = [var.services_subnet_cidr]
  service_endpoints    = ["Microsoft.KeyVault"]
}

resource "azurerm_key_vault" "main" {
  name                       = substr(replace("${local.name_prefix}kv", "-", ""), 0, 24)
  location                   = azurerm_resource_group.core.location
  resource_group_name        = azurerm_resource_group.core.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = true
  tags                       = local.tags

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = ["Get", "List", "Set", "Delete", "Recover", "Backup", "Restore"]
    key_permissions    = ["Get", "List", "Create", "Delete", "Recover", "Backup", "Restore"]
  }

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = var.key_vault_admin_object_id

    secret_permissions = ["Get", "List", "Set", "Purge", "Recover", "Backup", "Restore"]
    key_permissions    = ["Get", "List", "Create", "Delete", "Purge", "Recover", "Backup", "Restore"]
  }

  network_acls {
    bypass         = "AzureServices"
    default_action = "Deny"
    ip_rules       = var.allowed_ip_ranges
    virtual_network_subnet_ids = [
      azurerm_subnet.services.id
    ]
  }
}

resource "azurerm_kubernetes_cluster" "aks" {
  name                = "${local.name_prefix}-aks"
  location            = azurerm_resource_group.core.location
  resource_group_name = azurerm_resource_group.core.name
  dns_prefix          = "${local.name_prefix}-aks"
  sku_tier            = "Standard"

  default_node_pool {
    name                = "system"
    vm_size             = var.aks_vm_size
    node_count          = var.aks_node_count
    vnet_subnet_id      = azurerm_subnet.aks.id
    type                = "VirtualMachineScaleSets"
    enable_auto_scaling = true
    min_count           = 3
    max_count           = 10
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin    = "azure"
    network_policy    = "azure"
    dns_service_ip    = "10.2.0.10"
    service_cidr      = "10.2.0.0/16"
    docker_bridge_cidr = "172.17.0.1/16"
  }

  monitor_metrics {
    tier = var.enable_monitoring ? "Basic" : "None"
  }

  oms_agent {
    msi_auth_for_monitoring_enabled = var.enable_monitoring
    log_analytics_workspace_id      = var.enable_monitoring ? azurerm_log_analytics_workspace.main.id : null
  }

  tags = local.tags
}

resource "azurerm_role_assignment" "aks_acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.aks.kubelet_identity[0].object_id
}
