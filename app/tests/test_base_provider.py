"""Tests for base provider implementation."""

import pytest
from app.providers.base import CloudProvider


class TestCloudProvider:
    """Tests for CloudProvider base class."""

    def test_collect_all_calls_provider_methods(self, mocker):
        """Test that collect_all calls all required provider methods."""
        # Create a concrete implementation for testing
        class TestProvider(CloudProvider):
            def __init__(self):
                pass

            def get_name(self):
                return "test"

            def get_iam_policies(self):
                return {"policies": ["policy1"]}

            def get_security_findings(self):
                return [{"finding": "test"}]

            def get_audit_logs(self):
                return [{"log": "test"}]

        provider = TestProvider()
        
        # Mock all methods to track calls
        mocker.patch.object(provider, 'get_name', return_value="test")
        mocker.patch.object(provider, 'get_iam_policies', return_value={"policies": ["policy1"]})
        mocker.patch.object(provider, 'get_security_findings', return_value=[{"finding": "test"}])
        mocker.patch.object(provider, 'get_audit_logs', return_value=[{"log": "test"}])
        
        # Call collect_all
        result = provider.collect_all()
        
        # Verify all methods were called
        provider.get_name.assert_called_once()
        provider.get_iam_policies.assert_called_once()
        provider.get_security_findings.assert_called_once()
        provider.get_audit_logs.assert_called_once()
        
        # Verify result structure
        assert result["provider"] == "test"
        assert result["iam_policies"] == {"policies": ["policy1"]}
        assert result["security_findings"] == [{"finding": "test"}]
        assert result["audit_logs"] == [{"log": "test"}]

    def test_collect_with_retry_success(self, mocker):
        """Test collect_with_retry succeeds on first attempt."""
        class TestProvider(CloudProvider):
            def __init__(self):
                self.retry_delay = 0.1
                self.max_retries = 3

            def get_name(self):
                return "test"

            def get_iam_policies(self):
                return {}

            def get_security_findings(self):
                return []

            def get_audit_logs(self):
                return []

        provider = TestProvider()
        mock_func = mocker.Mock(return_value={"data": "test"})
        
        result = provider.collect_with_retry(mock_func)
        
        assert result == {"data": "test"}
        assert mock_func.call_count == 1

    def test_collect_with_retry_eventual_success(self, mocker):
        """Test collect_with_retry succeeds after failures."""
        class TestProvider(CloudProvider):
            def __init__(self):
                self.retry_delay = 0.001  # Fast retry for testing
                self.max_retries = 3

            def get_name(self):
                return "test"

            def get_iam_policies(self):
                return {}

            def get_security_findings(self):
                return []

            def get_audit_logs(self):
                return []

        provider = TestProvider()
        mock_func = mocker.Mock(
            side_effect=[Exception("Error 1"), Exception("Error 2"), {"data": "test"}]
        )
        
        result = provider.collect_with_retry(mock_func)
        
        assert result == {"data": "test"}
        assert mock_func.call_count == 3

    def test_collect_with_retry_all_failures(self, mocker):
        """Test collect_with_retry returns fallback after all retries fail."""
        class TestProvider(CloudProvider):
            def __init__(self):
                self.retry_delay = 0.001  # Fast retry for testing
                self.max_retries = 2

            def get_name(self):
                return "test"

            def get_iam_policies(self):
                return {}

            def get_security_findings(self):
                return []

            def get_audit_logs(self):
                return []

        provider = TestProvider()
        mock_func = mocker.Mock(side_effect=Exception("Always fails"))
        
        result = provider.collect_with_retry(mock_func, fallback_value={"fallback": True})
        
        assert result == {"fallback": True}
        assert mock_func.call_count == 2