"""Tests for common data models."""

import pytest

from common.models import SecurityFinding


class TestSecurityFinding:
    """Test cases for SecurityFinding dataclass."""

    def test_initialization(self):
        """Test SecurityFinding initialization."""
        finding = SecurityFinding(
            title="Test Finding",
            severity="HIGH",
            explanation="This is a test explanation",
            recommendation="This is a test recommendation"
        )
        
        assert finding.title == "Test Finding"
        assert finding.severity == "HIGH"
        assert finding.explanation == "This is a test explanation"
        assert finding.recommendation == "This is a test recommendation"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        finding = SecurityFinding(
            title="Overprivileged Service Account",
            severity="CRITICAL",
            explanation="Service account has excessive permissions",
            recommendation="Apply least privilege principle"
        )
        
        result = finding.to_dict()
        
        assert isinstance(result, dict)
        assert result["title"] == "Overprivileged Service Account"
        assert result["severity"] == "CRITICAL"
        assert result["explanation"] == "Service account has excessive permissions"
        assert result["recommendation"] == "Apply least privilege principle"
        assert len(result) == 4  # Should only have 4 fields

    def test_multiple_instances(self):
        """Test that multiple instances are independent."""
        finding1 = SecurityFinding(
            title="Finding 1",
            severity="LOW",
            explanation="Explanation 1",
            recommendation="Recommendation 1"
        )
        
        finding2 = SecurityFinding(
            title="Finding 2",
            severity="HIGH",
            explanation="Explanation 2",
            recommendation="Recommendation 2"
        )
        
        # Ensure they are independent
        assert finding1.title != finding2.title
        assert finding1.severity != finding2.severity
        assert finding1.to_dict() != finding2.to_dict()

    def test_empty_strings(self):
        """Test handling of empty strings."""
        finding = SecurityFinding(
            title="",
            severity="",
            explanation="",
            recommendation=""
        )
        
        result = finding.to_dict()
        
        assert result["title"] == ""
        assert result["severity"] == ""
        assert result["explanation"] == ""
        assert result["recommendation"] == ""

    def test_special_characters(self):
        """Test handling of special characters."""
        finding = SecurityFinding(
            title="Finding with 'quotes' and \"double quotes\"",
            severity="MEDIUM",
            explanation="Explanation with\nnewlines\nand\ttabs",
            recommendation="Use `code` blocks and **markdown**"
        )
        
        result = finding.to_dict()
        
        assert "quotes" in result["title"]
        assert "\n" in result["explanation"]
        assert "`code`" in result["recommendation"]