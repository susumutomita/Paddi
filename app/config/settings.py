"""Configuration settings for Paddi."""

import os
from pathlib import Path
from typing import Any, Dict


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        """Initialize settings from environment."""
        # AI Provider settings
        self.ai_provider = os.getenv("AI_PROVIDER", "gemini").lower()
        
        # Gemini settings
        self.gcp_project_id = os.getenv("GCP_PROJECT_ID", "example-project-123")
        self.vertex_ai_location = os.getenv("VERTEX_AI_LOCATION", "asia-northeast1")
        self.vertex_ai_model = os.getenv("VERTEX_AI_MODEL", "gemini-1.5-flash")
        
        # Ollama settings
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
        self.ollama_endpoint = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
        
        # General settings
        self.use_mock = os.getenv("USE_MOCK", "true").lower() == "true"
        self.temperature = float(os.getenv("AI_TEMPERATURE", "0.2"))
        self.max_output_tokens = int(os.getenv("AI_MAX_OUTPUT_TOKENS", "2048"))
        
        # Data paths
        self.data_dir = Path(os.getenv("DATA_DIR", "data"))
        self.output_dir = Path(os.getenv("OUTPUT_DIR", "output"))
        
        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "ai_provider": self.ai_provider,
            "gcp_project_id": self.gcp_project_id,
            "vertex_ai_location": self.vertex_ai_location,
            "vertex_ai_model": self.vertex_ai_model,
            "ollama_model": self.ollama_model,
            "ollama_endpoint": self.ollama_endpoint,
            "use_mock": self.use_mock,
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
            "data_dir": str(self.data_dir),
            "output_dir": str(self.output_dir),
        }
    
    def validate(self) -> None:
        """Validate settings."""
        if self.ai_provider not in ["gemini", "ollama"]:
            raise ValueError(f"Invalid AI_PROVIDER: {self.ai_provider}. Must be 'gemini' or 'ollama'")
        
        if self.temperature < 0 or self.temperature > 1:
            raise ValueError(f"Invalid AI_TEMPERATURE: {self.temperature}. Must be between 0 and 1")
        
        if self.max_output_tokens < 1:
            raise ValueError(f"Invalid AI_MAX_OUTPUT_TOKENS: {self.max_output_tokens}. Must be positive")


# Global settings instance
settings = Settings()