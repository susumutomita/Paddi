"""
メトリクスコンポーネント - KPIメトリクスの表示
"""

import streamlit as st
from typing import Dict, Any, Optional, List


def display_metric_card(
    label: str,
    value: Any,
    delta: Optional[str] = None,
    delta_color: str = "normal",
    help_text: Optional[str] = None,
    custom_css_class: Optional[str] = None,
) -> None:
    """
    カスタマイズされたメトリクスカードを表示

    Args:
        label: メトリクスのラベル
        value: 表示する値
        delta: 変化量（オプション）
        delta_color: deltaの色（normal, inverse, off）
        help_text: ヘルプテキスト（オプション）
        custom_css_class: カスタムCSSクラス（オプション）
    """
    if custom_css_class:
        st.markdown(f'<div class="{custom_css_class}">', unsafe_allow_html=True)

    st.metric(
        label=label,
        value=value,
        delta=delta,
        delta_color=delta_color,
        help=help_text,
    )

    if custom_css_class:
        st.markdown("</div>", unsafe_allow_html=True)


def display_metric_row(metrics: List[Dict[str, Any]], columns: int = 4) -> None:
    """
    メトリクスを横一列に表示

    Args:
        metrics: メトリクスのリスト
        columns: 列数
    """
    cols = st.columns(columns)

    for i, metric in enumerate(metrics):
        with cols[i % columns]:
            display_metric_card(**metric)


def calculate_security_score(findings: List[Dict[str, Any]]) -> int:
    """
    セキュリティスコアを計算

    Args:
        findings: 脆弱性のリスト

    Returns:
        セキュリティスコア（0-100）
    """
    if not findings:
        return 100

    # 重要度ごとの重み
    severity_weights = {
        "HIGH": 10,
        "CRITICAL": 15,
        "MEDIUM": 5,
        "LOW": 2,
        "INFO": 1,
    }

    total_penalty = 0
    for finding in findings:
        severity = finding.get("severity", "MEDIUM").upper()
        penalty = severity_weights.get(severity, 5)
        total_penalty += penalty

    # スコアを計算（最小値は0）
    score = max(0, 100 - total_penalty)

    return score


def get_severity_counts(findings: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    重要度ごとの脆弱性数を取得

    Args:
        findings: 脆弱性のリスト

    Returns:
        重要度ごとのカウント
    """
    counts = {
        "CRITICAL": 0,
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
        "INFO": 0,
    }

    for finding in findings:
        severity = finding.get("severity", "MEDIUM").upper()
        if severity in counts:
            counts[severity] += 1

    return counts


def display_security_summary(data: Dict[str, Any]) -> None:
    """
    セキュリティサマリーを表示

    Args:
        data: セキュリティデータ
    """
    findings = data.get("findings", [])

    # スコアとカウントを計算
    score = calculate_security_score(findings)
    severity_counts = get_severity_counts(findings)
    total_findings = len(findings)

    # メトリクスの定義
    metrics = [
        {
            "label": "セキュリティスコア",
            "value": score,
            "delta": "-5" if score < 80 else "+3",
            "help_text": "100点満点のセキュリティ評価スコア",
        },
        {
            "label": "検出された脆弱性",
            "value": total_findings,
            "delta": f"+{severity_counts['HIGH'] + severity_counts['CRITICAL']}"
            if severity_counts["HIGH"] + severity_counts["CRITICAL"] > 0
            else "0",
            "delta_color": "inverse",
            "help_text": "現在検出されている脆弱性の総数",
        },
        {
            "label": "クリティカル/高リスク",
            "value": severity_counts["CRITICAL"] + severity_counts["HIGH"],
            "delta": None,
            "help_text": "早急な対応が必要な脆弱性",
        },
        {
            "label": "自動修正可能",
            "value": sum(
                1 for f in findings if f.get("auto_fixable", False)
            ),
            "delta": None,
            "help_text": "自動修正で対応可能な脆弱性",
        },
    ]

    # メトリクスを表示
    display_metric_row(metrics)


def display_trend_indicator(
    current_value: float,
    previous_value: float,
    label: str,
    format_str: str = "{:.1f}",
    improve_direction: str = "increase",
) -> None:
    """
    トレンドインジケーターを表示

    Args:
        current_value: 現在の値
        previous_value: 前回の値
        label: ラベル
        format_str: フォーマット文字列
        improve_direction: 改善の方向（increase/decrease）
    """
    change = current_value - previous_value
    change_pct = (change / previous_value * 100) if previous_value != 0 else 0

    # 改善かどうかを判定
    is_improvement = (
        (change > 0 and improve_direction == "increase")
        or (change < 0 and improve_direction == "decrease")
    )

    # 色を決定
    color = "green" if is_improvement else "red" if change != 0 else "gray"

    # アイコンを決定
    icon = "📈" if change > 0 else "📉" if change < 0 else "➡️"

    # 表示
    col1, col2 = st.columns([3, 1])

    with col1:
        st.write(f"**{label}**")
        st.write(format_str.format(current_value))

    with col2:
        st.markdown(
            f'<div style="color: {color}; text-align: right;">'
            f"{icon} {change_pct:+.1f}%"
            f"</div>",
            unsafe_allow_html=True,
        )


def create_metric_dashboard(
    title: str,
    metrics_data: List[Dict[str, Any]],
    columns: int = 4,
) -> None:
    """
    メトリクスダッシュボードを作成

    Args:
        title: ダッシュボードのタイトル
        metrics_data: メトリクスデータのリスト
        columns: 列数
    """
    st.markdown(f"### {title}")

    # カスタムスタイルの適用
    st.markdown(
        """
        <style>
        .metric-dashboard {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: #1f77b4;
        }
        .metric-label {
            font-size: 0.9rem;
            color: #666;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container():
        display_metric_row(metrics_data, columns)