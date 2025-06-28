variable "project_id" {
  description = "GCPプロジェクトID"
  type        = string
}

variable "region" {
  description = "デフォルトリージョン"
  type        = string
  default     = "asia-northeast1"
}

variable "environment" {
  description = "環境名"
  type        = string
  default     = "demo"
}

variable "gemini_model" {
  description = "使用するGeminiモデル"
  type        = string
  default     = "gemini-1.5-flash-002"
}

variable "enable_auto_destroy" {
  description = "自動削除を有効にするか"
  type        = bool
  default     = false
}

variable "auto_destroy_schedule" {
  description = "自動削除のスケジュール（cron形式）"
  type        = string
  default     = "0 2 * * *" # 毎日午前2時
}