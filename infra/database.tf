# Managed PostgreSQL — OVH handles backups, updates and availability
resource "ovh_cloud_project_database" "postgres" {
  service_name = var.ovh_project_id
  description  = "rag-postgres"
  engine       = "postgresql"
  version      = "16"
  plan         = "essential"
  flavor       = "db1-4"

  nodes {
    region = var.db_region
  }
}

resource "ovh_cloud_project_database_user" "rag" {
  service_name   = var.ovh_project_id
  cluster_id     = ovh_cloud_project_database.postgres.id
  engine         = "postgresql"
  name           = "rag_user"
  password_reset = var.postgres_password
}

resource "ovh_cloud_project_database_database" "ragdb" {
  service_name = var.ovh_project_id
  cluster_id   = ovh_cloud_project_database.postgres.id
  engine       = "postgresql"
  name         = "ragdb"
}

# Grant pg_vector role so the rag_user can create the vector extension
resource "ovh_cloud_project_database_postgresql_user_roles" "pgvector" {
  service_name = var.ovh_project_id
  cluster_id   = ovh_cloud_project_database.postgres.id
  user_id      = ovh_cloud_project_database_user.rag.id

  roles = ["pg_vector"]

  depends_on = [ovh_cloud_project_database_database.ragdb]
}
