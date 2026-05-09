output "vm_ip" {
  description = "VM's IP"
  value = openstack_compute_instance_v2.app.access_ip_v4
}

output "app_url" {
  description = "App url"
  value = "https://${var.domain_name}"
}

output "db_host" {
  description = "DB host"
  value = ovh_cloud_project_database.postgres.endpoints[0].domain
  sensitive = true
}