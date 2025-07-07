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
from google.auth.exceptions import RefreshError
from grpc import StatusCode
from grpc._channel import _InactiveRpcError

from app.common.auth import check_gcp_credentials
from app.common.exceptions import AuthenticationError, CollectionError

# Configure logging
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
        # Ensure use_mock is properly converted to boolean
        if isinstance(use_mock, str):
            self.use_mock = use_mock.lower() in ("true", "1", "yes", "on")
        else:
            self.use_mock = bool(use_mock)
        logger.info(
            "IAMCollector initialized: project_id=%s, use_mock=%s (converted from %s)",
            project_id,
            self.use_mock,
            use_mock,
        )

    def _convert_bindings(self, policy) -> List[Dict[str, Any]]:
        """Convert policy bindings to dictionary format."""
        bindings = []
        for binding in policy.bindings:
            bindings.append({"role": binding.role, "members": list(binding.members)})
        return bindings

    def _encode_etag(self, etag: bytes) -> str:
        """Encode etag safely, handling non-UTF-8 data."""
        if not etag:
            return ""
        try:
            return etag.decode("utf-8")
        except UnicodeDecodeError:
            import base64

            logger.warning("Etag contained non-UTF-8 data, using base64 encoding")
            return base64.b64encode(etag).decode("ascii")

    def _raise_auth_error(self, exception=None) -> None:
        """Raise authentication error with consistent message."""
        error_msg = (
            "認証エラー: Google Cloud の認証に問題があります。\n"
            "以下のコマンドを実行して再認証してください:\n"
            "  gcloud auth application-default login"
        )
        logger.error(error_msg)
        raise AuthenticationError(
            "GCP", {"solution": "gcloud auth application-default login"}
        ) from exception

    def collect(self) -> Dict[str, Any]:  # pylint: disable=inconsistent-return-statements
        """Collect IAM policies."""
        logger.info(
            "IAMCollector.collect() called: self.use_mock=%s (type: %s)",
            self.use_mock,
            type(self.use_mock),
        )
        if self.use_mock:
            logger.info("Using mock data because self.use_mock is True")
            return self._get_mock_iam_data()

        try:
            logger.info("Attempting to collect real IAM data for project: %s", self.project_id)
            logger.info("🔑 Google Cloud API に接続中...")
            from google.cloud import resourcemanager_v3
            from google.iam.v1 import iam_policy_pb2

            # Initialize Resource Manager client to get IAM policy
            logger.info("Resource Manager クライアントを初期化中...")
            client = resourcemanager_v3.ProjectsClient()

            # Get IAM policy for the project
            resource = f"projects/{self.project_id}"
            logger.info("📝 IAM ポリシーを取得中: %s", resource)
            request = iam_policy_pb2.GetIamPolicyRequest(resource=resource)

            policy = client.get_iam_policy(request=request)
            logger.info("IAM policy retrieved successfully")

            # Convert protobuf to dict
            bindings = self._convert_bindings(policy)
            logger.info(
                "Successfully collected %d IAM bindings from project %s",
                len(bindings),
                self.project_id,
            )

            # Handle etag encoding safely
            etag_str = self._encode_etag(policy.etag)

            return {"bindings": bindings, "etag": etag_str, "version": policy.version}

        except ImportError:
            logger.error("google-cloud-resource-manager がインストールされていません")
            logger.info("pip install google-cloud-resource-manager を実行してください")
            return self._get_mock_iam_data()
        except RefreshError:
            self._raise_auth_error()
        except _InactiveRpcError as e:
            if e.code() == StatusCode.UNAUTHENTICATED:
                self._raise_auth_error(e)
            logger.error("GCP API エラー: %s", e.details())
            raise CollectionError("IAM", {"error_type": "APIError", "error": e.details()}) from e
        except Exception as e:
            error_type = type(e).__name__
            if "RefreshError" in str(e) or "Reauthentication" in str(e):
                self._raise_auth_error(e)
            logger.error("IAMデータの収集中にエラーが発生しました: %s", error_type)
            raise CollectionError("IAM", {"error_type": error_type, "error": str(e)}) from e

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


class SCCCollectorAdapter(CollectorInterface):
    """Adapter for the dedicated SCCCollector to maintain backward compatibility."""

    def __init__(self, organization_id: str, use_mock: bool = False):
        """Initialize SCCCollectorAdapter with organization configuration."""
        # Import the dedicated SCC collector
        from .scc_collector import SCCCollector

        self.organization_id = organization_id
        # Ensure use_mock is properly converted to boolean
        if isinstance(use_mock, str):
            self.use_mock = use_mock.lower() in ("true", "1", "yes", "on")
        else:
            self.use_mock = bool(use_mock)
        logger.info(
            "SCCCollectorAdapter initialized: organization_id=%s, use_mock=%s (converted from %s)",
            organization_id,
            self.use_mock,
            use_mock,
        )
        self.scc_collector = SCCCollector(organization_id)

    def collect(self) -> List[Dict[str, Any]]:
        """Collect SCC findings using the dedicated collector."""
        try:
            return self.scc_collector.collect_findings(use_mock=self.use_mock)
        except RefreshError:
            error_msg = (
                "Google Cloud の認証が期限切れです。\n"
                "以下のコマンドを実行して再認証してください:\n"
                "  gcloud auth application-default login"
            )
            logger.error(error_msg)
            raise AuthenticationError(
                "GCP", {"solution": "gcloud auth application-default login"}
            ) from None
        except Exception as e:
            error_type = type(e).__name__
            logger.error("SCCデータの収集中にエラーが発生しました: %s", error_type)
            raise CollectionError("SCC", {"error_type": error_type, "error": str(e)}) from e


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
        logger.info(
            "Initializing IAMCollector with project_id=%s, use_mock=%s", project_id, use_mock
        )
        self.iam_collector = IAMCollector(project_id, use_mock)
        logger.info(
            "Initializing SCCCollector with organization_id=%s, use_mock=%s",
            self.organization_id,
            use_mock,
        )
        self.scc_collector = SCCCollectorAdapter(self.organization_id, use_mock)

    def collect_all(self) -> Dict[str, Any]:
        """Collect all GCP configurations."""
        logger.info("Starting GCP configuration collection for project: %s", self.project_id)

        # Collect IAM policies with debugging
        logger.info("About to call IAM collector...")
        iam_data = self.iam_collector.collect()
        logger.info("IAM data collected, type: %s", type(iam_data))
        if isinstance(iam_data, dict) and "bindings" in iam_data:
            logger.info("IAM bindings count: %d", len(iam_data["bindings"]))
            for i, binding in enumerate(iam_data["bindings"][:2]):  # Log first 2 bindings
                logger.info(
                    "Binding %d: role=%s, members=%s",
                    i,
                    binding.get("role"),
                    binding.get("members"),
                )

        # Collect SCC findings
        logger.info("About to call SCC collector...")
        scc_data = self.scc_collector.collect()
        logger.info("SCC data collected, type: %s", type(scc_data))

        collected_data = {
            "metadata": {
                "project_id": self.project_id,
                "organization_id": self.organization_id,
                "timestamp": self._get_timestamp(),
            },
            "iam_policies": iam_data,
            "scc_findings": scc_data,
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
    github_token: Optional[str] = None,
    github_owner: Optional[str] = None,
    github_repo: Optional[str] = None,
    **kwargs,
):
    """
    Collect cloud configuration data for security audit.

    Args:
        project_id: GCP project ID to audit (for backward compatibility)
        organization_id: GCP organization ID for SCC findings
        use_mock: Use mock data instead of real cloud APIs
        output_dir: Directory to save collected data
        provider: Single cloud provider (gcp, aws, azure, github)
        providers: JSON string with list of provider configs for multi-cloud
        account_id: AWS account ID
        subscription_id: Azure subscription ID
        github_token: GitHub personal access token
        github_owner: GitHub repository owner
        github_repo: GitHub repository name
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
            # Use multi-cloud collector for AWS/Azure/GitHub
            provider_config = {"provider": provider, "use_mock": use_mock}
            if provider.lower() == "aws" and account_id:
                provider_config["account_id"] = account_id
            elif provider.lower() == "azure" and subscription_id:
                provider_config["subscription_id"] = subscription_id
            elif provider.lower() == "github":
                if github_token:
                    provider_config["access_token"] = github_token
                if github_owner:
                    provider_config["owner"] = github_owner
                if github_repo:
                    provider_config["repo"] = github_repo
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
