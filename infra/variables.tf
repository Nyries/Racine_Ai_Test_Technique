variable "ovh_project_id" {
  description = "OVH Public Cloud project ID (OS_TENANT_ID in openrc.sh)"
  type        = string
}

variable "vm_flavor" {
  description = "VM instance flavor (b3-16 = 4 vCPU, 15 GB RAM)"
  type        = string
  default     = "b3-16"
}

variable "ssh_public_key" {
  description = "SSH public key for VM access (contents of ~/.ssh/id_ed25519.pub)"
  type        = string
}

variable "domain_name" {
  description = "Application domain name (e.g. rag.mon-domaine.duckdns.org)"
  type        = string
}

variable "postgres_password" {
  description = "PostgreSQL password for the Docker Compose db container"
  type        = string
  sensitive   = true
}

variable "openrouter_api_key" {
  description = "OpenRouter API key"
  type        = string
  sensitive   = true
}

variable "artifacts_bucket" {
  description = "OVH Object Storage bucket name for artifacts"
  type        = string
  default     = "rag-artifacts"
}
