# Cloud Run デプロイメントガイド

## 前提条件

1. Google Cloud プロジェクトを作成済み
2. Google Cloud CLI (`gcloud`) をインストール済み
3. 請求先アカウントを設定済み

## デプロイ手順

### 1. Google Cloud 認証

```bash
# Google Cloudにログイン
gcloud auth login

# プロジェクトを設定
gcloud config set project YOUR_PROJECT_ID
```

### 2. 必要なAPIを有効化

```bash
# Cloud Run APIを有効化
gcloud services enable run.googleapis.com

# Container Registry APIを有効化
gcloud services enable containerregistry.googleapis.com

# Cloud Build APIを有効化
gcloud services enable cloudbuild.googleapis.com

# Vertex AI APIを有効化（Gemini使用のため）
gcloud services enable aiplatform.googleapis.com
```

### 3. デプロイ実行

```bash
# プロジェクトIDを環境変数に設定
export GOOGLE_CLOUD_PROJECT="your-project-id"

# デプロイスクリプトを実行
./deploy.sh
```

## デプロイ後の確認

デプロイが成功すると、以下のようなURLが表示されます：

```
Service URL: https://paddi-xxxxx-an.a.run.app
```

## アクセス方法

### Webダッシュボード
ブラウザで Service URL にアクセス

### API経由での監査実行
```bash
# 監査を実行
curl -X POST https://paddi-xxxxx-an.a.run.app/api/audit \
  -H "Content-Type: application/json" \
  -d '{"provider": "gcp", "use_mock": true}'
```

## トラブルシューティング

### エラー: APIs not enabled
```bash
# 必要なAPIを一括で有効化
gcloud services enable \
  run.googleapis.com \
  containerregistry.googleapis.com \
  cloudbuild.googleapis.com \
  aiplatform.googleapis.com
```

### エラー: Quota exceeded
- Cloud Runの無料枠を確認
- リージョンを変更してみる（us-central1など）

### エラー: Build failed
```bash
# ローカルでDockerビルドをテスト
docker build -t paddi-test .
docker run -p 8080:8080 paddi-test
```