"""
Paddi Security Dashboard - メインアプリケーション
視覚的なインパクトのあるセキュリティダッシュボード
"""

import streamlit as st
import json
import os
from pathlib import Path

st.set_page_config(
    page_title="Paddi Security Dashboard",
    page_icon="🩹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown(
    """
<style>
    /* ダークテーマのメトリクスカード */
    .stMetric {
        background-color: #1e1e1e;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #333;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    /* 成功時のハイライト */
    .success-metric {
        border-left: 4px solid #00ff00;
    }
    
    /* 警告時のハイライト */
    .warning-metric {
        border-left: 4px solid #ff9800;
    }
    
    /* エラー時のハイライト */
    .danger-metric {
        border-left: 4px solid #ff0000;
    }
    
    /* ヘッダーのスタイリング */
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #00ff00, #0099ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    /* サイドバーのスタイリング */
    .css-1d391kg {
        background-color: #1a1a1a;
    }
    
    /* ボタンのアニメーション */
    .stButton > button {
        transition: all 0.3s ease;
        border-radius: 0.5rem;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
</style>
""",
    unsafe_allow_html=True,
)

# ヘッダー
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown(
        '<h1 class="main-header">🩹 Paddi Security Dashboard</h1>',
        unsafe_allow_html=True,
    )
    st.markdown("**クラウドセキュリティの自動監査・修正ツール**")

# メインページのコンテンツ
st.markdown("---")

# サンプルデータの読み込み
data_path = Path(__file__).parent.parent.parent / "data" / "sample_collected.json"
try:
    if data_path.exists():
        with open(data_path, "r", encoding="utf-8") as f:
            collected_data = json.load(f)
    else:
        collected_data = {"findings": []}
except Exception:
    collected_data = {"findings": []}

# メトリクスの計算
total_findings = len(collected_data.get("findings", []))
high_severity = sum(
    1
    for f in collected_data.get("findings", [])
    if f.get("severity", "").upper() == "HIGH"
)
resolved = 0  # 初期値
security_score = max(0, 100 - (total_findings * 5))  # シンプルなスコア計算

# KPIメトリクスの表示
st.markdown("### 📊 セキュリティ概要")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="セキュリティスコア",
        value=f"{security_score}",
        delta="-5" if security_score < 80 else "+3",
        help="100点満点のセキュリティ評価スコア",
    )

with col2:
    st.metric(
        label="検出された脆弱性",
        value=total_findings,
        delta=f"+{high_severity}" if high_severity > 0 else "0",
        delta_color="inverse",
        help="現在検出されている脆弱性の総数",
    )

with col3:
    st.metric(
        label="修正済み項目",
        value=resolved,
        delta="+0",
        help="自動修正が完了した項目数",
    )

with col4:
    time_saved = resolved * 15  # 1項目あたり15分の節約と仮定
    st.metric(
        label="節約時間（分）",
        value=time_saved,
        delta="+0",
        help="自動修正により節約された推定時間",
    )

# アクションボタン
st.markdown("---")
st.markdown("### 🚀 クイックアクション")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔍 新規スキャン実行", use_container_width=True, type="primary"):
        st.info("スキャンページに移動してください")

with col2:
    if st.button("📈 分析結果を表示", use_container_width=True):
        st.info("分析ページに移動してください")

with col3:
    if st.button("🔧 自動修正を開始", use_container_width=True):
        st.warning("修正ページに移動してください")

# 最新の検出結果プレビュー
st.markdown("---")
st.markdown("### 🔔 最新の検出結果")

if total_findings > 0:
    # 最新5件を表示
    latest_findings = collected_data.get("findings", [])[:5]
    for i, finding in enumerate(latest_findings):
        severity = finding.get("severity", "MEDIUM").upper()
        color = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(severity, "⚪")

        with st.expander(
            f"{color} {finding.get('category', 'Unknown')} - {finding.get('name', 'Unnamed Finding')}"
        ):
            st.write(f"**重要度**: {severity}")
            st.write(f"**説明**: {finding.get('description', 'No description')}")
            if finding.get("resource_name"):
                st.write(f"**リソース**: {finding.get('resource_name')}")
else:
    st.success("✅ 現在、検出された脆弱性はありません！")

# フッター
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>Paddi - AI-Powered Cloud Security Automation</p>
        <p>第2回 AI Agent Hackathon with Google Cloud</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# サイドバーの情報
with st.sidebar:
    st.markdown("### ℹ️ システム情報")
    st.info(
        """
        **バージョン**: 1.0.0
        
        **対応クラウド**:
        - Google Cloud Platform
        - Amazon Web Services
        - Microsoft Azure
        
        **エージェント**:
        - 🤖 Collector Agent
        - 🧠 Explainer Agent
        - 📄 Reporter Agent
        """
    )

    st.markdown("### 📚 ドキュメント")
    st.markdown(
        """
        - [使い方ガイド](https://github.com/susumutomita/Paddi)
        - [API リファレンス](https://github.com/susumutomita/Paddi)
        - [トラブルシューティング](https://github.com/susumutomita/Paddi)
        """
    )