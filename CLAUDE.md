# .CLAUDE.md

## 🧠 プロジェクト概要

本プロジェクト「Paddi（パディ）」は、[第2回 AI Agent Hackathon with Google Cloud](https://zenn.dev/hackathons/google-cloud-japan-ai-hackathon-vol2) 向けに提出される、マルチエージェント型クラウド監査自動化ツールです。
従来の手作業による監査業務を、Google Cloud の設定データと Gemini（Vertex AI）を活用してコードベースで再現・自動化します。

このフォルダ以下の Python 実装は Claude Code が担当してください。全体のアーキテクチャと実装はPythonで統一されます。

---

## 📐 エージェント構成と責務

### 🔹 Agent A: `collector/agent_collector.py`

- 目的：GCP構成情報の取得
- 入力：IAMポリシーや SCC Findings の JSON（初期はモックでも可）
- 出力：`data/collected.json`
- 備考：初期実装では固定サンプルで問題なし

---

### 🔹 Agent B: `explainer/agent_explainer.py`

- 目的：Vertex AI (Gemini) を用いてセキュリティリスクを自然言語で説明
- 入力：`data/collected.json`
- 出力：`data/explained.json`（構造は以下）

```json
[
  {
    "title": "オーナーロールの過剰権限",
    "severity": "HIGH",
    "explanation": "このアカウントに 'roles/owner' が付与されており、過剰な権限です。",
    "recommendation": "最小権限の原則に従い、オーナーロールを外してください。"
  }
]

- 使用SDK：google-cloud-aiplatform

⸻

🔹 Agent C: reporter/agent_reporter.py
- 目的：explained.json を Markdown と HTML に変換
- 出力：
- output/audit.md（Obsidian など対応）
- output/audit.html（シンプルな静的ページ）
- テンプレート：templates/report.md.j2（Jinja2）

⸻

🧪 品質基準・開発ルール

以下は必須です：

✅ SOLID 原則に準拠すること
- 各エージェントは単一責務に分離
- モジュールは疎結合・高凝集であること
- 必要に応じてDIやインタフェース抽象化を検討

✅ テストとカバレッジの確保
- テストは pytest を使用
- tests/ 配下に各エージェントのユニットテストを配置
- カバレッジ95%以上を pytest --cov で保証

✅ make before-commit を必ず通すこと

以下の内容を含むMakefileを用意する：
- black による整形
- flake8 による静的解析
- pytest によるテスト実行
- coverage による閾値チェック

⸻

📁 ディレクトリ構成（簡易）

app/
├── collector/
│   └── agent_collector.py
├── explainer/
│   └── agent_explainer.py
├── reporter/
│   └── agent_reporter.py
├── requirements.txt
└── tests/
    ├── test_collector.py
    ├── test_explainer.py
    └── test_reporter.py

- 中間ファイル：data/
- 出力ファイル：output/

⸻

📦 必要ライブラリ（requirements.txt）

google-cloud-aiplatform
jinja2
fire
pytest
pytest-cov
flake8
black


⸻

✅ 完了目標

以下の手順で一連の処理が完結すること：

# メインCLIで全エージェントを統合実行
python main.py audit

# または個別実行も可能
python main.py collect
python main.py analyze
python main.py report

これにより、GCP構成 → Geminiによる説明 → Markdown/HTMLレポートの自動生成が可能となる。

⸻

💬 補足事項
- フロントエンドは不要。CLIベースで構築すること。
- Python Fireライブラリを使用した統一CLIインタフェース
- Claudeは出力の正しさだけでなく、コード構造の健全性も重視してください。
