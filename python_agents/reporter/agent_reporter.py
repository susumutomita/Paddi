#!/usr/bin/env python3
"""
Agent C: Security Audit Report Generator

This agent reads the explained security findings and generates
human-readable audit reports in multiple formats.

This file provides backward compatibility for the original GCP-only reporter
while leveraging the new multi-cloud architecture.
"""

import json
import logging
from pathlib import Path
from typing import Optional

import fire

from .multi_cloud_reporter import MultiCloudReportService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(
    findings_file: str = "data/explained.json",
    collected_file: str = "data/collected.json",
    output_dir: str = "output",
    template_dir: Optional[str] = None,
    formats: str = "markdown,html",
    # Legacy parameters
    honkit: bool = False,
    honkit_dir: str = "honkit_docs",
):
    """
    Generate security audit reports from analyzed findings.
    
    Supports both legacy GCP-only format and new multi-cloud format.
    
    Args:
        findings_file: Path to the security findings from explainer
        collected_file: Path to the original collected data  
        output_dir: Directory to save generated reports
        template_dir: Directory containing report templates
        formats: Comma-separated list of output formats (markdown,html,honkit)
        honkit: Generate HonKit documentation structure (legacy)
        honkit_dir: Directory for HonKit documentation (legacy)
    """
    try:
        # Handle legacy honkit parameter
        if honkit and "honkit" not in formats:
            formats += ",honkit"
        
        # Use multi-cloud report service
        service = MultiCloudReportService(
            findings_file=findings_file,
            collected_file=collected_file,
            output_dir=output_dir,
            template_dir=template_dir,
        )
        
        # Load data to check format
        findings_data = service.load_findings()
        collected_data = service.load_collected_data()
        
        # Check if this is legacy GCP-only format
        is_legacy = ("iam_policies" in collected_data and "providers" not in collected_data) or \
                   (findings_data and "provider" not in findings_data[0])
        
        if is_legacy:
            logger.info("Detected legacy GCP-only format")
        
        # Parse requested formats
        requested_formats = [f.strip().lower() for f in formats.split(",")]
        
        # Generate standard reports
        markdown_path = None
        html_path = None
        
        if "markdown" in requested_formats:
            report = service.create_report(findings_data, collected_data)
            markdown_path = service.generate_markdown(report)
        
        if "html" in requested_formats:
            if not markdown_path:  # Avoid reloading if already loaded
                report = service.create_report(findings_data, collected_data)
            html_path = service.generate_html(report)
        
        # Handle HonKit format (legacy support)
        if "honkit" in requested_formats:
            if not markdown_path:
                report = service.create_report(findings_data, collected_data)
            
            # Create HonKit structure
            honkit_path = Path(honkit_dir)
            honkit_path.mkdir(exist_ok=True, parents=True)
            
            # Create SUMMARY.md
            summary_content = "# Summary\n\n* [Security Audit Report](README.md)\n"
            
            # Add chapters for each provider
            if len(report.providers) > 1:
                for provider in report.providers:
                    summary_content += f"  * [{provider.upper()} Findings]({provider}_findings.md)\n"
            else:
                # Legacy single provider
                summary_content += "  * [Security Findings](findings.md)\n"
            
            with open(honkit_path / "SUMMARY.md", "w") as f:
                f.write(summary_content)
            
            # Create README.md with overview
            readme_content = f"""# Security Audit Report

**Generated:** {report.audit_date}  
**Total Findings:** {report.total_findings}

## Overview

This security audit report contains findings from your {"multi-cloud" if len(report.providers) > 1 else "cloud"} infrastructure.

### Summary

"""
            for severity, count in sorted(report.severity_counts.items()):
                readme_content += f"- **{severity}**: {count} findings\n"
            
            with open(honkit_path / "README.md", "w") as f:
                f.write(readme_content)
            
            # Create findings pages
            if len(report.providers) > 1:
                # Multi-cloud: separate file per provider
                for provider in report.providers:
                    provider_findings = [f for f in report.findings if f.provider == provider]
                    if provider_findings:
                        content = f"# {provider.upper()} Security Findings\n\n"
                        for i, finding in enumerate(provider_findings, 1):
                            content += f"## {i}. {finding.title}\n\n"
                            content += f"**Severity:** {finding.severity}\n\n"
                            content += f"**Explanation:** {finding.explanation}\n\n"
                            content += f"**Recommendation:** {finding.recommendation}\n\n"
                            content += "---\n\n"
                        
                        with open(honkit_path / f"{provider}_findings.md", "w") as f:
                            f.write(content)
            else:
                # Legacy single provider
                content = "# Security Findings\n\n"
                for i, finding in enumerate(report.findings, 1):
                    content += f"## {i}. {finding.title}\n\n"
                    content += f"**Severity:** {finding.severity}\n\n"
                    content += f"**Explanation:** {finding.explanation}\n\n"
                    content += f"**Recommendation:** {finding.recommendation}\n\n"
                    content += "---\n\n"
                
                with open(honkit_path / "findings.md", "w") as f:
                    f.write(content)
            
            logger.info(f"HonKit documentation generated: {honkit_path}")
        
        print("✅ Reports generated successfully!")
        if markdown_path:
            print(f"📄 Markdown: {markdown_path}")
        if html_path:
            print(f"🌐 HTML: {html_path}")
        if "honkit" in requested_formats:
            print(f"📚 HonKit: {honkit_dir}/")
        
        # Show summary
        if is_legacy:
            # Legacy GCP summary
            print(f"\n📊 Report Summary:")
            print(f"   - Total Findings: {report.total_findings}")
            for severity, count in sorted(report.severity_counts.items()):
                print(f"   - {severity}: {count}")
        else:
            # Multi-cloud summary
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