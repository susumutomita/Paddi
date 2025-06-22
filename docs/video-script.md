# Paddi Demo Video Script (3 Minutes)

## 🎬 Video Overview
**Title:** Paddi - AI-Driven Multi-Cloud Security Automation
**Duration:** 3:00
**Language:** Japanese narration
**Target:** AI Agent Hackathon with Google Cloud judges

---

## 📝 Scene-by-Scene Script

### Scene 1: Problem Introduction (0:00-0:30)
**Visual:** Show manual security audit documents, spreadsheets with security findings
**Narration (Japanese):**
```
クラウドセキュリティ監査は、手作業で行うと時間がかかり、
人的ミスも発生しやすい課題があります。
セキュリティエンジニアは、膨大な設定を一つ一つ確認し、
リスクを評価する必要があります。
この作業は、マルチクラウド環境では更に複雑になります。
```

**Caption:** 
- 手動監査の課題
- 時間とコストの問題
- 人的ミスのリスク

### Scene 2: Solution Overview (0:30-1:00)
**Visual:** Paddi architecture diagram showing multi-agent system
**Narration:**
```
Paddiは、Google CloudのGemini AIを活用した
マルチエージェント型の自動監査ツールです。
3つのAIエージェントが協調して、
クラウド環境の設定を収集、分析、レポート化します。
Rustで実装された高速なCLIで、
開発者にとって使いやすいインターフェースを提供します。
```

**Animation:** Show flow: Collector → Explainer → Reporter

### Scene 3: Live Demo Setup (1:00-1:15)
**Visual:** Terminal window, project directory
**Commands:**
```bash
# Paddiのセットアップ
cd ~/projects/paddi-demo
ls -la

# 設定ファイルの確認
cat paddi.toml
```

**Narration:**
```
実際にPaddiを使ってみましょう。
まず、paddi initコマンドで初期設定を行います。
```

### Scene 4: Initialize and Configure (1:15-1:30)
**Visual:** Terminal showing paddi init
**Commands:**
```bash
# Paddiの初期化
paddi init

# プロバイダーとしてGCPを選択
# プロジェクトIDを入力
# Vertex AI設定を確認
```

**Narration:**
```
対話的なセットアップで、
Google Cloudの認証情報とVertex AIの設定を行います。
```

### Scene 5: Run Security Audit (1:30-2:00)
**Visual:** Terminal showing real-time analysis
**Commands:**
```bash
# セキュリティ監査の実行
paddi audit --provider gcp --format all

# リアルタイムでAIが分析中...
# ✓ IAMポリシーを収集中...
# ✓ Security Command Centerからデータ取得中...
# ✓ Geminiで脅威を分析中...
# ✓ レポートを生成中...
```

**Narration:**
```
3つのエージェントが順番に動作します。
CollectorがGCPの設定を収集し、
ExplainerがGemini AIで脅威を分析、
最後にReporterが分かりやすいレポートを生成します。
```

### Scene 6: Show Generated Reports (2:00-2:20)
**Visual:** Split screen - HTML report in browser, Markdown in VS Code
**Actions:**
- Open `output/audit.html` in browser
- Show risk severity levels (HIGH, MEDIUM, LOW)
- Show AI-generated explanations in Japanese
- Open `output/audit.md` in VS Code

**Narration:**
```
生成されたレポートには、
AIが発見したセキュリティリスクが
重要度別に整理されています。
各リスクには、具体的な改善提案も含まれています。
```

### Scene 7: Extensibility & CI/CD (2:20-2:30)
**Visual:** GitHub Actions workflow, multi-cloud logos
**Narration:**
```
PaddiはCI/CDパイプラインに統合可能で、
AWS、Azure、GCPのマルチクラウドに対応予定です。
```

### Scene 8: Impact & Vision (2:30-3:00)
**Visual:** Before/After comparison, time savings visualization
**Narration:**
```
Paddiは、数日かかっていた監査作業を
数分で完了させることができます。
AIの力で、より安全なクラウド環境の実現を支援します。
第2回 AI Agent Hackathonに向けて開発された
Paddiの可能性にご期待ください。
```

**End Card:**
- GitHub: github.com/susumutomita/Paddi
- Built for: 第2回 AI Agent Hackathon with Google Cloud
- Powered by: Gemini AI (Vertex AI)

---

## 🎥 Recording Tips

1. **Terminal Settings:**
   - Font size: 16-18pt
   - Theme: Dark background with high contrast
   - Clear command prompt

2. **Screen Recording:**
   - Resolution: 1920x1080 (Full HD)
   - Frame rate: 30fps minimum
   - Use OBS Studio with scene transitions

3. **Audio:**
   - Clear narration without background noise
   - Background music: Soft, professional (fade during narration)
   - Export with normalized audio levels

4. **Post-Production:**
   - Add captions for key points
   - Highlight important commands
   - Use smooth transitions between scenes
   - Add Paddi logo watermark

5. **File Export:**
   - Format: MP4 (H.264)
   - Bitrate: 5-10 Mbps
   - Exactly 3:00 duration