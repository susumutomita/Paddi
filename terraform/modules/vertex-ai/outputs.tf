output "paddi_sa_email" {
  description = "PaddiサービスアカウントのEmail"
  value       = google_service_account.paddi.email
}

output "paddi_sa_key_path" {
  description = "Paddiサービスアカウントキーのファイルパス"
  value       = local_file.paddi_key_file.filename
  sensitive   = true
}

output "enabled_apis" {
  description = "有効化されたAPI"
  value = [
    "aiplatform.googleapis.com"
  ]
}

output "paddi_permissions" {
  description = "Paddiに付与された権限"
  value = [
    "roles/aiplatform.user",
    "roles/securitycenter.findingsViewer",
    "roles/iam.securityReviewer",
    "roles/storage.objectViewer",
    "roles/compute.viewer"
  ]
}