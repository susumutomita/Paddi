"""Tests for authentication utilities."""

import os
from unittest.mock import patch

from common.auth import check_gcp_credentials


class TestCheckGCPCredentials:
    """Test cases for check_gcp_credentials function."""

    @patch.dict(os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": "/path/to/creds.json"})
    def test_with_credentials_set(self, caplog):
        """Test when GOOGLE_APPLICATION_CREDENTIALS is set."""
        check_gcp_credentials(use_mock=False)

        # Should not log any warning
        assert len([r for r in caplog.records if r.levelname == "WARNING"]) == 0

    @patch.dict(os.environ, {}, clear=True)
    def test_without_credentials_set(self, caplog):
        """Test when GOOGLE_APPLICATION_CREDENTIALS is not set."""
        # Ensure the env var is not set
        if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
            del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

        check_gcp_credentials(use_mock=False)

        # Should log a warning
        warning_records = [r for r in caplog.records if r.levelname == "WARNING"]
        assert len(warning_records) == 1
        assert "GOOGLE_APPLICATION_CREDENTIALS not set" in warning_records[0].message

    def test_with_mock_mode(self, caplog):
        """Test when using mock mode."""
        # Clear any existing env var
        env_backup = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
            del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

        try:
            check_gcp_credentials(use_mock=True)

            # Should not log any warning in mock mode
            assert len([r for r in caplog.records if r.levelname == "WARNING"]) == 0
        finally:
            # Restore env var if it existed
            if env_backup:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = env_backup

    @patch.dict(os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": ""})
    def test_with_empty_credentials(self, caplog):
        """Test when GOOGLE_APPLICATION_CREDENTIALS is empty string."""
        check_gcp_credentials(use_mock=False)

        # Empty string should be treated as not set
        warning_records = [r for r in caplog.records if r.levelname == "WARNING"]
        assert len(warning_records) == 1
        assert "GOOGLE_APPLICATION_CREDENTIALS not set" in warning_records[0].message
