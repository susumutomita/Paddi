"""Common data models shared across agents."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RecommendationStep:
    """A step in the recommendation process."""

    order: int
    action: str
    command: Optional[str] = None
    code_snippet: Optional[str] = None
    validation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "order": self.order,
            "action": self.action,
        }
        if self.command:
            result["command"] = self.command
        if self.code_snippet:
            result["code_snippet"] = self.code_snippet
        if self.validation:
            result["validation"] = self.validation
        return result


@dataclass
class EnhancedRecommendation:
    """Enhanced recommendation with detailed steps."""

    summary: str
    steps: List[RecommendationStep] = field(default_factory=list)
    estimated_time: Optional[str] = None
    required_skills: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {"summary": self.summary, "steps": [step.to_dict() for step in self.steps]}
        if self.estimated_time:
            result["estimated_time"] = self.estimated_time
        if self.required_skills:
            result["required_skills"] = self.required_skills
        return result


@dataclass
class SecurityFinding:
    """Data class representing a security finding with enhanced metadata."""

    title: str
    severity: str
    explanation: str
    recommendation: str

    # Enhanced fields (optional for backward compatibility)
    finding_id: Optional[str] = None
    source: Optional[str] = None
    classification: Optional[str] = None
    classification_reason: Optional[str] = None
    business_impact: Optional[str] = None
    enhanced_recommendation: Optional[EnhancedRecommendation] = None
    priority_score: Optional[int] = None
    compliance_mapping: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "title": self.title,
            "severity": self.severity,
            "explanation": self.explanation,
            "recommendation": self.recommendation,
        }

        # Add enhanced fields if present
        if self.finding_id:
            result["finding_id"] = self.finding_id
        if self.source:
            result["source"] = self.source
        if self.classification:
            result["classification"] = self.classification
        if self.classification_reason:
            result["classification_reason"] = self.classification_reason
        if self.business_impact:
            result["business_impact"] = self.business_impact
        if self.enhanced_recommendation:
            result["enhanced_recommendation"] = self.enhanced_recommendation.to_dict()
        if self.priority_score is not None:
            result["priority_score"] = self.priority_score
        if self.compliance_mapping:
            result["compliance_mapping"] = self.compliance_mapping

        return result
