variable "subscription_id" {
  type        = string
  description = "ID de la suscripción. Se puede dejar vacío si se obtiene de las credenciales del provider."
  default     = ""
}

variable "tenant_id" {
  type        = string
  description = "ID del tenant. Se puede dejar vacío si se obtiene del contexto del provider."
  default     = ""
}

variable "location" {
  type        = string
  description = "Región primaria de Azure (ej. eastus2)."
}

variable "project_name" {
  type        = string
  description = "Nombre base del proyecto (ej. aura360)."
}

variable "environment" {
  type        = string
  description = "Etiqueta del entorno (dev, stg, prod)."
  default     = "dev"
}

variable "tags" {
  type        = map(string)
  description = "Etiquetas adicionales para todos los recursos."
  default     = {}
}

variable "address_space" {
  type        = list(string)
  description = "Bloques CIDR para la VNet principal."
  default     = ["10.30.0.0/16"]
}

variable "aks_subnet_cidr" {
  type        = string
  description = "CIDR de la subred donde vivirá AKS."
  default     = "10.30.0.0/20"
}

variable "services_subnet_cidr" {
  type        = string
  description = "CIDR para servicios administrados/privados."
  default     = "10.30.16.0/20"
}

variable "key_vault_admin_object_id" {
  type        = string
  description = "Object ID que recibirá acceso administrativo en Key Vault."
}

variable "acr_sku" {
  type        = string
  description = "SKU del Container Registry."
  default     = "Premium"
}

variable "aks_node_count" {
  type        = number
  description = "Número de nodos iniciales en el node pool system."
  default     = 3
}

variable "aks_vm_size" {
  type        = string
  description = "SKU de VM para el node pool system."
  default     = "Standard_D4ads_v5"
}

variable "enable_monitoring" {
  type        = bool
  description = "Habilitar Azure Monitor Container Insights."
  default     = true
}

variable "storage_sku" {
  type        = string
  description = "SKU del Storage Account multiuso."
  default     = "Standard_LRS"
}

variable "log_analytics_sku" {
  type        = string
  description = "SKU del workspace de Log Analytics."
  default     = "PerGB2018"
}

variable "allowed_ip_ranges" {
  type        = list(string)
  description = "Lista de rangos CIDR permitidos para la regla de firewall del Key Vault (además de las redes privadas)."
  default     = []
}
