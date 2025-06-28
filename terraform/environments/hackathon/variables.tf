variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "gemini_model" {
  description = "Gemini model to use"
  type        = string
  default     = "gemini-1.5-flash"
}