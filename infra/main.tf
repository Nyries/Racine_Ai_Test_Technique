terraform {
  required_version = ">= 1.6"

  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = ">= 2.1"
    }
    ovh = {
      source  = "ovh/ovh"
      version = ">= 0.40"
    }
  }

  # Remote state stored in OVH Object Storage (S3-compatible)
  # The bucket "tfstate-rag" must be created manually once before "terraform init"
  backend "s3" {
    bucket = "tfstate-rag"
    key    = "prod/terraform.tfstate"
    region = "gra"
    endpoints = {
      s3 = "https://s3.gra.io.cloud.ovh.net"
    }
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    skip_region_validation      = true
    skip_requesting_account_id  = true
    use_path_style              = true
  }
}

# OVH provider — for Secret Manager (OKMS)
# Credentials from env vars: OVH_ENDPOINT, OVH_APPLICATION_KEY, OVH_APPLICATION_SECRET, OVH_CONSUMER_KEY
provider "ovh" {
  endpoint = "ovh-eu"
}

# Storage provider — region GRA (Object Storage)
# Credentials from env vars: OS_AUTH_URL, OS_USERNAME, OS_PASSWORD, OS_TENANT_ID
provider "openstack" {
  region = "GRA"
}

# Compute provider — region GRA11 (VM instances)
# Same credentials, different region where compute endpoints live
provider "openstack" {
  alias  = "compute"
  region = "GRA9"
}
