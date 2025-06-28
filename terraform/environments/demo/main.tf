terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 脆弱なIAM設定モジュール
module "vulnerable_iam" {
  source      = "../../modules/vulnerable-iam"
  project_id  = var.project_id
  environment = var.environment
}

# 公開ストレージモジュール
module "public_storage" {
  source      = "../../modules/public-storage"
  project_id  = var.project_id
  environment = var.environment
}

# Vertex AIモジュール
module "vertex_ai" {
  source       = "../../modules/vertex-ai"
  project_id   = var.project_id
  environment  = var.environment
  gemini_model = var.gemini_model
}

# コスト管理: Pub/Sub トピックとスケジューラー
resource "google_pubsub_topic" "destroy_trigger" {
  name = "paddi-demo-destroy-trigger"
}

resource "google_project_service" "scheduler" {
  service            = "cloudscheduler.googleapis.com"
  disable_on_destroy = false
}

# 自動削除ジョブ（デフォルトは無効）
resource "google_cloud_scheduler_job" "destroy_demo" {
  count       = var.enable_auto_destroy ? 1 : 0
  name        = "destroy-demo-env-${var.environment}"
  description = "デモ環境を自動削除（コスト削減）"
  schedule    = var.auto_destroy_schedule
  time_zone   = "Asia/Tokyo"
  
  pubsub_target {
    topic_name = google_pubsub_topic.destroy_trigger.id
    data       = base64encode(jsonencode({
      action      = "destroy"
      environment = var.environment
      project_id  = var.project_id
    }))
  }
  
  depends_on = [google_project_service.scheduler]
}

# 脆弱性サマリーをローカルファイルに出力
resource "local_file" "vulnerability_summary" {
  filename = "${path.root}/vulnerability-summary.json"
  content = jsonencode({
    project_id  = var.project_id
    environment = var.environment
    created_at  = timestamp()
    
    iam_vulnerabilities     = module.vulnerable_iam.vulnerable_findings
    storage_vulnerabilities = module.public_storage.storage_vulnerabilities
    
    resources = {
      service_accounts = [
        module.vulnerable_iam.overprivileged_sa_email,
        module.vulnerable_iam.unnecessary_admin_sa_email,
        module.vertex_ai.paddi_sa_email
      ]
      storage_buckets = [
        module.public_storage.public_bucket_name,
        module.public_storage.backup_bucket_name
      ]
    }
    
    paddi_config = {
      service_account = module.vertex_ai.paddi_sa_email
      key_path        = module.vertex_ai.paddi_sa_key_path
    }
  })
  
  file_permission = "0644"
}