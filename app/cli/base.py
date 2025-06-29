"""Base classes for command pattern implementation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class CommandContext:
    """Context object containing all command parameters."""
    
    # Common parameters
    project_id: str = "example-project-123"
    organization_id: Optional[str] = None
    use_mock: bool = True
    verbose: bool = False
    output_dir: str = "output"
    
    # AI-specific parameters
    location: str = "us-central1"
    ai_provider: Optional[str] = None
    ollama_model: Optional[str] = None
    ollama_endpoint: Optional[str] = None
    
    # Init-specific parameters
    skip_run: bool = False
    
    # Multi-cloud parameters
    collect_all: bool = True
    aws_account_id: Optional[str] = None
    aws_region: str = "us-east-1"
    azure_subscription_id: Optional[str] = None
    azure_tenant_id: Optional[str] = None
    github_owner: Optional[str] = None
    github_repo: Optional[str] = None


class Command(ABC):
    """Abstract base class for commands."""
    
    @abstractmethod
    def execute(self, context: CommandContext) -> None:
        """Execute the command with given context."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the command name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Return the command description."""
        pass