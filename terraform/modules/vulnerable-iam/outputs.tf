output "overprivileged_sa_email" {
  description = "過剰権限サービスアカウントのメールアドレス"
  value       = google_service_account.overprivileged.email
}

output "unnecessary_admin_sa_email" {
  description = "不要な管理者権限サービスアカウントのメールアドレス"
  value       = google_service_account.unnecessary_admin.email
}

output "vulnerable_findings" {
  description = "Paddiが検出すべき脆弱性のリスト"
  value = [
    {
      type        = "OVERPRIVILEGED_SERVICE_ACCOUNT"
      resource    = google_service_account.overprivileged.email
      severity    = "CRITICAL"
      description = "サービスアカウントにOwner権限が付与されています"
    },
    {
      type        = "EXCESSIVE_PERMISSIONS"
      resource    = google_service_account.unnecessary_admin.email
      severity    = "HIGH"
      description = "サービスアカウントにEditor権限が付与されています"
    },
    {
      type        = "SERVICE_ACCOUNT_KEY_EXISTS"
      resource    = google_service_account.overprivileged.email
      severity    = "MEDIUM"
      description = "サービスアカウントキーが存在します"
    }
  ]
}