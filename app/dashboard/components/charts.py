"""
チャートコンポーネント - グラフ表示用のユーティリティ
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta


def create_security_gauge(
    score: int,
    title: str = "セキュリティスコア",
    reference_value: int = 80,
) -> go.Figure:
    """
    セキュリティスコアのゲージチャートを作成

    Args:
        score: スコア値（0-100）
        title: チャートのタイトル
        reference_value: 基準値

    Returns:
        Plotlyのゲージチャート
    """
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": title},
            delta={"reference": reference_value, "increasing": {"color": "green"}},
            gauge={
                "axis": {"range": [None, 100]},
                "bar": {"color": "#1f77b4"},
                "steps": [
                    {"range": [0, 50], "color": "#ffcccc"},
                    {"range": [50, 80], "color": "#ffffcc"},
                    {"range": [80, 100], "color": "#ccffcc"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": reference_value,
                },
            },
        )
    )

    fig.update_layout(
        height=400,
        font={"size": 16},
    )

    return fig


def create_severity_pie_chart(
    findings: List[Dict[str, Any]],
    title: str = "重要度別分布",
) -> go.Figure:
    """
    重要度別の円グラフを作成

    Args:
        findings: 脆弱性のリスト
        title: チャートのタイトル

    Returns:
        Plotlyの円グラフ
    """
    severity_counts = {}
    for finding in findings:
        severity = finding.get("severity", "MEDIUM").upper()
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

    if not severity_counts:
        severity_counts = {"なし": 1}

    # 重要度の順序と色
    severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    severity_colors = {
        "CRITICAL": "#8B0000",
        "HIGH": "#FF0000",
        "MEDIUM": "#FFA500",
        "LOW": "#FFFF00",
        "INFO": "#00FF00",
        "なし": "#CCCCCC",
    }

    # データの準備
    labels = []
    values = []
    colors = []

    for severity in severity_order:
        if severity in severity_counts:
            labels.append(severity)
            values.append(severity_counts[severity])
            colors.append(severity_colors[severity])

    # 円グラフの作成
    fig = px.pie(
        values=values,
        names=labels,
        title=title,
        color_discrete_sequence=colors,
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hoverinfo="label+percent+value",
    )

    return fig


def create_trend_line_chart(
    dates: pd.DatetimeIndex,
    values: List[float],
    title: str,
    y_label: str = "値",
    reference_line: Optional[float] = None,
) -> go.Figure:
    """
    トレンドラインチャートを作成

    Args:
        dates: 日付のインデックス
        values: 値のリスト
        title: チャートのタイトル
        y_label: Y軸のラベル
        reference_line: 基準線の値

    Returns:
        Plotlyのラインチャート
    """
    fig = px.line(
        x=dates,
        y=values,
        title=title,
        labels={"x": "日付", "y": y_label},
    )

    # スタイリング
    fig.update_traces(
        line_color="#1f77b4",
        line_width=3,
    )

    # 基準線の追加
    if reference_line is not None:
        fig.add_hline(
            y=reference_line,
            line_dash="dash",
            line_color="green",
            annotation_text=f"目標: {reference_line}",
        )

    fig.update_layout(
        hovermode="x unified",
        height=400,
    )

    return fig


def create_heatmap(
    data: pd.DataFrame,
    title: str = "リスクヒートマップ",
    color_scale: str = "RdYlGn_r",
) -> go.Figure:
    """
    ヒートマップを作成

    Args:
        data: ヒートマップ用のデータフレーム
        title: チャートのタイトル
        color_scale: カラースケール

    Returns:
        Plotlyのヒートマップ
    """
    fig = px.imshow(
        data,
        labels=dict(color="リスクレベル"),
        title=title,
        color_continuous_scale=color_scale,
        aspect="auto",
    )

    fig.update_xaxis(side="top")
    fig.update_layout(height=500)

    return fig


def create_stacked_bar_chart(
    data: pd.DataFrame,
    x_col: str,
    y_cols: List[str],
    title: str,
    colors: Optional[Dict[str, str]] = None,
) -> go.Figure:
    """
    積み上げ棒グラフを作成

    Args:
        data: データフレーム
        x_col: X軸のカラム名
        y_cols: Y軸のカラム名のリスト
        title: チャートのタイトル
        colors: カラーマップ

    Returns:
        Plotlyの積み上げ棒グラフ
    """
    fig = go.Figure()

    # デフォルトカラー
    default_colors = px.colors.qualitative.Set3

    for i, col in enumerate(y_cols):
        color = colors.get(col) if colors else default_colors[i % len(default_colors)]

        fig.add_trace(
            go.Bar(
                name=col,
                x=data[x_col],
                y=data[col],
                marker_color=color,
            )
        )

    fig.update_layout(
        barmode="stack",
        title=title,
        xaxis_title=x_col,
        yaxis_title="件数",
        height=400,
    )

    return fig


def create_activity_timeline(
    activities: List[Dict[str, Any]],
    title: str = "アクティビティタイムライン",
) -> go.Figure:
    """
    アクティビティタイムラインを作成

    Args:
        activities: アクティビティのリスト
        title: チャートのタイトル

    Returns:
        Plotlyのタイムライン
    """
    # データの準備
    df_activities = pd.DataFrame(activities)

    # ガントチャート風のタイムライン
    fig = px.timeline(
        df_activities,
        x_start="start",
        x_end="end",
        y="task",
        color="status",
        title=title,
        color_discrete_map={
            "completed": "#00CC00",
            "in_progress": "#FFA500",
            "pending": "#CCCCCC",
        },
    )

    fig.update_yaxis(autorange="reversed")
    fig.update_layout(height=400)

    return fig


def create_risk_matrix(
    risks: List[Dict[str, Any]],
    title: str = "リスクマトリックス",
) -> go.Figure:
    """
    リスクマトリックスを作成

    Args:
        risks: リスクのリスト
        title: チャートのタイトル

    Returns:
        Plotlyのリスクマトリックス
    """
    # データフレームの作成
    df_risks = pd.DataFrame(risks)

    # 散布図でリスクマトリックスを表現
    fig = px.scatter(
        df_risks,
        x="発生可能性",
        y="影響度",
        size="リスクスコア",
        color="カテゴリ",
        hover_data=["項目"],
        title=title,
    )

    # 背景の領域を追加
    shapes = [
        # 低リスク領域（緑）
        dict(
            type="rect",
            x0=0,
            y0=0,
            x1=2.5,
            y1=2.5,
            fillcolor="lightgreen",
            opacity=0.2,
            layer="below",
            line_width=0,
        ),
        # 中リスク領域（黄）
        dict(
            type="rect",
            x0=2.5,
            y0=0,
            x1=5,
            y1=2.5,
            fillcolor="yellow",
            opacity=0.2,
            layer="below",
            line_width=0,
        ),
        dict(
            type="rect",
            x0=0,
            y0=2.5,
            x1=2.5,
            y1=5,
            fillcolor="yellow",
            opacity=0.2,
            layer="below",
            line_width=0,
        ),
        # 高リスク領域（赤）
        dict(
            type="rect",
            x0=2.5,
            y0=2.5,
            x1=5,
            y1=5,
            fillcolor="red",
            opacity=0.2,
            layer="below",
            line_width=0,
        ),
    ]

    fig.update_layout(
        shapes=shapes,
        xaxis=dict(range=[0, 5.5], title="発生可能性"),
        yaxis=dict(range=[0, 5.5], title="影響度"),
        height=500,
    )

    return fig


def create_comparison_chart(
    categories: List[str],
    current_values: List[float],
    previous_values: List[float],
    title: str = "期間比較",
) -> go.Figure:
    """
    期間比較チャートを作成

    Args:
        categories: カテゴリのリスト
        current_values: 現在の値
        previous_values: 前回の値
        title: チャートのタイトル

    Returns:
        Plotlyの比較チャート
    """
    fig = go.Figure()

    # 前回の値
    fig.add_trace(
        go.Bar(
            name="前回",
            x=categories,
            y=previous_values,
            marker_color="lightgray",
        )
    )

    # 現在の値
    fig.add_trace(
        go.Bar(
            name="現在",
            x=categories,
            y=current_values,
            marker_color="#1f77b4",
        )
    )

    fig.update_layout(
        barmode="group",
        title=title,
        xaxis_title="カテゴリ",
        yaxis_title="件数",
        height=400,
    )

    return fig