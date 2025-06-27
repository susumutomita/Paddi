"""Tests for Ollama security analyzer."""

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from app.common.models import SecurityFinding
from app.explainer.ollama_explainer import OllamaSecurityAnalyzer


class TestOllamaSecurityAnalyzer:
    """Test suite for OllamaSecurityAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        return OllamaSecurityAnalyzer(
            model="llama3",
            endpoint="http://localhost:11434",
            use_mock=True
        )

    @pytest.fixture
    def sample_iam_data(self):
        """Sample IAM configuration data."""
        return {
            "iam_policies": [
                {
                    "resource": "projects/test-project",
                    "bindings": [
                        {
                            "role": "roles/owner",
                            "members": ["user:admin@example.com", "user:dev@example.com"]
                        }
                    ]
                }
            ]
        }

    @pytest.fixture
    def sample_scc_data(self):
        """Sample Security Command Center findings."""
        return {
            "scc_findings": [
                {
                    "name": "organizations/123/sources/456/findings/789",
                    "category": "PUBLIC_BUCKET",
                    "severity": "HIGH",
                    "resourceName": "//storage.googleapis.com/test-bucket"
                }
            ]
        }

    @pytest.fixture
    def sample_multi_cloud_data(self):
        """Sample multi-cloud configuration data."""
        return {
            "providers": [
                {
                    "provider": "gcp",
                    "iam_policies": [{"resource": "projects/test", "bindings": []}],
                    "security_findings": []
                },
                {
                    "provider": "aws",
                    "iam_policies": [{"user": "admin-user", "policies": ["AdministratorAccess"]}],
                    "security_findings": []
                },
                {
                    "provider": "azure",
                    "iam_policies": [{"subscription": "test-sub", "assignments": []}],
                    "security_findings": []
                }
            ]
        }

    def test_initialization_with_mock(self, analyzer):
        """Test analyzer initialization with mock mode."""
        assert analyzer.model == "llama3"
        assert analyzer.endpoint == "http://localhost:11434"
        assert analyzer.use_mock is True
        assert analyzer.temperature == 0.2
        assert analyzer.max_output_tokens == 2048

    @patch('requests.get')
    def test_verify_ollama_server_success(self, mock_get):
        """Test successful Ollama server verification."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3", "modified_at": "2024-01-01T00:00:00Z"},
                {"name": "codellama", "modified_at": "2024-01-01T00:00:00Z"}
            ]
        }
        mock_get.return_value = mock_response
        
        analyzer = OllamaSecurityAnalyzer(model="llama3", use_mock=False)
        assert analyzer.model == "llama3"

    @patch('requests.get')
    def test_verify_ollama_server_connection_error(self, mock_get):
        """Test Ollama server connection error."""
        mock_get.side_effect = requests.ConnectionError("Connection refused")
        
        with pytest.raises(requests.ConnectionError):
            OllamaSecurityAnalyzer(model="llama3", use_mock=False)

    @patch('requests.get')
    @patch('requests.post')
    def test_pull_model_when_not_found(self, mock_post, mock_get):
        """Test model pulling when model is not found."""
        # Mock the initial check showing model not found
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {"models": []}
        mock_get.return_value = mock_get_response
        
        # Mock the pull request
        mock_post_response = MagicMock()
        mock_post_response.json.return_value = {"status": "success"}
        mock_post.return_value = mock_post_response
        
        analyzer = OllamaSecurityAnalyzer(model="llama3", use_mock=False)
        
        # Verify pull was called
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:11434/api/pull"
        assert call_args[1]["json"]["name"] == "llama3"

    def test_analyze_security_risks_with_mock(self, analyzer, sample_iam_data):
        """Test security risk analysis with mock data."""
        findings = analyzer.analyze_security_risks(sample_iam_data)
        
        assert len(findings) > 0
        assert all(isinstance(f, SecurityFinding) for f in findings)
        assert all(f.severity in ["HIGH", "MEDIUM", "LOW"] for f in findings)

    def test_analyze_multi_cloud_data(self, analyzer, sample_multi_cloud_data):
        """Test multi-cloud data analysis."""
        findings = analyzer.analyze_security_risks(sample_multi_cloud_data)
        
        assert len(findings) > 0
        # Should have findings for multiple providers
        assert any("AWS" in f.title for f in findings)
        assert any("Azure" in f.title for f in findings)

    @patch('requests.post')
    def test_call_ollama_success(self, mock_post):
        """Test successful Ollama API call."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": json.dumps([
                {
                    "title": "Test Finding",
                    "severity": "HIGH",
                    "explanation": "Test explanation",
                    "recommendation": "Test recommendation"
                }
            ])
        }
        mock_post.return_value = mock_response
        
        analyzer = OllamaSecurityAnalyzer(use_mock=False)
        response = analyzer._call_ollama("test prompt")
        
        assert isinstance(response, str)
        assert "Test Finding" in response

    @patch('requests.post')
    def test_call_ollama_timeout(self, mock_post):
        """Test Ollama API call timeout."""
        mock_post.side_effect = requests.Timeout("Request timed out")
        
        analyzer = OllamaSecurityAnalyzer(use_mock=False, timeout=10)
        
        with pytest.raises(RuntimeError) as exc_info:
            analyzer._call_ollama("test prompt", max_retries=2)
        
        assert "Failed to get Ollama response" in str(exc_info.value)

    @patch('requests.post')
    def test_call_ollama_http_error(self, mock_post):
        """Test Ollama API HTTP error."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_post.return_value = mock_response
        
        analyzer = OllamaSecurityAnalyzer(use_mock=False)
        
        with pytest.raises(RuntimeError):
            analyzer._call_ollama("test prompt", max_retries=1)

    def test_parse_ollama_response_valid_json(self, analyzer):
        """Test parsing valid JSON response."""
        response = """Here's the analysis:
        [
            {
                "title": "Security Issue 1",
                "severity": "HIGH",
                "explanation": "This is a security issue",
                "recommendation": "Fix this issue"
            },
            {
                "title": "Security Issue 2",
                "severity": "medium",
                "explanation": "Another issue",
                "recommendation": "Address this"
            }
        ]
        """
        
        findings = analyzer._parse_ollama_response(response)
        
        assert len(findings) == 2
        assert findings[0]["title"] == "Security Issue 1"
        assert findings[0]["severity"] == "HIGH"
        assert findings[1]["severity"] == "MEDIUM"  # Should be normalized

    def test_parse_ollama_response_invalid_json(self, analyzer):
        """Test parsing invalid JSON response."""
        response = "This is not valid JSON"
        
        findings = analyzer._parse_ollama_response(response)
        assert findings == []

    def test_parse_ollama_response_missing_fields(self, analyzer):
        """Test parsing response with missing required fields."""
        response = """[
            {
                "title": "Complete Finding",
                "severity": "HIGH",
                "explanation": "Explanation",
                "recommendation": "Recommendation"
            },
            {
                "title": "Incomplete Finding",
                "severity": "HIGH"
            }
        ]"""
        
        findings = analyzer._parse_ollama_response(response)
        
        # Should only include the complete finding
        assert len(findings) == 1
        assert findings[0]["title"] == "Complete Finding"

    def test_analyze_iam_policies_mock(self, analyzer):
        """Test IAM policy analysis with mock data."""
        iam_data = {
            "policies": [{"role": "roles/owner"}]
        }
        
        findings = analyzer._analyze_iam_policies(iam_data)
        
        assert len(findings) > 0
        assert findings[0].severity == "HIGH"

    def test_analyze_iam_policies_by_provider(self, analyzer):
        """Test provider-specific IAM policy analysis."""
        # AWS
        aws_findings = analyzer._analyze_iam_policies({}, provider_name="aws")
        assert any("AWS" in f.title for f in aws_findings)
        
        # Azure
        azure_findings = analyzer._analyze_iam_policies({}, provider_name="azure")
        assert any("Azure" in f.title for f in azure_findings)
        
        # GCP
        gcp_findings = analyzer._analyze_iam_policies({}, provider_name="gcp")
        assert any("Owner" in f.title for f in gcp_findings)

    def test_analyze_provider_with_error(self, analyzer):
        """Test handling provider data with errors."""
        provider_data = {
            "provider": "aws",
            "error": "Failed to connect to AWS"
        }
        
        findings = analyzer._analyze_provider_data(provider_data, "aws")
        assert len(findings) == 0

    @patch('requests.post')
    def test_analyze_with_real_ollama_response(self, mock_post):
        """Test analysis with realistic Ollama response."""
        # Mock a realistic Ollama response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "model": "llama3",
            "created_at": "2024-01-01T00:00:00Z",
            "response": json.dumps([
                {
                    "title": "Excessive IAM Permissions Detected",
                    "severity": "HIGH",
                    "explanation": "The user 'admin@example.com' has been granted the 'roles/owner' role, which provides unrestricted access to all resources in the project. This violates the principle of least privilege and creates a significant security risk.",
                    "recommendation": "Remove the owner role and grant only the specific permissions required for the user's responsibilities. Consider using predefined roles like 'roles/editor' or create custom roles with minimal necessary permissions."
                }
            ]),
            "done": True
        }
        mock_post.return_value = mock_response
        
        analyzer = OllamaSecurityAnalyzer(use_mock=False)
        
        config_data = {
            "iam_policies": [
                {
                    "resource": "projects/test-project",
                    "bindings": [
                        {"role": "roles/owner", "members": ["user:admin@example.com"]}
                    ]
                }
            ]
        }
        
        findings = analyzer.analyze_security_risks(config_data)
        
        assert len(findings) == 1
        assert findings[0].title == "Excessive IAM Permissions Detected"
        assert findings[0].severity == "HIGH"
        assert "least privilege" in findings[0].explanation

    def test_temperature_and_token_settings(self):
        """Test custom temperature and token settings."""
        analyzer = OllamaSecurityAnalyzer(
            temperature=0.5,
            max_output_tokens=4096,
            use_mock=True
        )
        
        assert analyzer.temperature == 0.5
        assert analyzer.max_output_tokens == 4096