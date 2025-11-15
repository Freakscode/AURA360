location     = "eastus2"
project_name = "aura360"
environment  = "prod"

key_vault_admin_object_id = "429f59bd-e94f-44cc-a39e-0561144662f8" # Reemplazar si designas otro grupo/usuario
address_space        = ["10.60.0.0/16"]
aks_subnet_cidr      = "10.60.0.0/20"
services_subnet_cidr = "10.60.16.0/20"
aks_vm_size          = "Standard_D8ads_v5"
aks_node_count       = 4
# Sustituye por las IPs corporativas reales antes de aplicar.
allowed_ip_ranges    = ["203.0.113.0/24", "198.51.100.10/32"]

tags = {
  owner       = "infra-team"
  cost_center = "wellness-platform"
}
