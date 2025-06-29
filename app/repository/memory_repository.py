"""In-memory repository implementation."""

from typing import Any, Dict, List, Optional

from .base import Repository


class MemoryRepository(Repository):
    """In-memory repository for testing and caching."""
    
    def __init__(self):
        """Initialize memory repository."""
        self._storage: Dict[str, Any] = {}
    
    def save(self, key: str, data: Any, **kwargs) -> None:
        """Save data in memory."""
        self._storage[key] = data
    
    def load(self, key: str, **kwargs) -> Optional[Any]:
        """Load data from memory."""
        return self._storage.get(key)
    
    def exists(self, key: str) -> bool:
        """Check if key exists in memory."""
        return key in self._storage
    
    def delete(self, key: str) -> None:
        """Delete data from memory."""
        self._storage.pop(key, None)
    
    def list_keys(self) -> List[str]:
        """List all keys in memory."""
        return list(self._storage.keys())