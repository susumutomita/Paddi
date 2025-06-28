# Hackathon環境用の設定（demoを継承）

module "demo" {
  source = "../demo"
  
  # Hackathon特有の設定
  project_id            = var.project_id
  region                = var.region
  environment           = "hackathon"
  gemini_model          = var.gemini_model
  enable_auto_destroy   = true  # ハッカソン環境は自動削除を有効化
  auto_destroy_schedule = "0 6 * * *"  # 毎日午前6時に削除
}