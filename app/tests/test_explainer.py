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

    @patch("explainer.agent_explainer.time.sleep")
    def test_call_llm_with_retry(self, mock_sleep):
        """Test LLM call with retry logic"""
        analyzer = GeminiSecurityAnalyzer(
            project_id="test-project",
            use_mock=False,
        )

        # Mock the model
        mock_response = Mock()
        mock_response.text = (
            '[{"title": "Test", "severity": "HIGH", '
            '"explanation": "Test", "recommendation": "Test"}]'
        )
        analyzer._model = Mock()
        analyzer._model.generate_content.return_value = mock_response

        result = analyzer._call_llm_with_retry("test prompt")

        assert result == mock_response.text
        mock_sleep.assert_called_once_with(1.0)  # Rate limit delay

    @patch("explainer.agent_explainer.time.sleep")
    def test_call_llm_with_retry_failure(self, mock_sleep):
        """Test LLM call retry on failure"""
        analyzer = GeminiSecurityAnalyzer(
            project_id="test-project",
            use_mock=False,
        )

        # Mock the model to fail
        analyzer._model = Mock()
        analyzer._model.generate_content.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            analyzer._call_llm_with_retry("test prompt", max_retries=2)

        # Should have tried twice: 2 rate limit delays + 1 exponential backoff
        assert mock_sleep.call_count == 3

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
            with open(output_path, "r") as f:
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

    @patch("common.auth.os.getenv")
    def test_main_without_credentials_warning(self, mock_getenv):
        """Test warning when GOOGLE_APPLICATION_CREDENTIALS not set"""
        from explainer.agent_explainer import main

        mock_getenv.return_value = None

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
            with tempfile.TemporaryDirectory() as temp_dir:
                main(
                    project_id="test-project",
                    use_mock=False,
                    input_file=temp_file,
                    output_dir=temp_dir,
                )
        except Exception:
            # We expect it to fail without real credentials
            pass
        finally:
            Path(temp_file).unlink()

        mock_getenv.assert_called_with("GOOGLE_APPLICATION_CREDENTIALS")
