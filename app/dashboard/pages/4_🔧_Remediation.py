"""
修正ページ - 脆弱性の自動修正と管理
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime
import json

st.set_page_config(
    page_title="Remediation - Paddi Security Dashboard",
    page_icon="🔧",
    layout="wide",
)

st.title("🔧 自動修正")
st.markdown("検出された脆弱性の自動修正と管理")

# セッション状態の初期化
if "remediation_queue" not in st.session_state:
    st.session_state.remediation_queue = []
if "remediation_history" not in st.session_state:
    st.session_state.remediation_history = []

# ダミーの脆弱性データ
vulnerabilities = [
    {
        "id": "VUL-001",
        "title": "過剰な権限を持つIAMロール",
        "severity": "HIGH",
        "category": "IAM",
        "resource": "role/admin-role",
        "auto_fixable": True,
        "fix_script": "gcloud iam roles update admin-role --remove-permissions=compute.instances.delete",
        "estimated_time": 2,
    },
    {
        "id": "VUL-002",
        "title": "公開されたストレージバケット",
        "severity": "HIGH",
        "category": "ストレージ",
        "resource": "gs://public-data-bucket",
        "auto_fixable": True,
        "fix_script": "gsutil iam ch -d allUsers gs://public-data-bucket",
        "estimated_time": 1,
    },
    {
        "id": "VUL-003",
        "title": "暗号化されていないデータベース",
        "severity": "MEDIUM",
        "category": "暗号化",
        "resource": "cloudsql/production-db",
        "auto_fixable": True,
        "fix_script": "gcloud sql instances patch production-db --require-ssl",
        "estimated_time": 5,
    },
    {
        "id": "VUL-004",
        "title": "古いAPIキーの使用",
        "severity": "MEDIUM",
        "category": "認証",
        "resource": "apikey/old-api-key-123",
        "auto_fixable": False,
        "fix_script": None,
        "estimated_time": None,
    },
    {
        "id": "VUL-005",
        "title": "監査ログの無効化",
        "severity": "LOW",
        "category": "ログ",
        "resource": "logging/audit-config",
        "auto_fixable": True,
        "fix_script": "gcloud logging sinks create audit-sink logging.googleapis.com/projects/my-project/logs/cloudaudit.googleapis.com",
        "estimated_time": 1,
    },
]

# タブ
tab1, tab2, tab3, tab4 = st.tabs(
    ["🎯 修正対象", "⚡ 自動修正", "📜 修正履歴", "⚙️ 設定"]
)

with tab1:
    st.markdown("### 修正対象の脆弱性")

    # フィルター
    col1, col2, col3 = st.columns(3)

    with col1:
        severity_filter = st.multiselect(
            "重要度",
            ["HIGH", "MEDIUM", "LOW"],
            default=["HIGH", "MEDIUM", "LOW"],
        )

    with col2:
        category_filter = st.multiselect(
            "カテゴリ",
            ["IAM", "ストレージ", "暗号化", "認証", "ログ"],
            default=["IAM", "ストレージ", "暗号化", "認証", "ログ"],
        )

    with col3:
        auto_fixable_only = st.checkbox("自動修正可能なもののみ表示", value=False)

    # フィルタリング
    filtered_vulns = [
        v
        for v in vulnerabilities
        if v["severity"] in severity_filter
        and v["category"] in category_filter
        and (not auto_fixable_only or v["auto_fixable"])
    ]

    # 一括選択
    select_all = st.checkbox("すべて選択")

    # 脆弱性リスト
    for vuln in filtered_vulns:
        col1, col2, col3, col4, col5 = st.columns([0.5, 3, 1, 1, 1])

        with col1:
            selected = st.checkbox(
                "選択",
                key=f"select_{vuln['id']}",
                value=select_all,
            )

        with col2:
            severity_color = {
                "HIGH": "🔴",
                "MEDIUM": "🟡",
                "LOW": "🟢",
            }[vuln["severity"]]

            st.write(f"{severity_color} **{vuln['title']}**")
            st.caption(f"リソース: {vuln['resource']}")

        with col3:
            st.write(f"カテゴリ: {vuln['category']}")

        with col4:
            if vuln["auto_fixable"]:
                st.success("自動修正可能")
            else:
                st.warning("手動修正必要")

        with col5:
            if vuln["auto_fixable"]:
                if st.button("修正を追加", key=f"add_{vuln['id']}"):
                    if vuln not in st.session_state.remediation_queue:
                        st.session_state.remediation_queue.append(vuln)
                        st.success("修正キューに追加しました")

    # 一括アクション
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("選択した項目を修正キューに追加", type="primary"):
            added = 0
            for vuln in filtered_vulns:
                if st.session_state.get(f"select_{vuln['id']}", False) and vuln["auto_fixable"]:
                    if vuln not in st.session_state.remediation_queue:
                        st.session_state.remediation_queue.append(vuln)
                        added += 1
            if added > 0:
                st.success(f"{added}件の項目を修正キューに追加しました")

with tab2:
    st.markdown("### ⚡ 自動修正の実行")

    # 修正キュー
    st.markdown("#### 修正キュー")

    if st.session_state.remediation_queue:
        total_time = sum(v["estimated_time"] for v in st.session_state.remediation_queue)
        st.info(f"キュー内の項目: {len(st.session_state.remediation_queue)}件 | 推定所要時間: {total_time}分")

        for i, vuln in enumerate(st.session_state.remediation_queue):
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.write(f"{i+1}. {vuln['title']}")
                st.caption(f"推定時間: {vuln['estimated_time']}分")

            with col2:
                st.write(f"重要度: {vuln['severity']}")

            with col3:
                if st.button("削除", key=f"remove_{vuln['id']}"):
                    st.session_state.remediation_queue.remove(vuln)
                    st.rerun()

        # 実行ボタン
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button("🚀 修正を開始", type="primary", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()

                for i, vuln in enumerate(st.session_state.remediation_queue):
                    progress = (i + 1) / len(st.session_state.remediation_queue)
                    progress_bar.progress(progress)
                    status_text.text(f"修正中: {vuln['title']} ({i+1}/{len(st.session_state.remediation_queue)})")

                    # 修正のシミュレーション
                    time.sleep(1)

                    # 履歴に追加
                    st.session_state.remediation_history.append(
                        {
                            **vuln,
                            "fixed_at": datetime.now().isoformat(),
                            "status": "成功",
                        }
                    )

                st.session_state.remediation_queue = []
                st.success("✅ すべての修正が完了しました！")
                st.balloons()

        with col2:
            if st.button("🗑️ キューをクリア", use_container_width=True):
                st.session_state.remediation_queue = []
                st.rerun()

    else:
        st.info("修正キューは空です。修正対象タブから脆弱性を追加してください。")

    # 修正スクリプトのプレビュー
    st.markdown("#### 修正スクリプトのプレビュー")

    if st.session_state.remediation_queue:
        with st.expander("実行予定のスクリプトを表示"):
            for vuln in st.session_state.remediation_queue:
                st.code(vuln["fix_script"], language="bash")

with tab3:
    st.markdown("### 📜 修正履歴")

    if st.session_state.remediation_history:
        # 統計
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("総修正数", len(st.session_state.remediation_history))

        with col2:
            success_count = sum(1 for h in st.session_state.remediation_history if h["status"] == "成功")
            st.metric("成功率", f"{(success_count / len(st.session_state.remediation_history)) * 100:.1f}%")

        with col3:
            total_time_saved = sum(h["estimated_time"] for h in st.session_state.remediation_history)
            st.metric("節約時間", f"{total_time_saved}分")

        with col4:
            if st.button("履歴をクリア"):
                st.session_state.remediation_history = []
                st.rerun()

        # 履歴テーブル
        history_df = pd.DataFrame(
            [
                {
                    "修正日時": h["fixed_at"],
                    "タイトル": h["title"],
                    "重要度": h["severity"],
                    "カテゴリ": h["category"],
                    "ステータス": h["status"],
                }
                for h in st.session_state.remediation_history
            ]
        )

        st.dataframe(history_df, use_container_width=True, hide_index=True)

        # エクスポート
        if st.button("📥 履歴をダウンロード"):
            csv = history_df.to_csv(index=False, encoding="utf-8")
            st.download_button(
                label="CSVダウンロード",
                data=csv,
                file_name=f"remediation_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )

    else:
        st.info("修正履歴はまだありません。")

with tab4:
    st.markdown("### ⚙️ 自動修正の設定")

    # 基本設定
    st.markdown("#### 基本設定")

    col1, col2 = st.columns(2)

    with col1:
        dry_run_mode = st.checkbox(
            "ドライランモード",
            value=True,
            help="実際の修正を行わず、シミュレーションのみ実行します",
        )

        require_approval = st.checkbox(
            "修正前に承認を要求",
            value=True,
            help="各修正の実行前に確認プロンプトを表示します",
        )

        parallel_execution = st.checkbox(
            "並列実行",
            value=False,
            help="複数の修正を同時に実行します（高速ですがリスクがあります）",
        )

    with col2:
        max_parallel = st.number_input(
            "最大並列数",
            min_value=1,
            max_value=10,
            value=3,
            disabled=not parallel_execution,
        )

        timeout_minutes = st.number_input(
            "タイムアウト（分）",
            min_value=1,
            max_value=60,
            value=10,
        )

    # 通知設定
    st.markdown("#### 通知設定")

    notification_enabled = st.checkbox("修正完了時に通知を送信")

    if notification_enabled:
        col1, col2 = st.columns(2)

        with col1:
            notification_method = st.selectbox(
                "通知方法",
                ["メール", "Slack", "Webhook"],
            )

        with col2:
            if notification_method == "メール":
                notification_target = st.text_input("通知先メールアドレス")
            elif notification_method == "Slack":
                notification_target = st.text_input("Slack Webhook URL")
            else:
                notification_target = st.text_input("Webhook URL")

    # ポリシー設定
    st.markdown("#### 修正ポリシー")

    st.info(
        """
        以下の条件に基づいて自動修正の実行を制御できます：
        """
    )

    col1, col2 = st.columns(2)

    with col1:
        auto_fix_high = st.checkbox("高リスクの自動修正を許可", value=False)
        auto_fix_medium = st.checkbox("中リスクの自動修正を許可", value=True)
        auto_fix_low = st.checkbox("低リスクの自動修正を許可", value=True)

    with col2:
        business_hours_only = st.checkbox(
            "営業時間内のみ実行",
            value=True,
            help="9:00-18:00の間のみ自動修正を実行します",
        )

        max_daily_fixes = st.number_input(
            "1日の最大修正数",
            min_value=0,
            max_value=1000,
            value=100,
            help="0で無制限",
        )

    # 設定の保存
    if st.button("設定を保存", type="primary"):
        st.success("✅ 設定が保存されました")