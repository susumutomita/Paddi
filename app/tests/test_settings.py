"""Tests for configuration settings module."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from app.config.settings import Settings


class TestSettings:
    """Test suite for Settings class."""

    def test_default_settings(self):
        """Test default settings values."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            
            assert settings.ai_provider == "gemini"
            assert settings.gcp_project_id == "example-project-123"
            assert settings.vertex_ai_location == "asia-northeast1"
            assert settings.vertex_ai_model == "gemini-1.5-flash"
            assert settings.ollama_model == "llama3"
            assert settings.ollama_endpoint == "http://localhost:11434"
            assert settings.use_mock is True
            assert settings.temperature == 0.2
            assert settings.max_output_tokens == 2048
            assert settings.data_dir == Path("data")
            assert settings.output_dir == Path("output")

    def test_environment_variable_overrides(self):
        """Test that environment variables override defaults."""
        env_vars = {
            "AI_PROVIDER": "ollama",
            "GCP_PROJECT_ID": "my-project",
            "VERTEX_AI_LOCATION": "us-west1",
            "VERTEX_AI_MODEL": "gemini-1.5-pro",
            "OLLAMA_MODEL": "codellama",
            "OLLAMA_ENDPOINT": "http://remote:11434",
            "USE_MOCK": "false",
            "AI_TEMPERATURE": "0.5",
            "AI_MAX_OUTPUT_TOKENS": "4096",
            "DATA_DIR": "custom_data",
            "OUTPUT_DIR": "custom_output",
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            
            assert settings.ai_provider == "ollama"
            assert settings.gcp_project_id == "my-project"
            assert settings.vertex_ai_location == "us-west1"
            assert settings.vertex_ai_model == "gemini-1.5-pro"
            assert settings.ollama_model == "codellama"
            assert settings.ollama_endpoint == "http://remote:11434"
            assert settings.use_mock is False
            assert settings.temperature == 0.5
            assert settings.max_output_tokens == 4096
            assert settings.data_dir == Path("custom_data")
            assert settings.output_dir == Path("custom_output")

    def test_to_dict_method(self):
        """Test converting settings to dictionary."""
        with patch.dict(os.environ, {"AI_PROVIDER": "ollama"}, clear=True):
            settings = Settings()
            config_dict = settings.to_dict()
            
            assert isinstance(config_dict, dict)
            assert config_dict["ai_provider"] == "ollama"
            assert config_dict["gcp_project_id"] == "example-project-123"
            assert config_dict["use_mock"] is True
            assert config_dict["temperature"] == 0.2
            assert "data_dir" in config_dict
            assert "output_dir" in config_dict

    def test_validate_valid_settings(self):
        """Test validation with valid settings."""
        settings = Settings()
        settings.validate()  # Should not raise

    def test_validate_invalid_ai_provider(self):
        """Test validation with invalid AI provider."""
        with patch.dict(os.environ, {"AI_PROVIDER": "invalid"}, clear=True):
            settings = Settings()
            
            with pytest.raises(ValueError) as exc_info:
                settings.validate()
            
            assert "Invalid AI_PROVIDER: invalid" in str(exc_info.value)

    def test_validate_invalid_temperature(self):
        """Test validation with invalid temperature."""
        with patch.dict(os.environ, {"AI_TEMPERATURE": "1.5"}, clear=True):
            settings = Settings()
            
            with pytest.raises(ValueError) as exc_info:
                settings.validate()
            
            assert "Invalid AI_TEMPERATURE: 1.5" in str(exc_info.value)

    def test_validate_negative_temperature(self):
        """Test validation with negative temperature."""
        with patch.dict(os.environ, {"AI_TEMPERATURE": "-0.1"}, clear=True):
            settings = Settings()
            
            with pytest.raises(ValueError) as exc_info:
                settings.validate()
            
            assert "Invalid AI_TEMPERATURE" in str(exc_info.value)

    def test_validate_invalid_max_tokens(self):
        """Test validation with invalid max tokens."""
        with patch.dict(os.environ, {"AI_MAX_OUTPUT_TOKENS": "0"}, clear=True):
            settings = Settings()
            
            with pytest.raises(ValueError) as exc_info:
                settings.validate()
            
            assert "Invalid AI_MAX_OUTPUT_TOKENS: 0" in str(exc_info.value)

    def test_case_insensitive_ai_provider(self):
        """Test that AI provider is case insensitive."""
        with patch.dict(os.environ, {"AI_PROVIDER": "OLLAMA"}, clear=True):
            settings = Settings()
            assert settings.ai_provider == "ollama"
        
        with patch.dict(os.environ, {"AI_PROVIDER": "Gemini"}, clear=True):
            settings = Settings()
            assert settings.ai_provider == "gemini"

    def test_use_mock_parsing(self):
        """Test USE_MOCK environment variable parsing."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
            ("1", False),  # Only "true" is parsed as True
            ("yes", False),
            ("no", False),
        ]
        
        for env_value, expected in test_cases:
            with patch.dict(os.environ, {"USE_MOCK": env_value}, clear=True):
                settings = Settings()
                assert settings.use_mock == expected

    @patch("pathlib.Path.mkdir")
    def test_directory_creation(self, mock_mkdir):
        """Test that data and output directories are created."""
        Settings()
        
        # Should create both directories
        assert mock_mkdir.call_count == 2
        mock_mkdir.assert_any_call(exist_ok=True)