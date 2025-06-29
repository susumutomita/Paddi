"""Factory for creating repository instances."""

from .base import Repository
from .file_repository import FileRepository
from .memory_repository import MemoryRepository


class RepositoryFactory:
    """Factory for creating repository instances."""

    @staticmethod
    def create(repository_type: str = "file", **kwargs) -> Repository:
        """Create a repository instance.

        Args:
            repository_type: Type of repository ('file' or 'memory')
            **kwargs: Additional arguments for repository initialization

        Returns:
            Repository instance

        Raises:
            ValueError: If repository type is unknown
        """
        if repository_type == "file":
            base_path = kwargs.get("base_path", "data")
            return FileRepository(base_path)
        if repository_type == "memory":
            return MemoryRepository()
        raise ValueError(f"Unknown repository type: {repository_type}")

    @staticmethod
    def get_default() -> Repository:
        """Get the default repository (file-based)."""
        return RepositoryFactory.create("file")
