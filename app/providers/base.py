"""Base module for cloud provider interfaces."""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class CloudProvider(ABC):
    """Abstract base class for cloud providers."""

    def __init__(self, **kwargs):
        """Initialize the cloud provider with necessary credentials."""
        self.retry_delay = kwargs.get('retry_delay', 1.0)
        self.max_retries = kwargs.get('max_retries', 3)

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

    def collect_all(self) -> Dict[str, Any]:
        """Collect all security-related data from the cloud provider.
        
        This template method collects data from all provider methods
        and returns a standardized structure.
        """
        result = {
            "provider": self.get_name(),
        }
        
        # Add provider-specific attributes if they exist
        for attr in ['account_id', 'subscription_id', 'tenant_id', 'region', 'organization_id']:
            if hasattr(self, attr):
                result[attr] = getattr(self, attr)
        
        # Collect data with retry logic
        result["iam_policies"] = self.collect_with_retry(self.get_iam_policies)
        result["security_findings"] = self.collect_with_retry(self.get_security_findings)
        result["audit_logs"] = self.collect_with_retry(self.get_audit_logs)
        
        return result

    def collect_with_retry(
        self, 
        collect_func: Callable[[], Any], 
        fallback_value: Optional[Any] = None
    ) -> Any:
        """Execute a collection function with retry logic.
        
        Args:
            collect_func: Function to execute
            fallback_value: Value to return if all retries fail
            
        Returns:
            Result from the function or fallback value
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return collect_func()
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"{self.get_name()}: {collect_func.__name__} failed "
                    f"(attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
        
        logger.error(
            f"{self.get_name()}: {collect_func.__name__} failed after "
            f"{self.max_retries} attempts: {last_exception}"
        )
        
        if fallback_value is None:
            # Return appropriate empty value based on return type hint
            if hasattr(collect_func, '__annotations__'):
                return_type = collect_func.__annotations__.get('return', type(None))
                if hasattr(return_type, '__origin__'):
                    if return_type.__origin__ is list:
                        return []
                    elif return_type.__origin__ is dict:
                        return {}
            return {}  # Default fallback
        return fallback_value
