"""
分析ページ - セキュリティデータの詳細分析
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Analytics - Paddi Security Dashboard",
    page_icon="📈",
    layout="wide",
)

st.title("📈 セキュリティ分析")
st.markdown("セキュリティデータの詳細な分析とインサイト")

# タブの作成
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 統計分析", "🔮 予測分析", "🎯 リスク分析", "💡 インサイト"]
)

with tab1:
    st.markdown("### 📊 セキュリティ統計")

    # 期間選択
    col1, col2 = st.columns([1, 3])
    with col1:
        period = st.selectbox(
            "分析期間",
            ["過去7日間", "過去30日間", "過去90日間", "過去1年間"],
            index=1,
        )

    # 統計データの生成（ダミー）
    days = {"過去7日間": 7, "過去30日間": 30, "過去90日間": 90, "過去1年間": 365}[period]

    dates = pd.date_range(end=datetime.now(), periods=days, freq="D")

    # 脆弱性の推移データ
    vulnerability_data = pd.DataFrame(
        {
            "日付": dates,
            "高リスク": np.random.poisson(3, days),
            "中リスク": np.random.poisson(8, days),
            "低リスク": np.random.poisson(15, days),
        }
    )

    # 積み上げ面グラフ
    fig_area = px.area(
        vulnerability_data,
        x="日付",
        y=["高リスク", "中リスク", "低リスク"],
        title="脆弱性検出数の推移",
        color_discrete_map={
            "高リスク": "#ff4444",
            "中リスク": "#ff9800",
            "低リスク": "#4caf50",
        },
    )
    st.plotly_chart(fig_area, use_container_width=True)

    # カテゴリ別分析
    col1, col2 = st.columns(2)

    with col1:
        # カテゴリ別の脆弱性分布
        categories = ["IAM", "ネットワーク", "ストレージ", "暗号化", "ログ", "その他"]
        values = [25, 20, 18, 15, 12, 10]

        fig_donut = go.Figure(
            data=[
                go.Pie(
                    labels=categories,
                    values=values,
                    hole=0.3,
                )
            ]
        )
        fig_donut.update_layout(title="カテゴリ別脆弱性分布")
        st.plotly_chart(fig_donut, use_container_width=True)

    with col2:
        # 修正率の推移
        fix_rate_data = pd.DataFrame(
            {
                "月": ["1月", "2月", "3月", "4月", "5月", "6月"],
                "修正率": [65, 70, 75, 82, 88, 92],
            }
        )

        fig_fix_rate = px.line(
            fix_rate_data,
            x="月",
            y="修正率",
            title="月別修正率の推移",
            markers=True,
        )
        fig_fix_rate.add_hline(y=85, line_dash="dash", line_color="green", annotation_text="目標")
        st.plotly_chart(fig_fix_rate, use_container_width=True)

    # 詳細統計
    st.markdown("### 📊 詳細統計")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("平均検出数/日", "12.5", "+2.3")
        st.metric("平均修正時間", "2.5時間", "-30分")

    with col2:
        st.metric("最多検出カテゴリ", "IAM")
        st.metric("修正成功率", "95.2%", "+3.1%")

    with col3:
        st.metric("false positive率", "8.3%", "-1.2%")
        st.metric("自動修正適用率", "78.5%", "+5.5%")

    with col4:
        st.metric("MTBF", "168時間", "+24時間")
        st.metric("MTTR", "1.8時間", "-0.3時間")

with tab2:
    st.markdown("### 🔮 予測分析")

    # 将来の脆弱性予測
    future_dates = pd.date_range(start=datetime.now(), periods=30, freq="D")
    historical_avg = 25
    trend = 0.2

    # 予測データの生成
    predictions = []
    confidence_upper = []
    confidence_lower = []

    for i in range(30):
        base_prediction = historical_avg - (trend * i)
        predictions.append(base_prediction)
        confidence_upper.append(base_prediction + 5)
        confidence_lower.append(base_prediction - 5)

    # 予測グラフ
    fig_forecast = go.Figure()

    # 予測値
    fig_forecast.add_trace(
        go.Scatter(
            x=future_dates,
            y=predictions,
            mode="lines",
            name="予測値",
            line=dict(color="blue", width=3),
        )
    )

    # 信頼区間
    fig_forecast.add_trace(
        go.Scatter(
            x=future_dates,
            y=confidence_upper,
            mode="lines",
            name="上限",
            line=dict(color="rgba(0,100,255,0)"),
            showlegend=False,
        )
    )

    fig_forecast.add_trace(
        go.Scatter(
            x=future_dates,
            y=confidence_lower,
            mode="lines",
            name="下限",
            line=dict(color="rgba(0,100,255,0)"),
            fill="tonexty",
            fillcolor="rgba(0,100,255,0.2)",
            showlegend=False,
        )
    )

    fig_forecast.update_layout(
        title="脆弱性発生数の予測（30日間）",
        xaxis_title="日付",
        yaxis_title="予測脆弱性数",
        hovermode="x unified",
    )

    st.plotly_chart(fig_forecast, use_container_width=True)

    # 予測サマリー
    col1, col2, col3 = st.columns(3)

    with col1:
        st.info(
            """
            **予測サマリー**
            - 30日後の予測値: 19件/日
            - 改善率: 24%
            - 信頼度: 85%
            """
        )

    with col2:
        st.warning(
            """
            **注意が必要な領域**
            - IAMカテゴリ: 増加傾向
            - ネットワーク: 横ばい
            - ストレージ: 改善傾向
            """
        )

    with col3:
        st.success(
            """
            **推奨アクション**
            - IAM監査の強化
            - 自動修正ルールの追加
            - 定期スキャンの頻度向上
            """
        )

with tab3:
    st.markdown("### 🎯 リスク分析")

    # リスクマトリックス
    st.markdown("#### リスクマトリックス")

    # リスクデータの生成
    risk_items = []
    for i in range(20):
        risk_items.append(
            {
                "項目": f"リスク{i+1}",
                "発生可能性": np.random.randint(1, 6),
                "影響度": np.random.randint(1, 6),
                "カテゴリ": np.random.choice(["IAM", "ネットワーク", "ストレージ", "暗号化"]),
            }
        )

    risk_df = pd.DataFrame(risk_items)
    risk_df["リスクスコア"] = risk_df["発生可能性"] * risk_df["影響度"]

    # 散布図でリスクマトリックスを表現
    fig_risk = px.scatter(
        risk_df,
        x="発生可能性",
        y="影響度",
        size="リスクスコア",
        color="カテゴリ",
        hover_data=["項目"],
        title="リスクマトリックス",
    )

    # 背景色の追加
    fig_risk.add_shape(
        type="rect",
        x0=0,
        y0=0,
        x1=2.5,
        y1=2.5,
        fillcolor="lightgreen",
        opacity=0.2,
        layer="below",
        line_width=0,
    )
    fig_risk.add_shape(
        type="rect",
        x0=2.5,
        y0=2.5,
        x1=5,
        y1=5,
        fillcolor="red",
        opacity=0.2,
        layer="below",
        line_width=0,
    )

    st.plotly_chart(fig_risk, use_container_width=True)

    # トップリスク
    st.markdown("#### トップ10リスク")

    top_risks = risk_df.nlargest(10, "リスクスコア")
    fig_top_risks = px.bar(
        top_risks,
        x="リスクスコア",
        y="項目",
        orientation="h",
        color="カテゴリ",
        title="高リスク項目",
    )
    st.plotly_chart(fig_top_risks, use_container_width=True)

with tab4:
    st.markdown("### 💡 セキュリティインサイト")

    # AIによる分析結果（ダミー）
    st.info(
        """
        🤖 **AI分析によるインサイト**

        過去30日間のデータ分析により、以下の傾向が確認されました：
        """
    )

    insights = [
        {
            "title": "IAM設定の脆弱性が増加傾向",
            "detail": "過去2週間でIAM関連の脆弱性が35%増加しています。特にサービスアカウントの過剰な権限付与が目立ちます。",
            "action": "IAMポリシーの定期レビューと最小権限の原則の徹底を推奨します。",
            "priority": "高",
        },
        {
            "title": "自動修正による効率改善",
            "detail": "自動修正機能の導入により、平均修正時間が65%短縮されました。",
            "action": "より多くの脆弱性タイプに対して自動修正ルールを追加することを推奨します。",
            "priority": "中",
        },
        {
            "title": "週末のセキュリティリスク上昇",
            "detail": "週末に検出される脆弱性が平日比で20%多いことが判明しました。",
            "action": "週末の監視体制強化と自動アラートの設定を推奨します。",
            "priority": "中",
        },
        {
            "title": "暗号化設定の改善",
            "detail": "暗号化関連の脆弱性が先月比で40%減少しました。",
            "action": "現在の暗号化ポリシーを維持し、他のカテゴリにも同様のアプローチを適用することを推奨します。",
            "priority": "低",
        },
    ]

    for insight in insights:
        priority_color = {"高": "🔴", "中": "🟡", "低": "🟢"}[insight["priority"]]

        with st.expander(f"{priority_color} {insight['title']}"):
            st.write(f"**詳細**: {insight['detail']}")
            st.write(f"**推奨アクション**: {insight['action']}")
            st.write(f"**優先度**: {insight['priority']}")

    # 改善提案
    st.markdown("### 🚀 改善提案")

    col1, col2 = st.columns(2)

    with col1:
        st.success(
            """
            **短期的改善案（1-2週間）**
            - ✅ 高リスクIAM脆弱性の即時修正
            - ✅ 自動スキャンの頻度を日次に変更
            - ✅ アラート通知の最適化
            """
        )

    with col2:
        st.info(
            """
            **長期的改善案（1-3ヶ月）**
            - 📋 セキュリティポリシーの全面見直し
            - 📋 AIベースの異常検知システム導入
            - 📋 セキュリティトレーニングの実施
            """
        )