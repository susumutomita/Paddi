"""
アラートコンポーネント - アラート表示用のユーティリティ
"""

import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


def display_alert(
    message: str,
    alert_type: str = "info",
    icon: Optional[str] = None,
    dismissible: bool = True,
) -> None:
    """
    アラートを表示

    Args:
        message: アラートメッセージ
        alert_type: アラートタイプ（info, success, warning, error）
        icon: アイコン（オプション）
        dismissible: 閉じるボタンの表示
    """
    # アラートタイプごとのデフォルトアイコン
    default_icons = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
    }

    # アラートタイプごとの色
    colors = {
        "info": "#0066cc",
        "success": "#00cc00",
        "warning": "#ff9900",
        "error": "#cc0000",
    }

    # アイコンの決定
    display_icon = icon or default_icons.get(alert_type, "📢")

    # Streamlitの組み込みアラート関数を使用
    if alert_type == "info":
        st.info(f"{display_icon} {message}")
    elif alert_type == "success":
        st.success(f"{display_icon} {message}")
    elif alert_type == "warning":
        st.warning(f"{display_icon} {message}")
    elif alert_type == "error":
        st.error(f"{display_icon} {message}")


def display_security_alerts(findings: List[Dict[str, Any]], limit: int = 5) -> None:
    """
    セキュリティアラートを表示

    Args:
        findings: 脆弱性のリスト
        limit: 表示する最大数
    """
    if not findings:
        display_alert("現在、アクティブなセキュリティアラートはありません。", "success")
        return

    st.markdown("### 🚨 セキュリティアラート")

    # 重要度でソート
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
    sorted_findings = sorted(
        findings,
        key=lambda x: severity_order.get(x.get("severity", "MEDIUM").upper(), 5),
    )

    # 上位のアラートを表示
    for finding in sorted_findings[:limit]:
        severity = finding.get("severity", "MEDIUM").upper()
        title = finding.get("name", "Unknown Finding")
        description = finding.get("description", "No description available")
        resource = finding.get("resource_name", "Unknown resource")

        # 重要度に応じたアラートタイプ
        if severity in ["CRITICAL", "HIGH"]:
            alert_type = "error"
        elif severity == "MEDIUM":
            alert_type = "warning"
        else:
            alert_type = "info"

        # アラートの表示
        with st.expander(f"{severity} - {title}", expanded=(severity in ["CRITICAL", "HIGH"])):
            st.write(f"**説明**: {description}")
            st.write(f"**対象リソース**: `{resource}`")

            if finding.get("recommendation"):
                st.write(f"**推奨事項**: {finding['recommendation']}")

            # アクションボタン
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("詳細を表示", key=f"detail_{finding.get('id', hash(title))}"):
                    st.info("詳細ページに移動します")

            with col2:
                if finding.get("auto_fixable"):
                    if st.button("自動修正", key=f"fix_{finding.get('id', hash(title))}"):
                        st.success("修正キューに追加しました")

            with col3:
                if st.button("無視", key=f"ignore_{finding.get('id', hash(title))}"):
                    st.warning("この脆弱性を無視リストに追加しました")


def create_alert_summary(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    アラートのサマリーを作成

    Args:
        findings: 脆弱性のリスト

    Returns:
        アラートサマリー
    """
    summary = {
        "total": len(findings),
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0,
        "auto_fixable": 0,
        "categories": {},
    }

    for finding in findings:
        severity = finding.get("severity", "MEDIUM").upper()
        category = finding.get("category", "その他")

        # 重要度別カウント
        if severity == "CRITICAL":
            summary["critical"] += 1
        elif severity == "HIGH":
            summary["high"] += 1
        elif severity == "MEDIUM":
            summary["medium"] += 1
        elif severity == "LOW":
            summary["low"] += 1
        else:
            summary["info"] += 1

        # 自動修正可能な項目
        if finding.get("auto_fixable", False):
            summary["auto_fixable"] += 1

        # カテゴリ別カウント
        if category not in summary["categories"]:
            summary["categories"][category] = 0
        summary["categories"][category] += 1

    return summary


def display_alert_timeline(alerts: List[Dict[str, Any]]) -> None:
    """
    アラートのタイムラインを表示

    Args:
        alerts: アラートのリスト（timestamp付き）
    """
    st.markdown("### 📅 アラートタイムライン")

    if not alerts:
        st.info("表示するアラートはありません")
        return

    # タイムスタンプでソート（新しい順）
    sorted_alerts = sorted(
        alerts,
        key=lambda x: x.get("timestamp", datetime.now().isoformat()),
        reverse=True,
    )

    for alert in sorted_alerts[:10]:  # 最新10件
        timestamp = alert.get("timestamp", datetime.now().isoformat())
        severity = alert.get("severity", "INFO")
        title = alert.get("title", "Unknown Alert")
        status = alert.get("status", "active")

        # ステータスアイコン
        status_icon = "🔴" if status == "active" else "✅"

        # タイムラインアイテムの表示
        col1, col2, col3 = st.columns([1, 3, 1])

        with col1:
            st.write(timestamp.split("T")[0])  # 日付のみ
            st.caption(timestamp.split("T")[1].split(".")[0])  # 時刻

        with col2:
            st.write(f"{status_icon} **{title}**")
            st.caption(f"重要度: {severity}")

        with col3:
            if status == "active":
                if st.button("対応", key=f"respond_{alert.get('id', hash(title))}"):
                    st.info("対応ページに移動します")


def create_alert_notification(
    title: str,
    message: str,
    notification_type: str = "info",
    actions: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """
    通知スタイルのアラートを作成

    Args:
        title: アラートのタイトル
        message: アラートメッセージ
        notification_type: 通知タイプ
        actions: アクションボタンのリスト
    """
    # カスタムHTML/CSSで通知を作成
    notification_html = f"""
    <div style="
        background-color: {'#e3f2fd' if notification_type == 'info' else '#ffebee'};
        border-left: 4px solid {'#2196f3' if notification_type == 'info' else '#f44336'};
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.25rem;
    ">
        <h4 style="margin: 0 0 0.5rem 0;">{title}</h4>
        <p style="margin: 0;">{message}</p>
    </div>
    """

    st.markdown(notification_html, unsafe_allow_html=True)

    # アクションボタン
    if actions:
        cols = st.columns(len(actions))
        for i, action in enumerate(actions):
            with cols[i]:
                if st.button(action["label"], key=action.get("key")):
                    action["callback"]()


def monitor_alert_conditions(
    data: Dict[str, Any],
    conditions: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    アラート条件を監視して、該当するアラートを生成

    Args:
        data: 監視対象のデータ
        conditions: アラート条件のリスト

    Returns:
        生成されたアラートのリスト
    """
    alerts = []

    for condition in conditions:
        # 条件の評価
        if evaluate_condition(data, condition):
            alert = {
                "id": f"alert_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "title": condition["title"],
                "message": condition["message"],
                "severity": condition["severity"],
                "condition": condition["condition"],
                "status": "active",
            }
            alerts.append(alert)

    return alerts


def evaluate_condition(data: Dict[str, Any], condition: Dict[str, Any]) -> bool:
    """
    アラート条件を評価

    Args:
        data: 評価対象のデータ
        condition: 評価条件

    Returns:
        条件に合致するかどうか
    """
    # シンプルな条件評価の実装例
    condition_type = condition.get("type", "threshold")
    field = condition.get("field")
    operator = condition.get("operator", "gt")
    value = condition.get("value")

    if condition_type == "threshold":
        actual_value = data.get(field)
        if actual_value is None:
            return False

        if operator == "gt":
            return actual_value > value
        elif operator == "gte":
            return actual_value >= value
        elif operator == "lt":
            return actual_value < value
        elif operator == "lte":
            return actual_value <= value
        elif operator == "eq":
            return actual_value == value
        elif operator == "ne":
            return actual_value != value

    return False