"""Tests for the safety validator module."""

import pytest

from app.safety.models import CommandType, RiskLevel
from app.safety.validator import SafetyValidator


class TestSafetyValidator:
    """Test cases for SafetyValidator."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return SafetyValidator()

    def test_safe_read_only_commands(self, validator):
        """Test that read-only commands are marked as safe."""
        safe_commands = [
            "gcloud projects list",
            "gsutil ls gs://my-bucket",
            "kubectl get pods",
            "systemctl status nginx",
            "cat /etc/hosts",
        ]

        for command in safe_commands:
            result = validator.validate_command(command)
            assert result.is_safe
            assert result.risk_level == RiskLevel.LOW
            assert result.command_type == CommandType.READ_ONLY
            assert not result.risks
            assert not result.requires_approval

    def test_critical_risk_firewall_commands(self, validator):
        """Test critical risk firewall commands."""
        command = "firewall-cmd --permanent --remove-port=443/tcp"
        result = validator.validate_command(command)

        assert not result.is_safe
        assert result.risk_level == RiskLevel.CRITICAL
        assert result.command_type == CommandType.NETWORK
        assert "Removing firewall rules can block critical services" in result.risks
        assert result.requires_approval

    def test_high_risk_iam_commands(self, validator):
        """Test high risk IAM commands."""
        command = (
            "gcloud projects remove-iam-policy-binding my-project "
            "--member='user:admin@example.com' --role='roles/owner'"
        )
        result = validator.validate_command(command)

        assert not result.is_safe
        assert result.risk_level == RiskLevel.HIGH
        assert result.command_type == CommandType.PERMISSION
        assert "Removing IAM bindings can break service authentication" in result.risks
        assert result.requires_approval

    def test_critical_risk_deletion_commands(self, validator):
        """Test critical risk deletion commands."""
        commands = [
            "gsutil rm -r gs://production-bucket",
            "rm -rf /",
            "gcloud compute instances delete my-instance --quiet",
        ]

        for command in commands:
            result = validator.validate_command(command)
            assert not result.is_safe
            assert result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
            assert result.command_type == CommandType.DELETION
            assert result.requires_approval

    def test_medium_risk_service_commands(self, validator):
        """Test medium risk service commands."""
        command = "systemctl stop nginx"
        result = validator.validate_command(command)

        assert result.risk_level == RiskLevel.MEDIUM
        assert result.command_type == CommandType.CONFIGURATION
        assert "Stopping or disabling services can affect availability" in result.risks

    def test_production_resource_warning(self, validator):
        """Test that production resources trigger warnings."""
        commands = [
            "gcloud compute instances delete production-server",
            "gsutil rm gs://prod-backup/data.tar.gz",
        ]

        for command in commands:
            result = validator.validate_command(command)
            assert result.requires_approval
            assert any("production" in warning.lower() for warning in result.warnings)

    def test_wildcard_warning(self, validator):
        """Test that wildcards trigger warnings."""
        command = "rm *.log"
        result = validator.validate_command(command)

        assert any("wildcard" in warning.lower() for warning in result.warnings)

    def test_get_safe_alternatives(self, validator):
        """Test safe alternative suggestions."""
        # Firewall command
        command = "firewall-cmd --permanent --remove-port=80/tcp"
        alternatives = validator.get_safe_alternatives(command)
        assert any("rich-rule" in alt for alt in alternatives)
        assert any("list-all" in alt for alt in alternatives)

        # IAM command
        command = "gcloud projects remove-iam-policy-binding"
        alternatives = validator.get_safe_alternatives(command)
        assert any("get-iam-policy" in alt for alt in alternatives)

        # Deletion command
        command = "rm -rf /var/log"
        alternatives = validator.get_safe_alternatives(command)
        assert any("backup" in alt.lower() for alt in alternatives)

    def test_unknown_command_type(self, validator):
        """Test commands that don't match any pattern."""
        command = "echo 'Hello World'"
        result = validator.validate_command(command)

        assert result.command_type == CommandType.READ_ONLY  # Echo is safe pattern
        assert result.is_safe

    def test_case_insensitive_matching(self, validator):
        """Test that pattern matching is case insensitive."""
        commands = [
            "GCLOUD PROJECTS LIST",
            "Firewall-Cmd --REMOVE-PORT=443/tcp",
            "RM -RF /tmp",
        ]

        results = [validator.validate_command(cmd) for cmd in commands]

        assert results[0].command_type == CommandType.READ_ONLY
        assert results[1].command_type == CommandType.NETWORK
        assert results[2].command_type == CommandType.DELETION
