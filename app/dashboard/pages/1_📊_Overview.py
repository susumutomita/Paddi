"""
概要ページ - セキュリティステータスの全体像を表示
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Overview - Paddi Security Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("📊 セキュリティ概要")
st.markdown("クラウド環境のセキュリティ状態を一目で把握")

# データの読み込み
data_path = Path(__file__).parent.parent.parent.parent / "data" / "sample_collected.json"
try:
    if data_path.exists():
        with open(data_path, "r", encoding="utf-8") as f:
            collected_data = json.load(f)
    else:
        collected_data = {"findings": []}
except Exception:
    collected_data = {"findings": []}

findings = collected_data.get("findings", [])

# タブの作成
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 ダッシュボード", "📈 トレンド分析", "🗺️ リスクマップ", "📋 詳細レポート"]
)

with tab1:
    # セキュリティスコアゲージ
    st.markdown("### セキュリティスコア")

    score = max(0, 100 - (len(findings) * 5))

    fig_gauge = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "総合スコア"},
            delta={"reference": 80, "increasing": {"color": "green"}},
            gauge={
                "axis": {"range": [None, 100]},
                "bar": {"color": "darkblue"},
                "steps": [
                    {"range": [0, 50], "color": "lightgray"},
                    {"range": [50, 80], "color": "gray"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": 90,
                },
            },
        )
    )

    fig_gauge.update_layout(height=400)
    st.plotly_chart(fig_gauge, use_container_width=True)

    # 脆弱性の分類
    st.markdown("### 脆弱性の分類")

    col1, col2 = st.columns(2)

    with col1:
        # 重要度別の円グラフ
        severity_counts = {}
        for finding in findings:
            severity = finding.get("severity", "MEDIUM")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        if severity_counts:
            fig_pie = px.pie(
                values=list(severity_counts.values()),
                names=list(severity_counts.keys()),
                title="重要度別分布",
                color_discrete_map={
                    "HIGH": "#ff4444",
                    "MEDIUM": "#ff9800",
                    "LOW": "#4caf50",
                },
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("脆弱性が検出されていません")

    with col2:
        # カテゴリ別の棒グラフ
        category_counts = {}
        for finding in findings:
            category = finding.get("category", "その他")
            category_counts[category] = category_counts.get(category, 0) + 1

        if category_counts:
            fig_bar = px.bar(
                x=list(category_counts.values()),
                y=list(category_counts.keys()),
                orientation="h",
                title="カテゴリ別分布",
                labels={"x": "件数", "y": "カテゴリ"},
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("脆弱性が検出されていません")

with tab2:
    st.markdown("### セキュリティスコアの推移")

    # ダミーデータで推移を表示
    dates = pd.date_range(end=datetime.now(), periods=30, freq="D")
    scores = [max(0, 100 - (len(findings) * 5) + i % 10 - 5) for i in range(30)]

    fig_trend = px.line(
        x=dates,
        y=scores,
        title="過去30日間のスコア推移",
        labels={"x": "日付", "y": "スコア"},
    )
    fig_trend.add_hline(y=80, line_dash="dash", line_color="green", annotation_text="目標ライン")
    fig_trend.update_layout(height=400)
    st.plotly_chart(fig_trend, use_container_width=True)

    # 修正活動の推移
    st.markdown("### 修正活動の推移")

    # ダミーデータ
    activities = pd.DataFrame(
        {
            "日付": dates,
            "検出": [5 + i % 3 for i in range(30)],
            "修正": [3 + i % 2 for i in range(30)],
        }
    )

    fig_activity = px.bar(
        activities,
        x="日付",
        y=["検出", "修正"],
        title="検出と修正の推移",
        labels={"value": "件数", "variable": "種別"},
    )
    st.plotly_chart(fig_activity, use_container_width=True)

with tab3:
    st.markdown("### リスクヒートマップ")

    # クラウドプロバイダー別のリスク分布
    providers = ["GCP", "AWS", "Azure"]
    risk_categories = ["IAM", "ネットワーク", "ストレージ", "暗号化", "ログ"]

    # ダミーデータ
    risk_data = []
    for provider in providers:
        for category in risk_categories:
            risk_data.append(
                {
                    "プロバイダー": provider,
                    "カテゴリ": category,
                    "リスクレベル": (hash(provider + category) % 10) + 1,
                }
            )

    risk_df = pd.DataFrame(risk_data)
    risk_pivot = risk_df.pivot(index="カテゴリ", columns="プロバイダー", values="リスクレベル")

    fig_heatmap = px.imshow(
        risk_pivot,
        labels=dict(x="プロバイダー", y="カテゴリ", color="リスクレベル"),
        title="クラウドプロバイダー別リスクヒートマップ",
        color_continuous_scale="RdYlGn_r",
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

with tab4:
    st.markdown("### 詳細レポート")

    # サマリー統計
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("総検出数", len(findings))
        st.metric("クリティカル", sum(1 for f in findings if f.get("severity") == "HIGH"))

    with col2:
        st.metric("平均修正時間", "15分")
        st.metric("自動修正率", "85%")

    with col3:
        st.metric("MTTR", "30分")
        st.metric("コンプライアンス率", f"{score}%")

    # 詳細テーブル
    st.markdown("### 最新の検出項目")

    if findings:
        df_findings = pd.DataFrame(findings[:10])  # 最新10件
        # 必要なカラムのみ選択
        display_columns = ["name", "severity", "category", "resource_name"]
        available_columns = [col for col in display_columns if col in df_findings.columns]

        if available_columns:
            st.dataframe(
                df_findings[available_columns],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("表示可能なデータがありません")
    else:
        st.success("✅ 検出された脆弱性はありません")

    # エクスポートボタン
    st.markdown("### レポートのエクスポート")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📄 PDFでエクスポート", use_container_width=True):
            st.info("PDF生成機能は準備中です")

    with col2:
        if st.button("📊 Excelでエクスポート", use_container_width=True):
            st.info("Excel生成機能は準備中です")