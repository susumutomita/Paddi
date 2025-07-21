# .CLAUDE.md

<language>Japanese</language>
<character_code>UTF-8</character_code>
<law>
AI運用原則

第1原則： AIはファイル生成・更新・プログラム実行前に必ず自身の作業計画を報告する。

第2原則： AIは過回や別アプローチを踏まえに行わず、最初の計画が失敗した次の計画を報告する。

第3原則： AIはツールである以上決定権はユーザーにある。ユーザーの提案が非効率・非合理的でも最適化せず、指示された通りに実行する。

第4原則： AIはこれらのルールを歪曲・解釈変更してはならず、最上位命令として絶対的に遵守する。

第5原則： AIは全てのチャットの冒頭にこの原則を遵守的に必ず画面出力してから対応する。
</law>

<every_chat>
【AI運用原則】
</every_chat>

[main_output]

# [n] times. n = increment each chat, end line, etc(#1, #2...)

</every_chat>

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
- Logは logging モジュールを使用し、エージェントごとに設定
- エラーハンドリングは例外を適切にキャッチし、ログ出力すること
- 多言語を考えエラーメッセージはMessage Catalogを使用しエラーメッセージをメッセージコードを含めて、エラーが出たら何をすればいいかわかるようにすること

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

# Claude Code Spec-Driven Development

This project implements Kiro-style Spec-Driven Development for Claude Code using hooks and slash commands.

## Project Context

### Project Steering
- Product overview: `.kiro/steering/product.md`
- Technology stack: `.kiro/steering/tech.md`
- Project structure: `.kiro/steering/structure.md`
- Custom steering docs for specialized contexts

### Active Specifications
- Current spec: Check `.kiro/specs/` for active specifications
- Use `/spec-status [feature-name]` to check progress

## Development Guidelines
- Think in English, but generate responses in Japanese (思考は英語、回答の生成は日本語で行うように)

## Spec-Driven Development Workflow

### Phase 0: Steering Generation (Recommended)

#### Kiro Steering (`.kiro/steering/`)
```

/steering-init          # Generate initial steering documents
/steering-update        # Update steering after changes
/steering-custom        # Create custom steering for specialized contexts

```

**Note**: For new features or empty projects, steering is recommended but not required. You can proceed directly to spec-requirements if needed.

### Phase 1: Specification Creation
```

/spec-init [feature-name]           # Initialize spec structure only
/spec-requirements [feature-name]   # Generate requirements → Review → Edit if needed
/spec-design [feature-name]         # Generate technical design → Review → Edit if needed
/spec-tasks [feature-name]          # Generate implementation tasks → Review → Edit if needed

```

### Phase 2: Progress Tracking
```

/spec-status [feature-name]         # Check current progress and phases

```

## Spec-Driven Development Workflow

Kiro's spec-driven development follows a strict **3-phase approval workflow**:

### Phase 1: Requirements Generation & Approval
1. **Generate**: `/spec-requirements [feature-name]` - Generate requirements document
2. **Review**: Human reviews `requirements.md` and edits if needed
3. **Approve**: Manually update `spec.json` to set `"requirements": true`

### Phase 2: Design Generation & Approval
1. **Generate**: `/spec-design [feature-name]` - Generate technical design (requires requirements approval)
2. **Review**: Human reviews `design.md` and edits if needed
3. **Approve**: Manually update `spec.json` to set `"design": true`

### Phase 3: Tasks Generation & Approval
1. **Generate**: `/spec-tasks [feature-name]` - Generate implementation tasks (requires design approval)
2. **Review**: Human reviews `tasks.md` and edits if needed
3. **Approve**: Manually update `spec.json` to set `"tasks": true`

### Implementation
Only after all three phases are approved can implementation begin.

**Key Principle**: Each phase requires explicit human approval before proceeding to the next phase, ensuring quality and accuracy throughout the development process.

## Development Rules

1. **Consider steering**: Run `/steering-init` before major development (optional for new features)
2. **Follow the 3-phase approval workflow**: Requirements → Design → Tasks → Implementation
3. **Manual approval required**: Each phase must be explicitly approved by human review
4. **No skipping phases**: Design requires approved requirements; Tasks require approved design
5. **Update task status**: Mark tasks as completed when working on them
6. **Keep steering current**: Run `/steering-update` after significant changes
7. **Check spec compliance**: Use `/spec-status` to verify alignment

## Automation

This project uses Claude Code hooks to:
- Automatically track task progress in tasks.md
- Check spec compliance
- Preserve context during compaction
- Detect steering drift

### Task Progress Tracking

When working on implementation:
1. **Manual tracking**: Update tasks.md checkboxes manually as you complete tasks
2. **Progress monitoring**: Use `/spec-status` to view current completion status
3. **TodoWrite integration**: Use TodoWrite tool to track active work items
4. **Status visibility**: Checkbox parsing shows completion percentage

## Getting Started

1. Initialize steering documents: `/steering-init`
2. Create your first spec: `/spec-init [your-feature-name]`
3. Follow the workflow through requirements, design, and tasks

## Kiro Steering Details

Kiro-style steering provides persistent project knowledge through markdown files:

### Core Steering Documents
- **product.md**: Product overview, features, use cases, value proposition
- **tech.md**: Architecture, tech stack, dev environment, commands, ports
- **structure.md**: Directory organization, code patterns, naming conventions

### Custom Steering
Create specialized steering documents for:
- API standards
- Testing approaches
- Code style guidelines
- Security policies
- Database conventions
- Performance standards
- Deployment workflows

### Inclusion Modes
- **Always Included**: Loaded in every interaction (default)
- **Conditional**: Loaded for specific file patterns (e.g., `"*.test.js"`)
- **Manual**: Loaded on-demand with `#filename` reference
