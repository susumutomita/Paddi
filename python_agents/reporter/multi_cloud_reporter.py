#!/usr/bin/env python3
"""
Multi-Cloud Security Audit Report Generator

This agent reads the explained security findings from the multi-cloud explainer
and generates human-readable audit reports in multiple formats.
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import fire
from jinja2 import Environment, FileSystemLoader, select_autoescape

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MultiCloudSecurityFinding:
    """Data class representing a multi-cloud security finding."""
    title: str
    severity: str
    explanation: str
    recommendation: str
    provider: str
    resource: Optional[str] = None


@dataclass
class MultiCloudAuditReport:
    """Data class representing the complete multi-cloud audit report."""
    findings: List[MultiCloudSecurityFinding]
    audit_date: str
    total_findings: int
    severity_counts: Dict[str, int]
    providers: List[str]
    provider_summary: Dict[str, Dict[str, int]] = field(default_factory=dict)
    compliance_summary: Optional[Dict[str, Any]] = None
    cross_cloud_insights: Optional[str] = None
    project_name: Optional[str] = None  # For backward compatibility


class MultiCloudMarkdownGenerator:
    """Generates Markdown reports for multi-cloud findings."""

    def generate(self, report: MultiCloudAuditReport, template_path: Optional[Path] = None) -> str:
        """Generate Markdown report content."""
        if template_path and template_path.exists():
            return self._generate_from_template(report, template_path)
        
        # Use multi-cloud template by default
        templates_dir = Path(__file__).parent.parent / "templates"
        multi_cloud_template = templates_dir / "multi_cloud_report.md.j2"
        
        if multi_cloud_template.exists():
            return self._generate_from_template(report, multi_cloud_template)
        
        return self._generate_default(report)

    def _generate_default(self, report: MultiCloudAuditReport) -> str:
        """Generate default Markdown report."""
        lines = [
            "# Multi-Cloud Security Audit Report",
            "",
            f"**Audit Date:** {report.audit_date}",
            f"**Total Findings:** {report.total_findings}",
            f"**Cloud Providers:** {', '.join(report.providers)}",
            "",
            "## Executive Summary",
            "",
            f"This security audit identified {report.total_findings} findings across your multi-cloud infrastructure.",
            "",
            "### Severity Breakdown",
            "",
        ]

        for severity, count in sorted(report.severity_counts.items()):
            lines.append(f"- **{severity}**: {count} findings")

        lines.extend(["", "### Findings by Cloud Provider", ""])
        
        for provider, counts in report.provider_summary.items():
            lines.append(f"- **{provider.upper()}**: {counts['total']} findings")

        lines.extend(["", "## Detailed Findings", ""])

        # Group findings by provider
        for provider in report.providers:
            provider_findings = [f for f in report.findings if f.provider == provider]
            if provider_findings:
                lines.extend(["", f"### {provider.upper()} Findings", ""])
                
                for i, finding in enumerate(provider_findings, 1):
                    lines.extend([
                        f"#### {i}. {finding.title}",
                        "",
                        f"**Severity:** {finding.severity}",
                        f"**Provider:** {finding.provider.upper()}",
                    ])
                    
                    if finding.resource:
                        lines.append(f"**Resource:** {finding.resource}")
                    
                    lines.extend([
                        "",
                        f"**Explanation:** {finding.explanation}",
                        "",
                        f"**Recommendation:** {finding.recommendation}",
                        "",
                        "---",
                        "",
                    ])

        return "\n".join(lines)

    def _generate_from_template(self, report: MultiCloudAuditReport, template_path: Path) -> str:
        """Generate Markdown report from template."""
        env = Environment(
            loader=FileSystemLoader(template_path.parent),
            autoescape=select_autoescape(),
        )
        template = env.get_template(template_path.name)
        return template.render(report=report)


class MultiCloudHTMLGenerator:
    """Generates HTML reports for multi-cloud findings."""

    def generate(self, report: MultiCloudAuditReport, template_path: Optional[Path] = None) -> str:
        """Generate HTML report content."""
        return self._generate_default(report)

    def _generate_default(self, report: MultiCloudAuditReport) -> str:
        """Generate default HTML report with styling."""
        severity_colors = {
            "CRITICAL": "#D32F2F",
            "HIGH": "#F44336",
            "MEDIUM": "#FF9800",
            "LOW": "#FFC107",
            "INFO": "#2196F3",
        }
        
        provider_colors = {
            "gcp": "#4285F4",
            "aws": "#FF9900",
            "azure": "#0078D4",
        }

        # Generate provider summary rows
        provider_rows = ""
        for provider, counts in report.provider_summary.items():
            provider_rows += f"""
            <tr>
                <td style="font-weight: bold; color: {provider_colors.get(provider, '#333')}">{provider.upper()}</td>
                <td style="text-align: center">{counts['total']}</td>
                <td style="text-align: center; color: {severity_colors['HIGH']}">{counts.get('HIGH', 0)}</td>
                <td style="text-align: center; color: {severity_colors['MEDIUM']}">{counts.get('MEDIUM', 0)}</td>
                <td style="text-align: center; color: {severity_colors['LOW']}">{counts.get('LOW', 0)}</td>
            </tr>
            """

        # Generate findings by provider
        findings_html = ""
        for provider in report.providers:
            provider_findings = [f for f in report.findings if f.provider == provider]
            if provider_findings:
                findings_html += f"""
                <h2 style="color: {provider_colors.get(provider, '#333')}">{provider.upper()} Findings</h2>
                """
                
                for finding in provider_findings:
                    color = severity_colors.get(finding.severity, "#999")
                    findings_html += f"""
                    <div class="finding">
                        <h3>{finding.title}</h3>
                        <div class="metadata">
                            <span class="severity" style="background-color: {color}">{finding.severity}</span>
                            <span class="provider">{finding.provider.upper()}</span>
                            {f'<span class="resource">{finding.resource}</span>' if finding.resource else ''}
                        </div>
                        <div class="explanation">
                            <strong>Issue:</strong> {finding.explanation}
                        </div>
                        <div class="recommendation">
                            <strong>Recommendation:</strong> {finding.recommendation}
                        </div>
                    </div>
                    """

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Cloud Security Audit Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
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
            color: #1a237e;
            border-bottom: 3px solid #3f51b5;
            padding-bottom: 10px;
        }}
        h2 {{
            margin-top: 30px;
        }}
        .summary {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric {{
            background-color: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .metric-value {{
            font-size: 36px;
            font-weight: bold;
            color: #3f51b5;
        }}
        .metric-label {{
            color: #666;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: bold;
        }}
        .finding {{
            background-color: #f8f9fa;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            border-left: 4px solid #3f51b5;
        }}
        .finding h3 {{
            margin-top: 0;
            color: #1a237e;
        }}
        .metadata {{
            margin: 10px 0;
        }}
        .severity {{
            color: white;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            margin-right: 10px;
        }}
        .provider {{
            background-color: #e3f2fd;
            color: #1976d2;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            margin-right: 10px;
        }}
        .resource {{
            background-color: #f3e5f5;
            color: #7b1fa2;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
        }}
        .explanation, .recommendation {{
            margin: 15px 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Multi-Cloud Security Audit Report</h1>
        
        <div class="summary">
            <p><strong>Audit Date:</strong> {report.audit_date}</p>
            <p><strong>Cloud Providers Analyzed:</strong> {', '.join([p.upper() for p in report.providers])}</p>
        </div>

        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{report.total_findings}</div>
                <div class="metric-label">Total Findings</div>
            </div>
            <div class="metric">
                <div class="metric-value" style="color: {severity_colors['HIGH']}">{report.severity_counts.get('HIGH', 0)}</div>
                <div class="metric-label">High Severity</div>
            </div>
            <div class="metric">
                <div class="metric-value" style="color: {severity_colors['MEDIUM']}">{report.severity_counts.get('MEDIUM', 0)}</div>
                <div class="metric-label">Medium Severity</div>
            </div>
            <div class="metric">
                <div class="metric-value" style="color: {severity_colors['LOW']}">{report.severity_counts.get('LOW', 0)}</div>
                <div class="metric-label">Low Severity</div>
            </div>
        </div>

        <h2>Findings by Cloud Provider</h2>
        <table>
            <thead>
                <tr>
                    <th>Cloud Provider</th>
                    <th style="text-align: center">Total</th>
                    <th style="text-align: center">High</th>
                    <th style="text-align: center">Medium</th>
                    <th style="text-align: center">Low</th>
                </tr>
            </thead>
            <tbody>
                {provider_rows}
            </tbody>
        </table>

        {findings_html}

        <div class="footer">
            <p>Generated by Paddi - Multi-Agent Cloud Security Auditor</p>
            <p>Report Version: Multi-Cloud Support v1.0</p>
        </div>
    </div>
</body>
</html>"""

        return html


class MultiCloudReportService:
    """Main service for generating multi-cloud security audit reports."""

    def __init__(
        self,
        findings_file: str = "data/explained.json",
        collected_file: str = "data/collected.json",
        output_dir: str = "output",
        template_dir: Optional[str] = None,
    ):
        self.findings_file = Path(findings_file)
        self.collected_file = Path(collected_file)
        self.output_dir = Path(output_dir)
        self.template_dir = Path(template_dir) if template_dir else Path(__file__).parent.parent / "templates"
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize generators
        self.markdown_generator = MultiCloudMarkdownGenerator()
        self.html_generator = MultiCloudHTMLGenerator()

    def load_findings(self) -> List[Dict[str, Any]]:
        """Load security findings from the explainer output."""
        if not self.findings_file.exists():
            raise FileNotFoundError(f"Findings file not found: {self.findings_file}")
        
        with open(self.findings_file, "r") as f:
            return json.load(f)

    def load_collected_data(self) -> Dict[str, Any]:
        """Load original collected data for additional context."""
        if not self.collected_file.exists():
            logger.warning(f"Collected data file not found: {self.collected_file}")
            return {}
        
        with open(self.collected_file, "r") as f:
            return json.load(f)

    def create_report(self, findings_data: List[Dict[str, Any]], collected_data: Dict[str, Any]) -> MultiCloudAuditReport:
        """Create audit report from findings."""
        findings = []
        severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        providers = set()
        provider_summary = {}
        
        # Process findings
        for finding_dict in findings_data:
            # Handle both legacy and multi-cloud formats
            provider = finding_dict.get("provider", "gcp")  # Default to GCP for legacy
            
            finding = MultiCloudSecurityFinding(
                title=finding_dict["title"],
                severity=finding_dict["severity"],
                explanation=finding_dict["explanation"],
                recommendation=finding_dict["recommendation"],
                provider=provider,
                resource=finding_dict.get("resource")
            )
            findings.append(finding)
            
            # Update counts
            severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1
            providers.add(provider)
            
            # Update provider summary
            if provider not in provider_summary:
                provider_summary[provider] = {"total": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
            provider_summary[provider]["total"] += 1
            provider_summary[provider][finding.severity] += 1
        
        # Extract project name from collected data (for backward compatibility)
        project_name = None
        if "project_id" in collected_data:
            project_name = collected_data["project_id"]
        elif "providers" in collected_data and "gcp" in collected_data["providers"]:
            # Try to get from multi-cloud format
            gcp_data = collected_data["providers"]["gcp"]
            if "iam" in gcp_data and "policies" in gcp_data["iam"] and gcp_data["iam"]["policies"]:
                project_name = gcp_data["iam"]["policies"][0].get("resource", "Multi-Cloud")
        
        # Get compliance summary if available
        compliance_summary = None
        if "providers" in collected_data:
            compliance_summary = {}
            for provider, data in collected_data["providers"].items():
                if "security" in data and "compliance" in data["security"]:
                    compliance = data["security"]["compliance"]
                    for standard, info in compliance.get("standards", {}).items():
                        if standard not in compliance_summary:
                            compliance_summary[standard] = {}
                        compliance_summary[standard][provider] = f"{info.get('score', 0)*100:.0f}%"
        
        return MultiCloudAuditReport(
            findings=findings,
            audit_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_findings=len(findings),
            severity_counts=severity_counts,
            providers=sorted(list(providers)),
            provider_summary=provider_summary,
            compliance_summary=compliance_summary,
            project_name=project_name or "Multi-Cloud Infrastructure"
        )

    def generate_markdown(self, report: MultiCloudAuditReport) -> Path:
        """Generate Markdown report."""
        template_path = self.template_dir / "multi_cloud_report.md.j2"
        if not template_path.exists():
            template_path = self.template_dir / "report.md.j2"  # Fallback to legacy
        
        content = self.markdown_generator.generate(report, template_path)
        
        output_path = self.output_dir / "audit.md"
        with open(output_path, "w") as f:
            f.write(content)
        
        logger.info(f"Markdown report generated: {output_path}")
        return output_path

    def generate_html(self, report: MultiCloudAuditReport) -> Path:
        """Generate HTML report."""
        content = self.html_generator.generate(report)
        
        output_path = self.output_dir / "audit.html"
        with open(output_path, "w") as f:
            f.write(content)
        
        logger.info(f"HTML report generated: {output_path}")
        return output_path

    def generate_reports(self) -> tuple[Path, Path]:
        """Generate all report formats."""
        # Load data
        findings_data = self.load_findings()
        collected_data = self.load_collected_data()
        
        # Create report
        report = self.create_report(findings_data, collected_data)
        
        # Generate reports
        markdown_path = self.generate_markdown(report)
        html_path = self.generate_html(report)
        
        return markdown_path, html_path


def main(
    findings_file: str = "data/explained.json",
    collected_file: str = "data/collected.json",
    output_dir: str = "output",
    template_dir: Optional[str] = None,
    formats: str = "markdown,html",
):
    """
    Generate multi-cloud security audit reports from analyzed findings.
    
    Args:
        findings_file: Path to the security findings from explainer
        collected_file: Path to the original collected data
        output_dir: Directory to save generated reports
        template_dir: Directory containing report templates
        formats: Comma-separated list of output formats (markdown,html)
    """
    try:
        service = MultiCloudReportService(
            findings_file=findings_file,
            collected_file=collected_file,
            output_dir=output_dir,
            template_dir=template_dir,
        )
        
        # Parse requested formats
        requested_formats = [f.strip().lower() for f in formats.split(",")]
        
        markdown_path = None
        html_path = None
        
        if "markdown" in requested_formats:
            findings_data = service.load_findings()
            collected_data = service.load_collected_data()
            report = service.create_report(findings_data, collected_data)
            markdown_path = service.generate_markdown(report)
        
        if "html" in requested_formats:
            if not markdown_path:  # Avoid reloading if already loaded
                findings_data = service.load_findings()
                collected_data = service.load_collected_data()
                report = service.create_report(findings_data, collected_data)
            html_path = service.generate_html(report)
        
        print("✅ Reports generated successfully!")
        if markdown_path:
            print(f"📄 Markdown: {markdown_path}")
        if html_path:
            print(f"🌐 HTML: {html_path}")
        
        # Show summary
        total_providers = len(report.providers)
        print(f"\n📊 Report Summary:")
        print(f"   - Cloud Providers: {', '.join([p.upper() for p in report.providers])}")
        print(f"   - Total Findings: {report.total_findings}")
        print(f"   - High Severity: {report.severity_counts.get('HIGH', 0)}")
        print(f"   - Medium Severity: {report.severity_counts.get('MEDIUM', 0)}")
        print(f"   - Low Severity: {report.severity_counts.get('LOW', 0)}")
        
    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        logger.info("Please run the collector and explainer agents first.")
        raise
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise


if __name__ == "__main__":
    fire.Fire(main)