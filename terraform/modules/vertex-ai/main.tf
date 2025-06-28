# Vertex AI Module - Paddi用のAI環境設定

# Vertex AI APIを有効化
resource "google_project_service" "aiplatform" {
  service            = "aiplatform.googleapis.com"
  disable_on_destroy = false
}

# Paddi専用のサービスアカウント
resource "google_service_account" "paddi" {
  account_id   = "paddi-analyzer"
  display_name = "Paddi Security Analyzer"
  description  = "GCPセキュリティ監査を実行するPaddiのサービスアカウント"
}

# Vertex AI使用権限
resource "google_project_iam_member" "vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.paddi.email}"
  
  depends_on = [google_project_service.aiplatform]
}

# Security Command Center閲覧権限
resource "google_project_iam_member" "scc_viewer" {
  project = var.project_id
  role    = "roles/securitycenter.findingsViewer"
  member  = "serviceAccount:${google_service_account.paddi.email}"
}

# IAMポリシー閲覧権限
resource "google_project_iam_member" "iam_viewer" {
  project = var.project_id
  role    = "roles/iam.securityReviewer"
  member  = "serviceAccount:${google_service_account.paddi.email}"
}

# ストレージ閲覧権限（監査用）
resource "google_project_iam_member" "storage_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.paddi.email}"
}

# Compute閲覧権限（監査用）
resource "google_project_iam_member" "compute_viewer" {
  project = var.project_id
  role    = "roles/compute.viewer"
  member  = "serviceAccount:${google_service_account.paddi.email}"
}

# サービスアカウントキー生成（ローカル実行用）
resource "google_service_account_key" "paddi_key" {
  service_account_id = google_service_account.paddi.name
}

# キーをローカルファイルに保存
resource "local_file" "paddi_key_file" {
  content  = base64decode(google_service_account_key.paddi_key.private_key)
  filename = "${path.root}/paddi-sa-key.json"
  
  # ファイル権限を制限
  file_permission = "0600"
}