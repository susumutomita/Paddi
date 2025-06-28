variable "project_id" {
  description = "GCPプロジェクトID"
  type        = string
}

variable "environment" {
  description = "環境名（demo, hackathon など）"
  type        = string
  default     = "demo"
}