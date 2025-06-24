"""
Multi-cloud collector module for handling data collection from multiple cloud providers.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from app.providers.factory import CloudProviderFactory


class MultiCloudCollector:
    """Collector that supports multiple cloud providers."""

    def __init__(self, output_dir: str = "data"):
        """Initialize multi-cloud collector."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def collect_from_provider(self, provider_config: Dict[str, Any]) -> Dict[str, Any]:
        """Collect data from a single cloud provider."""
        if "provider" not in provider_config:
            raise ValueError("Provider configuration must include 'provider' key")

        factory = CloudProviderFactory()

        # Create provider instance
        provider = factory.create_provider(provider_config)

        # Collect all data from the provider
        data = provider.collect_all()

        return data

    def collect_from_multiple_providers(self, providers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Collect data from multiple cloud providers."""
        all_data = {"providers": [], "summary": {}}

        total_findings = 0
        findings_by_severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        findings_by_provider = {}

        for provider_config in providers:
            try:
                # Collect from single provider
                provider_data = self.collect_from_provider(provider_config)
                all_data["providers"].append(provider_data)

                # Count findings (mock data for now)
                provider_name = provider_data["provider"]
                if provider_name == "gcp":
                    # GCP has different structure
                    num_findings = len(provider_data.get("security_findings", []))
                else:
                    # AWS/Azure mock data
                    num_findings = len(provider_data.get("security_findings", []))

                findings_by_provider[provider_name] = num_findings
                total_findings += num_findings

                # Update severity counts (simplified for mock)
                if num_findings > 0:
                    findings_by_severity["CRITICAL"] += num_findings // 4
                    findings_by_severity["HIGH"] += num_findings // 4
                    findings_by_severity["MEDIUM"] += num_findings // 4
                    findings_by_severity["LOW"] += num_findings - (3 * (num_findings // 4))

            except Exception as e:
                # Log error and add failed provider info
                error_data = {
                    "provider": provider_config.get("provider", "unknown"),
                    "error": str(e),
                    "status": "failed",
                }
                all_data["providers"].append(error_data)

        # Create summary
        all_data["summary"] = {
            "total_providers": len(providers),
            "total_findings": total_findings,
            "findings_by_severity": findings_by_severity,
            "findings_by_provider": findings_by_provider,
            "timestamp": self._get_timestamp(),
        }

        return all_data

    def save_data(self, data: Dict[str, Any], filename: str = "collected.json") -> Path:
        """Save collected data to JSON file."""
        output_path = self.output_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return output_path

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()
