# 実データ収集のセットアップガイド

このガイドでは、Paddiで実際のGCPおよびGitHubデータを収集するための設定方法を説明します。

## 1. GCP (Google Cloud Platform) のセットアップ

### 前提条件
- Google Cloud プロジェクトへのアクセス権限
- 以下のGCPロールが必要です：
  - **Security Reviewer** (`roles/iam.securityReviewer`)
  - **Security Center Findings Viewer** (`roles/securitycenter.findingsViewer`)
  - **Logs Viewer** (`roles/logging.viewer`)

### 認証方法

#### 方法1: ローカル開発用（推奨）
```bash
# Google Cloud CLIでログイン
gcloud auth application-default login

# プロジェクトIDを設定
export GCP_PROJECT_ID="your-project-id"
```

#### 方法2: サービスアカウントを使用
```bash
# サービスアカウントキーのパスを設定
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
export GCP_PROJECT_ID="your-project-id"
```

### Security Command Centerの有効化
Security Command Centerは組織レベルの設定が必要です：
1. [GCPコンソール](https://console.cloud.google.com/security/command-center)でSCCを有効化
2. 組織レベルでSCCのAPIを有効化
3. 適切な権限を持つサービスアカウントまたはユーザーアカウントでアクセス

## 2. GitHub のセットアップ

### 前提条件
- GitHubリポジトリへのアクセス権限
- Personal Access Token (PAT) または GitHub App トークン

### Personal Access Tokenの作成
1. GitHubの[Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)にアクセス
2. "Generate new token (classic)" をクリック
3. 以下のスコープを選択：
   - `repo` (フルアクセス)
   - `read:org` (組織情報の読み取り)
   - `read:user` (ユーザー情報の読み取り)
4. トークンを生成し、安全に保管

### 環境変数の設定
```bash
export GITHUB_ACCESS_TOKEN="your-github-token"
export GITHUB_OWNER="your-org-or-username"
export GITHUB_REPO="your-repo-name"
```

## 3. Paddiでの実データ収集の実行

### 必要なライブラリのインストール
```bash
pip install -r requirements.txt
```

### GCPのみの監査実行
```bash
# 実データを使用してGCP監査を実行
python main.py audit --provider gcp --project-id $GCP_PROJECT_ID

# または環境変数を使用
python main.py audit --provider gcp
```

### GitHubのみの監査実行
```bash
# 実データを使用してGitHub監査を実行
python main.py audit --provider github \
  --github-token $GITHUB_ACCESS_TOKEN \
  --github-owner $GITHUB_OWNER \
  --github-repo $GITHUB_REPO
```

### 複数プロバイダーの監査実行
```bash
# GCPとGitHubの両方を監査
python main.py audit --provider gcp,github \
  --project-id $GCP_PROJECT_ID \
  --github-token $GITHUB_ACCESS_TOKEN \
  --github-owner $GITHUB_OWNER \
  --github-repo $GITHUB_REPO
```

## 4. トラブルシューティング

### 認証エラーが発生する場合
1. 認証情報が正しく設定されているか確認：
   ```bash
   gcloud auth application-default print-access-token  # GCP
   echo $GITHUB_ACCESS_TOKEN  # GitHub
   ```

2. 必要な権限があるか確認：
   - GCP: IAM設定で必要なロールが付与されているか
   - GitHub: トークンに必要なスコープがあるか

### APIエラーが発生する場合
1. APIが有効化されているか確認（GCP）：
   ```bash
   gcloud services list --enabled
   ```

2. レート制限に達していないか確認（GitHub）

### モックデータへのフォールバック
認証エラーやAPIエラーが発生した場合、自動的にモックデータにフォールバックします。
強制的にモックデータを使用する場合：
```bash
python main.py audit --use-mock
```

## 5. セキュリティのベストプラクティス

1. **認証情報の管理**
   - トークンやキーを直接コードに記述しない
   - 環境変数または安全な認証情報管理システムを使用
   - `.env`ファイルを使用する場合は`.gitignore`に追加

2. **最小権限の原則**
   - 必要最小限の権限のみを付与
   - 監査専用のサービスアカウントを作成

3. **監査ログ**
   - 実データアクセス時のログを確認
   - 異常なアクセスパターンを監視

## 6. 高度な設定

### カスタムフィルターの適用
```python
# 特定のリソースタイプのみを監査
python main.py audit --resource-filter "compute.instances"

# 特定の重要度以上の問題のみを報告
python main.py audit --severity-threshold HIGH
```

### 出力形式のカスタマイズ
```bash
# JSON形式で出力
python main.py audit --output-format json

# HTMLレポートのみ生成
python main.py audit --output-format html
```