variable "project_id"      { type = string }
variable "region"          { type = string }
variable "frontend_domain" { type = string }
variable "api_domain"      { type = string }

variable "agent_env" {
  description = "Env vars for Cloud Run service (map)"
  type        = map(string)
}

variable "rag_env" {
  description = "Env vars for Cloud Run job (map)"
  type        = map(string)
}
