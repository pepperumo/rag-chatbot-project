provider "google" {
  project = var.project_id
  region  = var.region
}
provider "google-beta" {
  project = var.project_id
  region  = var.region
}

################  Artifact Registry  ################
resource "google_artifact_registry_repository" "docker" {
  location      = var.region
  repository_id = "docker-artifacts"
  format        = "DOCKER"
}

################  Static-site bucket + HTTPS LB  ####
resource "google_storage_bucket" "frontend" {
  name                        = var.frontend_domain       # must match domain
  location                    = "US"
  uniform_bucket_level_access = true
  
  # Explicitly disable public access prevention to allow allUsers
  public_access_prevention = "inherited"
  
  website {
    main_page_suffix = "index.html"
    not_found_page   = "index.html"
  }
}

# Add public access
resource "google_storage_bucket_iam_member" "public_access" {
  bucket = google_storage_bucket.frontend.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

# Get project data for service account
data "google_project" "project" {}

# Give load balancer service account access to bucket
resource "google_storage_bucket_iam_member" "backend_bucket_access" {
  bucket = google_storage_bucket.frontend.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:service-${data.google_project.project.number}@compute-system.iam.gserviceaccount.com"
}

# Also give broader access for troubleshooting
resource "google_storage_bucket_iam_member" "backend_bucket_legacy" {
  bucket = google_storage_bucket.frontend.name
  role   = "roles/storage.legacyBucketReader"
  member = "serviceAccount:service-${data.google_project.project.number}@compute-system.iam.gserviceaccount.com"
}

resource "google_compute_managed_ssl_certificate" "frontend_ssl" {
  name    = "frontend-ssl"
  managed { domains = [var.frontend_domain] }
}

# Backend bucket with CDN
resource "google_compute_backend_bucket" "frontend" {
  name        = "frontend-backend-bucket"
  bucket_name = google_storage_bucket.frontend.name
  enable_cdn  = true
  
  cdn_policy {
    cache_mode        = "CACHE_ALL_STATIC"
    default_ttl       = 3600
    max_ttl           = 86400
    client_ttl        = 3600
    negative_caching  = true
  }
}

# URL map
resource "google_compute_url_map" "frontend" {
  name            = "frontend-lb"
  default_service = google_compute_backend_bucket.frontend.self_link
}

# HTTPS proxy
resource "google_compute_target_https_proxy" "frontend" {
  name             = "frontend-https-proxy"
  url_map          = google_compute_url_map.frontend.self_link
  ssl_certificates = [google_compute_managed_ssl_certificate.frontend_ssl.self_link]
}

# Global forwarding rule
resource "google_compute_global_forwarding_rule" "frontend" {
  name       = "frontend-lb-forwarding-rule"
  target     = google_compute_target_https_proxy.frontend.self_link
  port_range = "443"
}

# HTTP to HTTPS redirect
resource "google_compute_url_map" "https_redirect" {
  name = "frontend-https-redirect"
  default_url_redirect {
    https_redirect = true
    strip_query    = false
  }
}

resource "google_compute_target_http_proxy" "https_redirect" {
  name    = "frontend-http-proxy"
  url_map = google_compute_url_map.https_redirect.self_link
}

resource "google_compute_global_forwarding_rule" "https_redirect" {
  name       = "frontend-http-forwarding-rule"
  target     = google_compute_target_http_proxy.https_redirect.self_link
  port_range = "80"
}

################  Cloud Run service (Agent API) #####
resource "google_cloud_run_v2_service" "agent" {
  name     = "backend-agent-api"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker.repository_id}/backend_agent_api:latest"
      ports {
        container_port = 8001
      }
      dynamic "env" {
        for_each = var.agent_env
        content {
          name  = env.key
          value = env.value
        }
      }
    }
  }
  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
}

# Make Cloud Run publicly accessible via IAM policy
resource "google_cloud_run_v2_service_iam_policy" "public_access" {
  name     = google_cloud_run_v2_service.agent.name
  location = var.region
  
  policy_data = jsonencode({
    bindings = [
      {
        role = "roles/run.invoker"
        members = ["allUsers"]
      }
    ]
  })
}

################  Cloud Run job (RAG)  ##############
resource "google_cloud_run_v2_job" "rag" {
  provider = google-beta
  name     = "backend-rag-pipeline"
  location = var.region

  template {
    template {
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker.repository_id}/backend_rag_pipeline:latest"
        dynamic "env" {
          for_each = var.rag_env
          content {
            name  = env.key
            value = env.value
          }
        }
      }
      max_retries = 0
      timeout     = "900s"
    }
  }

  # Add native Cloud Run scheduling
  lifecycle {
    ignore_changes = [
      # Allow manual trigger configuration in console
      annotations
    ]
  }
}

# Service account for Cloud Scheduler
resource "google_service_account" "scheduler" {
  account_id   = "rag-scheduler"
  display_name = "RAG Pipeline Scheduler"
}

# Grant Cloud Run invoker role to scheduler service account
resource "google_cloud_run_v2_job_iam_binding" "scheduler_binding" {
  provider = google-beta
  name     = google_cloud_run_v2_job.rag.name
  location = var.region
  role     = "roles/run.invoker"
  members = [
    "serviceAccount:${google_service_account.scheduler.email}"
  ]
}

# Cloud Scheduler job to trigger RAG pipeline every 10 minutes
resource "google_cloud_scheduler_job" "rag_trigger" {
  name        = "rag-every-10m"
  description = "Trigger RAG pipeline every 10 minutes"
  schedule    = "*/10 * * * *"
  region      = var.region
  
  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${data.google_project.project.number}/jobs/${google_cloud_run_v2_job.rag.name}:run"
    
    oauth_token {
      service_account_email = google_service_account.scheduler.email
    }
  }
  
  depends_on = [
    google_cloud_run_v2_job.rag,
    google_cloud_run_v2_job_iam_binding.scheduler_binding
  ]
}

################  Domain mapping (API)  ##############
resource "google_cloud_run_domain_mapping" "api_domain" {
  name     = var.api_domain
  location = var.region
  metadata { namespace = var.project_id }
  spec     { route_name = google_cloud_run_v2_service.agent.name }
}

################  Outputs  ###########################
output "frontend_url" { value = "https://${var.frontend_domain}" }
output "api_url"      { value = "https://${var.api_domain}" }
