# Object Storage bucket for artifacts (exported CPT model, datasets, long-term logs)
resource "openstack_objectstorage_container_v1" "artifacts" {
  name = var.artifacts_bucket
}
