resource "ovh_domain_zone_record" "app_a_record" {
  zone      = var.domain_name
  subdomain = ""
  fieldtype = "A"
  target    = openstack_compute_instance_v2.app.access_ip_v4
}