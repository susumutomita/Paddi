"""
Cloud provider abstraction interfaces.

This module provides abstract base classes for implementing
cloud-specific collectors in a provider-agnostic way.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Any, Optional


class CloudProvider(Enum):
    """Supported cloud providers."""
    GCP = "gcp"
    AWS = "aws"
    AZURE = "azure"


@dataclass
class CloudConfig:
    """Configuration for cloud provider access."""
    provider: CloudProvider
    project_id: Optional[str] = None  # GCP
    account_id: Optional[str] = None  # AWS
    subscription_id: Optional[str] = None  # Azure
    region: Optional[str] = None
    credentials_path: Optional[str] = None
    use_mock: bool = False


class CloudProviderInterface(ABC):
    """Abstract base class for cloud provider implementations."""
    
    def __init__(self, config: CloudConfig):
        self.config = config
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the cloud provider name."""
        pass
    
    @abstractmethod
    def validate_credentials(self) -> bool:
        """Validate that credentials are properly configured."""
        pass


class IAMCollectorInterface(ABC):
    """Abstract interface for collecting IAM/identity data across clouds."""
    
    @abstractmethod
    def collect_users(self) -> List[Dict[str, Any]]:
        """Collect user/identity information."""
        pass
    
    @abstractmethod
    def collect_roles(self) -> List[Dict[str, Any]]:
        """Collect role definitions."""
        pass
    
    @abstractmethod
    def collect_policies(self) -> List[Dict[str, Any]]:
        """Collect policy attachments and definitions."""
        pass


class SecurityCollectorInterface(ABC):
    """Abstract interface for collecting security findings across clouds."""
    
    @abstractmethod
    def collect_findings(self, severity_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Collect security findings/alerts."""
        pass
    
    @abstractmethod
    def collect_compliance_status(self) -> Dict[str, Any]:
        """Collect compliance/security posture information."""
        pass


class LogCollectorInterface(ABC):
    """Abstract interface for collecting audit logs across clouds."""
    
    @abstractmethod
    def collect_recent_logs(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Collect recent audit/activity logs."""
        pass
    
    @abstractmethod
    def collect_suspicious_activities(self) -> List[Dict[str, Any]]:
        """Collect logs indicating suspicious activities."""
        pass


class CloudCollectorFactory:
    """Factory for creating cloud-specific collector implementations."""
    
    _providers: Dict[CloudProvider, type] = {}
    
    @classmethod
    def register(cls, provider: CloudProvider, implementation: type):
        """Register a cloud provider implementation."""
        cls._providers[provider] = implementation
    
    @classmethod
    def create(cls, config: CloudConfig) -> CloudProviderInterface:
        """Create a cloud provider instance based on config."""
        if config.provider not in cls._providers:
            raise ValueError(f"Unsupported cloud provider: {config.provider}")
        
        implementation = cls._providers[config.provider]
        return implementation(config)