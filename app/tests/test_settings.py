import os
import pytest
from unittest.mock import patch

from app.config.settings import Settings, get_settings


class TestSettings:
    """設定モジュールのテスト"""
    
    def test_default_settings(self):
        """デフォルト設定のテスト"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.ai_provider == "gemini"
            assert settings.ollama_model == "llama3"
            assert settings.ollama_endpoint == "http://localhost:11434"
            assert settings.vertex_ai_location == "asia-northeast1"
    
    def test_env_var_settings(self):
        """環境変数からの設定読み込みテスト"""
        env_vars = {
            "AI_PROVIDER": "ollama",
            "OLLAMA_MODEL": "codellama",
            "OLLAMA_ENDPOINT": "http://custom:8080",
            "PROJECT_ID": "test-project",
            "VERTEX_AI_LOCATION": "us-west1"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.ai_provider == "ollama"
            assert settings.ollama_model == "codellama"
            assert settings.ollama_endpoint == "http://custom:8080"
            assert settings.project_id == "test-project"
            assert settings.vertex_ai_location == "us-west1"
    
    def test_validate_invalid_provider(self):
        """無効なAIプロバイダーの検証テスト"""
        with patch.dict(os.environ, {"AI_PROVIDER": "invalid"}, clear=True):
            settings = Settings()
            with pytest.raises(ValueError, match="Invalid AI_PROVIDER"):
                settings.validate()
    
    def test_validate_gemini_without_project_id(self):
        """Gemini使用時のproject_id必須チェック"""
        with patch.dict(os.environ, {"AI_PROVIDER": "gemini"}, clear=True):
            settings = Settings()
            with pytest.raises(ValueError, match="PROJECT_ID is required"):
                settings.validate()
    
    def test_validate_gemini_with_project_id(self):
        """Gemini使用時の正常な検証"""
        with patch.dict(os.environ, {
            "AI_PROVIDER": "gemini",
            "PROJECT_ID": "test-project"
        }, clear=True):
            settings = Settings()
            settings.validate()  # Should not raise
    
    def test_validate_ollama_without_endpoint(self):
        """Ollama使用時のendpoint必須チェック"""
        settings = Settings()
        settings.ai_provider = "ollama"
        settings.ollama_endpoint = ""
        with pytest.raises(ValueError, match="OLLAMA_ENDPOINT is required"):
            settings.validate()
    
    def test_validate_ollama_without_model(self):
        """Ollama使用時のmodel必須チェック"""
        settings = Settings()
        settings.ai_provider = "ollama"
        settings.ollama_model = ""
        with pytest.raises(ValueError, match="OLLAMA_MODEL is required"):
            settings.validate()
    
    def test_validate_ollama_success(self):
        """Ollama使用時の正常な検証"""
        with patch.dict(os.environ, {"AI_PROVIDER": "ollama"}, clear=True):
            settings = Settings()
            settings.validate()  # Should not raise
    
    def test_get_settings(self):
        """get_settings関数のテスト"""
        with patch.dict(os.environ, {
            "AI_PROVIDER": "gemini",
            "PROJECT_ID": "test-project"
        }, clear=True):
            settings = get_settings()
            assert isinstance(settings, Settings)
            assert settings.ai_provider == "gemini"
            assert settings.project_id == "test-project"