terraform {
  required_version = ">= 1.7"
  required_providers {
    google       = { source = "hashicorp/google",       version = "~> 5.21" }
    google-beta  = { source = "hashicorp/google-beta",  version = "~> 5.21" }
  }

  # backend bucket created manually the first time
  # Uncomment and replace YOUR-PROJECT-ID with actual project ID
  #backend "gcs" {
  #  bucket = "tfstate-YOUR-PROJECT-ID"
  #  prefix = "prod"
  #}
}
