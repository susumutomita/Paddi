# Public Storage Module - 意図的に公開設定（デモ用）

resource "google_storage_bucket" "public_data" {
  name          = "${var.project_id}-public-demo-${var.environment}"
  location      = "ASIA-NORTHEAST1"
  force_destroy = true

  # 意図的に公開設定（セキュリティリスク）
  uniform_bucket_level_access = false

  lifecycle_rule {
    condition {
      age = 7 # 7日後に自動削除（コスト削減）
    }
    action {
      type = "Delete"
    }
  }

  versioning {
    enabled = false
  }
}

# バケット全体を公開（危険な設定）
resource "google_storage_bucket_iam_member" "public_viewer" {
  bucket = google_storage_bucket.public_data.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

# 機密データっぽいダミーファイルを配置
resource "google_storage_bucket_object" "sensitive_data" {
  name    = "sensitive/customer-data.csv"
  bucket  = google_storage_bucket.public_data.name
  content = <<-EOT
    customer_id,name,email,credit_card
    1,Demo User,demo@example.com,****-****-****-1234
    2,Test User,test@example.com,****-****-****-5678
  EOT
}

resource "google_storage_bucket_object" "api_keys" {
  name   = "config/api-keys.json"
  bucket = google_storage_bucket.public_data.name
  content = jsonencode({
    api_key = "DEMO-API-KEY-${var.environment}"
    secret  = "THIS-IS-A-DEMO-SECRET"
    note    = "これはPaddiデモ用のダミーデータです"
  })
}

# 別の公開バケット（バックアップと称して）
resource "google_storage_bucket" "public_backup" {
  name          = "${var.project_id}-backup-demo-${var.environment}"
  location      = "ASIA-NORTHEAST1"
  force_destroy = true

  uniform_bucket_level_access = false

  lifecycle_rule {
    condition {
      age = 7
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket_iam_member" "backup_public" {
  bucket = google_storage_bucket.public_backup.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}