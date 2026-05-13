#!/bin/bash
# Copy this file to setup-env.sh, fill in the values, then run:
#   source infra/setup-env.sh
# Never commit setup-env.sh (it is gitignored).

# OpenStack credentials — from your OVH Public Cloud openrc.sh
export OS_AUTH_URL=https://auth.cloud.ovh.net/v3
export OS_IDENTITY_API_VERSION=3
export OS_USER_DOMAIN_NAME="Default"
export OS_PROJECT_DOMAIN_NAME="Default"
export OS_TENANT_ID="<your-project-id>"           # ovh_project_id in terraform.tfvars
export OS_TENANT_NAME="<your-account-number>"
export OS_USERNAME="<your-openstack-username>"
export OS_REGION_NAME="GRA"
echo "Enter OpenStack password for $OS_USERNAME:"
read -sr OS_PASSWORD
export OS_PASSWORD

# OVH API credentials — create at https://api.ovh.com/createApp/
# then generate a consumer key via POST /auth/credential
export OVH_ENDPOINT="ovh-eu"
export OVH_APPLICATION_KEY="<your-app-key>"
export OVH_APPLICATION_SECRET="<your-app-secret>"
export OVH_CONSUMER_KEY="<your-consumer-key>"

# OVH Object Storage S3 credentials — for Terraform remote state
# Generate in OVH console: Object Storage → S3 credentials
export AWS_ACCESS_KEY_ID="<your-s3-access-key>"
export AWS_SECRET_ACCESS_KEY="<your-s3-secret-key>"

echo "Environment ready."
