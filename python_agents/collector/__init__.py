"""
Collector module for multi-cloud configuration collection.

Supports collecting security configurations from:
- Google Cloud Platform (GCP)
- Amazon Web Services (AWS)
- Microsoft Azure
"""

from .cloud_provider import (
    CloudProvider,
    CloudConfig,
    CloudProviderInterface,
    IAMCollectorInterface,
    SecurityCollectorInterface,
    LogCollectorInterface,
    CloudCollectorFactory
)

from .multi_cloud_collector import MultiCloudConfigurationCollector

# Import providers to register them with the factory
from . import gcp_provider
from . import aws_provider
from . import azure_provider

__all__ = [
    'CloudProvider',
    'CloudConfig',
    'CloudProviderInterface',
    'IAMCollectorInterface',
    'SecurityCollectorInterface',
    'LogCollectorInterface',
    'CloudCollectorFactory',
    'MultiCloudConfigurationCollector'
]