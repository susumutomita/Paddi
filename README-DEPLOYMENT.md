# 🚀 Paddi デプロイメント＆使用ガイド

## デプロイ方法（開発者向け）

### 1. 事前準備
```bash
# Google Cloud CLIをインストール
brew install google-cloud-sdk  # macOS
# または
curl https://sdk.cloud.google.com | bash

# ログイン
gcloud auth login

# プロジェクト作成（まだの場合）
gcloud projects create my-paddi-demo --name="Paddi Demo"

# 請求先アカウントをリンク（必須）
gcloud billing projects link my-paddi-demo --billing-account=BILLING_ACCOUNT_ID
```

### 2. デプロイ実行
```bash
# プロジェクトIDを設定
export GOOGLE_CLOUD_PROJECT="my-paddi-demo"

# デプロイ（約5分）
./deploy.sh
```

### 3. デプロイ完了後
```
✅ Deployment complete!
Service URL: https://paddi-xxxxx-an.a.run.app

You can now access:
- Web Dashboard: https://paddi-xxxxx-an.a.run.app
- API: https://paddi-xxxxx-an.a.run.app/api/audit
```

## 使い方（エンドユーザー向け）

### 🌐 Webブラウザで使う

1. **Service URLにアクセス**
   - モダンなダッシュボードが表示されます
   - 認証不要ですぐに試せます

2. **「Start Audit」をクリック**
   - デモ用のセキュリティ監査が実行されます
   - リアルタイムで脆弱性が表示されます

3. **レポートをダウンロード**
   - Markdown、HTML、PDF形式で出力可能

### 🔧 APIとして使う

```bash
# セキュリティ監査を実行
curl -X POST https://paddi-xxxxx.a.run.app/api/audit \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "gcp",
    "project_id": "demo-project",
    "use_mock": true
  }'

# レスポンス例
{
  "status": "success",
  "findings": [
    {
      "title": "Service Account with Owner Role",
      "severity": "CRITICAL",
      "description": "Service account has excessive permissions",
      "recommendation": "Apply principle of least privilege"
    }
  ],
  "report_url": "/api/export/html"
}
```

### 🔗 CI/CDパイプラインに組み込む

```yaml
# GitHub Actions例
- name: Security Audit
  run: |
    RESPONSE=$(curl -s -X POST ${{ secrets.PADDI_URL }}/api/audit \
      -H "Content-Type: application/json" \
      -d '{"provider": "gcp"}')
    
    # 重大な脆弱性があれば失敗
    if echo "$RESPONSE" | jq '.findings[] | select(.severity == "CRITICAL")' | grep -q .; then
      echo "Critical vulnerabilities found!"
      exit 1
    fi
```

## セキュリティとアクセス制御

### 現在（デモ版）
- ✅ **認証不要** - すぐに試せます
- ✅ **モックデータ使用** - 実際のGCPアクセスは不要
- ✅ **読み取り専用** - 何も変更しません

### 将来（本番版）
- 🔐 **OAuth2認証** - ユーザーが自分のGCPを安全に接続
- 🔐 **APIキー管理** - プログラマティックアクセス用
- 🔐 **監査ログ** - 全アクセスを記録

## よくある質問

### Q: GCPアカウントは必要ですか？
**A: いいえ！** デモ版はモックデータで動作するため、GCPアカウントは不要です。

### Q: 料金はかかりますか？
**A: Cloud Runの無料枠内で動作します。**
- 月間200万リクエストまで無料
- 月間360,000 GB秒のメモリまで無料

### Q: 実際のGCPプロジェクトを監査できますか？
**A: 将来的には可能です。** 現在はデモ用ですが、以下を追加予定：
1. OAuth2でGCP接続
2. サービスアカウントサポート
3. マルチテナント対応

### Q: オンプレミスで動かせますか？
**A: はい！** Dockerコンテナなので、以下で動作：
- Kubernetes
- Docker Compose
- 任意のコンテナランタイム

## サポート

- 📧 Email: oyster880@gmail.com
- 🐛 Issues: https://github.com/susumutomita/Paddi/issues
- 📖 Docs: https://github.com/susumutomita/Paddi/wiki