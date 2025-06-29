"""Tests for repository factory module."""

from unittest.mock import Mock, patch

import pytest

from app.repository.factory import RepositoryFactory


class TestRepositoryFactory:
    """Test RepositoryFactory class."""

    def test_create_file_repository_default_path(self):
        """Test creating file repository with default path."""
        with patch("app.repository.factory.FileRepository") as mock_file_repo:
            mock_instance = Mock()
            mock_file_repo.return_value = mock_instance

            result = RepositoryFactory.create("file")

            assert result == mock_instance
            mock_file_repo.assert_called_once_with("data")

    def test_create_file_repository_custom_path(self):
        """Test creating file repository with custom path."""
        with patch("app.repository.factory.FileRepository") as mock_file_repo:
            mock_instance = Mock()
            mock_file_repo.return_value = mock_instance
            custom_path = "custom/path"

            result = RepositoryFactory.create("file", base_path=custom_path)

            assert result == mock_instance
            mock_file_repo.assert_called_once_with(custom_path)

    def test_create_memory_repository(self):
        """Test creating memory repository."""
        with patch("app.repository.factory.MemoryRepository") as mock_memory_repo:
            mock_instance = Mock()
            mock_memory_repo.return_value = mock_instance

            result = RepositoryFactory.create("memory")

            assert result == mock_instance
            mock_memory_repo.assert_called_once_with()

    def test_create_memory_repository_ignores_kwargs(self):
        """Test that memory repository ignores extra kwargs."""
        with patch("app.repository.factory.MemoryRepository") as mock_memory_repo:
            mock_instance = Mock()
            mock_memory_repo.return_value = mock_instance

            result = RepositoryFactory.create("memory", base_path="ignored", extra="also_ignored")

            assert result == mock_instance
            mock_memory_repo.assert_called_once_with()

    def test_create_unknown_repository_type(self):
        """Test creating repository with unknown type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            RepositoryFactory.create("unknown")

        assert "Unknown repository type: unknown" in str(exc_info.value)

    def test_create_with_empty_string(self):
        """Test creating repository with empty string type."""
        with pytest.raises(ValueError) as exc_info:
            RepositoryFactory.create("")

        assert "Unknown repository type: " in str(exc_info.value)

    def test_get_default_returns_file_repository(self):
        """Test get_default returns file repository with default path."""
        with patch("app.repository.factory.FileRepository") as mock_file_repo:
            mock_instance = Mock()
            mock_file_repo.return_value = mock_instance

            result = RepositoryFactory.get_default()

            assert result == mock_instance
            mock_file_repo.assert_called_once_with("data")

    def test_get_default_multiple_calls(self):
        """Test multiple calls to get_default create new instances."""
        with patch("app.repository.factory.FileRepository") as mock_file_repo:
            mock_instance1 = Mock()
            mock_instance2 = Mock()
            mock_file_repo.side_effect = [mock_instance1, mock_instance2]

            result1 = RepositoryFactory.get_default()
            result2 = RepositoryFactory.get_default()

            assert result1 == mock_instance1
            assert result2 == mock_instance2
            assert mock_file_repo.call_count == 2

    def test_create_is_static_method(self):
        """Test that create is a static method."""
        # Should be callable without instance
        assert callable(RepositoryFactory.create)
        # Should not have self parameter
        import inspect

        params = inspect.signature(RepositoryFactory.create).parameters
        assert "self" not in params
        assert "cls" not in params

    def test_get_default_is_static_method(self):
        """Test that get_default is a static method."""
        # Should be callable without instance
        assert callable(RepositoryFactory.get_default)
        # Should not have self parameter
        import inspect

        params = inspect.signature(RepositoryFactory.get_default).parameters
        assert "self" not in params
        assert "cls" not in params
