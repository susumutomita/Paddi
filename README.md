# 🩹 Paddi: AI駆動型マルチエージェントクラウド監査システム

[![CI](https://github.com/susumutomita/Paddi/actions/workflows/ci.yml/badge.svg)](https://github.com/susumutomita/Paddi/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/susumutomita/Paddi/branch/main/graph/badge.svg)](https://codecov.io/gh/susumutomita/Paddi)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

![Last commit](https://img.shields.io/github/last-commit/susumutomita/Paddi)
![Top language](https://img.shields.io/github/languages/top/susumutomita/Paddi)
![Pull requests](https://img.shields.io/github/issues-pr/susumutomita/Paddi)
![Code size](https://img.shields.io/github/languages/code-size/susumutomita/Paddi)
![Repo size](https://img.shields.io/github/repo-size/susumutomita/Paddi)

**Paddi（パディ）** は、Google Cloud AIを使用して
クラウドセキュリティ監査を自動化するマルチエージェントシステムです。

[第2回 AI Agent Hackathon with Google Cloud](https://zenn.dev/hackathons/google-cloud-japan-ai-hackathon-vol2)
向けに開発しました。

---

## 🎯 対象ユーザーと解決する課題

### 解決する課題

プロダクトのリリース直前、開発チームのSlackには「監査対応お願いします」というメッセージが飛び交います。
セキュリティ監査担当者は、膨大なIAMポリシーや設定ファイルを一つひとつ目視で確認し、脆弱性のリストをExcelにまとめていきます。
「この権限は本当に必要なのか」「この設定はベストプラクティスに沿っているのか」開発者と監査人の間で質疑応答が繰り返され、修正の可否を判断し、再度チェック。
やっとの思いで監査レポートが完成した頃には、リリース予定日が目前に迫っている。

そんな経験はありませんか。この手作業中心の監査プロセスは、人的ミスや見落としのリスク専門知識が必要なため属人化しやすい頻繁なリリースサイクルに追いつけない
工数増大によるリリース遅延といった課題を生み出します。Paddiは、こうした現場でよくある課題を根本から変えます。
AIエージェントがクラウド設定を自動で収集・分析し、リスクを洗い出し、分かりやすい監査レポートを自動生成。
監査人はAIがまとめたレポートを確認し、必要な指摘や承認するだけ。開発チームは、監査対応のために手を止めることなく、より速く・安全にリリースを進められます。
「監査のためにリリースが遅れる」「セキュリティチェックが属人化して不安」そんな悩みを、Paddiが“当たり前に自動化”する時代へ。

### 対象ユーザー

- **クラウドセキュリティエンジニア**: 定期的なセキュリティ監査を実施する必要がある
- **DevOpsチーム**: CI/CDパイプラインにセキュリティチェックを統合したい
- **コンプライアンス担当者**: 監査レポートの作成と管理を効率化したい
- **中小企業のIT管理者**: 専門知識がなくてもセキュリティを確保したい

---

## 🏗️ システムアーキテクチャ

Paddiは**3つのエージェントによるパイプライン**アーキテクチャを実装し、各エージェントは単一の明確な責任を持ちます。

```mermaid
graph LR
    A[Collector Agent] -->|collected.json| B[Explainer Agent]
    B -->|explained.json| C[Reporter Agent]
    C --> D[監査レポート]

    style A fill:#4285f4,stroke:#1a73e8,stroke-width:2px,color:#fff
    style B fill:#ea4335,stroke:#d33b27,stroke-width:2px,color:#fff
    style C fill:#34a853,stroke:#1e8e3e,stroke-width:2px,color:#fff
    style D fill:#fbbc04,stroke:#f9ab00,stroke-width:2px,color:#000
```

### 使用している Google Cloud サービス

#### 🖥️ コンピューティングサービス

- **Cloud Run**: 各エージェントのデプロイとスケーリング（予定）
- **Cloud Build**: CI/CDパイプライン（GitHub Actions経由）

#### 🤖 AIサービス

- **Vertex AI (Gemini Pro)**: セキュリティリスクの自然言語分析
- **IAM API**: ポリシー情報の収集
- **Security Command Center API**: セキュリティfindingsの取得

---

## 🚀 クイックスタート

1分以内でPaddiを開始できます。

```bash
# リポジトリのクローン
git clone https://github.com/susumutomita/Paddi.git
cd Paddi

# Python環境のセットアップ
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# サンプルデータでPaddiを試す - 設定不要！
python main.py init

# 出力:
# ✅ Paddi init 完了:
#   • Markdown: output/audit.md
#   • HTML: output/audit.html（ブラウザで開けます）
#   • サイトプレビュー: npx honkit serve docs/
```

これだけですPaddiは自動的にサンプルGCPデータで完全な監査パイプラインを実行し、GCPクレデンシャルや設定なしでその機能を実証します。

---

## 🎬 デモビデオ

[3分間のデモビデオをYouTubeで見る](https://youtube.com/xxxxx) _(準備中)_。

デモの内容は以下のとおりです。

1. `python main.py init` でのクイックスタート
2. 実際のGCPプロジェクトでの監査実行
3. 生成されたレポートの確認
4. CI/CDパイプラインへの統合

---

## 📚 エージェントの詳細

### 1. **Collector Agent** (`app/collector/`)

- **目的**: GCP設定データの収集
- **入力**: GCPプロジェクトIDまたはモックデータフラグ
- **出力**: IAMポリシーとSecurity Command Center findingsを含む `data/collected.json`
- **主な機能**:
  - `google-cloud-iam` と `google-cloud-securitycenter` による実際のGCP API統合
  - テストとデモ用のモックデータサポート
  - 複数のクラウドプロバイダーに拡張可能

### 2. **Explainer Agent** (`app/explainer/`)

- **目的**: AIを使用したセキュリティリスクの分析
- **入力**: Collectorからの `data/collected.json`
- **出力**: AI生成のセキュリティインサイトを含む `data/explained.json`
- **主な機能**:
  - Google Gemini AI (Vertex AI経由) を搭載
  - 重要度別の分類（CRITICAL, HIGH, MEDIUM, LOW）
  - 自然言語での実用的な推奨事項
  - オフライン開発用のモックモード

### 3. **Reporter Agent** (`app/reporter/`)

- **目的**: 人間が読めるレポートの生成
- **入力**: Explainerからの `data/explained.json`
- **出力**: 複数のレポート形式:
  - `output/audit.md` - ドキュメントツール用のMarkdown
  - `output/audit.html` - インタラクティブHTMLレポート
  - `docs/` - Webホスティング用のHonKitサイト構造
- **主な機能**:
  - カスタマイズ可能なレポート用Jinja2テンプレート
  - 複数の出力形式
  - 重要度ベースの整理
  - 日本語と英語のサポート

### オーケストレーションレイヤー

**Python CLI** (`main.py`) はエージェントを調整する統一インタフェースを提供します。

```python
# 簡略化されたオーケストレーションフロー
orchestrator.run_collector()
orchestrator.run_explainer()
orchestrator.run_reporter(formats)
```

---

## 📚 CLI使用ガイド

### インストール

```bash
# リポジトリのクローン
git clone https://github.com/susumutomita/Paddi.git
cd Paddi

# Python環境のセットアップ
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### コアコマンド

#### `python main.py init` - ゼロセットアップ試用

```bash
# サンプルデータで完全な監査を実行
python main.py init

# 自動パイプライン実行をスキップ
python main.py init --skip-run

# 出力ディレクトリを指定
python main.py init --output custom-output/
```

#### `python main.py audit` - 完全なパイプライン

```bash
# 完全な監査パイプラインを実行
python main.py audit

# 実際のGCPの代わりにモックデータを使用
python main.py audit --use-mock

# GCPプロジェクトを指定
python main.py audit --project-id my-gcp-project

# 詳細出力
python main.py audit -v
```

#### `python main.py collect` - データ収集のみ

```bash
# 実際のGCPプロジェクトから収集
python main.py collect --project-id my-gcp-project

# テスト用のモックデータを収集
python main.py collect --use-mock
```

#### `python main.py analyze` - AI分析のみ

```bash
# 収集したデータをAIで分析
python main.py analyze

# モックAIレスポンスを使用
python main.py analyze --use-mock
```

#### `python main.py report` - レポート生成

```bash
# デフォルトレポート（Markdown + HTML）を生成
python main.py report

# 特定の形式を生成
python main.py report --format markdown,html,honkit

# カスタム入力/出力ディレクトリ
python main.py report --input-dir data/ --output-dir reports/
```

---

## 🎯 ユースケース

### 1. **開発とテスト**

```bash
# サンプルデータでクイックスタート
python main.py init

# 個々のエージェントをテスト
python main.py collect --use-mock
python main.py analyze --use-mock
python main.py report
```

### 2. **実際のGCP監査**

```bash
# GCPで認証
gcloud auth application-default login

# 完全な監査を実行
python main.py audit --project-id production-project
```

### 3. **CI/CD統合**

```yaml
# GitHub Actionsの例
- name: Python環境セットアップ
  uses: actions/setup-python@v4
  with:
    python-version: '3.10'

- name: 依存関係インストール
  run: |
    pip install -r requirements.txt

- name: セキュリティ監査を実行
  run: |
    python main.py audit --project-id ${{ secrets.GCP_PROJECT }}

- name: レポートをアップロード
  uses: actions/upload-artifact@v3
  with:
    name: audit-reports
    path: output/
```

### 4. **定期監査**

```bash
# 週次監査のcronジョブ
0 0 * * 0 cd /path/to/paddi && python main.py audit --project-id prod && \
  gsutil cp output/audit.html gs://audit-reports/$(date +%Y%m%d).html
```

---

## 📊 サンプル出力

### Markdownレポート (`output/audit.md`)

```markdown
# セキュリティ監査レポート - example-project-123

**監査日:** 2024-01-21
**総findings数:** 4

## エグゼクティブサマリー

このセキュリティ監査により、GCPインフラストラクチャ全体で4つのfindingsが特定されました。

### 重要度の内訳
- **CRITICAL**: 1 findings
- **HIGH**: 1 findings
- **MEDIUM**: 1 findings
- **LOW**: 1 findings

## 詳細なFindings

### 1. パブリックバケットアクセス
**重要度:** CRITICAL
**説明:** バケット'sensitive-data-bucket'でパブリックアクセスが有効になっています...
**推奨事項:** バケットIAMポリシーからallUsersとallAuthenticatedUsersを削除
```

### HonKitドキュメント (`docs/`)

- インタラクティブなWebドキュメント
- 重要度ベースのナビゲーション
- 日本語ローカライゼーション
- 検索可能なコンテンツ
- PDF出力機能

---

## 🛠️ 開発

### 前提条件

- Python 3.10+
- Google Cloud SDK（実際のGCP監査用）

### 開発環境のセットアップ

```bash
# Python環境のセットアップ
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 品質チェックを実行
make before-commit
```

### テスト

```bash
# Pythonテスト
make test

# 統合テスト
pytest tests/integration/
```

---

## 🌐 技術スタック

- **Python 3.10+**: エージェント実装とCLI
- **Google Vertex AI**: AI分析用Gemini Pro
- **Google Cloud APIs**: IAM、Security Command Center
- **Fire**: PythonコマンドラインインタフェースCLI
- **Jinja2**: レポートテンプレート
- **HonKit**: ドキュメント生成

---

## 🚀 ロードマップ

- [ ] PyPIパッケージとしての配布
- [ ] AWSとAzureのサポート
- [ ] カスタムルール定義
- [ ] Slack/Teams通知
- [ ] コンプライアンスフレームワーク（SOC2、ISO 27001）
- [ ] Web UIダッシュボード
- [ ] エージェントマーケットプレイス

---

## 👥 貢献者

- **戦略とアーキテクチャ**: [Susumu Tomita](https://susumutomita.netlify.app/) - フルスタック開発者
- **実装**: Claude Code + AIコラボレーション

## 🤝 貢献

詳細は[ガイド](docs/contributing/development.md)をご覧ください。

```bash
# フォークとクローン
git clone https://github.com/YOUR-USERNAME/Paddi.git

# フィーチャーブランチを作成
git checkout -b feature/amazing-feature

# 変更とテスト
make test

# PRを送信
git push origin feature/amazing-feature
```

---

## 📄 ライセンス

Paddiは[MITライセンス](LICENSE)の下でライセンスされています。
