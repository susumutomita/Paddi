# Cloud Run デプロイガイド

## 前提条件

- Google Cloud アカウント
- gcloud CLI インストール済み

## デプロイ手順

### 1. プロジェクトIDを設定
```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

### 2. デプロイ実行
```bash
./deploy.sh
```

## デプロイ後の確認

デプロイが成功すると、以下のようなURLが表示されます：
```
Service URL: https://paddi-xxxxx-an.a.run.app
```

このURLにブラウザでアクセスすると、Paddiのダッシュボードが表示されます。

## トラブルシューティング

### APIが有効になっていない場合
```bash
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

### ローカルでのテスト
```bash
docker build -t paddi-test .
docker run -p 8080:8080 -e PORT=8080 -e USE_MOCK_DATA=true paddi-test
```

ブラウザで http://localhost:8080 にアクセス