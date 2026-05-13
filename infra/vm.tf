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
    postgres_password     = var.postgres_password
    openrouter_api_key    = var.openrouter_api_key
    domain_name           = var.domain_name
    grafana_prom_url      = var.grafana_prom_url
    grafana_prom_user     = var.grafana_prom_user
    grafana_prom_password = var.grafana_prom_password
    grafana_loki_url      = var.grafana_loki_url
    grafana_loki_user     = var.grafana_loki_user
    grafana_loki_password = var.grafana_loki_password
  })

  # "Ext-Net" is OVH's public network — assigns a public IP to the VM
  network {
    name = "Ext-Net"
  }
}
