"""Enhanced prompt templates for security analysis with project context awareness."""
from typing import Dict, Any


ENHANCED_SECURITY_ANALYSIS_PROMPT = """
あなたはクラウドセキュリティとアプリケーションセキュリティの専門家です。
以下のデータを分析し、プロジェクトのコンテキストに基づいて実用的な推奨事項を提供してください。

## 分析対象データ

### インフラストラクチャセキュリティ（GCP）
{infrastructure_data}

### アプリケーションセキュリティ（GitHub Dependabot）
{application_data}

## プロジェクトコンテキスト
- プロジェクト名: {project_name}
- 環境: {environment}
- 公開設定: {exposure_level}
- 使用技術スタック: {tech_stack}
- プロジェクトタイプ: {project_type}
- 重要な資産: {critical_assets}

## 分析要件

1. **影響分析**
   - このプロジェクトの特性を考慮したリスク評価
   - ビジネスインパクトの具体的な説明

2. **分類と理由付け**
   - 要対応（Critical Action Required）
   - 影響軽微（Low Impact）
   - 対応不要（No Action Needed）

3. **具体的改善提案**
   - 修正コマンド
   - 設定ファイルの変更例
   - 実装コードスニペット

各脆弱性について、以下のJSON形式で出力してください：
{{
  "finding_id": "一意のID",
  "source": "検出元（例：GCP-IAM, GitHub-Dependabot）",
  "title": "脆弱性のタイトル",
  "severity": "HIGH/MEDIUM/LOW",
  "classification": "要対応/影響軽微/対応不要",
  "classification_reason": "分類の理由",
  "business_impact": "ビジネスへの影響の説明",
  "recommendation": {{
    "summary": "推奨事項の概要",
    "steps": [
      {{
        "order": 1,
        "action": "実施すべきアクション",
        "command": "実行コマンド（あれば）",
        "code_snippet": "コード例（あれば）",
        "validation": "検証方法"
      }}
    ],
    "estimated_time": "推定作業時間",
    "required_skills": ["必要なスキル"]
  }},
  "priority_score": 1-100の優先度スコア,
  "compliance_mapping": {{
    "cis_benchmark": "該当するCISベンチマーク",
    "iso_27001": "該当するISO 27001要件"
  }}
}}
"""


SYSTEM_PROMPT_ENHANCED = """
あなたは以下の専門知識を持つセキュリティエキスパートです：
- クラウドセキュリティ（AWS, Azure, GCP）
- アプリケーションセキュリティ
- コンプライアンスフレームワーク（CIS, ISO 27001, PCI-DSS）
- MITRE ATT&CKフレームワーク
- DevSecOpsのベストプラクティス

分析結果は常に実用的で、実装可能な推奨事項を含めてください。
"""


IAM_ANALYSIS_PROMPT_ENHANCED = """
以下のIAM設定を分析し、セキュリティリスクを評価してください。

## IAMポリシーデータ
{iam_data}

## プロジェクトコンテキスト
- 環境: {environment}
- 公開レベル: {exposure_level}
- チームサイズ: {team_size}

## 分析観点
1. 最小権限の原則の遵守状況
2. 権限の分離（SoD）の実装状況
3. サービスアカウントの管理状況
4. 外部アクセスのリスク
5. 権限昇格の可能性

各リスクについて、以下を含めて報告してください：
- リスクの詳細説明
- MITRE ATT&CKテクニックへのマッピング
- 具体的な修正コマンド（gcloud CLI）
- 修正後の検証方法
"""


DEPENDENCY_ANALYSIS_PROMPT = """
以下の依存関係の脆弱性を分析してください。

## 脆弱性データ
{vulnerability_data}

## プロジェクト情報
- 言語/フレームワーク: {tech_stack}
- 公開設定: {exposure_level}
- デプロイ環境: {environment}

## 分析要件
1. 各脆弱性の実際の影響度（プロジェクト固有）
2. 悪用可能性の評価
3. 修正の優先順位
4. 代替ソリューションの提案

出力には以下を含めてください：
- CVE番号とCVSSスコア
- 実際の影響（このプロジェクトにおいて）
- 修正コマンド（npm/yarn/pip等）
- 一時的な緩和策
"""


MULTI_CLOUD_ANALYSIS_PROMPT = """
複数のクラウドプロバイダーにまたがるセキュリティ設定を分析してください。

## クラウド環境
{cloud_providers}

## セキュリティ設定
{security_configs}

## 分析ポイント
1. クロスクラウドのアクセス管理
2. データ転送のセキュリティ
3. 統一的なセキュリティポリシーの適用
4. コンプライアンス要件の充足

各プロバイダー固有のツールとコマンドを使用した推奨事項を提供してください。
"""


def get_enhanced_prompt(
    prompt_type: str,
    context: Dict[str, Any],
    data: Dict[str, Any]
) -> str:
    """
    Get an enhanced prompt with project context.
    
    Args:
        prompt_type: Type of prompt (security_analysis, iam_analysis, etc.)
        context: Project context information
        data: Security data to analyze
        
    Returns:
        Formatted prompt string
    """
    prompt_templates = {
        "security_analysis": ENHANCED_SECURITY_ANALYSIS_PROMPT,
        "iam_analysis": IAM_ANALYSIS_PROMPT_ENHANCED,
        "dependency_analysis": DEPENDENCY_ANALYSIS_PROMPT,
        "multi_cloud": MULTI_CLOUD_ANALYSIS_PROMPT,
    }
    
    template = prompt_templates.get(prompt_type, ENHANCED_SECURITY_ANALYSIS_PROMPT)
    
    # Merge context and data for formatting
    format_data = {**context, **data}
    
    # Handle missing keys gracefully
    for key in ["project_name", "environment", "exposure_level", "tech_stack",
                "project_type", "critical_assets", "team_size"]:
        if key not in format_data:
            format_data[key] = "不明"
    
    return template.format(**format_data)


def build_analysis_prompt(
    infrastructure_findings: list,
    application_findings: list,
    project_context: Dict[str, Any]
) -> str:
    """
    Build a comprehensive analysis prompt combining all security findings.
    
    Args:
        infrastructure_findings: List of infrastructure security findings
        application_findings: List of application security findings
        project_context: Project context information
        
    Returns:
        Complete analysis prompt
    """
    # Convert findings to structured text
    infra_text = "\n".join([
        f"- {f.get('title', '不明')}: {f.get('description', '')}"
        for f in infrastructure_findings
    ])
    
    app_text = "\n".join([
        f"- {f.get('title', '不明')}: {f.get('description', '')}"
        for f in application_findings
    ])
    
    return get_enhanced_prompt(
        "security_analysis",
        project_context,
        {
            "infrastructure_data": infra_text or "なし",
            "application_data": app_text or "なし"
        }
    )