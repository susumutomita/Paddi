"""Settings module for Paddi application."""

import os


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        # AI Provider settings
        self.ai_provider = os.getenv("AI_PROVIDER", "gemini").lower()

        # Gemini settings
        self.project_id = os.getenv("PROJECT_ID", "")
        self.vertex_ai_location = os.getenv("VERTEX_AI_LOCATION", "asia-northeast1")

        # Ollama settings
        self.ollama_model = os.getenv("OLLAMA_MODEL", "gemma3:latest")
        self.ollama_endpoint = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")

    def validate(self) -> None:
        """設定値の検証"""
        if self.ai_provider not in ["gemini", "ollama"]:
            raise ValueError(
                f"Invalid AI_PROVIDER: {self.ai_provider}. Must be 'gemini' or 'ollama'"
            )

        if self.ai_provider == "gemini" and not self.project_id:
            raise ValueError("PROJECT_ID is required when using Gemini")

        if self.ai_provider == "ollama":
            if not self.ollama_endpoint:
                raise ValueError("OLLAMA_ENDPOINT is required when using Ollama")
            if not self.ollama_model:
                raise ValueError("OLLAMA_MODEL is required when using Ollama")


def get_settings() -> Settings:
    """設定のシングルトンインスタンスを取得"""
    settings = Settings()
    settings.validate()
    return settings
