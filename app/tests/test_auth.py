"""
Unit tests for the authentication utilities.
"""

import logging
from unittest.mock import patch

import pytest
from common.auth import check_gcp_credentials


class TestCheckGCPCredentials:
    """Test cases for check_gcp_credentials function."""

    @patch("common.auth.os.getenv")
    def test_check_gcp_credentials_with_mock(self, mock_getenv):
        """Test that no warning is logged when use_mock is True."""
        with patch("common.auth.logger") as mock_logger:
            check_gcp_credentials(use_mock=True)
            mock_logger.warning.assert_not_called()
            mock_getenv.assert_not_called()

    @patch("common.auth.os.getenv")
    def test_check_gcp_credentials_with_credentials_set(self, mock_getenv):
        """Test that no warning is logged when credentials are set."""
        mock_getenv.return_value = "/path/to/credentials.json"
        
        with patch("common.auth.logger") as mock_logger:
            check_gcp_credentials(use_mock=False)
            mock_logger.warning.assert_not_called()
            mock_getenv.assert_called_once_with("GOOGLE_APPLICATION_CREDENTIALS")

    @patch("common.auth.os.getenv")
    def test_check_gcp_credentials_without_credentials(self, mock_getenv):
        """Test that warning is logged when credentials are not set."""
        mock_getenv.return_value = None
        
        with patch("common.auth.logger") as mock_logger:
            check_gcp_credentials(use_mock=False)
            mock_logger.warning.assert_called_once_with(
                "GOOGLE_APPLICATION_CREDENTIALS not set. Using application default credentials."
            )
            mock_getenv.assert_called_once_with("GOOGLE_APPLICATION_CREDENTIALS")

    @patch("common.auth.os.getenv")
    def test_check_gcp_credentials_with_empty_string(self, mock_getenv):
        """Test that warning is logged when credentials are empty string."""
        mock_getenv.return_value = ""
        
        with patch("common.auth.logger") as mock_logger:
            check_gcp_credentials(use_mock=False)
            mock_logger.warning.assert_called_once_with(
                "GOOGLE_APPLICATION_CREDENTIALS not set. Using application default credentials."
            )