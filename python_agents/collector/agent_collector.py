#!/usr/bin/env python3
"""
Agent A: Multi-Cloud Configuration Collector

This agent collects cloud configurations from GCP, AWS, and Azure for security audits.
It supports both real cloud environments and mocked data for testing.

This file provides backward compatibility for the original GCP-only collector
while leveraging the new multi-cloud architecture.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timezone

import fire

from .multi_cloud_collector import MultiCloudConfigurationCollector
from .cloud_provider import CloudConfig, CloudProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Backward compatibility classes for existing tests
class IAMCollector:
    """Legacy IAM Collector for backward compatibility."""
    
    def __init__(self, project_id: str, use_mock: bool = True):
        self.project_id = project_id
        self.use_mock = use_mock
    
    def collect(self) -> Dict[str, Any]:
        """Collect IAM data in legacy format."""
        if self.use_mock:
            return self._get_mock_iam_data()
        
        try:
            # Try to import and use real Google Cloud IAM
            from google.cloud import iam
            # This would be the real implementation
            logger.warning("Real GCP IAM collection not implemented, falling back to mock data")
            return self._get_mock_iam_data()
        except ImportError:
            logger.warning("google-cloud-iam not installed, using mock data")
            return self._get_mock_iam_data()
        except Exception as e:
            logger.error(f"Error collecting IAM data: {e}, falling back to mock data")
            return self._get_mock_iam_data()
    
    def _get_mock_iam_data(self) -> Dict[str, Any]:
        """Get mock IAM data in legacy format."""
        return {
            "bindings": [
                {
                    "role": "roles/owner",
                    "members": ["user:admin@example.com"]
                },
                {
                    "role": "roles/viewer",
                    "members": ["user:viewer@example.com", "serviceAccount:sa@project.iam.gserviceaccount.com"]
                }
            ],
            "etag": "BwXqWz123456",
            "version": 1
        }


class SCCCollector:
    """Legacy Security Command Center Collector for backward compatibility."""
    
    def __init__(self, organization_id: str, use_mock: bool = True):
        self.organization_id = organization_id
        self.use_mock = use_mock
    
    def collect(self) -> List[Dict[str, Any]]:
        """Collect SCC findings in legacy format."""
        if self.use_mock:
            return self._get_mock_scc_data()
        
        try:
            # Try to import and use real Google Cloud Security Command Center
            from google.cloud import securitycenter
            # This would be the real implementation
            logger.warning("Real GCP SCC collection not implemented, falling back to mock data")
            return self._get_mock_scc_data()
        except ImportError:
            logger.warning("google-cloud-securitycenter not installed, using mock data")
            return self._get_mock_scc_data()
        except Exception as e:
            logger.error(f"Error collecting SCC data: {e}, falling back to mock data")
            return self._get_mock_scc_data()
    
    def _get_mock_scc_data(self) -> List[Dict[str, Any]]:
        """Get mock SCC findings in legacy format."""
        return [
            {
                "name": f"organizations/{self.organization_id}/sources/1234567890/findings/finding1",
                "category": "OVERPRIVILEGED_SERVICE_ACCOUNT",
                "resource_name": "//iam.googleapis.com/projects/example-project/serviceAccounts/overpriv-sa@example-project.iam.gserviceaccount.com",
                "state": "ACTIVE",
                "severity": "HIGH",
                "finding_class": "MISCONFIGURATION",
                "indicator": {"domains": [], "ip_addresses": []}
            },
            {
                "name": f"organizations/{self.organization_id}/sources/1234567890/findings/finding2",
                "category": "PUBLIC_BUCKET",
                "resource_name": "//storage.googleapis.com/buckets/public-data-bucket",
                "state": "ACTIVE",
                "severity": "MEDIUM",
                "finding_class": "MISCONFIGURATION",
                "indicator": {"domains": [], "ip_addresses": []}
            }
        ]


class GCPConfigurationCollector:
    """Legacy GCP Configuration Collector for backward compatibility."""
    
    def __init__(
        self,
        project_id: str,
        organization_id: Optional[str] = None,
        use_mock: bool = True,
        output_dir: str = "data"
    ):
        self.project_id = project_id
        self.organization_id = organization_id or "123456"
        self.use_mock = use_mock
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize sub-collectors
        self.iam_collector = IAMCollector(project_id, use_mock)
        self.scc_collector = SCCCollector(self.organization_id, use_mock)
    
    def collect_all(self) -> Dict[str, Any]:
        """Collect all GCP configurations in legacy format."""
        logger.info(f"Starting GCP configuration collection for project: {self.project_id}")
        
        data = {
            "project_id": self.project_id,
            "organization_id": self.organization_id,
            "timestamp": self._get_timestamp(),
            "iam_policies": self.iam_collector.collect(),
            "scc_findings": self.scc_collector.collect()
        }
        
        logger.info("GCP configuration collection completed")
        return data
    
    def save_to_file(self, data: Dict[str, Any], filename: str = "collected.json") -> Path:
        """Save collected data to file."""
        output_path = self.output_dir / filename
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Data saved to: {output_path}")
        return output_path
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()


def main(
    # Multi-cloud parameters
    providers: Optional[str] = None,
    # Legacy GCP-specific parameters
    project_id: str = "example-project",
    organization_id: Optional[str] = None,
    use_mock: bool = True,
    output_dir: str = "data",
    # Additional cloud parameters
    provider: Optional[str] = None,
    account_id: Optional[str] = None,
    subscription_id: Optional[str] = None,
    region: Optional[str] = None,
):
    """
    Collect cloud configuration data for security audit.
    
    Supports both legacy GCP-only mode and new multi-cloud mode.

    Args:
        providers: JSON string or file path for multi-cloud configurations
        project_id: GCP project ID (legacy parameter)
        organization_id: GCP organization ID (legacy parameter)
        use_mock: Use mock data instead of real cloud APIs
        output_dir: Directory to save collected data
        provider: Cloud provider for single-cloud mode ('gcp', 'aws', 'azure')
        account_id: AWS account ID
        subscription_id: Azure subscription ID
        region: Cloud region
    
    Examples:
        # Legacy GCP-only mode
        python agent_collector.py --project_id=my-project
        
        # Single cloud mode
        python agent_collector.py --provider=aws --account_id=123456789012
        
        # Multi-cloud mode
        python agent_collector.py --providers='[{"provider": "gcp", "project_id": "my-project"}, {"provider": "aws", "account_id": "123456789012"}]'
    """
    try:
        # Check if we're in legacy GCP-only mode
        if not providers and not provider:
            # Legacy mode - convert to new format but maintain backward compatibility
            logger.info("Running in legacy GCP-only mode for backward compatibility")
            provider_configs = [{
                "provider": "gcp",
                "project_id": project_id
            }]
            
            # Initialize multi-cloud collector with GCP-only config
            collector = MultiCloudConfigurationCollector(
                providers=provider_configs,
                use_mock=use_mock,
                output_dir=output_dir,
            )
            
            # Collect data
            multi_cloud_data = collector.collect_all()
            
            # Convert back to legacy format for backward compatibility
            if "gcp" in multi_cloud_data["providers"]:
                gcp_data = multi_cloud_data["providers"]["gcp"]
                legacy_data = {
                    "project_id": project_id,
                    "organization_id": organization_id or "123456",
                    "timestamp": multi_cloud_data["timestamp"],
                    "iam_policies": {
                        "bindings": [
                            {
                                "role": role,
                                "members": members
                            }
                            for policy in gcp_data["iam"]["policies"]
                            for binding in policy.get("bindings", [])
                            for role, members in [(binding["role"], binding["members"])]
                        ] if gcp_data["iam"]["policies"] else [],
                        "etag": "BwXqWz123456",
                        "version": 1
                    },
                    "scc_findings": [
                        {
                            "name": f"organizations/123456/sources/789/findings/{f['id']}",
                            "category": f.get("category", "UNKNOWN"),
                            "resource_name": f.get("resource", ""),
                            "state": f.get("status", "ACTIVE"),
                            "severity": f.get("severity", "MEDIUM"),
                            "finding_class": f.get("finding_type", "MISCONFIGURATION").upper(),
                            "indicator": {"domains": [], "ip_addresses": []}
                        }
                        for f in gcp_data["security"]["findings"]
                    ]
                }
                
                # Save in legacy format
                output_path = Path(output_dir) / "collected.json"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(legacy_data, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Collection successful! Data saved to: {output_path}")
            else:
                raise Exception("Failed to collect GCP data")
        else:
            # New multi-cloud mode - delegate to multi_cloud_collector
            from .multi_cloud_collector import main as multi_cloud_main
            multi_cloud_main(
                providers=providers,
                use_mock=use_mock,
                output_dir=output_dir,
                provider=provider,
                project_id=project_id,
                account_id=account_id,
                subscription_id=subscription_id,
                region=region
            )
            
    except Exception as e:
        logger.error(f"Collection failed: {e}")
        raise


if __name__ == "__main__":
    fire.Fire(main)