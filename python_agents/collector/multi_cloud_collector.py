#!/usr/bin/env python3
"""
Multi-Cloud Configuration Collector

This agent collects cloud configurations from multiple providers (GCP, AWS, Azure)
for security audits. It supports both real cloud environments and mocked data for testing.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import fire

from .cloud_provider import CloudConfig, CloudProvider, CloudCollectorFactory
from .gcp_provider import GCPProvider  # This imports and registers GCP
from .aws_provider import AWSProvider  # This imports and registers AWS
from .azure_provider import AzureProvider  # This imports and registers Azure

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MultiCloudConfigurationCollector:
    """Main orchestrator for collecting configurations from multiple cloud providers."""

    def __init__(
        self,
        providers: List[Dict[str, Any]],
        use_mock: bool = False,
        output_dir: str = "data",
    ):
        """
        Initialize multi-cloud collector.
        
        Args:
            providers: List of provider configurations, each containing:
                - provider: Cloud provider name ('gcp', 'aws', 'azure')
                - project_id: GCP project ID (for GCP)
                - account_id: AWS account ID (for AWS)
                - subscription_id: Azure subscription ID (for Azure)
                - region: Cloud region (optional)
                - credentials_path: Path to credentials file (optional)
            use_mock: Use mock data instead of real cloud APIs
            output_dir: Directory to save collected data
        """
        self.providers = providers
        self.use_mock = use_mock
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize cloud provider instances
        self.cloud_providers = []
        for provider_config in providers:
            config = CloudConfig(
                provider=CloudProvider(provider_config['provider']),
                project_id=provider_config.get('project_id'),
                account_id=provider_config.get('account_id'),
                subscription_id=provider_config.get('subscription_id'),
                region=provider_config.get('region'),
                credentials_path=provider_config.get('credentials_path'),
                use_mock=use_mock
            )
            
            try:
                provider_instance = CloudCollectorFactory.create(config)
                self.cloud_providers.append(provider_instance)
                logger.info(f"Initialized {provider_instance.provider_name} collector")
            except ValueError as e:
                logger.error(f"Failed to initialize provider: {e}")

    def collect_all(self) -> Dict[str, Any]:
        """Collect configurations from all cloud providers."""
        logger.info(f"Starting multi-cloud configuration collection for {len(self.cloud_providers)} providers")
        
        collected_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "providers": {},
            "summary": {
                "total_users": 0,
                "total_roles": 0,
                "total_findings": 0,
                "high_severity_findings": 0,
                "providers_analyzed": []
            }
        }
        
        for provider in self.cloud_providers:
            provider_name = provider.config.provider.value
            logger.info(f"Collecting data from {provider.provider_name}")
            
            try:
                # Validate credentials first
                if not provider.validate_credentials():
                    logger.warning(f"Invalid credentials for {provider_name}, skipping...")
                    continue
                
                # Collect data from each component
                provider_data = {
                    "provider_name": provider.provider_name,
                    "iam": {
                        "users": provider.iam_collector.collect_users(),
                        "roles": provider.iam_collector.collect_roles(),
                        "policies": provider.iam_collector.collect_policies()
                    },
                    "security": {
                        "findings": provider.security_collector.collect_findings(),
                        "compliance": provider.security_collector.collect_compliance_status()
                    },
                    "logs": {
                        "recent_activities": provider.log_collector.collect_recent_logs(hours=24),
                        "suspicious_activities": provider.log_collector.collect_suspicious_activities()
                    }
                }
                
                collected_data["providers"][provider_name] = provider_data
                
                # Update summary
                collected_data["summary"]["total_users"] += len(provider_data["iam"]["users"])
                collected_data["summary"]["total_roles"] += len(provider_data["iam"]["roles"])
                collected_data["summary"]["total_findings"] += len(provider_data["security"]["findings"])
                collected_data["summary"]["high_severity_findings"] += sum(
                    1 for f in provider_data["security"]["findings"] 
                    if f.get("severity") in ["HIGH", "CRITICAL"]
                )
                collected_data["summary"]["providers_analyzed"].append(provider_name)
                
                logger.info(f"Successfully collected data from {provider_name}")
                
            except Exception as e:
                logger.error(f"Error collecting data from {provider_name}: {e}")
                collected_data["providers"][provider_name] = {
                    "error": str(e),
                    "status": "failed"
                }
        
        logger.info("Multi-cloud collection completed successfully")
        return collected_data

    def save_to_file(self, data: Dict[str, Any], filename: str = "collected.json") -> Path:
        """Save collected data to JSON file."""
        output_path = self.output_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Data saved to: {output_path}")
        return output_path


def main(
    providers: Optional[str] = None,
    use_mock: bool = True,
    output_dir: str = "data",
    # Legacy single-provider parameters for backward compatibility
    provider: Optional[str] = None,
    project_id: Optional[str] = None,
    account_id: Optional[str] = None,
    subscription_id: Optional[str] = None,
    region: Optional[str] = None,
):
    """
    Collect cloud configuration data from multiple providers for security audit.

    Args:
        providers: JSON string or file path containing provider configurations.
                  Example: '[{"provider": "gcp", "project_id": "my-project"},
                            {"provider": "aws", "account_id": "123456789012"}]'
        use_mock: Use mock data instead of real cloud APIs
        output_dir: Directory to save collected data
        
        Legacy single-provider parameters (for backward compatibility):
        provider: Single cloud provider ('gcp', 'aws', 'azure')
        project_id: GCP project ID
        account_id: AWS account ID
        subscription_id: Azure subscription ID
        region: Cloud region
    """
    try:
        # Parse providers configuration
        if providers:
            # Try to parse as JSON string
            try:
                provider_configs = json.loads(providers)
            except json.JSONDecodeError:
                # Try to load from file
                try:
                    with open(providers, 'r') as f:
                        provider_configs = json.load(f)
                except Exception:
                    logger.error("Failed to parse providers configuration")
                    raise ValueError("providers must be a valid JSON string or file path")
        elif provider:
            # Legacy single-provider mode
            provider_configs = [{
                "provider": provider,
                "project_id": project_id,
                "account_id": account_id,
                "subscription_id": subscription_id,
                "region": region
            }]
        else:
            # Default to GCP with example project for backward compatibility
            provider_configs = [{
                "provider": "gcp",
                "project_id": project_id or "example-project"
            }]
        
        # Set up cloud authentication if not using mock
        if not use_mock:
            # Check for credentials
            if any(p['provider'] == 'gcp' for p in provider_configs):
                if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                    logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set for GCP")
            
            if any(p['provider'] == 'aws' for p in provider_configs):
                if not (os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("AWS_PROFILE")):
                    logger.warning("AWS credentials not configured")
            
            if any(p['provider'] == 'azure' for p in provider_configs):
                if not os.getenv("AZURE_CLIENT_ID"):
                    logger.warning("Azure credentials not configured")
        
        # Initialize collector
        collector = MultiCloudConfigurationCollector(
            providers=provider_configs,
            use_mock=use_mock,
            output_dir=output_dir,
        )
        
        # Collect data
        data = collector.collect_all()
        
        # Save to file
        output_path = collector.save_to_file(data)
        
        print(f"✅ Collection successful! Data saved to: {output_path}")
        print(f"📊 Summary:")
        print(f"   - Providers analyzed: {', '.join(data['summary']['providers_analyzed'])}")
        print(f"   - Total users/identities: {data['summary']['total_users']}")
        print(f"   - Total roles: {data['summary']['total_roles']}")
        print(f"   - Total security findings: {data['summary']['total_findings']}")
        print(f"   - High severity findings: {data['summary']['high_severity_findings']}")
        
    except Exception as e:
        logger.error(f"Collection failed: {e}")
        raise


if __name__ == "__main__":
    fire.Fire(main)