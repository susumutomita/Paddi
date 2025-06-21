"""
Unit tests for common data models.
"""

import pytest
from common.models import SecurityFinding


class TestSecurityFinding:
    """Test cases for SecurityFinding dataclass."""

    def test_security_finding_creation(self):
        """Test creating a SecurityFinding instance with all fields."""
        finding = SecurityFinding(
            title="Test Security Issue",
            severity="HIGH",
            explanation="This is a detailed explanation of the security issue.",
            recommendation="This is what you should do to fix it."
        )
        
        assert finding.title == "Test Security Issue"
        assert finding.severity == "HIGH"
        assert finding.explanation == "This is a detailed explanation of the security issue."
        assert finding.recommendation == "This is what you should do to fix it."

    def test_security_finding_to_dict(self):
        """Test converting SecurityFinding to dictionary."""
        finding = SecurityFinding(
            title="Sample Finding",
            severity="CRITICAL",
            explanation="Critical security vulnerability detected.",
            recommendation="Apply security patch immediately."
        )
        
        result = finding.to_dict()
        
        assert isinstance(result, dict)
        assert result["title"] == "Sample Finding"
        assert result["severity"] == "CRITICAL"
        assert result["explanation"] == "Critical security vulnerability detected."
        assert result["recommendation"] == "Apply security patch immediately."
        assert len(result) == 4

    def test_security_finding_with_different_severities(self):
        """Test SecurityFinding with various severity levels."""
        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        
        for severity in severities:
            finding = SecurityFinding(
                title=f"{severity} severity finding",
                severity=severity,
                explanation=f"This is a {severity} severity issue.",
                recommendation=f"Fix for {severity} severity issue."
            )
            
            assert finding.severity == severity
            assert finding.to_dict()["severity"] == severity

    def test_security_finding_with_special_characters(self):
        """Test SecurityFinding handles special characters correctly."""
        finding = SecurityFinding(
            title="SQL Injection in user's input: '; DROP TABLE users;--",
            severity="CRITICAL",
            explanation="User input contains SQL injection: <script>alert('XSS')</script>",
            recommendation="Use parameterized queries & escape HTML entities"
        )
        
        dict_result = finding.to_dict()
        assert dict_result["title"] == "SQL Injection in user's input: '; DROP TABLE users;--"
        assert "<script>" in dict_result["explanation"]
        assert "&" in dict_result["recommendation"]

    def test_security_finding_immutability(self):
        """Test that to_dict returns a new dictionary each time."""
        finding = SecurityFinding(
            title="Test",
            severity="LOW",
            explanation="Test explanation",
            recommendation="Test recommendation"
        )
        
        dict1 = finding.to_dict()
        dict2 = finding.to_dict()
        
        # Ensure they are different objects
        assert dict1 is not dict2
        # But with same content
        assert dict1 == dict2
        
        # Modifying one shouldn't affect the other
        dict1["title"] = "Modified"
        assert dict2["title"] == "Test"