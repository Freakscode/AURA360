location     = "eastus2"
project_name = "aura360"
environment  = "dev"

# Usa el mismo Object ID que en prod o el de tu equipo de DevOps.
key_vault_admin_object_id = "429f59bd-e94f-44cc-a39e-0561144662f8"

# Espacio de direcciones separado del entorno prod (10.60.0.0/16)
address_space        = ["10.40.0.0/16"]
aks_subnet_cidr      = "10.40.0.0/22"
services_subnet_cidr = "10.40.4.0/22"

# Capacidad reducida para dev/testing
aks_vm_size    = "Standard_D4ads_v5"
aks_node_count = 2

# Reemplaza con las IPs públicas autorizadas para acceder a Key Vault
allowed_ip_ranges = [
  "203.0.113.10/32", # oficina CDMX (ejemplo)
  "198.51.100.24/32" # VPN (ejemplo)
]

tags = {
  owner       = "platform-dev"
  cost_center = "wellness-platform-dev"
}
