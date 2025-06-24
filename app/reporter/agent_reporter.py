"""Agent C: Security Audit Report Generator.

This agent reads the explained security findings from Agent B and generates
human-readable audit reports in Markdown and HTML formats.
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import fire
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.common.models import SecurityFinding

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AuditReport:
    """Data class representing the complete audit report."""

    findings: List[SecurityFinding]
    project_name: str
    audit_date: str
    total_findings: int
    severity_counts: Dict[str, int]
    providers: Optional[List[str]] = None
    provider_distribution: Optional[Dict[str, int]] = None


class ReportGenerator(ABC):
    """Abstract base class for report generators."""

    @abstractmethod
    def generate(self, report: AuditReport, template_path: Optional[Path] = None) -> str:
        """Generate report content."""


class MarkdownGenerator(ReportGenerator):
    """Generates Markdown reports."""

    def generate(self, report: AuditReport, template_path: Optional[Path] = None) -> str:
        """Generate Markdown report content."""
        if template_path:
            return self._generate_from_template(report, template_path)
        return self._generate_default(report)

    def _generate_default(self, report: AuditReport) -> str:
        """Generate default Markdown report."""
        lines = [
            f"# Security Audit Report - {report.project_name}",
            "",
            f"**Audit Date:** {report.audit_date}",
            f"**Total Findings:** {report.total_findings}",
            "",
            "## Executive Summary",
            "",
            (
                f"This security audit identified {report.total_findings} findings "
                f"across your "
                f"{'multi-cloud' if report.providers and len(report.providers) > 1 else 'cloud'} "
                f"infrastructure."
            ),
            "",
            "### Severity Breakdown",
            "",
        ]

        for severity, count in sorted(report.severity_counts.items()):
            lines.append(f"- **{severity}**: {count} findings")

        if report.providers and len(report.providers) > 1:
            lines.extend(["", "### Provider Distribution", ""])
            for provider, count in sorted(report.provider_distribution.items()):
                lines.append(f"- **{provider.upper()}**: {count} findings")

        lines.extend(["", "## Detailed Findings", ""])

        for i, finding in enumerate(report.findings, 1):
            lines.extend(
                [
                    f"### {i}. {finding.title}",
                    "",
                    f"**Severity:** {finding.severity}",
                    "",
                    f"**Explanation:** {finding.explanation}",
                    "",
                    f"**Recommendation:** {finding.recommendation}",
                    "",
                    "---",
                    "",
                ]
            )

        return "\n".join(lines)

    def _generate_from_template(self, report: AuditReport, template_path: Path) -> str:
        """Generate Markdown report from template."""
        env = Environment(
            loader=FileSystemLoader(template_path.parent),
            autoescape=select_autoescape(),
        )
        template = env.get_template(template_path.name)
        return template.render(report=report)


class HTMLGenerator(ReportGenerator):
    """Generates HTML reports."""

    def generate(self, report: AuditReport, template_path: Optional[Path] = None) -> str:
        """Generate HTML report content."""
        if template_path:
            return self._generate_from_template(report, template_path)
        return self._generate_default(report)

    def _generate_default(self, report: AuditReport) -> str:
        """Generate default HTML report with styling."""
        severity_colors = {
            "CRITICAL": "#D32F2F",
            "HIGH": "#F44336",
            "MEDIUM": "#FF9800",
            "LOW": "#FFC107",
            "INFO": "#2196F3",
        }

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Audit Report - {report.project_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1a73e8;
            border-bottom: 3px solid #1a73e8;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #202124;
            margin-top: 30px;
        }}
        h3 {{
            color: #5f6368;
        }}
        .metadata {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
        .severity-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            color: white;
            font-weight: bold;
            font-size: 14px;
        }}
        .finding {{
            background-color: #f8f9fa;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            border-left: 4px solid #e0e0e0;
        }}
        .finding-critical {{ border-left-color: #D32F2F; }}
        .finding-high {{ border-left-color: #F44336; }}
        .finding-medium {{ border-left-color: #FF9800; }}
        .finding-low {{ border-left-color: #FFC107; }}
        .finding-info {{ border-left-color: #2196F3; }}
        .recommendation {{
            background-color: #e8f5e9;
            padding: 15px;
            border-radius: 5px;
            margin-top: 10px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .summary-card {{
            text-align: center;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
        }}
        .summary-card h4 {{
            margin: 0;
            color: #5f6368;
        }}
        .summary-card .count {{
            font-size: 32px;
            font-weight: bold;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Security Audit Report - {report.project_name}</h1>

        <div class="metadata">
            <strong>Audit Date:</strong> {report.audit_date}<br>
            <strong>Total Findings:</strong> {report.total_findings}
        </div>

        <h2>Executive Summary</h2>
        <p>This security audit identified {report.total_findings} findings
        across your GCP infrastructure.</p>

        <h3>Severity Breakdown</h3>
        <div class="summary-grid">
"""

        for severity, count in sorted(report.severity_counts.items()):
            color = severity_colors.get(severity, "#9E9E9E")
            html += f"""
            <div class="summary-card">
                <h4>{severity}</h4>
                <div class="count" style="color: {color};">{count}</div>
            </div>
"""

        html += """
        </div>

        <h2>Detailed Findings</h2>
"""

        for i, finding in enumerate(report.findings, 1):
            severity_class = f"finding-{finding.severity.lower()}"
            badge_color = severity_colors.get(finding.severity, "#9E9E9E")
            html += f"""
        <div class="finding {severity_class}">
            <h3>{i}. {finding.title}</h3>
            <p><span class="severity-badge"
            style="background-color: {badge_color};">{finding.severity}</span></p>
            <p><strong>Explanation:</strong> {finding.explanation}</p>
            <div class="recommendation">
                <strong>Recommendation:</strong> {finding.recommendation}
            </div>
        </div>
"""

        html += """
    </div>
</body>
</html>"""
        return html

    def _generate_from_template(self, report: AuditReport, template_path: Path) -> str:
        """Generate HTML report from template."""
        env = Environment(
            loader=FileSystemLoader(template_path.parent),
            autoescape=select_autoescape(["html", "xml"]),
        )
        template = env.get_template(template_path.name)
        return template.render(report=report)


class HonKitGenerator(ReportGenerator):
    """Generates HonKit documentation structure."""

    def __init__(self, output_dir: Path):
        """Initialize HonKitReportGenerator with output directory."""
        self.output_dir = output_dir / "docs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, report: AuditReport, template_path: Optional[Path] = None) -> str:
        """Generate HonKit documentation structure."""
        # Create README.md (main page)
        readme_content = self._generate_readme(report)
        with open(self.output_dir / "README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)

        # Create SUMMARY.md (table of contents)
        summary_content = self._generate_summary(report)
        with open(self.output_dir / "SUMMARY.md", "w", encoding="utf-8") as f:
            f.write(summary_content)

        # Create individual pages for each severity level
        self._generate_severity_pages(report)

        # Create book.json for HonKit configuration
        book_config = {
            "title": f"Security Audit Report - {report.project_name}",
            "author": "Paddi Security Audit Tool",
            "description": "Automated security audit report for GCP infrastructure",
            "language": "ja",
            "plugins": ["theme-default", "search", "sharing"],
            "pluginsConfig": {"theme-default": {"showLevel": True}},
        }
        with open(self.output_dir / "book.json", "w", encoding="utf-8") as f:
            json.dump(book_config, f, indent=2)

        return str(self.output_dir)

    def _generate_readme(self, report: AuditReport) -> str:
        """Generate main README.md page."""
        return f"""# Security Audit Report - {report.project_name}

## 概要

**監査日:** {report.audit_date}
**総検出数:** {report.total_findings}

このセキュリティ監査レポートは、Paddiを使用してGCPインフラストラクチャの自動セキュリティ分析を実行した結果です。

## エグゼクティブサマリー

このセキュリティ監査では、GCPインフラストラクチャ全体で{report.total_findings}件の問題を特定しました。

### 重要度別の内訳

| 重要度 | 検出数 | 説明 |
|--------|--------|------|
| CRITICAL | {report.severity_counts.get('CRITICAL', 0)} | 即座の対応が必要な重大なセキュリティリスク |
| HIGH | {report.severity_counts.get('HIGH', 0)} | 早急な対応が推奨される高リスクの問題 |
| MEDIUM | {report.severity_counts.get('MEDIUM', 0)} | 計画的な対応が必要な中程度のリスク |
| LOW | {report.severity_counts.get('LOW', 0)} | 改善が推奨される低リスクの問題 |

## レポートの構成

このレポートは重要度別に整理されています。各セクションでは、検出された問題の詳細な説明と推奨される対策を提供しています。

## 次のステップ

1. **CRITICAL**および**HIGH**の問題から優先的に対処してください
2. 各推奨事項を実装する際は、変更による影響を慎重に評価してください
3. 修正後は再度監査を実行して、問題が解決されたことを確認してください

---

*このレポートは[Paddi](https://github.com/susumutomita/Paddi)によって自動生成されました。*
"""

    def _generate_summary(self, report: AuditReport) -> str:
        """Generate SUMMARY.md for HonKit."""
        lines = [
            "# Summary",
            "",
            "* [はじめに](README.md)",
            "",
            "## 重要度別の検出事項",
            "",
        ]

        severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        for severity in severity_order:
            if report.severity_counts.get(severity, 0) > 0:
                lines.append(f"* [{severity}レベルの問題]({severity.lower()}.md)")

        lines.extend(
            [
                "",
                "## 付録",
                "",
                "* [監査方法について](methodology.md)",
                "* [用語集](glossary.md)",
            ]
        )

        return "\n".join(lines)

    def _generate_severity_pages(self, report: AuditReport) -> None:
        """Generate individual pages for each severity level."""
        findings_by_severity = {}
        for finding in report.findings:
            if finding.severity not in findings_by_severity:
                findings_by_severity[finding.severity] = []
            findings_by_severity[finding.severity].append(finding)

        for severity, findings in findings_by_severity.items():
            content = self._generate_severity_page(severity, findings)
            with open(self.output_dir / f"{severity.lower()}.md", "w", encoding="utf-8") as f:
                f.write(content)

        # Generate methodology page
        methodology = """# 監査方法について

## 監査プロセス

1. **データ収集**: GCP APIを使用してIAMポリシーとSecurity Command Centerの検出事項を収集
2. **AI分析**: Gemini AIを使用してセキュリティリスクを分析
3. **レポート生成**: 検出事項を重要度別に整理し、推奨事項を提供

## 重要度の定義

- **CRITICAL**: 即座の対応が必要な重大なセキュリティリスク
- **HIGH**: 早急な対応が推奨される高リスクの問題
- **MEDIUM**: 計画的な対応が必要な中程度のリスク
- **LOW**: 改善が推奨される低リスクの問題
"""
        with open(self.output_dir / "methodology.md", "w", encoding="utf-8") as f:
            f.write(methodology)

        # Generate glossary page
        glossary = """# 用語集

## IAM (Identity and Access Management)
Google Cloudのアクセス管理サービス。ユーザー、グループ、サービスアカウントに対する権限を管理します。

## Security Command Center (SCC)
Google Cloudのセキュリティおよびリスク管理プラットフォーム。セキュリティの脅威を検出し、対処するための中央管理ツールです。

## 最小権限の原則
ユーザーやサービスアカウントには、タスクを実行するために必要な最小限の権限のみを付与するというセキュリティの基本原則。

## サービスアカウント
アプリケーションやVMインスタンスが使用するGoogle Cloudのアカウント。人間のユーザーではなく、サービス間の認証に使用されます。
"""
        with open(self.output_dir / "glossary.md", "w", encoding="utf-8") as f:
            f.write(glossary)

    def _generate_severity_page(self, severity: str, findings: List[SecurityFinding]) -> str:
        """Generate a page for a specific severity level."""
        severity_descriptions = {
            "CRITICAL": "これらの問題は、システムに重大なセキュリティリスクをもたらし、即座の対応が必要です。",
            "HIGH": "これらの問題は高いセキュリティリスクを示しており、早急な対応が推奨されます。",
            "MEDIUM": "これらの問題は中程度のリスクを示しており、計画的な対応が必要です。",
            "LOW": "これらの問題は低リスクですが、セキュリティ体制の改善のために対処することが推奨されます。",
        }

        lines = [
            f"# {severity}レベルの問題",
            "",
            severity_descriptions.get(severity, ""),
            "",
            f"**検出数:** {len(findings)}",
            "",
            "---",
            "",
        ]

        for i, finding in enumerate(findings, 1):
            lines.extend(
                [
                    f"## {i}. {finding.title}",
                    "",
                    "### 説明",
                    finding.explanation,
                    "",
                    "### 推奨事項",
                    finding.recommendation,
                    "",
                    "---",
                    "",
                ]
            )

        return "\n".join(lines)


class ReportService:
    """Service class for generating reports."""

    def __init__(
        self,
        input_dir: Path = Path("data"),
        output_dir: Path = Path("output"),
        template_dir: Optional[Path] = None,
    ):
        """Initialize ReportService with directories."""
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.template_dir = template_dir
        self.output_dir.mkdir(exist_ok=True)

    def load_findings(self) -> List[Dict[str, Any]]:
        """Load security findings from explained.json."""
        explained_file = self.input_dir / "explained.json"
        if not explained_file.exists():
            logger.error("Input file not found: %s", explained_file)
            return []

        with open(explained_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_metadata(self) -> Dict[str, Any]:
        """Load project metadata from collected.json."""
        collected_file = self.input_dir / "collected.json"
        if not collected_file.exists():
            logger.warning("Metadata file not found: %s", collected_file)
            return {"project_id": "unknown-project"}

        with open(collected_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Handle multi-cloud data structure
            if "providers" in data:
                providers = []
                project_names = []
                for provider_data in data.get("providers", []):
                    provider_name = provider_data.get("provider", "unknown")
                    providers.append(provider_name)
                    if provider_name == "gcp":
                        project_names.append(provider_data.get("project_id", "unknown"))
                    elif provider_name == "aws":
                        project_names.append(provider_data.get("account_id", "unknown"))
                    elif provider_name == "azure":
                        project_names.append(provider_data.get("subscription_id", "unknown"))

                return {
                    "project_id": " / ".join(project_names) if project_names else "Multi-Cloud",
                    "providers": providers,
                    "multi_cloud": True,
                }
            # Handle single provider (backward compatibility)
            return data.get("metadata", {"project_id": "unknown-project"})

    def create_report(
        self, findings_data: List[Dict[str, Any]], metadata: Dict[str, Any]
    ) -> AuditReport:
        """Create AuditReport from raw data."""
        findings = [
            SecurityFinding(
                title=f.get("title", "Unknown Issue"),
                severity=f.get("severity", "INFO"),
                explanation=f.get("explanation", "No explanation provided"),
                recommendation=f.get("recommendation", "No recommendation provided"),
            )
            for f in findings_data
        ]

        severity_counts = {}
        provider_distribution = {}

        # Count findings by severity and provider (if multi-cloud)
        for i, finding in enumerate(findings):
            severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1

            # For multi-cloud, track provider distribution
            if metadata.get("multi_cloud") and metadata.get("providers"):
                # Simple heuristic: distribute findings across providers
                # In real implementation, findings would have provider metadata
                provider_idx = i % len(metadata["providers"])
                provider = metadata["providers"][provider_idx]
                provider_distribution[provider] = provider_distribution.get(provider, 0) + 1

        return AuditReport(
            findings=findings,
            project_name=metadata.get("project_id", "Unknown Project"),
            audit_date=datetime.now().strftime("%Y-%m-%d"),
            total_findings=len(findings),
            severity_counts=severity_counts,
            providers=metadata.get("providers"),
            provider_distribution=provider_distribution if metadata.get("multi_cloud") else None,
        )

    def generate_reports(self, formats: Optional[List[str]] = None):
        """Generate reports in specified formats.

        Args:
            formats: List of formats to generate. Defaults to ["markdown", "html"].
                    Supported formats: "markdown", "html", "honkit"
        """
        if formats is None:
            formats = ["markdown", "html"]

        findings_data = self.load_findings()
        if not findings_data:
            logger.warning("No findings to report")
            return

        metadata = self.load_metadata()
        report = self.create_report(findings_data, metadata)

        # Generate Markdown report
        if "markdown" in formats:
            md_generator = MarkdownGenerator()
            md_template = None
            if self.template_dir:
                md_template_path = self.template_dir / "report.md.j2"
                if md_template_path.exists():
                    md_template = md_template_path

            md_content = md_generator.generate(report, md_template)
            md_output = self.output_dir / "audit.md"
            with open(md_output, "w", encoding="utf-8") as f:
                f.write(md_content)
            logger.info("Markdown report generated: %s", md_output)

        # Generate HTML report
        if "html" in formats:
            html_generator = HTMLGenerator()
            html_template = None
            if self.template_dir:
                html_template_path = self.template_dir / "report.html.j2"
                if html_template_path.exists():
                    html_template = html_template_path

            html_content = html_generator.generate(report, html_template)
            html_output = self.output_dir / "audit.html"
            with open(html_output, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info("HTML report generated: %s", html_output)

        # Generate HonKit documentation
        if "honkit" in formats:
            honkit_generator = HonKitGenerator(self.output_dir.parent)
            docs_dir = honkit_generator.generate(report)
            logger.info("HonKit documentation generated: %s", docs_dir)


def main(
    input_dir: str = "data",
    output_dir: str = "output",
    template_dir: Optional[str] = "app/templates",
    formats: Optional[List[str]] = None,
):
    """Generate security audit reports from explained findings.

    Args:
        input_dir: Directory containing explained.json
        output_dir: Directory to save generated reports
        template_dir: Optional directory containing custom templates
        formats: List of formats to generate (markdown, html, honkit)
    """
    service = ReportService(
        input_dir=Path(input_dir),
        output_dir=Path(output_dir),
        template_dir=Path(template_dir) if template_dir else None,
    )
    service.generate_reports(formats)


if __name__ == "__main__":
    fire.Fire(main)
