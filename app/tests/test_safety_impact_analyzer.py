"""Tests for the impact analyzer module."""

import pytest

from app.safety.impact_analyzer import ImpactAnalyzer
from app.safety.models import CommandType, RiskLevel


class TestImpactAnalyzer:
    """Test cases for ImpactAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create an analyzer instance."""
        return ImpactAnalyzer()

    def test_identify_affected_resources(self, analyzer):
        """Test resource identification in commands."""
        command = (
            "gcloud projects remove-iam-policy-binding my-project-123 "
            "--member='serviceAccount:app@my-project.iam.gserviceaccount.com' "
            "--role='roles/storage.admin'"
        )

        impact = analyzer.analyze_impact(command, CommandType.PERMISSION, RiskLevel.HIGH)

        # Check identified resources
        resources = impact.affected_resources
        assert any("gcp_project: my-project-123" in r for r in resources)
        assert any(
            "service_account: app@my-project.iam.gserviceaccount.com" in r for r in resources
        )
        assert any("iam_role: storage.admin" in r for r in resources)

    def test_identify_affected_resources_with_bucket(self, analyzer):
        """Test bucket resource identification."""
        command = "gsutil rm -r gs://production-backup-bucket/"

        impact = analyzer.analyze_impact(command, CommandType.DELETION, RiskLevel.CRITICAL)

        resources = impact.affected_resources
        assert any("gcp_bucket: production-backup-bucket" in r for r in resources)

    def test_wildcard_resource_detection(self, analyzer):
        """Test detection of wildcard operations."""
        command = "rm -rf /var/log/*.log"

        impact = analyzer.analyze_impact(command, CommandType.DELETION, RiskLevel.HIGH)

        assert any("wildcard" in r.lower() for r in impact.affected_resources)

    def test_identify_affected_services(self, analyzer):
        """Test service identification."""
        # Web service command
        command = "firewall-cmd --remove-port=443/tcp"
        impact = analyzer.analyze_impact(command, CommandType.NETWORK, RiskLevel.CRITICAL)

        assert "web" in impact.affected_services
        assert "networking" in impact.affected_services
        assert "connectivity" in impact.affected_services

        # Database command
        command = "systemctl stop postgresql"
        impact = analyzer.analyze_impact(command, CommandType.CONFIGURATION, RiskLevel.MEDIUM)

        assert "database" in impact.affected_services

        # Storage command
        command = "gsutil rm -r gs://backup-bucket/"
        impact = analyzer.analyze_impact(command, CommandType.DELETION, RiskLevel.HIGH)

        assert "storage" in impact.affected_services

    def test_estimate_downtime_network_commands(self, analyzer):
        """Test downtime estimation for network commands."""
        test_cases = [
            (RiskLevel.LOW, None),
            (RiskLevel.MEDIUM, "Brief connectivity interruption"),
            (RiskLevel.HIGH, "5-15 minutes"),
            (RiskLevel.CRITICAL, "15-60 minutes"),
        ]

        for risk_level, expected_downtime in test_cases:
            impact = analyzer.analyze_impact(
                "firewall-cmd --remove-port=80/tcp", CommandType.NETWORK, risk_level
            )

            if expected_downtime:
                assert expected_downtime in impact.estimated_downtime
            else:
                assert impact.estimated_downtime is None

    def test_estimate_downtime_deletion_commands(self, analyzer):
        """Test downtime estimation for deletion commands."""
        impact = analyzer.analyze_impact(
            "gsutil rm -r gs://critical-data/", CommandType.DELETION, RiskLevel.CRITICAL
        )

        assert "Permanent" in impact.estimated_downtime
        assert "complete data loss" in impact.estimated_downtime

    def test_reversibility_assessment(self, analyzer):
        """Test reversibility assessment."""
        # Deletion - generally not reversible
        impact = analyzer.analyze_impact("rm -rf /data", CommandType.DELETION, RiskLevel.CRITICAL)
        assert not impact.reversible

        # Network change - reversible
        impact = analyzer.analyze_impact(
            "firewall-cmd --remove-port=443/tcp", CommandType.NETWORK, RiskLevel.HIGH
        )
        assert impact.reversible

        # Permission change - reversible
        impact = analyzer.analyze_impact(
            "gcloud projects remove-iam-policy-binding", CommandType.PERMISSION, RiskLevel.HIGH
        )
        assert impact.reversible

        # Deletion with backup keyword - reversible
        impact = analyzer.analyze_impact(
            "rm backup-old.tar.gz", CommandType.DELETION, RiskLevel.LOW
        )
        assert impact.reversible

    def test_generate_rollback_commands(self, analyzer):
        """Test rollback command generation."""
        # Firewall port removal
        command = "firewall-cmd --permanent --remove-port=443/tcp"
        impact = analyzer.analyze_impact(command, CommandType.NETWORK, RiskLevel.HIGH)

        assert impact.rollback_command
        assert "--add-port=443/tcp" in impact.rollback_command

        # IAM binding removal
        command = (
            "gcloud projects remove-iam-policy-binding my-project "
            '--member="user:admin@example.com" --role="roles/owner"'
        )
        impact = analyzer.analyze_impact(command, CommandType.PERMISSION, RiskLevel.HIGH)

        assert impact.rollback_command
        assert "add-iam-policy-binding" in impact.rollback_command
        assert "user:admin@example.com" in impact.rollback_command
        assert "roles/owner" in impact.rollback_command

        # System service
        command = "systemctl stop nginx"
        impact = analyzer.analyze_impact(command, CommandType.CONFIGURATION, RiskLevel.MEDIUM)

        assert impact.rollback_command == "systemctl start nginx"

    def test_data_loss_risk_assessment(self, analyzer):
        """Test data loss risk assessment."""
        # All deletion commands have data loss risk
        command = "rm -rf /var/data"
        impact = analyzer.analyze_impact(command, CommandType.DELETION, RiskLevel.HIGH)
        assert impact.data_loss_risk

        # SQL truncate
        command = "mysql -e 'TRUNCATE TABLE users;'"
        impact = analyzer.analyze_impact(command, CommandType.UNKNOWN, RiskLevel.HIGH)
        assert impact.data_loss_risk

        # Overwrite redirection
        command = "echo '' > important.conf"
        impact = analyzer.analyze_impact(command, CommandType.UNKNOWN, RiskLevel.MEDIUM)
        assert impact.data_loss_risk

        # Safe command
        command = "gcloud projects list"
        impact = analyzer.analyze_impact(command, CommandType.READ_ONLY, RiskLevel.LOW)
        assert not impact.data_loss_risk

    def test_mitigation_suggestions(self, analyzer):
        """Test mitigation suggestion generation."""
        # High data loss risk
        command = "gsutil rm -r gs://production-data/"
        impact = analyzer.analyze_impact(command, CommandType.DELETION, RiskLevel.CRITICAL)
        suggestions = analyzer.get_mitigation_suggestions(impact)

        assert any("backup" in s.lower() for s in suggestions)
        assert any("versioning" in s.lower() for s in suggestions)

        # With downtime
        command = "firewall-cmd --remove-port=443/tcp"
        impact = analyzer.analyze_impact(command, CommandType.NETWORK, RiskLevel.HIGH)
        suggestions = analyzer.get_mitigation_suggestions(impact)

        assert any("maintenance window" in s.lower() for s in suggestions)
        assert any("notify" in s.lower() for s in suggestions)

        # Non-reversible
        command = "DROP TABLE users;"
        impact = analyzer.analyze_impact(command, CommandType.UNKNOWN, RiskLevel.CRITICAL)
        impact.reversible = False
        impact.data_loss_risk = True
        suggestions = analyzer.get_mitigation_suggestions(impact)

        assert any("document current state" in s.lower() for s in suggestions)
        assert any("test in non-production" in s.lower() for s in suggestions)
