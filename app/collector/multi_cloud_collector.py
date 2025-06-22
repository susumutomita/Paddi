import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from ..providers.factory import CloudProviderFactory


class MultiCloudCollector:
    """Collector that supports multiple cloud providers."""

    def __init__(self, output_dir: str = "data"):
        """Initialize multi-cloud collector."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def collect_from_provider(self, provider_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collect data from a single cloud provider.

        Args:
            provider_config: Configuration dict with 'provider' key and provider-specific params

        Returns:
            Collected data from the provider
        """
        provider_name = provider_config.get("provider")
        if not provider_name:
            raise ValueError("Provider configuration must include 'provider' key")

        # Remove 'provider' key and pass remaining as kwargs
        provider_params = {k: v for k, v in provider_config.items() if k != "provider"}

        # Create provider instance and collect data
        provider = CloudProviderFactory.create(provider_name, **provider_params)
        return provider.collect_all()

    def collect_from_multiple_providers(self, providers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Collect data from multiple cloud providers.

        Args:
            providers: List of provider configurations

        Returns:
            Combined data from all providers
        """
        all_data = {
            "providers": [],
            "summary": {
                "total_providers": len(providers),
                "total_findings": 0,
                "findings_by_severity": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
                "findings_by_provider": {},
            },
        }

        for provider_config in providers:
            try:
                provider_data = self.collect_from_provider(provider_config)
                all_data["providers"].append(provider_data)

                # Update summary statistics
                provider_name = provider_data["provider"]
                findings_count = len(provider_data.get("security_findings", []))
                all_data["summary"]["total_findings"] += findings_count
                all_data["summary"]["findings_by_provider"][provider_name] = findings_count

                # Count findings by severity
                for finding in provider_data.get("security_findings", []):
                    # Handle different severity formats
                    if provider_name == "gcp":
                        severity = finding.get("severity", "LOW")
                    elif provider_name == "aws":
                        severity = finding.get("Severity", {}).get("Label", "LOW")
                    elif provider_name == "azure":
                        severity = finding.get("properties", {}).get("severity", "Low").upper()
                    else:
                        severity = "LOW"

                    if severity in all_data["summary"]["findings_by_severity"]:
                        all_data["summary"]["findings_by_severity"][severity] += 1

            except Exception as e:
                print(f"Error collecting from provider {provider_config}: {e}")
                all_data["providers"].append(
                    {
                        "provider": provider_config.get("provider", "unknown"),
                        "error": str(e),
                        "status": "failed",
                    }
                )

        return all_data

    def save_data(self, data: Dict[str, Any], filename: str = "collected.json") -> Path:
        """Save collected data to JSON file."""
        output_path = self.output_dir / filename
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        return output_path