output "vm_ip" {
  description = "VM public IP — update your DuckDNS record to point to this address"
  value       = openstack_compute_instance_v2.app.access_ip_v4
}

output "app_url" {
  description = "Application URL"
  value       = "https://${var.domain_name}"
}
