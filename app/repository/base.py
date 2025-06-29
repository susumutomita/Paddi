"""Base repository interface for data persistence."""

from abc import ABC, abstractmethod
from typing import Any, List, Optional


class Repository(ABC):
    """Abstract base class for data repositories."""

    @abstractmethod
    def save(self, key: str, data: Any, **kwargs) -> None:
        """Save data with the given key."""

    @abstractmethod
    def load(self, key: str, **kwargs) -> Optional[Any]:
        """Load data by key. Returns None if not found."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if data exists for the given key."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete data by key."""

    @abstractmethod
    def list_keys(self) -> List[str]:
        """List all available keys."""
