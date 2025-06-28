# Paddi Terraform インフラストラクチャ

このディレクトリには、Paddiのデモ環境を自動構築するためのTerraformコードが含まれています。

## 🎯 概要

Paddiは、GCPのセキュリティ監査を自動化するツールです。このTerraformコードは、Paddiが検出すべき**意図的に脆弱な環境**をワンコマンドで構築します。

### 作成される脆弱性（デモ用）

1. **過剰なIAM権限**
   - Owner権限を持つサービスアカウント
   - Editor権限を持つ不要なサービスアカウント
   - 長期間有効なサービスアカウントキー

2. **公開ストレージ**
   - allUsersに公開されたバケット
   - 機密データ（ダミー）を含む公開バケット
   - APIキー（ダミー）を含む設定ファイル

3. **Vertex AI環境**
   - Paddi実行用のサービスアカウントと権限

## 🚀 クイックスタート

### 前提条件

- Terraform >= 1.0
- Google Cloud SDK (gcloud)
- 有効なGCPプロジェクト
- 適切な権限（Project Editor以上）

### デプロイ手順

```bash
# 1. 設定ファイルを準備
cd terraform/environments/demo
cp terraform.tfvars.example terraform.tfvars
vim terraform.tfvars  # project_id を設定

# 2. デプロイ実行（5分程度）
../../scripts/deploy.sh

# 3. Paddiで監査実行
cd ../../..
python main.py audit --project-id YOUR_PROJECT_ID
```

### 環境削除

```bash
# コスト削減のため、使用後は必ず削除してください
cd terraform/environments/demo
../../scripts/destroy.sh
```

## 📁 ディレクトリ構造

```
terraform/
├── environments/          # 環境別設定
│   ├── demo/             # デモ環境
│   └── hackathon/        # ハッカソン環境
├── modules/              # 再利用可能なモジュール
│   ├── vulnerable-iam/   # 脆弱なIAM設定
│   ├── public-storage/   # 公開ストレージ
│   └── vertex-ai/        # Vertex AI設定
└── scripts/              # 自動化スクリプト
    ├── deploy.sh         # デプロイスクリプト
    └── destroy.sh        # 削除スクリプト
```

## ⚙️ 設定オプション

`terraform.tfvars` で以下の設定が可能：

```hcl
# 必須
project_id = "your-gcp-project-id"

# オプション
region                = "asia-northeast1"
environment           = "demo"
enable_auto_destroy   = true              # 自動削除を有効化
auto_destroy_schedule = "0 2 * * *"       # 毎日午前2時に削除
```

## 💰 コスト管理

- **自動削除機能**: 指定時刻に環境を自動削除
- **ライフサイクルルール**: ストレージは7日後に自動削除
- **推定コスト**: 1日あたり$5-10程度（使用量による）

## ⚠️ セキュリティ警告

このTerraformコードは**教育・デモ目的**で意図的に脆弱な環境を作成します：

- ❌ 本番環境では絶対に使用しないでください
- ❌ 実際のデータを配置しないでください
- ✅ 使用後は必ず環境を削除してください

## 🔧 トラブルシューティング

### APIが有効化されていないエラー

```bash
# 必要なAPIを手動で有効化
gcloud services enable compute.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable iam.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

### 権限エラー

```bash
# 現在の認証情報を確認
gcloud auth list

# プロジェクトを設定
gcloud config set project YOUR_PROJECT_ID
```

### Terraform状態ファイルの破損

```bash
# バックアップから復元
cd terraform/environments/demo
cp backups/最新のバックアップ/terraform.tfstate ./
```

## 📚 参考資料

- [Terraform Google Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [GCP IAMベストプラクティス](https://cloud.google.com/iam/docs/best-practices)
- [Paddiプロジェクト](https://github.com/susumutomita/Paddi)