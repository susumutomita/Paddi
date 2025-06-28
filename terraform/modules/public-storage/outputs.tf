output "public_bucket_name" {
  description = "公開バケット名"
  value       = google_storage_bucket.public_data.name
}

output "public_bucket_url" {
  description = "公開バケットのURL"
  value       = google_storage_bucket.public_data.url
}

output "backup_bucket_name" {
  description = "公開バックアップバケット名"
  value       = google_storage_bucket.public_backup.name
}

output "storage_vulnerabilities" {
  description = "Paddiが検出すべきストレージの脆弱性"
  value = [
    {
      type        = "PUBLIC_STORAGE_BUCKET"
      resource    = google_storage_bucket.public_data.name
      severity    = "CRITICAL"
      description = "ストレージバケットが全世界に公開されています"
    },
    {
      type        = "SENSITIVE_DATA_EXPOSED"
      resource    = "${google_storage_bucket.public_data.name}/sensitive/customer-data.csv"
      severity    = "CRITICAL"
      description = "機密データが公開バケットに保存されています"
    },
    {
      type        = "API_KEYS_EXPOSED"
      resource    = "${google_storage_bucket.public_data.name}/config/api-keys.json"
      severity    = "CRITICAL"
      description = "APIキーが公開バケットに保存されています"
    },
    {
      type        = "PUBLIC_BACKUP_BUCKET"
      resource    = google_storage_bucket.public_backup.name
      severity    = "HIGH"
      description = "バックアップバケットが公開されています"
    }
  ]
}