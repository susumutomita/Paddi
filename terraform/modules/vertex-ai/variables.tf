variable "project_id" {
  description = "GCPプロジェクトID"
  type        = string
}

variable "environment" {
  description = "環境名（demo, hackathon など）"
  type        = string
  default     = "demo"
}

variable "gemini_model" {
  description = "使用するGeminiモデル"
  type        = string
  default     = "gemini-1.5-flash-002"
}