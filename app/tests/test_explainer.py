"""
Unit tests for Agent B: Security Risk Explainer
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from explainer.agent_explainer import (
    GeminiSecurityAnalyzer,
    SecurityFinding,
    SecurityRiskExplainer,
    get_analyzer,
)


class TestSecurityFinding:
    """Test SecurityFinding dataclass"""

    def test_security_finding_creation(self):
        """Test creating a SecurityFinding instance"""
        finding = SecurityFinding(
            title="Test Finding",
            severity="HIGH",
            explanation="This is a test explanation",
            recommendation="This is a test recommendation",
        )

        assert finding.title == "Test Finding"
        assert finding.severity == "HIGH"
        assert finding.explanation == "This is a test explanation"
        assert finding.recommendation == "This is a test recommendation"

    def test_security_finding_to_dict(self):
        """Test converting SecurityFinding to dictionary"""
        finding = SecurityFinding(
            title="Test Finding",
            severity="MEDIUM",
            explanation="Test explanation",
            recommendation="Test recommendation",
        )

        result = finding.to_dict()

        assert isinstance(result, dict)
        assert result["title"] == "Test Finding"
        assert result["severity"] == "MEDIUM"
        assert result["explanation"] == "Test explanation"
        assert result["recommendation"] == "Test recommendation"


class TestGeminiSecurityAnalyzer:
    """Test GeminiSecurityAnalyzer class"""

    def test_initialization_with_mock(self):
        """Test initializing analyzer with mock mode"""
        analyzer = GeminiSecurityAnalyzer(
            project_id="test-project",
            location="us-central1",
            use_mock=True,
        )

        assert analyzer.project_id == "test-project"
        assert analyzer.location == "us-central1"
        assert analyzer.use_mock is True
        assert analyzer._model is None

    @patch("explainer.agent_explainer.aiplatform")
    @patch("explainer.agent_explainer.models")
    def test_initialization_without_mock(self, mock_models, mock_aiplatform):
        """Test initializing analyzer without mock mode"""
        # Mock GenerativeModel
        mock_models.GenerativeModel = Mock()

        GeminiSecurityAnalyzer(
            project_id="test-project",
            location="us-central1",
            use_mock=False,
        )

        mock_aiplatform.init.assert_called_once_with(project="test-project", location="us-central1")
        mock_models.GenerativeModel.assert_called_once_with("gemini-1.5-flash")

    def test_analyze_security_risks_with_mock(self):
        """Test analyzing security risks with mock data"""
        analyzer = GeminiSecurityAnalyzer(
            project_id="test-project",
            use_mock=True,
        )

        configuration = {
            "iam_policies": {"bindings": []},
            "scc_findings": [],
        }

        findings = analyzer.analyze_security_risks(configuration)

        assert len(findings) > 0
        assert all(isinstance(f, SecurityFinding) for f in findings)
        assert all(f.severity in ["HIGH", "MEDIUM", "LOW"] for f in findings)

    def test_mock_iam_findings(self):
        """Test mock IAM findings generation"""
        analyzer = GeminiSecurityAnalyzer(
            project_id="test-project",
            use_mock=True,
        )

        findings = analyzer._get_mock_iam_findings()

        assert len(findings) == 2
        assert findings[0].severity == "HIGH"
        assert "Owner Role" in findings[0].title
        assert findings[1].severity == "MEDIUM"
        assert "Service Account" in findings[1].title

    def test_mock_scc_findings(self):
        """Test mock SCC findings generation"""
        analyzer = GeminiSecurityAnalyzer(
            project_id="test-project",
            use_mock=True,
        )

        findings = analyzer._get_mock_scc_findings()

        assert len(findings) == 2
        assert any("Service Account" in f.title for f in findings)
        assert any("Storage Bucket" in f.title for f in findings)

    def test_parse_llm_response_valid_json(self):
        """Test parsing valid JSON from LLM response"""
        analyzer = GeminiSecurityAnalyzer(
            project_id="test-project",
            use_mock=True,
        )

        response = """Here are the findings:
        [
          {
            "title": "Test Finding",
            "severity": "HIGH",
            "explanation": "Test explanation",
            "recommendation": "Test recommendation"
          }
        ]
        """

        result = analyzer._parse_llm_response(response)

        assert len(result) == 1
        assert result[0]["title"] == "Test Finding"
        assert result[0]["severity"] == "HIGH"

    def test_parse_llm_response_invalid_json(self):
        """Test parsing invalid JSON from LLM response"""
        analyzer = GeminiSecurityAnalyzer(
            project_id="test-project",
            use_mock=True,
        )

        response = "This is not valid JSON"

        result = analyzer._parse_llm_response(response)

        assert result == []

    def test_parse_llm_response_malformed_json(self):
        """Test parsing malformed JSON from LLM response"""
        analyzer = GeminiSecurityAnalyzer(
            project_id="test-project",
            use_mock=True,
        )

        response = '[{"title": "Test", "severity": "HIGH"'  # Incomplete JSON

        result = analyzer._parse_llm_response(response)

        assert result == []


class TestSecurityRiskExplainer:
    """Test SecurityRiskExplainer class"""

    def test_initialization(self):
        """Test initializing SecurityRiskExplainer"""
        explainer = SecurityRiskExplainer(
            project_id="test-project",
            location="us-central1",
            use_mock=True,
        )

        assert explainer.project_id == "test-project"
        assert explainer.location == "us-central1"
        assert explainer.use_mock is True
        assert isinstance(explainer.analyzer, GeminiSecurityAnalyzer)

    def test_load_configuration(self):
        """Test loading configuration from file"""
        # Create temporary test file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            test_data = {
                "project_id": "test-project",
                "iam_policies": {"bindings": []},
                "scc_findings": [],
            }
            json.dump(test_data, f)
            temp_file = f.name

        try:
            explainer = SecurityRiskExplainer(
                project_id="test-project",
                use_mock=True,
                input_file=temp_file,
            )

            config = explainer.load_configuration()

            assert config["project_id"] == "test-project"
            assert "iam_policies" in config
            assert "scc_findings" in config
        finally:
            Path(temp_file).unlink()

    def test_load_configuration_file_not_found(self):
        """Test loading configuration when file doesn't exist"""
        explainer = SecurityRiskExplainer(
            project_id="test-project",
            use_mock=True,
            input_file="nonexistent.json",
        )

        with pytest.raises(FileNotFoundError):
            explainer.load_configuration()

    def test_analyze(self):
        """Test analyze method"""
        # Create temporary test file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            test_data = {
                "project_id": "test-project",
                "iam_policies": {"bindings": []},
                "scc_findings": [],
            }
            json.dump(test_data, f)
            temp_file = f.name

        try:
            explainer = SecurityRiskExplainer(
                project_id="test-project",
                use_mock=True,
                input_file=temp_file,
            )

            findings = explainer.analyze()

            assert isinstance(findings, list)
            assert len(findings) > 0
            assert all(isinstance(f, SecurityFinding) for f in findings)
        finally:
            Path(temp_file).unlink()

    def test_save_findings(self):
        """Test saving findings to file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            explainer = SecurityRiskExplainer(
                project_id="test-project",
                use_mock=True,
                output_dir=temp_dir,
            )

            findings = [
                SecurityFinding(
                    title="Test Finding 1",
                    severity="HIGH",
                    explanation="Test explanation 1",
                    recommendation="Test recommendation 1",
                ),
                SecurityFinding(
                    title="Test Finding 2",
                    severity="MEDIUM",
                    explanation="Test explanation 2",
                    recommendation="Test recommendation 2",
                ),
            ]

            output_path = explainer.save_findings(findings)

            assert output_path.exists()
            assert output_path.name == "explained.json"

            # Verify saved content
            with open(output_path, "r", encoding="utf-8") as f:
                saved_data = json.load(f)

            assert len(saved_data) == 2
            assert saved_data[0]["title"] == "Test Finding 1"
            assert saved_data[0]["severity"] == "HIGH"
            assert saved_data[1]["title"] == "Test Finding 2"
            assert saved_data[1]["severity"] == "MEDIUM"


class TestMainFunction:
    """Test main function"""

    @patch("explainer.agent_explainer.SecurityRiskExplainer")
    def test_main_success(self, mock_explainer_class):
        """Test successful main execution"""
        from explainer.agent_explainer import main

        # Mock the explainer instance
        mock_explainer = Mock()
        mock_findings = [
            SecurityFinding("Test 1", "HIGH", "Explanation 1", "Recommendation 1"),
            SecurityFinding("Test 2", "MEDIUM", "Explanation 2", "Recommendation 2"),
            SecurityFinding("Test 3", "LOW", "Explanation 3", "Recommendation 3"),
        ]
        mock_explainer.analyze.return_value = mock_findings
        mock_explainer.save_findings.return_value = Path("data/explained.json")
        mock_explainer_class.return_value = mock_explainer

        # Run main
        main(
            project_id="test-project",
            location="us-central1",
            use_mock=True,
        )

        # Verify calls
        mock_explainer_class.assert_called_once()
        mock_explainer.analyze.assert_called_once()
        mock_explainer.save_findings.assert_called_once_with(mock_findings)

    @patch("explainer.agent_explainer.SecurityRiskExplainer")
    def test_main_file_not_found(self, mock_explainer_class):
        """Test main handling FileNotFoundError"""
        from explainer.agent_explainer import main

        # Mock the explainer to raise FileNotFoundError
        mock_explainer = Mock()
        mock_explainer.analyze.side_effect = FileNotFoundError("Input file not found")
        mock_explainer_class.return_value = mock_explainer

        # Run main and expect exception
        with pytest.raises(FileNotFoundError):
            main(
                project_id="test-project",
                use_mock=True,
            )


class TestMultiCloudAnalysis:
    """Test multi-cloud analysis capabilities"""

    def test_analyze_multi_cloud_data(self):
        """Test analyzing multi-cloud collected data"""
        analyzer = GeminiSecurityAnalyzer(
            project_id="test-project",
            use_mock=True,
        )

        # Multi-cloud data structure
        multi_cloud_data = {
            "providers": [
                {
                    "provider": "gcp",
                    "project_id": "gcp-project",
                    "iam_policies": {"bindings": []},
                    "security_findings": [],
                },
                {
                    "provider": "aws",
                    "account_id": "123456789012",
                    "iam_policies": {"users": [], "roles": []},
                    "security_findings": [],
                },
                {
                    "provider": "azure",
                    "subscription_id": "test-sub",
                    "iam_policies": {"users": [], "service_principals": []},
                    "security_findings": [],
                },
            ]
        }

        findings = analyzer.analyze_security_risks(multi_cloud_data)

        assert isinstance(findings, list)
        assert len(findings) > 0

        # Should have findings from all providers
        finding_titles = [f.title for f in findings]
        assert any("AWS" in title for title in finding_titles)
        assert any("Azure" in title for title in finding_titles)

    def test_analyze_single_provider_backward_compatibility(self):
        """Test backward compatibility with single provider data"""
        analyzer = GeminiSecurityAnalyzer(
            project_id="test-project",
            use_mock=True,
        )

        # Single provider (GCP) data structure
        single_provider_data = {
            "metadata": {"project_id": "test-project"},
            "iam_policies": {"bindings": []},
            "scc_findings": [],
        }

        findings = analyzer.analyze_security_risks(single_provider_data)

        assert isinstance(findings, list)
        assert len(findings) > 0

    def test_provider_specific_mock_findings(self):
        """Test provider-specific mock findings"""
        analyzer = GeminiSecurityAnalyzer(
            project_id="test-project",
            use_mock=True,
        )

        # Test AWS IAM findings
        aws_iam_findings = analyzer._get_mock_aws_iam_findings()
        assert len(aws_iam_findings) > 0
        assert any("AWS" in f.title for f in aws_iam_findings)
        assert any("AdministratorAccess" in f.explanation for f in aws_iam_findings)

        # Test Azure IAM findings
        azure_iam_findings = analyzer._get_mock_azure_iam_findings()
        assert len(azure_iam_findings) > 0
        assert any("Azure" in f.title for f in azure_iam_findings)
        assert any("Owner" in f.explanation for f in azure_iam_findings)

        # Test AWS security findings
        aws_security_findings = analyzer._get_mock_aws_security_findings()
        assert len(aws_security_findings) > 0
        assert any("S3" in f.title for f in aws_security_findings)

        # Test Azure security findings
        azure_security_findings = analyzer._get_mock_azure_security_findings()
        assert len(azure_security_findings) > 0
        assert any("Storage Account" in f.title for f in azure_security_findings)

    def test_analyze_provider_with_error(self):
        """Test handling provider with collection error"""
        analyzer = GeminiSecurityAnalyzer(
            project_id="test-project",
            use_mock=True,
        )

        data_with_error = {
            "providers": [
                {
                    "provider": "gcp",
                    "project_id": "gcp-project",
                    "iam_policies": {"bindings": []},
                },
                {"provider": "aws", "error": "Failed to connect to AWS", "status": "failed"},
            ]
        }

        findings = analyzer.analyze_security_risks(data_with_error)

        # Should still get findings from successful provider
        assert isinstance(findings, list)
        assert len(findings) > 0


class TestAnalyzerFactory:
    """Test the get_analyzer factory function"""
    
    def test_get_analyzer_gemini_default(self):
        """Test getting Gemini analyzer by default"""
        config = {
            'project_id': 'test-project',
            'use_mock': True
        }
        
        analyzer = get_analyzer(config)
        assert isinstance(analyzer, GeminiSecurityAnalyzer)
    
    def test_get_analyzer_gemini_explicit(self):
        """Test getting Gemini analyzer explicitly"""
        config = {
            'ai_provider': 'gemini',
            'project_id': 'test-project',
            'location': 'asia-northeast1',
            'use_mock': True
        }
        
        analyzer = get_analyzer(config)
        assert isinstance(analyzer, GeminiSecurityAnalyzer)
    
    @patch('explainer.agent_explainer.OllamaSecurityAnalyzer')
    @patch('app.explainer.ollama_explainer.requests.get')
    def test_get_analyzer_ollama(self, mock_get, mock_ollama_class):
        """Test getting Ollama analyzer"""
        # Mock Ollama connection check
        mock_get.return_value.json.return_value = {
            "models": [{"name": "llama3"}]
        }
        mock_get.return_value.raise_for_status = Mock()
        
        config = {
            'ai_provider': 'ollama',
            'ollama_model': 'codellama',
            'ollama_endpoint': 'http://custom:8080'
        }
        
        analyzer = get_analyzer(config)
        
        # Verify Ollama was instantiated with correct params
        mock_ollama_class.assert_called_once_with(
            model='codellama',
            endpoint='http://custom:8080'
        )
    
    def test_security_risk_explainer_with_ollama(self):
        """Test SecurityRiskExplainer with Ollama configuration"""
        import os
        
        with patch.dict(os.environ, {'AI_PROVIDER': 'ollama'}, clear=False):
            with patch('explainer.agent_explainer.get_analyzer') as mock_factory:
                mock_analyzer = Mock()
                mock_factory.return_value = mock_analyzer
                
                explainer = SecurityRiskExplainer(
                    use_mock=True,
                    ai_provider='ollama',
                    ollama_model='mistral'
                )
                
                # Verify factory was called with correct config
                mock_factory.assert_called_once()
                call_config = mock_factory.call_args[0][0]
                assert call_config['ai_provider'] == 'ollama'
                assert call_config['ollama_model'] == 'mistral'
