#!/usr/bin/env python3
"""
Example script demonstrating multi-cloud security audit workflow.

This script shows how to:
1. Collect configurations from multiple cloud providers
2. Analyze them for security risks using Gemini
3. Generate comprehensive audit reports
"""

import json
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_multi_cloud_audit():
    """Run a complete multi-cloud security audit."""
    
    # Define cloud providers to audit
    providers = [
        {
            "provider": "gcp",
            "project_id": "example-gcp-project"
        },
        {
            "provider": "aws",
            "account_id": "123456789012",
            "region": "us-east-1"
        },
        {
            "provider": "azure",
            "subscription_id": "00000000-0000-0000-0000-000000000000"
        }
    ]
    
    print("🚀 Starting Multi-Cloud Security Audit")
    print(f"   Providers: GCP, AWS, Azure")
    print()
    
    # Step 1: Collect cloud configurations
    print("📥 Step 1: Collecting cloud configurations...")
    from collector.multi_cloud_collector import main as collect_main
    
    collect_main(
        providers=json.dumps(providers),
        use_mock=True,  # Use mock data for demo
        output_dir="data"
    )
    print("   ✅ Collection complete!")
    print()
    
    # Step 2: Analyze security risks
    print("🔍 Step 2: Analyzing security risks with Gemini...")
    from explainer.multi_cloud_explainer import main as explain_main
    
    explain_main(
        project_id="example-project",
        use_mock=True,  # Use mock Gemini responses for demo
        input_file="data/collected.json",
        output_dir="data"
    )
    print("   ✅ Analysis complete!")
    print()
    
    # Step 3: Generate reports
    print("📊 Step 3: Generating audit reports...")
    from reporter.multi_cloud_reporter import main as report_main
    
    report_main(
        findings_file="data/explained.json",
        collected_file="data/collected.json",
        output_dir="output",
        formats="markdown,html"
    )
    print("   ✅ Reports generated!")
    print()
    
    # Display results summary
    print("📈 Audit Summary:")
    with open("data/explained.json") as f:
        findings = json.load(f)
    
    # Count findings by provider and severity
    provider_counts = {}
    severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    
    for finding in findings:
        provider = finding.get("provider", "unknown")
        severity = finding.get("severity", "UNKNOWN")
        
        if provider not in provider_counts:
            provider_counts[provider] = 0
        provider_counts[provider] += 1
        
        if severity in severity_counts:
            severity_counts[severity] += 1
    
    print(f"   Total Findings: {len(findings)}")
    print("   By Provider:")
    for provider, count in sorted(provider_counts.items()):
        print(f"     - {provider.upper()}: {count}")
    print("   By Severity:")
    for severity, count in sorted(severity_counts.items()):
        print(f"     - {severity}: {count}")
    print()
    
    print("✨ Multi-cloud audit complete!")
    print("   📄 View the Markdown report: output/audit.md")
    print("   🌐 View the HTML report: output/audit.html")


def run_single_cloud_audit(provider="aws"):
    """Run audit for a single cloud provider."""
    
    print(f"🚀 Starting {provider.upper()} Security Audit")
    print()
    
    # Configure the provider
    config = {}
    if provider == "gcp":
        config = {"provider": "gcp", "project_id": "example-project"}
    elif provider == "aws":
        config = {"provider": "aws", "account_id": "123456789012"}
    elif provider == "azure":
        config = {"provider": "azure", "subscription_id": "00000000-0000-0000-0000-000000000000"}
    
    # Run collection
    print(f"📥 Collecting {provider.upper()} configurations...")
    from collector.agent_collector import main as collect_main
    
    collect_main(
        provider=provider,
        project_id=config.get("project_id"),
        account_id=config.get("account_id"),
        subscription_id=config.get("subscription_id"),
        use_mock=True,
        output_dir="data"
    )
    
    # Run analysis
    print(f"🔍 Analyzing {provider.upper()} security risks...")
    from explainer.agent_explainer import main as explain_main
    
    explain_main(
        project_id="example-project",
        use_mock=True,
        input_file="data/collected.json",
        output_dir="data"
    )
    
    # Generate reports
    print(f"📊 Generating {provider.upper()} audit report...")
    from reporter.agent_reporter import main as report_main
    
    report_main(
        findings_file="data/explained.json",
        collected_file="data/collected.json",
        output_dir="output",
        formats="markdown,html"
    )
    
    print(f"✨ {provider.upper()} audit complete!")
    print("   📄 View the report: output/audit.md")


if __name__ == "__main__":
    import sys
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "multi":
            run_multi_cloud_audit()
        elif sys.argv[1] in ["gcp", "aws", "azure"]:
            run_single_cloud_audit(sys.argv[1])
        else:
            print("Usage: python run_multi_cloud_example.py [multi|gcp|aws|azure]")
            print("  multi - Run multi-cloud audit (default)")
            print("  gcp   - Run GCP-only audit")
            print("  aws   - Run AWS-only audit")
            print("  azure - Run Azure-only audit")
    else:
        # Default to multi-cloud
        run_multi_cloud_audit()