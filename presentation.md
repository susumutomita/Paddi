---
marp: true
theme: gaia
paginate: true
backgroundColor: #fff
backgroundImage: url('https://marp.app/assets/hero-background.svg')
---

<!-- _class: lead -->

# 🩹 **Paddi**

## AI-Powered Multi-Agent Cloud Audit System

**Google Cloud AI Hackathon: Multi-Agent Edition**

Susumu Tomita
2025-06-21

---

# 📋 **Agenda**

1. **Problem Statement** - クラウドセキュリティの課題
2. **Solution Overview** - Paddiの提案
3. **Architecture** - マルチエージェントシステム
4. **Demo** - 実際の動作
5. **Technical Details** - 実装の詳細
6. **Future Vision** - 今後の展望

---

<!-- _class: lead -->

# 🔥 **Problem Statement**

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

# 💡 **Solution: Paddi**

---

# **Paddiとは？**

## 🤖 **AIエージェントによる自動化**

**3つの専門エージェントが協調して動作：**

1. **Collector Agent** 📊
   - GCP設定を自動収集

2. **Explainer Agent** 🧠
   - Gemini LLMでリスクを分析

3. **Reporter Agent** 📝
   - 人間が読みやすいレポートを生成

---

# **なぜマルチエージェント？**

## 🎯 **Single Responsibility Principle**

各エージェントが**専門的なタスク**に集中

## 🔄 **Modularity & Scalability**

- エージェントの**独立した開発・テスト**が可能
- 新しいクラウドプロバイダーの**追加が容易**

## 🚀 **Performance**

- **並列処理**による高速化
- エージェント間の**効率的なデータパイプライン**

---

<!-- _class: lead -->

# 🏗️ **Architecture**

---

# **システムアーキテクチャ**

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Agent A:      │     │   Agent B:      │     │   Agent C:      │
│   Collector     │────▶│   Explainer     │────▶│   Reporter      │
│                 │     │                 │     │                 │
│ ・GCP IAM       │     │ ・Gemini Pro    │     │ ・Markdown      │
│ ・Security      │     │ ・Risk Analysis │     │ ・HTML          │
│   Command Center│     │ ・Best Practice │     │ ・Visualizations│
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
    JSON/YAML             Analysis Results         Audit Reports
```

---

# **技術スタック**

## 🐍 **Python Agents**
- `google-cloud-iam`
- `google-cloud-securitycenter`
- `google-cloud-aiplatform` (Vertex AI)

## 🦀 **Rust CLI**
- 高速な実行
- クロスプラットフォーム対応

## 📊 **Output Formats**
- Markdown (Obsidian対応)
- HTML with CSS
- YAML frontmatter

---

<!-- _class: lead -->

# 🎬 **Demo**

---

# **デモシナリオ**

## 1️⃣ **Configuration Collection**
```bash
$ paddi collect --project my-gcp-project
✓ IAM policies collected: 47
✓ SCC findings retrieved: 12
```

## 2️⃣ **AI Analysis**
```bash
$ paddi analyze
✓ Analyzing with Gemini Pro...
✓ Risk score calculated: 7.3/10
```

## 3️⃣ **Report Generation**
```bash
$ paddi report --format html
✓ Report generated: audit-2025-06-21.html
```

---

# **生成されるレポート例**

## 📊 **Executive Summary**
- Overall Risk Score: **7.3/10**
- Critical Findings: **3**
- Recommendations: **15**

## 🔍 **Key Findings**
1. **過剰な権限**: 5つのサービスアカウントにOwner権限
2. **未使用のIAMメンバー**: 90日以上アクセスなし
3. **暗号化の欠如**: 3つのストレージバケット

---

<!-- _class: lead -->

# 🔧 **Technical Details**

---

# **Geminiプロンプトエンジニアリング**

## 📝 **構造化プロンプト**

```python
prompt = f"""
As a cloud security expert, analyze the following
GCP IAM configuration:

{iam_config}

Identify:
1. Security risks and severity
2. Best practice violations
3. Specific remediation steps

Format: JSON with risk_score, findings, recommendations
"""
```

---

# **エージェント間通信**

## 📨 **データフロー**

```yaml
# Agent A Output
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

# 🚀 **Future Vision**

---

# **ロードマップ**

## 🌐 **Multi-Cloud Support**
- AWS (IAM, Security Hub)
- Azure (AD, Security Center)
- クロスクラウド比較レポート

## 🤖 **Advanced AI Features**
- 予測的リスク分析
- 自動修復提案
- カスタムポリシー学習

## 🔌 **Integrations**
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

# 🙏 **Thank You!**

## **Questions?**

### 🔗 Links
- GitHub: [github.com/susumutomita/Paddi](https://github.com/susumutomita/Paddi)
- Website: [susumutomita.netlify.app](https://susumutomita.netlify.app/)

### 📧 Contact
- Email: (your-email@example.com)

---

# **Appendix: 実装の詳細**

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