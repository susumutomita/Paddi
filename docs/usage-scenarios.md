# Paddi 使用シナリオ

## 🎯 想定される使用方法

### 1. ハッカソン審査員の使用方法

審査員は**実際のGCPアクセスは不要**です。Paddiはモックデータで完全に動作します。

```bash
# ブラウザでアクセス
https://paddi-xxxxx-an.a.run.app

# またはAPIで試す
curl -X POST https://paddi-xxxxx-an.a.run.app/api/audit \
  -H "Content-Type: application/json" \
  -d '{"provider": "gcp", "use_mock": true}'
```

### 2. 実際の企業での使用方法（将来）

#### A. SaaSとして提供する場合

```yaml
利用フロー:
1. ユーザーがPaddiにサインアップ
2. OAuth2でGCPプロジェクトへのアクセスを許可
3. Paddiが定期的に監査を実行
4. レポートをWebダッシュボードで確認
```

#### B. オンプレミス/プライベートCloud Runとして

```yaml
利用フロー:
1. 企業が自社のGCPプロジェクトにPaddiをデプロイ
2. サービスアカウントに必要な権限を付与
3. Cloud SchedulerやCI/CDから定期実行
4. 結果をSlackやメールに通知
```

## 🔐 セキュリティモデル

### 現在（ハッカソンデモ）
- **モックデータのみ使用**
- **認証情報不要**
- **誰でもアクセス可能**（`--allow-unauthenticated`）

### 本番環境での想定
```yaml
認証方法:
  - Option 1: OAuth2（ユーザーが自分のGCPを接続）
  - Option 2: サービスアカウント（事前設定）
  - Option 3: Workload Identity（GKE環境）

アクセス制御:
  - Cloud Run with IAM
  - Firebase Authentication
  - API Key管理
```

## 📊 デモシナリオ

### 1. Webダッシュボードデモ
1. トップページでセキュリティサマリーを表示
2. 「Start Audit」ボタンをクリック
3. リアルタイムで脆弱性を検出（モックデータ）
4. レポートをMarkdown/HTMLで出力

### 2. API統合デモ
```python
import requests

# Paddiで監査実行
response = requests.post(
    "https://paddi-xxxxx.a.run.app/api/audit",
    json={"provider": "gcp", "project_id": "demo-project"}
)

# 結果を取得
findings = response.json()["findings"]
for finding in findings:
    print(f"[{finding['severity']}] {finding['title']}")
```

### 3. CI/CD統合デモ
```yaml
# .github/workflows/security-audit.yml
name: Security Audit
on:
  schedule:
    - cron: '0 0 * * *'  # 毎日実行
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - name: Run Paddi Audit
        run: |
          curl -X POST ${{ secrets.PADDI_URL }}/api/audit \
            -H "Content-Type: application/json" \
            -d '{"provider": "gcp"}'
```

## 🚀 価値提案

1. **開発者向け**: CI/CDに組み込んで自動セキュリティチェック
2. **セキュリティチーム向け**: コード不要でGUI操作
3. **経営層向け**: コンプライアンスレポートを自動生成