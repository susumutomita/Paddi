"""Tests for Ollama security analyzer."""

import json
from unittest.mock import Mock, patch

import pytest

from app.explainer.ollama_explainer import OllamaSecurityAnalyzer


class TestOllamaSecurityAnalyzer:
    """OllamaSecurityAnalyzerのテスト"""

    @pytest.fixture
    def analyzer(self):
        """テスト用のアナライザーインスタンス"""
        with patch("app.explainer.ollama_explainer.requests.get") as mock_get:
            # モックレスポンスでモデルが存在することにする
            mock_get.return_value.json.return_value = {"models": [{"name": "llama3"}]}
            mock_get.return_value.raise_for_status = Mock()
            return OllamaSecurityAnalyzer(model="llama3", endpoint="http://localhost:11434")

    @pytest.fixture
    def sample_collected_data(self):
        """テスト用の収集データ"""
        return {
            "cloud_type": "multi",
            "findings": [
                {"name": "test-finding", "severity": "HIGH", "description": "Test security issue"}
            ],
            "iam_policies": [
                {
                    "resource": "projects/test-project",
                    "bindings": [{"role": "roles/owner", "members": ["user:admin@example.com"]}],
                }
            ],
        }

    def test_init_with_existing_model(self):
        """既存モデルでの初期化テスト"""
        with patch("app.explainer.ollama_explainer.requests.get") as mock_get:
            mock_get.return_value.json.return_value = {"models": [{"name": "gemma3:latest"}]}
            mock_get.return_value.raise_for_status = Mock()

            analyzer = OllamaSecurityAnalyzer()
            assert analyzer.model == "gemma3:latest"
            assert analyzer.endpoint == "http://localhost:11434"

    def test_init_with_missing_model(self):
        """モデルが存在しない場合の初期化テスト"""
        with patch("app.explainer.ollama_explainer.requests.get") as mock_get:
            # モデルが存在しない
            mock_get.return_value.json.return_value = {"models": []}
            mock_get.return_value.raise_for_status = Mock()

            with patch("app.explainer.ollama_explainer.requests.post") as mock_post:
                mock_post.return_value.raise_for_status = Mock()

                OllamaSecurityAnalyzer(model="codellama")
                # モデルのプルが呼ばれることを確認
                mock_post.assert_called_once()

    def test_connection_error(self):
        """接続エラーのテスト"""
        with patch("app.explainer.ollama_explainer.requests") as mock_requests:
            mock_requests.get.side_effect = Exception("Connection failed")
            mock_requests.exceptions.RequestException = Exception

            with pytest.raises(ConnectionError, match="Failed to connect to Ollama"):
                OllamaSecurityAnalyzer()

    def test_analyze_findings_success(self, analyzer, sample_collected_data):
        """正常な分析のテスト"""
        mock_response = {
            "response": json.dumps(
                [
                    {
                        "title": "オーナー権限の過剰付与",
                        "severity": "HIGH",
                        "explanation": "管理者にオーナー権限が付与されています",
                        "recommendation": "最小権限の原則に従ってください",
                    }
                ]
            )
        }

        with patch("app.explainer.ollama_explainer.requests.post") as mock_post:
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status = Mock()

            findings = analyzer.analyze_findings(sample_collected_data)

            assert len(findings) == 1
            assert findings[0]["title"] == "オーナー権限の過剰付与"
            assert findings[0]["severity"] == "HIGH"

    def test_analyze_findings_with_ollama_error(self, analyzer, sample_collected_data):
        """Ollamaエラー時のテスト"""
        with patch("app.explainer.ollama_explainer.requests.post") as mock_post:
            mock_post.side_effect = Exception("Ollama error")

            with pytest.raises(Exception, match="Ollama error"):
                analyzer.analyze_findings(sample_collected_data)

    def test_parse_ollama_response_valid_json(self, analyzer):
        """有効なJSONレスポンスのパーステスト"""
        response_text = """
        Here is the analysis:
        [
            {
                "title": "Test Finding",
                "severity": "MEDIUM",
                "explanation": "Test explanation",
                "recommendation": "Test recommendation"
            }
        ]
        """

        findings = analyzer._parse_ollama_response(response_text)
        assert len(findings) == 1
        assert findings[0]["title"] == "Test Finding"
        assert findings[0]["severity"] == "MEDIUM"

    def test_parse_ollama_response_invalid_json(self, analyzer):
        """無効なJSONレスポンスのパーステスト"""
        response_text = "This is not JSON"

        findings = analyzer._parse_ollama_response(response_text)
        assert len(findings) == 1
        assert findings[0]["title"] == "分析エラー"

    def test_parse_ollama_response_missing_fields(self, analyzer):
        """必須フィールドが欠けているレスポンスのテスト"""
        response_text = '[{"title": "Test"}]'

        findings = analyzer._parse_ollama_response(response_text)
        assert len(findings) == 1
        assert findings[0]["title"] == "Test"
        assert findings[0]["severity"] == "MEDIUM"  # デフォルト値
        assert findings[0]["explanation"] == "詳細情報なし"
        assert findings[0]["recommendation"] == "推奨事項なし"

    def test_build_analysis_prompt(self, analyzer, sample_collected_data):
        """プロンプト構築のテスト"""
        prompt = analyzer._build_analysis_prompt(sample_collected_data)

        assert "クラウドタイプ: multi" in prompt
        assert "発見事項:" in prompt
        assert "IAMポリシー:" in prompt
        assert "JSON" in prompt

    def test_multi_cloud_analysis(self, analyzer):
        """マルチクラウドデータの分析テスト"""
        multi_cloud_data = {
            "cloud_type": "multi",
            "findings": [],
            "iam_policies": [
                {"provider": "aws", "policies": [{"Version": "2012-10-17"}]},
                {"provider": "azure", "assignments": [{"principalId": "123"}]},
            ],
        }

        mock_response = {
            "response": json.dumps(
                [
                    {
                        "title": "AWS IAM Risk",
                        "severity": "HIGH",
                        "explanation": "AWS risk",
                        "recommendation": "Fix AWS",
                    },
                    {
                        "title": "Azure IAM Risk",
                        "severity": "MEDIUM",
                        "explanation": "Azure risk",
                        "recommendation": "Fix Azure",
                    },
                ]
            )
        }

        with patch("app.explainer.ollama_explainer.requests.post") as mock_post:
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status = Mock()

            findings = analyzer.analyze_findings(multi_cloud_data)
            assert len(findings) == 2
