#!/usr/bin/env python3
"""Agent A: GCP Configuration Collector.

This agent collects Google Cloud Platform configurations for security audits.
It follows SOLID principles with proper interfaces and error handling.
"""

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

import fire

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Interface definitions following SOLID principles
class DataCollector(ABC):
    """Abstract interface for data collection."""

    @abstractmethod
    def collect(self) -> Dict[str, Any]:
        """Collect data from the source."""
        pass


class DataExporter(ABC):
    """Abstract interface for data export."""

    @abstractmethod
    def export(self, data: Dict[str, Any], output_path: Path) -> None:
        """Export data to the specified path."""
        pass


class IAMCollector(DataCollector):
    """Collects IAM policies and roles from GCP."""

    def __init__(self, use_mock: bool = True):
        """Initialize IAM collector.

        Args:
            use_mock: If True, use mock data instead of real GCP API.
        """
        self.use_mock = use_mock

    def collect(self) -> Dict[str, Any]:
        """Collect IAM policies and roles.

        Returns:
            Dictionary containing IAM policies and roles.
        """
        logger.info("Collecting IAM policies and roles...")

        if self.use_mock:
            return self._get_mock_iam_data()

        # Real GCP implementation would go here
        try:
            # This would use google-cloud-iam SDK
            # For now, returning mock data
            return self._get_mock_iam_data()
        except Exception as e:
            logger.error(f"Failed to collect IAM data: {e}")
            raise

    def _get_mock_iam_data(self) -> Dict[str, Any]:
        """Get mock IAM data for testing."""
        return {
            "policies": [
                {
                    "resource": "projects/test-project",
                    "bindings": [
                        {
                            "role": "roles/owner",
                            "members": ["user:admin@example.com"],
                        },
                        {
                            "role": "roles/editor",
                            "members": [
                                "user:developer@example.com",
                                "serviceAccount:app@test-project.iam.gserviceaccount.com",
                            ],
                        },
                    ],
                }
            ],
            "custom_roles": [
                {
                    "name": "projects/test-project/roles/customDeveloper",
                    "title": "Custom Developer Role",
                    "permissions": ["compute.instances.list", "compute.instances.get"],
                }
            ],
        }


class SCCFindingsCollector(DataCollector):
    """Collects Security Command Center findings from GCP."""

    def __init__(self, use_mock: bool = True):
        """Initialize SCC findings collector.

        Args:
            use_mock: If True, use mock data instead of real GCP API.
        """
        self.use_mock = use_mock

    def collect(self) -> Dict[str, Any]:
        """Collect Security Command Center findings.

        Returns:
            Dictionary containing SCC findings.
        """
        logger.info("Collecting Security Command Center findings...")

        if self.use_mock:
            return self._get_mock_scc_data()

        # Real GCP implementation would go here
        try:
            # This would use google-cloud-securitycenter SDK
            # For now, returning mock data
            return self._get_mock_scc_data()
        except Exception as e:
            logger.error(f"Failed to collect SCC findings: {e}")
            raise

    def _get_mock_scc_data(self) -> Dict[str, Any]:
        """Get mock SCC findings for testing."""
        return {
            "findings": [
                {
                    "name": "organizations/123/sources/456/findings/789",
                    "category": "PUBLIC_BUCKET",
                    "severity": "HIGH",
                    "state": "ACTIVE",
                    "resource_name": "//storage.googleapis.com/public-bucket-123",
                    "source_properties": {
                        "explanation": "Storage bucket is publicly accessible",
                        "recommendation": "Remove allUsers and allAuthenticatedUsers from bucket IAM policy",
                    },
                },
                {
                    "name": "organizations/123/sources/456/findings/790",
                    "category": "OVERLY_PERMISSIVE_IAM",
                    "severity": "MEDIUM",
                    "state": "ACTIVE",
                    "resource_name": "//cloudresourcemanager.googleapis.com/projects/test-project",
                    "source_properties": {
                        "explanation": "Service account has editor role at project level",
                        "recommendation": "Apply principle of least privilege",
                    },
                },
            ]
        }


class JSONExporter(DataExporter):
    """Exports data to JSON format."""

    def export(self, data: Dict[str, Any], output_path: Path) -> None:
        """Export data to JSON file.

        Args:
            data: Data to export.
            output_path: Path to output file.
        """
        logger.info(f"Exporting data to {output_path}")

        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Successfully exported data to {output_path}")
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            raise


class GCPConfigurationCollector:
    """Main collector orchestrator following SOLID principles."""

    def __init__(
        self,
        collectors: Optional[List[DataCollector]] = None,
        exporter: Optional[DataExporter] = None,
    ):
        """Initialize the configuration collector.

        Args:
            collectors: List of data collectors to use.
            exporter: Data exporter to use.
        """
        self.collectors = collectors or []
        self.exporter = exporter or JSONExporter()

    def add_collector(self, collector: DataCollector) -> None:
        """Add a data collector.

        Args:
            collector: Data collector to add.
        """
        self.collectors.append(collector)

    def collect_all(self) -> Dict[str, Any]:
        """Collect data from all collectors.

        Returns:
            Combined data from all collectors.
        """
        logger.info("Starting data collection...")
        collected_data = {}

        for collector in self.collectors:
            try:
                collector_name = collector.__class__.__name__
                logger.info(f"Running {collector_name}...")
                data = collector.collect()
                collected_data[collector_name] = data
            except Exception as e:
                logger.error(f"Failed to collect from {collector_name}: {e}")
                # Continue with other collectors
                collected_data[collector_name] = {"error": str(e)}

        logger.info("Data collection completed")
        return collected_data

    def run(self, output_path: str = "data/collected.json") -> None:
        """Run the collection process and export results.

        Args:
            output_path: Path to output file.
        """
        data = self.collect_all()
        self.exporter.export(data, Path(output_path))


def main(
    output_path: str = "data/collected.json",
    use_mock: bool = True,
    verbose: bool = False,
) -> None:
    """Main entry point for the GCP Configuration Collector.

    Args:
        output_path: Path to output file.
        use_mock: If True, use mock data instead of real GCP API.
        verbose: If True, enable verbose logging.
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create collector with all components
    collector = GCPConfigurationCollector()

    # Add collectors
    collector.add_collector(IAMCollector(use_mock=use_mock))
    collector.add_collector(SCCFindingsCollector(use_mock=use_mock))

    # Run collection
    try:
        collector.run(output_path)
        logger.info("Collection completed successfully")
    except Exception as e:
        logger.error(f"Collection failed: {e}")
        raise


if __name__ == "__main__":
    fire.Fire(main)