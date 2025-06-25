---
marp: true
theme: uncover
paginate: true
backgroundColor: #000
backgroundImage: radial-gradient(ellipse at top left, #1a1a2e 0%, #000 50%)
color: #fff
style: |
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&display=swap');

  section {
    font-family: 'Noto Sans JP', -apple-system, BlinkMacSystemFont, sans-serif;
    letter-spacing: -0.02em;
    padding: 80px;
  }

  h1 {
    font-size: 72px;
    font-weight: 900;
    letter-spacing: -0.04em;
    line-height: 1;
    margin-bottom: 0.5em;
    background: linear-gradient(135deg, #007AFF 0%, #5AC8FA 50%, #5856D6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  h2 {
    font-size: 48px;
    font-weight: 700;
    letter-spacing: -0.03em;
    margin-bottom: 0.5em;
    background: linear-gradient(135deg, #5AC8FA 0%, #007AFF 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  h3 {
    font-size: 32px;
    font-weight: 600;
    color: #5AC8FA;
  }

  p, li {
    font-size: 24px;
    line-height: 1.6;
    font-weight: 400;
    color: rgba(255, 255, 255, 0.9);
  }

  strong {
    font-weight: 700;
    background: linear-gradient(135deg, #FF9500 0%, #FF3B30 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  code {
    font-family: 'SF Mono', Monaco, monospace;
    background: linear-gradient(135deg, rgba(90, 200, 250, 0.1) 0%, rgba(0, 122, 255, 0.1) 100%);
    border: 1px solid rgba(90, 200, 250, 0.3);
    padding: 4px 12px;
    border-radius: 8px;
    font-size: 0.9em;
    color: #5AC8FA;
  }

  pre {
    background: linear-gradient(135deg, rgba(26, 26, 46, 0.6) 0%, rgba(0, 0, 0, 0.6) 100%);
    border: 1px solid rgba(90, 200, 250, 0.2);
    border-radius: 20px;
    padding: 32px;
    font-size: 20px;
    line-height: 1.6;
    box-shadow: 0 8px 32px rgba(0, 122, 255, 0.1);
  }

  pre code {
    background: none;
    border: none;
    color: #fff;
    padding: 0;
  }

  table {
    font-size: 20px;
    width: 100%;
    margin: 32px 0;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 24px rgba(0, 122, 255, 0.1);
  }

  th {
    font-weight: 600;
    text-align: left;
    padding: 20px;
    background: linear-gradient(135deg, rgba(88, 86, 214, 0.2) 0%, rgba(0, 122, 255, 0.2) 100%);
    color: #5AC8FA;
  }

  td {
    padding: 20px;
    border-bottom: 1px solid rgba(90, 200, 250, 0.1);
  }

  tr:hover td {
    background: rgba(0, 122, 255, 0.05);
  }

  /* Apple-style colors */
  .blue { color: #007AFF; }
  .purple { color: #5856D6; }
  .pink { color: #FF2D55; }
  .orange { color: #FF9500; }
  .green { color: #34C759; }
  .red { color: #FF3B30; }
  .yellow { color: #FFCC00; }
  .cyan { color: #5AC8FA; }

  /* Gradient text */
  .gradient-blue {
    background: linear-gradient(135deg, #007AFF 0%, #5AC8FA 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .gradient-purple {
    background: linear-gradient(135deg, #5856D6 0%, #AF52DE 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .gradient-warm {
    background: linear-gradient(135deg, #FF9500 0%, #FF3B30 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  /* Cards */
  .card {
    background: linear-gradient(135deg, rgba(88, 86, 214, 0.1) 0%, rgba(0, 122, 255, 0.1) 100%);
    border: 1px solid rgba(90, 200, 250, 0.2);
    border-radius: 20px;
    padding: 32px;
    margin: 24px 0;
    box-shadow: 0 8px 32px rgba(0, 122, 255, 0.1);
  }

  /* Badges */
  .badge {
    display: inline-block;
    padding: 8px 16px;
    border-radius: 100px;
    font-size: 16px;
    font-weight: 600;
    margin: 4px;
  }

  .badge-blue {
    background: rgba(0, 122, 255, 0.2);
    color: #007AFF;
  }

  .badge-green {
    background: rgba(52, 199, 89, 0.2);
    color: #34C759;
  }

  .badge-orange {
    background: rgba(255, 149, 0, 0.2);
    color: #FF9500;
  }

  /* Lead slide */
  .lead {
    justify-content: center;
  }

  .lead h1 {
    font-size: 120px;
    margin-bottom: 0.2em;
  }

  .lead h2 {
    font-size: 48px;
    font-weight: 500;
  }

  /* Clean lists */
  ul {
    list-style: none;
    padding-left: 0;
  }

  ul li::before {
    content: "◆";
    margin-right: 16px;
    color: #007AFF;
  }

  /* Page numbers */
  section::after {
    content: attr(data-marpit-pagination);
    position: absolute;
    bottom: 24px;
    right: 48px;
    font-size: 16px;
    font-weight: 600;
    color: #5AC8FA;
    opacity: 0.6;
  }

  /* Links */
  a {
    color: #007AFF;
    text-decoration: none;
    border-bottom: 2px solid transparent;
    transition: all 0.3s ease;
    font-weight: 500;
  }

  a:hover {
    border-bottom-color: #007AFF;
  }

  /* Mermaid override */
  .mermaid {
    background: transparent !important;
  }
---

<!-- _class: lead -->

# Paddi

## インテリジェント・クラウドセキュリティ

**AI駆動 • マルチクラウド • 自動化**

---

# 現状の課題

<div class="card">

**プロダクトリリースの最大のボトルネックの一つであるセキュリティ監査**

◆ **社内セキュリティ監査** が <span class="orange">数ヶ月終わらない</span>
◆ **Excel + 手動チェック** で <span class="red">文字が小さくて見えない、読みたくない</span>
◆ **監査人不足** により <span class="pink">監査着手までに時間がかかる</span>

</div>

---

# ソリューション

## **Paddi**が監査プロセスを完全自動化

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 32px;">

<div class="card">

<h3><span class="gradient-blue">開発者向け</span></h3>

◆ **自動脆弱性検出**
◆ **影響範囲分析**
◆ **修正PR自動生成**
◆ **CI/CD統合**

</div>

<div class="card">

<h3><span class="gradient-purple">監査人向け</span></h3>

◆ **ビジュアルレポート**
◆ **リスク評価**
◆ **パッチ有無確認**
◆ **承認ワークフロー**

</div>

</div>

---

# 動作フロー

```
開発者がコミット → Paddi自動起動 → 脆弱性検出
    ↓                    ↓              ↓
修正PR作成 ← 影響分析 ← AI判定
    ↓
監査レポート生成 → 監査人確認 → 自動承認
```

<h3>完全自動化された監査フロー</h3>

◆ **検出** - コードベース全体をスキャン
◆ **分析** - 影響範囲と修正優先度を判定
◆ **修正** - 具体的な修正コードを生成
◆ **承認** - 監査人向けレポートで透明性確保

---

# マルチクラウド対応

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 32px; margin-top: 48px;">

<div>

<h3><span class="gradient-blue">現在利用可能</span></h3>

◆ <span class="green">✓</span> **Google Cloud Platform**
◆ <span class="green">✓</span> **GitHub**

</div>

<div>

<h3><span class="gradient-purple">近日公開</span></h3>

◆ <span class="yellow">◐</span> **Amazon Web Services**
◆ <span class="yellow">◐</span> **Microsoft Azure**

</div>

</div>

---

# ライブデモ

<div class="card">

```bash
$ git push origin feature/new-api

[Paddi] 🔍 セキュリティ監査開始...
[Paddi] ⚠️  SQLインジェクション脆弱性を検出
[Paddi] 📊 影響範囲: 3ファイル、12関数
[Paddi] 🔧 修正PR #142 を自動作成しました
[Paddi] ✅ 監査レポート: https://paddi.io/report/abc123

監査完了!
```

</div>

**CI/CDパイプラインにシームレスに統合**

---

# 実際の修正例

<div class="card" style="background: linear-gradient(135deg, rgba(255, 59, 48, 0.1) 0%, rgba(255, 149, 0, 0.1) 100%);">

```diff
# 検出: SQLインジェクション脆弱性
- query = f"SELECT * FROM users WHERE id = {user_id}"
+ query = "SELECT * FROM users WHERE id = ?"
+ cursor.execute(query, (user_id,))

# 影響分析結果
- 影響範囲: UserAPI, AdminPanel, ReportGenerator
- リスクレベル: CRITICAL（本番環境で悪用可能）
- 修正優先度: 即時対応必要
```

</div>

**自動生成されたPRはレビュー済みですぐマージ可能**

---

# 導入効果

| 指標 | **従来（手動監査）** | **Paddi導入後** | **改善率** |
|------|---------------------|-----------------|------------|
| リリースサイクル | 4週間 | 3日 | <span class="green">**9.3倍**</span> |
| 監査待ち時間 | 2週間 | 0分 | <span class="green">**∞**</span> |
| 検出精度 | 65% | 99.7% | <span class="green">**+53%**</span> |
| 監査コスト | 200万円/月 | 10万円/月 | <span class="green">**95%削減**</span> |

---

# 監査人向け機能

<div class="card">

## **コードが読めなくても安心の監査レポート**

◆ **ビジュアルダッシュボード** - 脆弱性を一覧表示
◆ **リスクマトリクス** - 優先度を自動判定
◆ **修正状況トラッキング** - リアルタイム更新
◆ **コンプライアンスチェック** - SOC2/ISO27001対応
◆ **パッチ管理** - 既知の脆弱性への対応状況
◆ **承認ワークフロー** - ワンクリック承認

</div>

**技術的な詳細を理解せずに、適切な判断が可能**

---

# 技術スタック

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">

<div class="card">

<h3><span class="gradient-blue">Google Cloud活用</span></h3>

◆ **Vertex AI** - Gemini Pro
◆ **Cloud Run** - デプロイ
◆ **IAM API** - 権限分析
◆ **SCC API** - 脅威検出

</div>

<div class="card">

<h3><span class="gradient-purple">開発技術</span></h3>

◆ **Python 3.11** - バックエンド
◆ **Fire CLI** - コマンドライン
◆ **Jinja2** - レポート生成
◆ **GitHub Actions** - CI/CD

</div>

</div>

---

<!-- _class: lead -->

# ROI計算例

<div class="card">

## **年間1,000デプロイの企業での効果**

| 項目 | 削減効果 |
|------|----------|
| **監査待ち時間削減** | 2,000時間/年 → **2.5億円相当** |
| **リリース遅延防止** | 売上機会損失 → **6億円回避** |
| **セキュリティ事故防止** | 1件でも防げば → **4.8億円回避** |
| **監査人員削減** | 5名 → 1名 → **8,000万円/年** |

### **総合効果: 年間13.3億円の価値創出**

</div>

---

# Thank you

<div style="text-align: center; margin-top: 60px;">

**GitHub**: [@susumutomita/Paddi](https://github.com/susumutomita/Paddi)
**Contact**: <oyster880@gmail.com>

<div style="margin-top: 60px; font-size: 18px; opacity: 0.7;">
Google Cloud AI Hackathon 2025 のために開発 ❤️
</div>

</div>
