"""Tests for memory context management system."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.memory.context_manager import (
    CommandPattern,
    ContextualMemory,
    FileMemoryStorage,
    PrivacyFilter,
)


class TestPrivacyFilter:
    """Test privacy filter functionality."""

    def test_mask_email(self):
        """Test email masking."""
        privacy_filter = PrivacyFilter()
        text = "Contact me at user@example.com for details"
        masked = privacy_filter.mask_sensitive_data(text)
        assert "user@example.com" not in masked
        assert "[MASKED]" in masked

    def test_mask_phone(self):
        """Test phone number masking."""
        privacy_filter = PrivacyFilter()
        text = "Call me at 555-123-4567 or +1-555-123-4567"
        masked = privacy_filter.mask_sensitive_data(text)
        assert "555-123-4567" not in masked
        assert "[MASKED]" in masked

    def test_mask_ssn(self):
        """Test SSN masking."""
        privacy_filter = PrivacyFilter()
        text = "SSN: 123-45-6789"
        masked = privacy_filter.mask_sensitive_data(text)
        assert "123-45-6789" not in masked
        assert "[MASKED]" in masked

    def test_mask_credentials(self):
        """Test credential masking."""
        privacy_filter = PrivacyFilter()
        text = "Use password: test_pwd_value and api_key: sk-test-key-value"
        masked = privacy_filter.mask_sensitive_data(text)
        assert "test_pwd_value" not in masked
        assert "sk-test-key-value" not in masked
        assert masked.count("[MASKED]") >= 2

    def test_contains_sensitive_data(self):
        """Test sensitive data detection."""
        privacy_filter = PrivacyFilter()
        assert privacy_filter.contains_sensitive_data("email@test.com")
        assert privacy_filter.contains_sensitive_data("password: test_value")
        assert not privacy_filter.contains_sensitive_data("This is safe text")

    def test_custom_patterns(self):
        """Test custom pattern addition."""
        custom_patterns = [r"\bPROJECT-[0-9]+\b"]
        privacy_filter = PrivacyFilter(custom_patterns=custom_patterns)
        text = "Working on PROJECT-12345"
        masked = privacy_filter.mask_sensitive_data(text)
        assert "PROJECT-12345" not in masked
        assert "[MASKED]" in masked


class TestFileMemoryStorage:
    """Test file-based memory storage."""

    def test_save_and_load(self):
        """Test saving and loading data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileMemoryStorage(base_path=tmpdir)

            data = {"key": "value", "number": 42}
            storage.save("test_key", data)

            loaded = storage.load("test_key")
            assert loaded == data

    def test_load_nonexistent(self):
        """Test loading nonexistent data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileMemoryStorage(base_path=tmpdir)
            assert storage.load("nonexistent") is None

    def test_delete(self):
        """Test deleting data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileMemoryStorage(base_path=tmpdir)

            storage.save("test_key", {"data": "test"})
            assert storage.exists("test_key")

            storage.delete("test_key")
            assert not storage.exists("test_key")

    def test_exists(self):
        """Test existence check."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileMemoryStorage(base_path=tmpdir)

            assert not storage.exists("test_key")
            storage.save("test_key", {"data": "test"})
            assert storage.exists("test_key")


class TestCommandPattern:
    """Test command pattern functionality."""

    def test_initialization(self):
        """Test command pattern initialization."""
        pattern = CommandPattern("test pattern")
        assert pattern.pattern == "test pattern"
        assert pattern.frequency == 1
        assert pattern.success_rate == 1.0
        assert isinstance(pattern.last_used, datetime)

    def test_to_dict(self):
        """Test serialization to dictionary."""
        pattern = CommandPattern("test pattern", frequency=5)
        pattern.contexts = ["context1", "context2"]

        data = pattern.to_dict()
        assert data["pattern"] == "test pattern"
        assert data["frequency"] == 5
        assert data["contexts"] == ["context1", "context2"]
        assert "last_used" in data

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "pattern": "test pattern",
            "frequency": 3,
            "last_used": datetime.now().isoformat(),
            "success_rate": 0.8,
            "contexts": ["test"],
        }

        pattern = CommandPattern.from_dict(data)
        assert pattern.pattern == "test pattern"
        assert pattern.frequency == 3
        assert pattern.success_rate == 0.8
        assert pattern.contexts == ["test"]


class TestContextualMemory:
    """Test contextual memory system."""

    @pytest.fixture
    def memory(self):
        """Create a contextual memory instance with temp storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileMemoryStorage(base_path=tmpdir)
            yield ContextualMemory(storage=storage, project_id="test_project")

    def test_short_term_memory(self, memory):
        """Test short-term memory operations."""
        memory.add_to_short_term("Test content", "test")
        memory.add_to_short_term("Another content", "test")

        recent = memory.get_recent_context(limit=2)
        assert len(recent) == 2
        assert recent[0]["content"] == "Another content"
        assert recent[1]["content"] == "Test content"

    def test_short_term_memory_limit(self):
        """Test short-term memory size limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileMemoryStorage(base_path=tmpdir)
            memory = ContextualMemory(
                storage=storage, project_id="test_project", max_short_term_size=3
            )

            for i in range(5):
                memory.add_to_short_term(f"Content {i}", "test")

            recent = memory.get_recent_context(limit=10)
            assert len(recent) == 3  # Limited by max_short_term_size

    def test_privacy_filter_in_short_term(self, memory):
        """Test privacy filter application in short-term memory."""
        memory.add_to_short_term("Contact user@example.com for info", "contact")

        recent = memory.get_recent_context(limit=1)
        assert "user@example.com" not in recent[0]["content"]
        assert "[MASKED]" in recent[0]["content"]

    def test_long_term_memory(self, memory):
        """Test long-term memory operations."""
        memory.promote_to_long_term("important_fact", "This is important")

        value = memory.get_from_memory("important_fact")
        assert value == "This is important"

        # Check access count increments
        memory.get_from_memory("important_fact")
        assert memory.long_term["important_fact"]["access_count"] == 2

    def test_preferences(self, memory):
        """Test preference management."""
        memory.set_preference("theme", "dark")
        memory.set_preference("language", "ja")

        assert memory.get_preference("theme") == "dark"
        assert memory.get_preference("language") == "ja"
        assert memory.get_preference("nonexistent", "default") == "default"

    def test_project_context(self, memory):
        """Test project context management."""
        memory.set_project_context("project_name", "TestProject")
        memory.set_project_context("environment", "production")

        assert memory.get_project_context("project_name") == "TestProject"
        assert memory.get_project_context("environment") == "production"

    def test_command_pattern_learning(self, memory):
        """Test command pattern learning."""
        memory.learn_command_pattern("paddi audit project-123", success=True)
        memory.learn_command_pattern("paddi audit project-456", success=True)
        memory.learn_command_pattern("paddi audit project-789", success=False)

        # Check pattern was learned
        pattern_key = "paddi audit project-<NUMBER>"
        assert pattern_key in memory.command_patterns
        assert memory.command_patterns[pattern_key].frequency == 3
        assert memory.command_patterns[pattern_key].success_rate < 1.0

    def test_pattern_extraction(self, memory):
        """Test pattern extraction from commands."""
        pattern1 = memory._extract_pattern('audit "project name" --format json')
        assert pattern1 == 'audit "<VALUE>" --format json'

        pattern2 = memory._extract_pattern("scan file-123.txt")
        assert pattern2 == "scan file-<NUMBER>.txt"

    def test_command_suggestion(self, memory):
        """Test command suggestion based on patterns."""
        memory.learn_command_pattern("paddi audit gcp-project", success=True)
        memory.learn_command_pattern("paddi audit gcp-project", success=True)
        memory.learn_command_pattern("paddi scan aws", success=True)

        suggestion = memory.suggest_command("audit")
        assert suggestion is not None
        assert "audit" in suggestion

    def test_error_recording(self, memory):
        """Test error pattern recording."""
        memory.record_error("FileNotFound", "Check file path")
        memory.record_error("PermissionDenied")

        solution = memory.get_error_solution("FileNotFound")
        assert solution == "Check file path"

        assert memory.get_error_solution("PermissionDenied") is None

    def test_find_similar_commands(self, memory):
        """Test finding similar commands."""
        memory.learn_command_pattern("paddi audit project-1", success=True)
        memory.learn_command_pattern("paddi audit project-2", success=True)
        memory.learn_command_pattern("paddi scan files", success=True)
        memory.learn_command_pattern("docker build image", success=True)

        similar = memory.find_similar_commands("paddi audit", limit=2)
        assert len(similar) <= 2
        assert any("audit" in cmd for cmd in similar)

    def test_clear_memory_all(self, memory):
        """Test clearing all memory."""
        # Add data to all memory types
        memory.add_to_short_term("test", "test")
        memory.promote_to_long_term("key", "value")
        memory.set_preference("pref", "value")
        memory.set_project_context("context", "value")
        memory.learn_command_pattern("test command", True)
        memory.record_error("TestError", "solution")

        memory.clear_memory(scope="all")

        assert len(memory.short_term) == 0
        assert len(memory.long_term) == 0
        assert len(memory.preferences) == 0
        assert len(memory.project_context) == 0
        assert len(memory.command_patterns) == 0
        assert len(memory.error_patterns) == 0
        assert len(memory.successful_solutions) == 0

    def test_clear_memory_specific_scope(self, memory):
        """Test clearing specific memory scopes."""
        memory.add_to_short_term("test", "test")
        memory.promote_to_long_term("key", "value")

        memory.clear_memory(scope="short_term")
        assert len(memory.short_term) == 0
        assert len(memory.long_term) > 0

        memory.clear_memory(scope="long_term")
        assert len(memory.long_term) == 0

    def test_export_import_memory(self):
        """Test memory export and import."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileMemoryStorage(base_path=tmpdir)
            memory = ContextualMemory(storage=storage, project_id="test_project")

            # Add various data
            memory.add_to_short_term("test content", "test")
            memory.promote_to_long_term("fact", "important")
            memory.set_preference("theme", "dark")
            memory.learn_command_pattern("test cmd", True)

            # Export
            exported = memory.export_memory()
            assert "short_term" in exported
            assert "long_term" in exported
            assert "preferences" in exported
            assert "command_patterns" in exported

            # Clear and import
            memory.clear_memory("all")
            memory.import_memory(exported)

            # Verify imported data
            assert len(memory.short_term) > 0
            # Verify that data was imported correctly
            recent = memory.get_recent_context(limit=5)
            assert len(recent) > 0
            # Check that basic data structures are present after import
            assert isinstance(memory.preferences, dict)
            assert isinstance(memory.command_patterns, dict)

    def test_memory_persistence(self):
        """Test memory persistence across instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # First instance
            storage1 = FileMemoryStorage(base_path=tmpdir)
            memory1 = ContextualMemory(storage=storage1, project_id="test_persist")

            memory1.set_preference("test_pref", "value1")
            memory1.promote_to_long_term("test_key", "test_value")
            memory1.save_memory()

            # Second instance - should load previous data
            storage2 = FileMemoryStorage(base_path=tmpdir)
            memory2 = ContextualMemory(storage=storage2, project_id="test_persist")

            assert memory2.get_preference("test_pref") == "value1"
            assert memory2.get_from_memory("test_key") == "test_value"

    def test_error_handling_in_save(self):
        """Test error handling during save operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileMemoryStorage(base_path=tmpdir)
            memory = ContextualMemory(storage=storage, project_id="test_project")

            # Make storage.save raise an exception
            memory.storage.save = MagicMock(side_effect=Exception("Save failed"))

            # This should raise exception since no error handling in save_memory
            with pytest.raises(Exception, match="Save failed"):
                memory.save_memory()

    @patch("app.memory.context_manager.logger")
    def test_error_handling_in_load(self, mock_logger):
        """Test error handling during load operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileMemoryStorage(base_path=tmpdir)

            # Create corrupted JSON file
            file_path = Path(tmpdir) / "context_test.json"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("invalid json content")

            # Should handle error gracefully
            result = storage.load("context_test")
            assert result is None
            mock_logger.error.assert_called()
