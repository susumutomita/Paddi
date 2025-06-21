---
marp: true
theme: gaia
paginate: true
backgroundColor: #fff
backgroundImage: url('https://marp.app/assets/hero-background.svg')
---

<!-- _class: lead -->

# 🩹 **Paddi**

## AI駆動型マルチエージェントクラウド監査システム

**第2回 AI Agent Hackathon with Google Cloud**

冨田 晋
2025-06-21

---

# 📋 **アジェンダ**

1. **問題提起** - クラウドセキュリティの課題
2. **ソリューション概要** - Paddiの提案
3. **アーキテクチャ** - マルチエージェントシステム
4. **デモ** - 実際の動作
5. **技術詳細** - 実装の詳細
6. **将来ビジョン** - 今後の展望

---

<!-- _class: lead -->

# 🔥 **問題提起**

---

# **クラウドセキュリティ監査の現状**

## 😫 **手動プロセスの課題**

- **時間がかかる**: 数百のIAMポリシーを手動でレビュー
- **エラーが発生しやすい**: 人的ミスによる見落とし
- **専門知識が必要**: セキュリティベストプラクティスの深い理解
- **スケールしない**: マルチクラウド環境での複雑性

## 💰 **ビジネスインパクト**

- セキュリティインシデントのリスク増大
- コンプライアンス違反による罰金
- 監査にかかる人件費の増加

---

<!-- _class: lead -->

# 💡 **ソリューション: Paddi**

---

# **Paddiとは？**

## 🤖 **AIエージェントによる自動化**

**3つの専門エージェントが協調して動作：**

1. **Collector Agent** 📊
   - GCP設定を自動収集

2. **Explainer Agent** 🧠
   - Gemini AIでリスクを分析

3. **Reporter Agent** 📝
   - 人間が読みやすいレポートを生成

---

# **なぜマルチエージェント？**

## 🎯 **単一責任の原則**

各エージェントが**専門的なタスク**に集中

## 🔄 **モジュール性とスケーラビリティ**

- エージェントの**独立した開発・テスト**が可能
- 新しいクラウドプロバイダーの**追加が容易**

## 🚀 **パフォーマンス**

- **並列処理**による高速化
- エージェント間の**効率的なデータパイプライン**

---

<!-- _class: lead -->

# 🏗️ **アーキテクチャ**

---

# **システムアーキテクチャ**

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Agent A:      │     │   Agent B:      │     │   Agent C:      │
│   Collector     │────▶│   Explainer     │────▶│   Reporter      │
│                 │     │                 │     │                 │
│ ・GCP IAM       │     │ ・Gemini Pro    │     │ ・Markdown      │
│ ・Security      │     │ ・リスク分析    │     │ ・HTML          │
│   Command Center│     │ ・ベスト        │     │ ・可視化        │
│                 │     │   プラクティス  │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
    JSON/YAML              分析結果              監査レポート
```

---

# **技術スタック**

## 🐍 **Pythonエージェント**
- `google-cloud-iam`
- `google-cloud-securitycenter`
- `google-cloud-aiplatform` (Vertex AI)

## 🦀 **Rust CLI**
- 高速な実行
- クロスプラットフォーム対応

## 📊 **出力形式**
- Markdown (Obsidian対応)
- CSS付きHTML
- HonKitサイト

---

# **Google Cloud サービスの活用**

## 🖥️ **コンピューティングサービス**
- **Cloud Run**: エージェントのデプロイとスケーリング（予定）
- **Cloud Build**: CI/CDパイプライン

## 🤖 **AIサービス**
- **Vertex AI (Gemini Pro)**: セキュリティリスクの分析
- **IAM API**: ポリシー情報の収集
- **Security Command Center API**: セキュリティfindingsの取得

---

<!-- _class: lead -->

# 🎬 **デモ**

---

# **デモシナリオ**

## 1️⃣ **設定の収集**
```bash
$ paddi collect --project my-gcp-project
✓ IAMポリシーを収集: 47件
✓ SCC findingsを取得: 12件
```

## 2️⃣ **AI分析**
```bash
$ paddi analyze
✓ Gemini Proで分析中...
✓ リスクスコア計算: 7.3/10
```

## 3️⃣ **レポート生成**
```bash
$ paddi report --format html
✓ レポート生成完了: audit-2025-06-21.html
```

---

# **生成されるレポート例**

## 📊 **エグゼクティブサマリー**
- 総合リスクスコア: **7.3/10**
- 重大な発見事項: **3件**
- 推奨事項: **15件**

## 🔍 **主な発見事項**
1. **過剰な権限**: 5つのサービスアカウントにOwner権限
2. **未使用のIAMメンバー**: 90日以上アクセスなし
3. **暗号化の欠如**: 3つのストレージバケット

---

<!-- _class: lead -->

# 🔧 **技術詳細**

---

# **Geminiプロンプトエンジニアリング**

## 📝 **構造化プロンプト**

```python
prompt = f"""
クラウドセキュリティ専門家として、以下の
GCP IAM設定を分析してください：

{iam_config}

以下を特定してください：
1. セキュリティリスクと重要度
2. ベストプラクティス違反
3. 具体的な修正手順

形式: リスクスコア、発見事項、推奨事項を含むJSON
"""
```

---

# **エージェント間通信**

## 📨 **データフロー**

```yaml
# Agent A 出力
collector_output:
  timestamp: "2025-06-21T10:00:00Z"
  project_id: "my-project"
  iam_policies:
    - member: "user:admin@example.com"
      role: "roles/owner"
  scc_findings:
    - severity: "HIGH"
      category: "PUBLIC_BUCKET"
```

---

<!-- _class: lead -->

# 🚀 **将来ビジョン**

---

# **ロードマップ**

## 🌐 **マルチクラウド対応**
- AWS (IAM, Security Hub)
- Azure (AD, Security Center)
- クロスクラウド比較レポート

## 🤖 **高度なAI機能**
- 予測的リスク分析
- 自動修復提案
- カスタムポリシー学習

## 🔌 **統合**
- Slack/Teams通知
- SIEM連携
- CI/CDパイプライン統合

---

# **ビジネスインパクト**

## 💰 **コスト削減**
- 監査時間を**80%削減**
- 手動エラーを**ゼロに**

## 🛡️ **セキュリティ向上**
- **24/7継続的監査**
- **プロアクティブなリスク検出**

## 📈 **スケーラビリティ**
- **無制限のプロジェクト**に対応
- **マルチクラウド**環境をサポート

---

<!-- _class: lead -->

# 🙏 **ありがとうございました！**

## **ご質問はありますか？**

### 🔗 リンク
- GitHub: [github.com/susumutomita/Paddi](https://github.com/susumutomita/Paddi)
- Website: [susumutomita.netlify.app](https://susumutomita.netlify.app/)

### 📧 連絡先
- Email: (メールアドレス)

---

# **付録: 実装の詳細**

## 🔐 **セキュリティ考慮事項**

- Application Default Credentialsの使用
- 最小権限の原則
- 監査ログの暗号化

## 🧪 **テスト戦略**

- 単体テスト: 各エージェント
- 統合テスト: エンドツーエンド
- モックGCP環境での検証

## 📚 **使用したリソース**

- Google Cloud Documentation
- Vertex AI Gemini API
- Python asyncio for concurrency