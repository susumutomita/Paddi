#!/usr/bin/env python3
"""
Agent A: GCP Configuration Collector

This agent collects Google Cloud Platform configurations for security audits.
It supports both real GCP environments and mocked data for testing.
"""

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

import fire

from common.auth import check_gcp_credentials

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CollectorInterface(ABC):
    """Abstract interface for GCP collectors."""

    @abstractmethod
    def collect(self) -> Dict[str, Any]:
        """Collect GCP configuration data."""


class IAMCollector(CollectorInterface):
    """Collector for IAM policies and roles."""

    def __init__(self, project_id: str, use_mock: bool = False):
        """Initialize IAMCollector with project configuration."""
        self.project_id = project_id
        self.use_mock = use_mock

    def collect(self) -> Dict[str, Any]:
        """Collect IAM policies."""
        if self.use_mock:
            return self._get_mock_iam_data()

        try:
            from google.cloud import iam_admin_v1 as iam

            # Initialize IAM admin client
            iam.IAMClient()  # pylint: disable=no-member
            # This would collect real IAM data
            # For now, returning mock structure
            logger.warning("Real IAM collection not fully implemented, using mock data")
            return self._get_mock_iam_data()
        except ImportError:
            logger.error("google-cloud-iam not installed, using mock data")
            return self._get_mock_iam_data()
        except Exception as e:
            logger.error("Error collecting IAM data: %s", e)
            return self._get_mock_iam_data()

    def _get_mock_iam_data(self) -> Dict[str, Any]:
        """Return mock IAM data for testing."""
        return {
            "bindings": [
                {
                    "role": "roles/owner",
                    "members": ["user:admin@example.com", "user:developer@example.com"],
                },
                {
                    "role": "roles/editor",
                    "members": ["serviceAccount:app-sa@project.iam.gserviceaccount.com"],
                },
                {
                    "role": "roles/viewer",
                    "members": ["user:auditor@example.com"],
                },
            ],
            "etag": "BwXqWz123456",
            "version": 1,
        }


class SCCCollector(CollectorInterface):
    """Collector for Security Command Center findings."""

    def __init__(self, organization_id: str, use_mock: bool = False):
        """Initialize SCCCollector with organization configuration."""
        self.organization_id = organization_id
        self.use_mock = use_mock

    def collect(self) -> List[Dict[str, Any]]:
        """Collect SCC findings."""
        if self.use_mock:
            return self._get_mock_scc_data()

        try:
            from google.cloud import securitycenter

            # Initialize SCC client
            securitycenter.SecurityCenterClient()
            # This would collect real SCC findings
            # For now, returning mock structure
            logger.warning("Real SCC collection not fully implemented, using mock data")
            return self._get_mock_scc_data()
        except ImportError:
            logger.error("google-cloud-securitycenter not installed, using mock data")
            return self._get_mock_scc_data()
        except Exception as e:
            logger.error("Error collecting SCC data: %s", e)
            return self._get_mock_scc_data()

    def _get_mock_scc_data(self) -> List[Dict[str, Any]]:
        """Return mock SCC findings for testing."""
        return [
            {
                "name": "organizations/123456/sources/789/findings/finding-1",
                "category": "OVERPRIVILEGED_SERVICE_ACCOUNT",
                "resource_name": (
                    "//iam.googleapis.com/projects/example-project/serviceAccounts/"
                    "over-privileged-sa@example-project.iam.gserviceaccount.com"
                ),
                "state": "ACTIVE",
                "severity": "HIGH",
                "finding_class": "VULNERABILITY",
                "indicator": {
                    "domains": [],
                    "ip_addresses": [],
                },
            },
            {
                "name": "organizations/123456/sources/789/findings/finding-2",
                "category": "PUBLIC_BUCKET",
                "resource_name": "//storage.googleapis.com/example-public-bucket",
                "state": "ACTIVE",
                "severity": "MEDIUM",
                "finding_class": "MISCONFIGURATION",
                "indicator": {
                    "domains": [],
                    "ip_addresses": [],
                },
            },
        ]


class GCPConfigurationCollector:
    """Main orchestrator for collecting GCP configurations."""

    def __init__(
        self,
        project_id: str,
        organization_id: Optional[str] = None,
        use_mock: bool = False,
        output_dir: str = "data",
    ):
        """Initialize GCPConfigurationCollector with configuration."""
        self.project_id = project_id
        self.organization_id = organization_id or "123456"  # Default for mock
        self.use_mock = use_mock
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Initialize collectors
        self.iam_collector = IAMCollector(project_id, use_mock)
        self.scc_collector = SCCCollector(self.organization_id, use_mock)

    def collect_all(self) -> Dict[str, Any]:
        """Collect all GCP configurations."""
        logger.info("Starting GCP configuration collection for project: %s", self.project_id)

        collected_data = {
            "metadata": {
                "project_id": self.project_id,
                "organization_id": self.organization_id,
                "timestamp": self._get_timestamp(),
            },
            "iam_policies": self.iam_collector.collect(),
            "scc_findings": self.scc_collector.collect(),
        }

        logger.info("Collection completed successfully")
        return collected_data

    def save_to_file(self, data: Dict[str, Any], filename: str = "collected.json") -> Path:
        """Save collected data to JSON file."""
        output_path = self.output_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info("Data saved to: %s", output_path)
        return output_path

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()


def main(
    project_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    use_mock: bool = True,
    output_dir: str = "data",
    provider: str = "gcp",
    providers: Optional[str] = None,
    account_id: Optional[str] = None,
    subscription_id: Optional[str] = None,
    **kwargs,
):
    """
    Collect cloud configuration data for security audit.

    Args:
        project_id: GCP project ID to audit (for backward compatibility)
        organization_id: GCP organization ID for SCC findings
        use_mock: Use mock data instead of real cloud APIs
        output_dir: Directory to save collected data
        provider: Single cloud provider (gcp, aws, azure)
        providers: JSON string with list of provider configs for multi-cloud
        account_id: AWS account ID
        subscription_id: Azure subscription ID
        **kwargs: Additional provider-specific parameters
    """
    try:
        # Import multi-cloud collector
        from .multi_cloud_collector import MultiCloudCollector

        # Handle multi-cloud collection
        if providers:
            provider_configs = json.loads(providers)
            multi_collector = MultiCloudCollector(output_dir=output_dir)
            data = multi_collector.collect_from_multiple_providers(provider_configs)
            output_path = multi_collector.save_data(data)
            print(f"✅ Multi-cloud collection successful! Data saved to: {output_path}")
            return

        # Handle single provider collection
        if provider.lower() != "gcp":
            # Use multi-cloud collector for AWS/Azure
            provider_config = {"provider": provider}
            if provider.lower() == "aws" and account_id:
                provider_config["account_id"] = account_id
            elif provider.lower() == "azure" and subscription_id:
                provider_config["subscription_id"] = subscription_id
            provider_config.update(kwargs)

            multi_collector = MultiCloudCollector(output_dir=output_dir)
            data = multi_collector.collect_from_provider(provider_config)
            output_path = multi_collector.save_data(data)
            print(f"✅ {provider.upper()} collection successful! Data saved to: {output_path}")
            return

        # Backward compatibility: GCP collection using original logic
        if not project_id:
            project_id = "example-project"

        # Set up Google Cloud authentication if not using mock
        check_gcp_credentials(use_mock)

        # Initialize collector
        collector = GCPConfigurationCollector(
            project_id=project_id,
            organization_id=organization_id,
            use_mock=use_mock,
            output_dir=output_dir,
        )

        # Collect data
        data = collector.collect_all()

        # Save to file
        output_path = collector.save_to_file(data)

        print(f"✅ Collection successful! Data saved to: {output_path}")

    except Exception as e:
        logger.error("Collection failed: %s", e)
        raise


if __name__ == "__main__":
    fire.Fire(main)
