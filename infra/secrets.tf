resource "ovh_okms" "rag" {
  ovh_subsidiary = "FR"
  region         = "eu-west-gra"
  display_name   = "rag-secrets"
}

resource "ovh_okms_secret" "postgres_password" {
  okms_id = ovh_okms.rag.id
  path    = "rag/postgres-password"
  version = {
    data = jsonencode({ value = var.postgres_password })
  }
}

resource "ovh_okms_secret" "openrouter_api_key" {
  okms_id = ovh_okms.rag.id
  path    = "rag/openrouter-api-key"
  version = {
    data = jsonencode({ value = var.openrouter_api_key })
  }
}
