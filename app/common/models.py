"""Common data models shared across agents."""

from dataclasses import dataclass
from typing import Dict


@dataclass
class SecurityFinding:
    """Data class representing a security finding."""

    title: str
    severity: str
    explanation: str
    recommendation: str

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for JSON serialization."""
        return {
            "title": self.title,
            "severity": self.severity,
            "explanation": self.explanation,
            "recommendation": self.recommendation,
        }
