"""Tests for common data models."""

from common.models import EnhancedRecommendation, RecommendationStep, SecurityFinding


class TestSecurityFinding:
    """Test cases for SecurityFinding dataclass."""

    def test_initialization(self):
        """Test SecurityFinding initialization."""
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

    def test_to_dict(self):
        """Test conversion to dictionary."""
        finding = SecurityFinding(
            title="Overprivileged Service Account",
            severity="CRITICAL",
            explanation="Service account has excessive permissions",
            recommendation="Apply least privilege principle",
        )

        result = finding.to_dict()

        assert isinstance(result, dict)
        assert result["title"] == "Overprivileged Service Account"
        assert result["severity"] == "CRITICAL"
        assert result["explanation"] == "Service account has excessive permissions"
        assert result["recommendation"] == "Apply least privilege principle"
        # Should only have basic fields since enhanced fields are not set
        assert "finding_id" not in result
        assert "source" not in result

    def test_multiple_instances(self):
        """Test that multiple instances are independent."""
        finding1 = SecurityFinding(
            title="Finding 1",
            severity="LOW",
            explanation="Explanation 1",
            recommendation="Recommendation 1",
        )

        finding2 = SecurityFinding(
            title="Finding 2",
            severity="HIGH",
            explanation="Explanation 2",
            recommendation="Recommendation 2",
        )

        # Ensure they are independent
        assert finding1.title != finding2.title
        assert finding1.severity != finding2.severity
        assert finding1.to_dict() != finding2.to_dict()

    def test_empty_strings(self):
        """Test handling of empty strings."""
        finding = SecurityFinding(title="", severity="", explanation="", recommendation="")

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
            recommendation="Use `code` blocks and **markdown**",
        )

        result = finding.to_dict()

        assert "quotes" in result["title"]
        assert "\n" in result["explanation"]
        assert "`code`" in result["recommendation"]

    def test_enhanced_fields(self):
        """Test SecurityFinding with enhanced fields."""
        finding = SecurityFinding(
            title="Over-privileged Service Account",
            severity="HIGH",
            explanation="Service account has owner permissions",
            recommendation="Apply least privilege",
            finding_id="gcp-iam-001",
            source="GCP-IAM",
            classification="要対応",
            classification_reason="Production environment risk",
            business_impact="Critical data exposure risk",
            priority_score=85,
            compliance_mapping={"cis_benchmark": "1.4", "iso_27001": "A.9.2.5", "pci_dss": "7.1"},
        )

        result = finding.to_dict()

        # Check basic fields
        assert result["title"] == "Over-privileged Service Account"
        assert result["severity"] == "HIGH"

        # Check enhanced fields
        assert result["finding_id"] == "gcp-iam-001"
        assert result["source"] == "GCP-IAM"
        assert result["classification"] == "要対応"
        assert result["classification_reason"] == "Production environment risk"
        assert result["business_impact"] == "Critical data exposure risk"
        assert result["priority_score"] == 85
        assert result["compliance_mapping"]["cis_benchmark"] == "1.4"
        assert result["compliance_mapping"]["iso_27001"] == "A.9.2.5"
        assert result["compliance_mapping"]["pci_dss"] == "7.1"


class TestRecommendationStep:
    """Test cases for RecommendationStep dataclass."""

    def test_basic_step(self):
        """Test basic recommendation step."""
        step = RecommendationStep(order=1, action="Review current permissions")

        assert step.order == 1
        assert step.action == "Review current permissions"
        assert step.command is None
        assert step.code_snippet is None
        assert step.validation is None

    def test_step_with_command(self):
        """Test step with command."""
        step = RecommendationStep(
            order=2,
            action="List current IAM bindings",
            command="gcloud projects get-iam-policy PROJECT_ID",
            validation="Check for overly permissive roles",
        )

        result = step.to_dict()

        assert result["order"] == 2
        assert result["action"] == "List current IAM bindings"
        assert result["command"] == "gcloud projects get-iam-policy PROJECT_ID"
        assert result["validation"] == "Check for overly permissive roles"
        assert "code_snippet" not in result  # Should not include None values

    def test_step_with_code_snippet(self):
        """Test step with code snippet."""
        code = """# role-definition.yaml
title: "Custom Role"
includedPermissions:
- storage.buckets.get"""

        step = RecommendationStep(
            order=3,
            action="Create custom role",
            code_snippet=code,
            command="gcloud iam roles create customRole --file=role-definition.yaml",
        )

        result = step.to_dict()

        assert result["code_snippet"] == code
        assert "role-definition.yaml" in result["code_snippet"]


class TestEnhancedRecommendation:
    """Test cases for EnhancedRecommendation dataclass."""

    def test_basic_recommendation(self):
        """Test basic enhanced recommendation."""
        rec = EnhancedRecommendation(summary="Apply least privilege principle")

        assert rec.summary == "Apply least privilege principle"
        assert rec.steps == []
        assert rec.estimated_time is None
        assert rec.required_skills == []

    def test_recommendation_with_steps(self):
        """Test recommendation with multiple steps."""
        steps = [
            RecommendationStep(
                order=1,
                action="Audit current permissions",
                command="gcloud policy-intelligence query-activity",
            ),
            RecommendationStep(
                order=2, action="Create custom role", command="gcloud iam roles create"
            ),
            RecommendationStep(
                order=3, action="Apply new role", command="gcloud projects add-iam-policy-binding"
            ),
        ]

        rec = EnhancedRecommendation(
            summary="Implement least privilege for service account",
            steps=steps,
            estimated_time="30分",
            required_skills=["GCP IAM", "gcloud CLI", "YAML"],
        )

        result = rec.to_dict()

        assert result["summary"] == "Implement least privilege for service account"
        assert len(result["steps"]) == 3
        assert result["steps"][0]["order"] == 1
        assert result["steps"][0]["action"] == "Audit current permissions"
        assert result["estimated_time"] == "30分"
        assert "GCP IAM" in result["required_skills"]
        assert "gcloud CLI" in result["required_skills"]

    def test_security_finding_with_enhanced_recommendation(self):
        """Test SecurityFinding with EnhancedRecommendation."""
        steps = [
            RecommendationStep(
                order=1,
                action="Remove owner role",
                command=(
                    "gcloud projects remove-iam-policy-binding PROJECT_ID "
                    "--member=serviceAccount:SA_EMAIL --role=roles/owner"
                ),
            )
        ]

        enhanced_rec = EnhancedRecommendation(
            summary="Remove excessive permissions",
            steps=steps,
            estimated_time="15分",
            required_skills=["GCP IAM"],
        )

        finding = SecurityFinding(
            title="Service Account with Owner Role",
            severity="HIGH",
            explanation="Service account has owner permissions",
            recommendation="Remove owner role and apply least privilege",
            enhanced_recommendation=enhanced_rec,
        )

        result = finding.to_dict()

        assert "enhanced_recommendation" in result
        assert result["enhanced_recommendation"]["summary"] == "Remove excessive permissions"
        assert len(result["enhanced_recommendation"]["steps"]) == 1
        assert result["enhanced_recommendation"]["estimated_time"] == "15分"
