# データディレクトリ

このディレクトリには、エージェント間でやり取りされるデータが保存されます。

## ファイル構成

- `collected.json` - Agent A (Collector) が収集したGCP構成情報
- `explained.json` - Agent B (Explainer) が分析したセキュリティ所見
- `audit.md` - Agent C (Reporter) が生成したMarkdownレポート
- `audit.html` - Agent C (Reporter) が生成したHTMLレポート

## Vertex AI 設定

Agent B (Explainer) でVertex AI (Gemini) を使用する際の環境変数：

```bash
# 必須: Google CloudプロジェクトID
export GOOGLE_CLOUD_PROJECT="your-project-id"

# オプション: Vertex AIのロケーション（デフォルト: asia-northeast1）
export VERTEX_AI_LOCATION="asia-northeast1"

# 認証
gcloud auth application-default login
```

## 使用例

```bash
# モックモードで実行（API呼び出しなし）
python app/explainer/agent_explainer.py --use_mock

# 実際のVertex AI APIを使用
export GOOGLE_CLOUD_PROJECT="your-project-id"
python app/explainer/agent_explainer.py --use_mock=False
```