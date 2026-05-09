# SSH key pair for VM access
resource "openstack_compute_keypair_v2" "main" {
  name       = "rag-keypair"
  public_key = var.ssh_public_key
}

# Application VM — runs backend + frontend via Docker Compose
# Caddy is installed on the host to handle TLS (automatic Let's Encrypt)
resource "openstack_compute_instance_v2" "app" {
  name            = "rag-app"
  image_name      = "Ubuntu 24.04"
  flavor_name     = var.vm_flavor
  key_pair        = openstack_compute_keypair_v2.main.name
  security_groups = ["default"]

  # "Ext-Net" is OVH's public network — assigns a public IP to the VM
  network {
    name = "Ext-Net"
  }

  # cloud-init: script executed once on first boot
  # Terraform injects secrets into the template at apply time
  user_data = templatefile("${path.module}/cloud-init.yaml", {
    database_url = join("", [
      "postgresql+asyncpg://rag_user:",
      var.postgres_password,
      "@",
      ovh_cloud_project_database.postgres.endpoints[0].domain,
      ":",
      tostring(ovh_cloud_project_database.postgres.endpoints[0].port),
      "/ragdb?ssl=require"
    ])
    postgres_password  = var.postgres_password
    openrouter_api_key = var.openrouter_api_key
    domain_name        = var.domain_name
  })

  # VM is created only after the managed database is ready
  depends_on = [
    ovh_cloud_project_database.postgres,
    ovh_cloud_project_database_database.ragdb,
  ]
}
