variable "ovh_project_id" {
  description = "OVH Public Cloud project ID (visible in the OVH console)"
  type        = string
}

variable "region" {
  description = "OVH region for compute resources"
  type        = string
  default     = "GRA11"
}

variable "db_region" {
  description = "OVH region for managed PostgreSQL"
  type        = string
  default     = "GRA"
}

variable "vm_flavor" {
  description = "VM instance flavor (b2-15 = 4 vCPU, 15 GB RAM — needed to load BGE-M3 and reranker models)"
  type        = string
  default     = "b2-15"
}

variable "ssh_public_key" {
  description = "SSH public key for VM access (contents of ~/.ssh/id_ed25519.pub)"
  type        = string
}

variable "domain_name" {
  description = "Application domain name (e.g. rag.my-domain.com or a nip.io subdomain)"
  type        = string
}

variable "postgres_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "openrouter_api_key" {
  description = "OpenRouter API key"
  type        = string
  sensitive   = true
}

variable "artifacts_bucket" {
  description = "OVH Object Storage bucket name for artifacts (models, datasets, long-term logs)"
  type        = string
  default     = "rag-artifacts"
}
