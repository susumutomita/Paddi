"""Factory module for creating cloud provider instances."""

from typing import Any, Dict

from .aws import AWSProvider
from .azure import AzureProvider
from .base import CloudProvider
from .gcp import GCPProvider


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
            supported = list(cls._providers.keys())
            raise ValueError(
                f"Unsupported provider: {provider_name}. " f"Supported providers: {supported}"
            )

        provider_class = cls._providers[provider_name]
        return provider_class(**kwargs)

    @classmethod
    def get_supported_providers(cls) -> list:
        """Get list of supported cloud providers."""
        return list(cls._providers.keys())

    def create_provider(self, provider_config: Dict[str, Any]) -> CloudProvider:
        """
        Create a cloud provider instance from configuration.

        This is an instance method for compatibility with the multi-cloud collector.

        Args:
            provider_config: Configuration dict with 'provider' key

        Returns:
            CloudProvider instance
        """
        provider_name = provider_config.get("provider", "").lower()
        provider_params = {k: v for k, v in provider_config.items() if k != "provider"}
        return self.create(provider_name, **provider_params)
