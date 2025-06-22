"""Base module for cloud provider interfaces."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class CloudProvider(ABC):
    """Abstract base class for cloud providers."""

    @abstractmethod
    def __init__(self, **kwargs):
        """Initialize the cloud provider with necessary credentials."""

    @abstractmethod
    def get_name(self) -> str:
        """Return the name of the cloud provider."""

    @abstractmethod
    def get_iam_policies(self) -> Dict[str, Any]:
        """Retrieve IAM/identity policies from the cloud provider."""

    @abstractmethod
    def get_security_findings(self) -> List[Dict[str, Any]]:
        """Retrieve security findings/alerts from the cloud provider."""

    @abstractmethod
    def get_audit_logs(self) -> List[Dict[str, Any]]:
        """Retrieve audit/activity logs from the cloud provider."""

    @abstractmethod
    def collect_all(self) -> Dict[str, Any]:
        """Collect all security-related data from the cloud provider."""
