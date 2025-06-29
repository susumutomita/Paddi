# 🩹 Paddi - クラウドセキュリティ監査自動化ツール

[![CI](https://github.com/susumutomita/Paddi/actions/workflows/ci.yml/badge.svg)](https://github.com/susumutomita/Paddi/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/susumutomita/Paddi/branch/main/graph/badge.svg)](https://codecov.io/gh/susumutomita/Paddi)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Google Cloudのセキュリティ設定をAIで自動監査し、わかりやすいレポートを生成します。

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

### 2. 実際のGCPプロジェクトを監査

```bash
# GCP認証を設定
gcloud auth application-default login

# 監査を実行（Gemini使用）
python main.py audit --project-id=あなたのプロジェクトID --use-mock=false

# Ollamaを使う場合（ローカルLLM）
export AI_PROVIDER=ollama
export OLLAMA_MODEL=llama3
python main.py audit --project-id=あなたのプロジェクトID --use-mock=false
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

#### Gemini（デフォルト）

```bash
export AI_PROVIDER=gemini
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

## 🤝 貢献・開発

開発に参加したい方は [DEVELOPMENT.md](DEVELOPMENT.md) をご覧ください。

## 📄 ライセンス

[MIT License](LICENSE)
