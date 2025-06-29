"""Tests for data service module."""

import logging
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.services.data_service import DataService


class TestDataService:
    """Test DataService class."""

    @pytest.fixture
    def mock_repository(self):
        """Create mock repository."""
        return MagicMock()

    @pytest.fixture
    def data_service(self, mock_repository):
        """Create data service with mock repository."""
        return DataService(repository=mock_repository)

    def test_init_with_repository(self, mock_repository):
        """Test initialization with repository."""
        service = DataService(repository=mock_repository)
        assert service.repository == mock_repository

    def test_init_without_repository(self):
        """Test initialization without repository (uses default)."""
        with patch("app.services.data_service.RepositoryFactory") as mock_factory:
            mock_default_repo = Mock()
            mock_factory.get_default.return_value = mock_default_repo

            service = DataService()
            assert service.repository == mock_default_repo
            mock_factory.get_default.assert_called_once()

    def test_save_collected_data(self, data_service, mock_repository):
        """Test saving collected data."""
        test_data = {"test": "data"}

        result = data_service.save_collected_data(test_data)

        assert result == "collected"
        mock_repository.save.assert_called_once_with("collected", test_data)

    def test_save_collected_data_custom_key(self, data_service, mock_repository):
        """Test saving collected data with custom key."""
        test_data = {"test": "data"}
        custom_key = "custom_collected"

        result = data_service.save_collected_data(test_data, key=custom_key)

        assert result == custom_key
        mock_repository.save.assert_called_once_with(custom_key, test_data)

    def test_load_collected_data_exists(self, data_service, mock_repository):
        """Test loading existing collected data."""
        test_data = {"test": "data"}
        mock_repository.load.return_value = test_data

        result = data_service.load_collected_data()

        assert result == test_data
        mock_repository.load.assert_called_once_with("collected")

    def test_load_collected_data_not_found(self, data_service, mock_repository, caplog):
        """Test loading non-existent collected data."""
        mock_repository.load.return_value = None

        with caplog.at_level(logging.WARNING):
            result = data_service.load_collected_data()

        assert result is None
        assert "No collected data found" in caplog.text

    def test_save_explained_data(self, data_service, mock_repository):
        """Test saving explained data."""
        test_findings = [{"severity": "HIGH", "description": "Test"}]

        result = data_service.save_explained_data(test_findings)

        assert result == "explained"
        mock_repository.save.assert_called_once_with("explained", test_findings)

    def test_save_explained_data_custom_key(self, data_service, mock_repository):
        """Test saving explained data with custom key."""
        test_findings = [{"severity": "HIGH", "description": "Test"}]
        custom_key = "custom_explained"

        result = data_service.save_explained_data(test_findings, key=custom_key)

        assert result == custom_key
        mock_repository.save.assert_called_once_with(custom_key, test_findings)

    def test_load_explained_data_exists(self, data_service, mock_repository):
        """Test loading existing explained data."""
        test_findings = [{"severity": "HIGH", "description": "Test"}]
        mock_repository.load.return_value = test_findings

        result = data_service.load_explained_data()

        assert result == test_findings
        mock_repository.load.assert_called_once_with("explained")

    def test_load_explained_data_not_found(self, data_service, mock_repository, caplog):
        """Test loading non-existent explained data."""
        mock_repository.load.return_value = None

        with caplog.at_level(logging.WARNING):
            result = data_service.load_explained_data()

        assert result is None
        assert "No explained data found" in caplog.text

    def test_save_report(self, data_service, mock_repository):
        """Test saving report."""
        report_content = "# Test Report"
        report_key = "audit_report"

        result = data_service.save_report(report_content, report_key)

        assert result == report_key
        mock_repository.save.assert_called_once_with(report_key, report_content, format="text")

    def test_save_report_with_format(self, data_service, mock_repository):
        """Test saving report with specific format."""
        report_content = "# Test Report"
        report_key = "audit_report"

        result = data_service.save_report(report_content, report_key, data_format="html")

        assert result == report_key
        mock_repository.save.assert_called_once_with(report_key, report_content, format="html")

    def test_load_report_exists(self, data_service, mock_repository):
        """Test loading existing report."""
        report_content = "# Test Report"
        mock_repository.load.return_value = report_content

        result = data_service.load_report("audit_report")

        assert result == report_content
        mock_repository.load.assert_called_once_with("audit_report")

    def test_load_report_not_found(self, data_service, mock_repository, caplog):
        """Test loading non-existent report."""
        mock_repository.load.return_value = None

        with caplog.at_level(logging.WARNING):
            result = data_service.load_report("audit_report")

        assert result is None
        assert "No report found" in caplog.text

    def test_list_available_data(self, data_service, mock_repository):
        """Test listing available data."""
        mock_keys = [
            "collected_2023",
            "collected_2024",
            "explained_2023",
            "explained_2024",
            "audit_report_2023",
            "report_2024",
            "random_data",
        ]
        mock_repository.list_keys.return_value = mock_keys

        result = data_service.list_available_data()

        assert len(result["collected"]) == 2
        assert len(result["explained"]) == 2
        assert len(result["reports"]) == 2
        assert len(result["other"]) == 1
        assert "collected_2023" in result["collected"]
        assert "explained_2023" in result["explained"]
        assert "audit_report_2023" in result["reports"]
        assert "random_data" in result["other"]

    def test_cleanup_old_data_no_cleanup_needed(self, data_service, mock_repository):
        """Test cleanup when no files need to be deleted."""
        mock_repository.list_keys.return_value = ["file1", "file2", "file3"]

        deleted_count = data_service.cleanup_old_data(keep_latest=5)

        assert deleted_count == 0
        mock_repository.delete.assert_not_called()

    def test_cleanup_old_data_with_deletion(self, data_service, mock_repository, caplog):
        """Test cleanup with file deletion."""
        # Mock many collected files
        collected_files = [f"collected_{i:02d}" for i in range(10)]
        mock_repository.list_keys.return_value = collected_files

        with caplog.at_level(logging.INFO):
            deleted_count = data_service.cleanup_old_data(keep_latest=3)

        assert deleted_count == 7  # Should delete 7 files (10 - 3)
        assert mock_repository.delete.call_count == 7
        assert "Cleaned up 7 old data files" in caplog.text

        # Verify the oldest files were deleted
        for i in range(7):
            mock_repository.delete.assert_any_call(f"collected_{i:02d}")

    def test_cleanup_old_data_multiple_categories(self, data_service, mock_repository):
        """Test cleanup with multiple categories."""
        mock_keys = []
        # Add 6 files for each category
        for i in range(6):
            mock_keys.extend(
                [
                    f"collected_{i:02d}",
                    f"explained_{i:02d}",
                    f"audit_report_{i:02d}",
                ]
            )

        mock_repository.list_keys.return_value = mock_keys

        deleted_count = data_service.cleanup_old_data(keep_latest=4)

        # Should delete 2 files from each category (6 - 4 = 2)
        assert deleted_count == 6  # 2 * 3 categories
        assert mock_repository.delete.call_count == 6
