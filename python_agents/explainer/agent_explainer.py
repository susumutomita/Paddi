#!/usr/bin/env python3
"""
Agent B: Security Risk Explainer

This agent analyzes cloud configurations collected by Agent A using Gemini LLM
to identify security risks and provide recommendations.

This file provides backward compatibility for the original GCP-only explainer
while leveraging the new multi-cloud architecture.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import fire

from .multi_cloud_explainer import MultiCloudSecurityExplainer

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main(
    project_id: str = "example-project",
    location: str = "us-central1",
    use_mock: bool = True,
    input_file: str = "data/collected.json",
    output_dir: str = "data",
):
    """
    Analyze cloud configuration for security risks using Gemini LLM.
    
    Supports both legacy GCP-only format and new multi-cloud format.

    Args:
        project_id: GCP project ID for Vertex AI
        location: GCP region for Vertex AI
        use_mock: Use mock responses instead of real LLM calls
        input_file: Path to configuration data from collector
        output_dir: Directory to save analysis results
    """
    try:
        # Initialize multi-cloud explainer
        explainer = MultiCloudSecurityExplainer(
            project_id=project_id,
            location=location,
            use_mock=use_mock,
            input_file=input_file,
            output_dir=output_dir,
        )
        
        # Load configuration to check format
        configuration = explainer.load_configuration()
        
        # Perform analysis
        findings = explainer.analyze()
        
        # Check if we need to convert back to legacy format
        if "iam_policies" in configuration and "providers" not in configuration:
            # Legacy GCP format - convert findings to legacy format
            legacy_findings = []
            for finding in findings:
                # Remove provider field for legacy format
                legacy_finding = {
                    "title": finding.title,
                    "severity": finding.severity,
                    "explanation": finding.explanation,
                    "recommendation": finding.recommendation
                }
                legacy_findings.append(legacy_finding)
            
            # Save in legacy format
            output_path = Path(output_dir) / "explained.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(legacy_findings, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Analysis successful! Found {len(findings)} security issues.")
            print(f"Results saved to: {output_path}")
            
            # Display legacy summary
            high_severity = sum(1 for f in findings if f.severity == "HIGH")
            medium_severity = sum(1 for f in findings if f.severity == "MEDIUM")
            low_severity = sum(1 for f in findings if f.severity == "LOW")
            
            print(f"\nSeverity summary:")
            print(f"  HIGH: {high_severity}")
            print(f"  MEDIUM: {medium_severity}")
            print(f"  LOW: {low_severity}")
        else:
            # Multi-cloud format - use default behavior
            output_path = explainer.save_findings(findings)
            
            print(f"✅ Analysis successful! Found {len(findings)} security issues.")
            print(f"Results saved to: {output_path}")
            
            # Display multi-cloud summary
            provider_summary = {}
            for finding in findings:
                provider = finding.provider
                if provider not in provider_summary:
                    provider_summary[provider] = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
                provider_summary[provider][finding.severity] += 1
            
            if len(provider_summary) == 1 and "gcp" in provider_summary:
                # Single GCP provider - show simple summary
                counts = provider_summary["gcp"]
                print(f"\nSeverity summary:")
                print(f"  HIGH: {counts['HIGH']}")
                print(f"  MEDIUM: {counts['MEDIUM']}")
                print(f"  LOW: {counts['LOW']}")
            else:
                # Multiple providers - show by provider
                print(f"\nSeverity summary by cloud provider:")
                for provider, counts in provider_summary.items():
                    print(f"\n{provider.upper()}:")
                    print(f"  HIGH: {counts['HIGH']}")
                    print(f"  MEDIUM: {counts['MEDIUM']}")
                    print(f"  LOW: {counts['LOW']}")

    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        logger.info("Please run agent_collector.py first to generate configuration data.")
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise


if __name__ == "__main__":
    fire.Fire(main)