output "project_id" {
  description = "GCPプロジェクトID"
  value       = var.project_id
}

output "paddi_sa_email" {
  description = "PaddiサービスアカウントのEmail"
  value       = module.vertex_ai.paddi_sa_email
}

output "paddi_sa_key_path" {
  description = "Paddiサービスアカウントキーのパス"
  value       = module.vertex_ai.paddi_sa_key_path
  sensitive   = true
}

output "vulnerable_resources" {
  description = "作成された脆弱なリソース"
  value = {
    overprivileged_sa   = module.vulnerable_iam.overprivileged_sa_email
    unnecessary_admin   = module.vulnerable_iam.unnecessary_admin_sa_email
    public_bucket       = module.public_storage.public_bucket_name
    public_backup       = module.public_storage.backup_bucket_name
  }
}

output "public_bucket_url" {
  description = "公開バケットのURL"
  value       = module.public_storage.public_bucket_url
}

output "paddi_command" {
  description = "Paddi実行コマンド"
  value       = "python main.py audit --project-id ${var.project_id}"
}

output "cleanup_command" {
  description = "環境削除コマンド"
  value       = "cd ${path.root} && terraform destroy -auto-approve"
}