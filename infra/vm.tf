# SSH key pair for VM access
resource "openstack_compute_keypair_v2" "main" {
  provider   = openstack.compute
  name       = "rag-keypair"
  public_key = var.ssh_public_key
}

# Application VM — runs the full Docker Compose stack (db + backend + frontend)
# Caddy is installed on the host to handle TLS (automatic Let's Encrypt)
resource "openstack_compute_instance_v2" "app" {
  provider        = openstack.compute
  name            = "rag-app"
  image_name      = "Ubuntu 24.04"
  flavor_name     = var.vm_flavor
  key_pair        = openstack_compute_keypair_v2.main.name
  security_groups = ["default"]

  user_data = templatefile("${path.module}/cloud-init.yaml", {
    postgres_password  = var.postgres_password
    openrouter_api_key = var.openrouter_api_key
    domain_name        = var.domain_name
  })

  # "Ext-Net" is OVH's public network — assigns a public IP to the VM
  network {
    name = "Ext-Net"
  }
}
