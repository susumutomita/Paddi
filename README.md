# 🩹 Paddi - マルチクラウドセキュリティ監査自動化ツール

[![CI](https://github.com/susumutomita/Paddi/actions/workflows/ci.yml/badge.svg)](https://github.com/susumutomita/Paddi/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/susumutomita/Paddi/branch/main/graph/badge.svg)](https://codecov.io/gh/susumutomita/Paddi)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

クラウド環境（GCP、AWS、Azure）のセキュリティ設定をAIで自動監査し、わかりやすいレポートを生成します。Vertex AI（Gemini）とOllamaによる高度なセキュリティ分析を提供します。

## 🚀 クイックスタート（1分）

```bash
git clone https://github.com/susumutomita/Paddi.git
cd Paddi

# Python環境のセットアップ
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# サンプルデータで試す
python main.py init
```

これで `output/audit.html` にレポートが生成されます。ブラウザで開いてご確認ください。

## 📋 基本的な使い方

### 1. サンプルデータで動作確認

```bash
# サンプルデータで全機能を試す
python main.py init
```

### 2. 実際のクラウドプロジェクトを監査

#### GCP監査

```bash
# GCP認証を設定
gcloud auth application-default login

# 監査を実行（Vertex AI使用）
python main.py audit --project-id=あなたのプロジェクトID --use-mock=false

# Ollamaを使う場合（ローカルLLM）
export AI_PROVIDER=ollama
export OLLAMA_MODEL=llama3
python main.py audit --project-id=あなたのプロジェクトID --use-mock=false
```

#### マルチクラウド監査

```bash
# 全クラウド環境を監査
python main.py collect --collect-all \
  --project-id=gcp-project-id \
  --aws-account-id=123456789012 \
  --azure-subscription-id=sub-id
```

### 3. 個別のステップを実行

```bash
# データ収集のみ
python main.py collect --project-id=あなたのプロジェクトID

# AI分析のみ
python main.py analyze

# レポート生成のみ
python main.py report
```

## 🔧 設定

### LLMプロバイダーの選択

#### Vertex AI（Gemini）- デフォルト

```bash
export AI_PROVIDER=vertexai
export PROJECT_ID=あなたのGCPプロジェクトID
export VERTEX_AI_LOCATION=asia-northeast1
```

#### Ollama（ローカルLLM）

```bash
# Ollamaを起動しておく
ollama serve

# 環境変数を設定
export AI_PROVIDER=ollama
export OLLAMA_MODEL=llama3
export OLLAMA_ENDPOINT=http://localhost:11434
export PROJECT_ID=監査対象のGCPプロジェクトID
```

### マルチクラウド設定

```bash
# AWS
export AWS_ACCOUNT_ID=your-aws-account-id
export AWS_REGION=us-east-1

# Azure
export AZURE_SUBSCRIPTION_ID=your-subscription-id
export AZURE_TENANT_ID=your-tenant-id

# GitHub
export GITHUB_OWNER=your-github-org
export GITHUB_REPO=your-repo-name
```

## 📊 出力形式

- **HTML**: `output/audit.html` - ブラウザで見やすいレポート
- **Markdown**: `output/audit.md` - ドキュメントツール用
- **JSON**: `data/explained.json` - プログラムで処理可能な生データ

## 🛡️ セキュリティ機能

AIが提案する修正の安全性を確保する機能を搭載しています。

```bash
# 危険なコマンドを検証
python main.py validate-command "rm -rf /"

# ドライランで確認
python main.py execute-remediation "gcloud iam policy update" --dry-run
```

### 🤖 AIエージェント機能

自然言語でセキュリティ監査できます。

```bash
# 🚀 再帰的自律型AI監査（推奨 - 外部API不要）
python main.py recursive-audit --project-id=your-project-id

# LangChainベースの完全自律型AI監査（要Google Search API）
python main.py langchain-audit --project-id=your-project-id

# AI自律監査 - 実際のGCPデータを使用した自動監査
python main.py ai-audit --project-id=your-project-id

# 自動修正も含めた完全自律監査
python main.py ai-audit --project-id=your-project-id --auto-fix

# 対話型AIアシスタントを起動
python main.py chat

# Web UIでの対話型アシスタント
python main.py chat --web

# ワンショットでAIエージェントに指示
python main.py ai-agent "GCPプロジェクトのセキュリティ監査を実行してください" --project-id=your-project-id
```

#### 再帰的AI監査の特徴（推奨）

`recursive-audit`コマンドは外部APIキーなしで完全自律監査を実行します。

1. **自律的探索**: AIが発見した問題から次の調査対象を自動決定
2. **深層調査**: 公開バケット発見→中身を調査→機密ファイル検出
3. **CIS準拠チェック**: CIS GCP Benchmarkに基づく自動チェック
4. **リアルタイム進捗**: 調査の進行状況をリアルタイムで表示
5. **AI意思決定ログ**: なぜその調査をしたかの理由も記録

#### LangChain AI監査の特徴

`langchain-audit`コマンドはLangChainフレームワークを使用。

1. **エージェント型**: LangChainのReActエージェントが自律的に行動
2. **外部リサーチ**: Web検索でセキュリティ基準を調査（要API key）
3. **ツール連携**: 複数のツールを組み合わせて調査

#### 通常のAI監査

`ai-audit`コマンドは以下を自動実行します。

1. **データ収集**: 実際のGCPプロジェクトからIAMポリシーやSCC findingsを収集
2. **AI分析**: Vertex AI (Gemini)を使用してセキュリティリスクを分析
3. **レポート生成**: HTML/Markdownで詳細なセキュリティレポートを作成
4. **自動修正**: `--auto-fix`オプションで修正PRも自動作成

## 🌟 主な機能

- **マルチクラウド対応**: GCP、AWS、Azure、GitHubのセキュリティ監査
- **AI駆動分析**: Vertex AI（Gemini）による高度なセキュリティ分析
- **自律型監査**: 再帰的な調査と意思決定を行うAIエージェント
- **安全な修正**: 危険なコマンドの検証と承認ワークフロー
- **包括的レポート**: HTML、Markdown、JSONでの詳細レポート
- **Web UI**: ブラウザベースのダッシュボードとAPI

## 🏗️ アーキテクチャ

- **コレクターエージェント**: クラウドリソースの構成情報を収集
- **エクスプレイナーエージェント**: AIによるセキュリティリスク分析
- **レポーターエージェント**: 分析結果をレポートに変換
- **オーケストレーター**: 複数エージェントの調整
- **セーフティシステム**: 修正コマンドの安全性確保

## 🤝 貢献・開発

開発に参加したい方は [DEVELOPMENT.md](DEVELOPMENT.md) をご覧ください。

## 📄 ライセンス

[MIT License](LICENSE)
