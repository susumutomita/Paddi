"""Tests for custom exceptions."""

import pytest

from app.common.exceptions import (
    AuthenticationError,
    CollectionError,
    ConfigurationError,
    PaddiException,
)


class TestPaddiException:
    """Test PaddiException class."""

    def test_init_with_message_only(self):
        """Test initialization with message only."""
        exc = PaddiException("Test error")
        assert str(exc) == "Test error"
        assert exc.message == "Test error"
        assert exc.details == {}

    def test_init_with_details(self):
        """Test initialization with message and details."""
        details = {"code": 500, "reason": "Internal error"}
        exc = PaddiException("Test error", details)
        assert exc.message == "Test error"
        assert exc.details == details
        assert exc.details["code"] == 500


class TestAuthenticationError:
    """Test AuthenticationError class."""

    def test_init_default_provider(self):
        """Test initialization with default provider."""
        exc = AuthenticationError()
        assert exc.message == "認証エラー: GCPへの認証に失敗しました。"
        assert exc.provider == "GCP"
        assert exc.details == {}

    def test_init_custom_provider(self):
        """Test initialization with custom provider."""
        exc = AuthenticationError("AWS")
        assert exc.message == "認証エラー: AWSへの認証に失敗しました。"
        assert exc.provider == "AWS"

    def test_init_with_details(self):
        """Test initialization with provider and details."""
        details = {"reason": "Invalid credentials"}
        exc = AuthenticationError("Azure", details)
        assert exc.message == "認証エラー: Azureへの認証に失敗しました。"
        assert exc.provider == "Azure"
        assert exc.details == details


class TestCollectionError:
    """Test CollectionError class."""

    def test_init_with_resource_type(self):
        """Test initialization with resource type."""
        exc = CollectionError("IAM Policies")
        assert exc.message == "収集エラー: IAM Policiesのデータ収集に失敗しました。"
        assert exc.resource_type == "IAM Policies"
        assert exc.details == {}

    def test_init_with_details(self):
        """Test initialization with resource type and details."""
        details = {"api_error": "Permission denied"}
        exc = CollectionError("SCC Findings", details)
        assert exc.message == "収集エラー: SCC Findingsのデータ収集に失敗しました。"
        assert exc.resource_type == "SCC Findings"
        assert exc.details == details


class TestConfigurationError:
    """Test ConfigurationError class."""

    def test_init_with_config_item(self):
        """Test initialization with config item."""
        exc = ConfigurationError("project_id")
        assert exc.message == "設定エラー: project_idの設定が無効です。"
        assert exc.config_item == "project_id"
        assert exc.details == {}

    def test_init_with_details(self):
        """Test initialization with config item and details."""
        details = {"expected": "string", "got": "number"}
        exc = ConfigurationError("api_key", details)
        assert exc.message == "設定エラー: api_keyの設定が無効です。"
        assert exc.config_item == "api_key"
        assert exc.details == details


class TestExceptionInheritance:
    """Test exception inheritance and behavior."""

    def test_all_inherit_from_paddi_exception(self):
        """Test that all custom exceptions inherit from PaddiException."""
        assert issubclass(AuthenticationError, PaddiException)
        assert issubclass(CollectionError, PaddiException)
        assert issubclass(ConfigurationError, PaddiException)

    def test_can_catch_as_paddi_exception(self):
        """Test that specific exceptions can be caught as PaddiException."""
        with pytest.raises(PaddiException):
            raise AuthenticationError()

        with pytest.raises(PaddiException):
            raise CollectionError("test")

        with pytest.raises(PaddiException):
            raise ConfigurationError("test")

    def test_can_catch_specific_exception(self):
        """Test that specific exceptions can be caught individually."""
        with pytest.raises(AuthenticationError):
            raise AuthenticationError()

        # Should not catch other exceptions
        with pytest.raises(CollectionError):
            try:
                raise CollectionError("test")
            except AuthenticationError:
                pass  # This should not catch CollectionError
