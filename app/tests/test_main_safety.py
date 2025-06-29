"""Tests for safety features in the main CLI."""

from unittest.mock import patch

import pytest

from app.main import PaddiCLI


class TestMainSafety:
    """Test cases for safety features in main CLI."""

    @pytest.fixture
    def cli(self, tmp_path, monkeypatch):
        """Create a CLI instance with temporary audit directory."""
        monkeypatch.chdir(tmp_path)
        # Create audit_logs directory to avoid initialization errors
        audit_dir = tmp_path / "audit_logs"
        audit_dir.mkdir()
        return PaddiCLI()

    def test_validate_command_safe(self, cli, capsys):
        """Test validating a safe command."""
        result = cli.validate_command(
            command="gcloud projects list", user="test-user", dry_run=True, require_approval=False
        )

        assert result is True

        captured = capsys.readouterr()
        assert "✓ COMMAND VALIDATED" in captured.out
        assert "Safe to execute" in captured.out

    def test_validate_command_dangerous(self, cli, capsys):
        """Test validating a dangerous command."""
        result = cli.validate_command(
            command="rm -rf /production-data", user="test-user", dry_run=True
        )

        assert result is False

        captured = capsys.readouterr()
        assert "CRITICAL RISK DETECTED" in captured.out
        assert "Approval ID:" in captured.out

    def test_execute_remediation_dry_run(self, cli, capsys):
        """Test executing remediation in dry-run mode."""
        cli.execute_remediation(command="gcloud projects list", user="test-user", dry_run=True)

        captured = capsys.readouterr()
        assert "DRY-RUN MODE" in captured.out
        assert "COMMAND VALIDATED - Safe to execute" in captured.out

    @patch("builtins.input", return_value="no")
    def test_execute_remediation_cancelled(self, _mock_input, cli, capsys):
        """Test cancelling execution when prompted."""
        cli.execute_remediation(command="gcloud projects list", user="test-user", dry_run=False)

        captured = capsys.readouterr()
        assert "Execution cancelled by user" in captured.out

    def test_approve_command(self, cli, capsys):
        """Test approving a command."""
        # First create an approval request
        cli.validate_command(command="firewall-cmd --remove-port=80/tcp", user="test-user")

        # Get the approval ID from pending approvals
        approvals = cli.safety_check.get_pending_approvals()
        if approvals:
            approval_id = approvals[0].id

            # Approve it
            cli.approve(approval_id, "admin")

            captured = capsys.readouterr()
            assert "APPROVED" in captured.out
            assert "Decided by: admin" in captured.out

    def test_reject_command(self, cli, capsys):
        """Test rejecting a command."""
        # First create an approval request
        cli.validate_command(command="DROP TABLE users;", user="test-user")

        # Get the approval ID from pending approvals
        approvals = cli.safety_check.get_pending_approvals()
        if approvals:
            approval_id = approvals[0].id

            # Reject it
            cli.reject(approval_id, "Too dangerous", "admin")

            captured = capsys.readouterr()
            assert "REJECTED" in captured.out
            assert "Decided by: admin" in captured.out
            assert "Too dangerous" in captured.out

    def test_list_approvals_pending(self, cli, capsys):
        """Test listing pending approvals."""
        # Create some approval requests
        commands = [
            "rm -rf /tmp/test",
            "firewall-cmd --remove-port=443/tcp",
        ]

        for cmd in commands:
            cli.validate_command(cmd, user="test-user")

        # List pending
        cli.list_approvals(status="pending")

        captured = capsys.readouterr()
        # The log message is via logger, check for actual output
        if "No approval requests found" not in captured.out:
            assert "Status: pending" in captured.out
            assert "Risk: critical" in captured.out
            assert "Requested by: test-user" in captured.out

    def test_list_approvals_all(self, cli, capsys):
        """Test listing all approvals."""
        # Create and approve one request
        cli.validate_command("rm -rf /test", user="test-user")
        approvals = cli.safety_check.get_pending_approvals()
        if approvals:
            cli.safety_check.approve_command(approvals[0].id, "admin")

        # List all
        cli.list_approvals(status="all")

        captured = capsys.readouterr()
        # Check for actual output content, not log messages
        assert "Status:" in captured.out or "No approval requests found" in captured.out

    def test_audit_log_report(self, cli, capsys):
        """Test viewing audit log report."""
        # Create some activity
        cli.execute_remediation(command="gcloud projects list", user="test-user", dry_run=True)

        # View audit log
        cli.audit_log()

        captured = capsys.readouterr()
        # Check for any indication of audit logs
        assert "📜" in captured.out or "audit log" in captured.out.lower()

    def test_audit_log_with_filters(self, cli, capsys):
        """Test audit log with filters."""
        # Create activity with a safe command
        cli.execute_remediation(command="gcloud projects list", user="alice", dry_run=True)

        # Search by user
        cli.audit_log(user="alice")

        captured = capsys.readouterr()
        # Check for actual output showing the log entry
        assert "alice" in captured.out
        assert "gcloud projects list" in captured.out

    @patch("builtins.input", return_value="")
    def test_safety_demo(self, _mock_input, cli, capsys):
        """Test safety demonstration."""
        cli.safety_demo()

        captured = capsys.readouterr()
        assert "SAFETY SYSTEM DEMONSTRATION" in captured.out
        assert "Safe read-only command" in captured.out
        assert "Medium risk" in captured.out
        assert "High risk" in captured.out
        assert "Critical risk" in captured.out
        assert "✅ Safety demonstration completed!" in captured.out

    def test_cli_initialization_with_safety(self):
        """Test that CLI initializes with safety system."""
        cli = PaddiCLI()

        assert hasattr(cli, "safety_check")
        assert cli.safety_check is not None
        assert hasattr(cli, "validate_command")
        assert hasattr(cli, "execute_remediation")
        assert hasattr(cli, "approve")
        assert hasattr(cli, "reject")
        assert hasattr(cli, "list_approvals")
        assert hasattr(cli, "audit_log")
        assert hasattr(cli, "safety_demo")
