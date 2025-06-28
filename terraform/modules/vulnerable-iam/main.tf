# Vulnerable IAM Module - 意図的に脆弱な設定を作成（デモ用）

resource "google_service_account" "overprivileged" {
  account_id   = "demo-overprivileged-sa"
  display_name = "過剰な権限を持つサービスアカウント（デモ用）"
  description  = "Paddiデモ用の意図的に脆弱なサービスアカウント"
}

# 意図的にOwner権限を付与（セキュリティ監査デモ用）
resource "google_project_iam_member" "sa_owner" {
  project = var.project_id
  role    = "roles/owner"
  member  = "serviceAccount:${google_service_account.overprivileged.email}"
}

# 過剰な権限を持つ別のサービスアカウント
resource "google_service_account" "unnecessary_admin" {
  account_id   = "demo-unnecessary-admin"
  display_name = "不要な管理者権限（デモ用）"
  description  = "Paddiが検出すべき過剰権限の例"
}

# Editor権限（これも過剰）
resource "google_project_iam_member" "sa_editor" {
  project = var.project_id
  role    = "roles/editor"
  member  = "serviceAccount:${google_service_account.unnecessary_admin.email}"
}

# 古いサービスアカウントキー（セキュリティリスク）
resource "google_service_account_key" "demo_key" {
  service_account_id = google_service_account.overprivileged.name
  public_key_type    = "TYPE_X509_PEM_FILE"
}