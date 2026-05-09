terraform {
  required_version = ">= 1.6"

  required_providers {
    # OVH provider — used for OVH-specific managed services (database, DNS)
    ovh = {
      source  = "ovh/ovh"
      version = "~> 1.3"
    }
    # OpenStack provider — used for compute and object storage
    # OVH is built on OpenStack and exposes the standard OpenStack API
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = "~> 2.1"
    }
  }

  # Remote state stored in OVH Object Storage (S3-compatible protocol)
  # This bucket must be created manually once before running "terraform init"
  # See README section "Redeploy" for step-by-step instructions
  backend "s3" {
    bucket                      = "tfstate-rag"
    key                         = "prod/terraform.tfstate"
    region                      = "gra"
    endpoint                    = "https://s3.gra.io.cloud.ovh.net"
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    skip_region_validation      = true
    force_path_style            = true
  }
}

provider "ovh" {
  endpoint = "ovh-eu"
  # Credentials via environment variables:
  # OVH_APPLICATION_KEY, OVH_APPLICATION_SECRET, OVH_CONSUMER_KEY
  # Generate them at https://api.ovh.com/createToken
}

provider "openstack" {
  auth_url    = "https://auth.cloud.ovh.net/v3"
  domain_name = "Default"
  tenant_id   = var.ovh_project_id
  region      = var.region
  # Credentials via environment variables:
  # OS_USERNAME, OS_PASSWORD
  # These are your OVH Public Cloud user credentials (not your OVH account)
}
