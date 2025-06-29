"""Tests for repository pattern implementation."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from app.repository.base import Repository
from app.repository.file_repository import FileRepository
from app.repository.memory_repository import MemoryRepository


class TestRepository:
    """Tests for base Repository class."""

    def test_repository_abstract_methods(self):
        """Test that Repository is abstract."""
        with pytest.raises(TypeError):
            Repository()  # Can't instantiate abstract class


class TestMemoryRepository:
    """Tests for MemoryRepository."""

    def test_save_and_load(self):
        """Test saving and loading data."""
        repo = MemoryRepository()
        data = {"test": "data", "numbers": [1, 2, 3]}
        
        # Save data
        repo.save("test_key", data)
        
        # Load data
        loaded = repo.load("test_key")
        assert loaded == data

    def test_load_nonexistent(self):
        """Test loading non-existent data."""
        repo = MemoryRepository()
        
        # Should return None for non-existent key
        assert repo.load("nonexistent") is None

    def test_exists(self):
        """Test checking if data exists."""
        repo = MemoryRepository()
        data = {"test": "data"}
        
        # Initially doesn't exist
        assert not repo.exists("test_key")
        
        # Save data
        repo.save("test_key", data)
        
        # Now it exists
        assert repo.exists("test_key")

    def test_delete(self):
        """Test deleting data."""
        repo = MemoryRepository()
        data = {"test": "data"}
        
        # Save data
        repo.save("test_key", data)
        assert repo.exists("test_key")
        
        # Delete data
        repo.delete("test_key")
        assert not repo.exists("test_key")

    def test_list_keys(self):
        """Test listing all keys."""
        repo = MemoryRepository()
        
        # Initially empty
        assert repo.list_keys() == []
        
        # Save multiple items
        repo.save("key1", {"data": 1})
        repo.save("key2", {"data": 2})
        repo.save("key3", {"data": 3})
        
        # Check keys
        keys = repo.list_keys()
        assert len(keys) == 3
        assert set(keys) == {"key1", "key2", "key3"}


class TestFileRepository:
    """Tests for FileRepository."""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temporary directory for tests."""
        return tmp_path / "test_repo"

    def test_initialization(self, temp_dir):
        """Test FileRepository initialization."""
        repo = FileRepository(temp_dir)
        
        # Directory should be created
        assert temp_dir.exists()
        assert temp_dir.is_dir()

    def test_save_and_load_json(self, temp_dir):
        """Test saving and loading JSON data."""
        repo = FileRepository(temp_dir)
        data = {"test": "data", "numbers": [1, 2, 3]}
        
        # Save data
        repo.save("test_file", data)
        
        # Check file exists
        file_path = temp_dir / "test_file.json"
        assert file_path.exists()
        
        # Load data
        loaded = repo.load("test_file")
        assert loaded == data

    def test_save_and_load_text(self, temp_dir):
        """Test saving and loading text data."""
        repo = FileRepository(temp_dir)
        text_data = "This is test text data\nWith multiple lines"
        
        # Save text data
        repo.save("test_text", text_data, format="text")
        
        # Check file exists
        file_path = temp_dir / "test_text.txt"
        assert file_path.exists()
        
        # Load data
        loaded = repo.load("test_text", format="text")
        assert loaded == text_data

    def test_load_nonexistent(self, temp_dir):
        """Test loading non-existent file."""
        repo = FileRepository(temp_dir)
        
        # Should return None for non-existent file
        assert repo.load("nonexistent") is None

    def test_exists(self, temp_dir):
        """Test checking if file exists."""
        repo = FileRepository(temp_dir)
        
        # Initially doesn't exist
        assert not repo.exists("test_file")
        
        # Save data
        repo.save("test_file", {"test": "data"})
        
        # Now it exists
        assert repo.exists("test_file")

    def test_delete(self, temp_dir):
        """Test deleting file."""
        repo = FileRepository(temp_dir)
        
        # Save data
        repo.save("test_file", {"test": "data"})
        assert repo.exists("test_file")
        
        # Delete file
        repo.delete("test_file")
        assert not repo.exists("test_file")
        
        # File should not exist on disk
        file_path = temp_dir / "test_file.json"
        assert not file_path.exists()

    def test_list_keys(self, temp_dir):
        """Test listing all keys."""
        repo = FileRepository(temp_dir)
        
        # Initially empty
        assert repo.list_keys() == []
        
        # Save multiple files
        repo.save("file1", {"data": 1})
        repo.save("file2", {"data": 2})
        repo.save("text_file", "text data", format="text")
        
        # Check keys
        keys = repo.list_keys()
        assert len(keys) == 3
        assert set(keys) == {"file1", "file2", "text_file"}

    def test_format_detection(self, temp_dir):
        """Test automatic format detection."""
        repo = FileRepository(temp_dir)
        
        # Save with different formats
        repo.save("json_file", {"data": "json"})
        repo.save("text_file", "text data", format="text")
        
        # Load should auto-detect format
        json_data = repo.load("json_file")
        assert json_data == {"data": "json"}
        
        text_data = repo.load("text_file")
        assert text_data == "text data"

    def test_invalid_format(self, temp_dir):
        """Test handling of invalid format."""
        repo = FileRepository(temp_dir)
        
        with pytest.raises(ValueError, match="Unsupported format"):
            repo.save("test", "data", format="invalid")