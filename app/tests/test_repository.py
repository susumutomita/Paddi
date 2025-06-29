"""Tests for repository pattern implementation."""

import pytest

from app.repository.base import Repository
from app.repository.file_repository import FileRepository
from app.repository.memory_repository import MemoryRepository


class TestRepository:
    """Tests for base Repository class."""

    def test_repository_abstract_methods(self):
        """Test that Repository is abstract and has required methods."""
        # Test that Repository cannot be instantiated directly
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            Repository()  # pylint: disable=abstract-class-instantiated

        # Verify abstract methods are defined
        assert hasattr(Repository, "save")
        assert hasattr(Repository, "load")
        assert hasattr(Repository, "exists")
        assert hasattr(Repository, "delete")
        assert hasattr(Repository, "list_keys")


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
        assert not repo.list_keys()

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
        FileRepository(temp_dir)

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
        repo.save("test_text", text_data, output_format="text")

        # Check file exists
        file_path = temp_dir / "test_text.txt"
        assert file_path.exists()

        # Load data
        loaded = repo.load("test_text", output_format="text")
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
        assert not repo.list_keys()

        # Save multiple files
        repo.save("file1", {"data": 1})
        repo.save("file2", {"data": 2})
        repo.save("text_file", "text data", output_format="text")

        # Check keys
        keys = repo.list_keys()
        assert len(keys) == 3
        assert set(keys) == {"file1", "file2", "text_file"}

    def test_format_detection(self, temp_dir):
        """Test automatic format detection."""
        repo = FileRepository(temp_dir)

        # Save with different formats
        repo.save("json_file", {"data": "json"})
        repo.save("text_file", "text data", output_format="text")

        # Load should auto-detect format
        json_data = repo.load("json_file")
        assert json_data == {"data": "json"}

        text_data = repo.load("text_file")
        assert text_data == "text data"

    def test_invalid_format(self, temp_dir):
        """Test handling of invalid format."""
        repo = FileRepository(temp_dir)

        with pytest.raises(ValueError, match="Unsupported format"):
            repo.save("test", "data", output_format="invalid")
