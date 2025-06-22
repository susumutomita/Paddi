from typing import Dict, Any
from .base import CloudProvider
from .gcp import GCPProvider
from .aws import AWSProvider
from .azure import AzureProvider


class CloudProviderFactory:
    """Factory class for creating cloud provider instances."""

    _providers = {
        "gcp": GCPProvider,
        "aws": AWSProvider,
        "azure": AzureProvider,
    }

    @classmethod
    def create(cls, provider_name: str, **kwargs) -> CloudProvider:
        """
        Create a cloud provider instance.

        Args:
            provider_name: Name of the cloud provider (gcp, aws, azure)
            **kwargs: Provider-specific configuration

        Returns:
            CloudProvider instance

        Raises:
            ValueError: If provider_name is not supported
        """
        provider_name = provider_name.lower()
        if provider_name not in cls._providers:
            raise ValueError(f"Unsupported provider: {provider_name}. Supported providers: {list(cls._providers.keys())}")

        provider_class = cls._providers[provider_name]
        return provider_class(**kwargs)

    @classmethod
    def get_supported_providers(cls) -> list:
        """Get list of supported cloud providers."""
        return list(cls._providers.keys())