"""Extended tests for paddi_cli to improve coverage."""

from unittest.mock import MagicMock, patch

from app.cli.paddi_cli import PaddiCLI


class TestPaddiCLIExtended:
    """Extended tests for PaddiCLI."""

    @patch("app.cli.paddi_cli.registry")
    def test_list_commands(self, mock_registry):
        """Test list_commands method."""
        cli = PaddiCLI()

        # Mock registry commands
        mock_registry.list_commands.return_value = {
            "audit": "Run complete audit",
            "collect": "Collect data",
            "report": "Generate report",
        }

        # Capture print output
        with patch("builtins.print") as mock_print:
            cli.list_commands()

        # Verify header was printed
        calls = [str(call[0][0]) for call in mock_print.call_args_list]
        assert any("Available Paddi Commands" in call for call in calls)
        assert any("audit" in call for call in calls)
        assert any("collect" in call for call in calls)

    def test_approve_command_success(self):
        """Test approve_command when approval succeeds."""
        cli = PaddiCLI()

        # Mock safety check
        mock_approval = MagicMock()
        mock_approval.status.value = "approved"
        mock_approval.id = "test-123"

        cli.safety_check.approve_command = MagicMock(return_value=mock_approval)

        with patch("builtins.print") as mock_print:
            cli.approve_command("test-123", "admin", "looks good")

        # Verify success message
        calls = [str(call[0][0]) for call in mock_print.call_args_list]
        assert any("✅ Command approved" in call for call in calls)
        assert any("admin" in call for call in calls)

    def test_approve_command_failure(self):
        """Test approve_command when approval fails."""
        cli = PaddiCLI()

        cli.safety_check.approve_command = MagicMock(return_value=None)

        with patch("builtins.print") as mock_print:
            cli.approve_command("test-123", "admin")

        # Verify failure message
        calls = [str(call[0][0]) for call in mock_print.call_args_list]
        assert any("❌ Failed to approve" in call for call in calls)

    def test_list_approvals_empty(self):
        """Test list_approvals when no approvals exist."""
        cli = PaddiCLI()

        cli.safety_check.get_pending_approvals = MagicMock(return_value=[])

        with patch("builtins.print") as mock_print:
            cli.list_approvals()

        mock_print.assert_called_with("No approval requests found")

    def test_list_approvals_with_history(self):
        """Test list_approvals with non-pending status."""
        cli = PaddiCLI()

        # Mock approval history
        mock_approval = MagicMock()
        mock_approval.id = "test-123"
        mock_approval.status.value = "approved"
        mock_approval.command = "test command"
        mock_approval.validation.risk_level.value = "medium"
        mock_approval.requested_by = "user1"

        cli.safety_check.approval_workflow.approval_history = [mock_approval]

        with patch("builtins.print") as mock_print:
            cli.list_approvals(status="all")

        # Verify approval details printed
        calls = [str(call[0][0]) for call in mock_print.call_args_list]
        assert any("test-123" in call for call in calls)
        assert any("approved" in call for call in calls)

    def test_audit_logs_alias(self):
        """Test audit_logs alias method."""
        cli = PaddiCLI()

        with patch.object(cli, "audit_log") as mock_audit_log:
            cli.audit_logs(user="testuser")

        mock_audit_log.assert_called_once_with(user="testuser")

    def test_execute_remediation_dry_run(self):
        """Test execute_remediation in dry run mode."""
        cli = PaddiCLI()

        cli.safety_check.execute_command = MagicMock(return_value=(True, "Success"))

        with patch("builtins.print") as mock_print:
            cli.execute_remediation("test command", dry_run=True)

        # Verify dry run message
        calls = [str(call[0][0]) for call in mock_print.call_args_list]
        assert any("DRY-RUN MODE" in call for call in calls)

    def test_execute_remediation_user_cancels(self):
        """Test execute_remediation when user cancels."""
        cli = PaddiCLI()

        cli.safety_check.execute_command = MagicMock(return_value=(True, "Success"))

        with patch("builtins.print") as mock_print, patch("builtins.input", return_value="no"):
            cli.execute_remediation("test command", dry_run=False)

        # Verify cancellation message
        calls = [str(call[0][0]) for call in mock_print.call_args_list]
        assert any("cancelled by user" in call for call in calls)

    def test_approve_method(self):
        """Test approve method (not approve_command)."""
        cli = PaddiCLI()

        mock_approval = MagicMock()
        mock_approval.id = "test-123"
        mock_approval.status.value = "approved"

        cli.safety_check.approve_command = MagicMock(return_value=mock_approval)
        cli.safety_check.approval_workflow.format_approval_request = MagicMock(
            return_value="Formatted approval"
        )

        with patch("builtins.print") as mock_print:
            cli.approve("test-123", "admin")

        # Verify output
        calls = [str(call[0][0]) for call in mock_print.call_args_list]
        assert any("✅ Approval Request" in call for call in calls)
        assert any("APPROVED" in call for call in calls)

    def test_reject_method(self):
        """Test reject method."""
        cli = PaddiCLI()

        mock_approval = MagicMock()
        mock_approval.id = "test-123"
        mock_approval.status.value = "rejected"

        cli.safety_check.reject_command = MagicMock(return_value=mock_approval)
        cli.safety_check.approval_workflow.format_approval_request = MagicMock(
            return_value="Formatted rejection"
        )

        with patch("builtins.print") as mock_print:
            cli.reject("test-123", "Not safe", "admin")

        # Verify output
        calls = [str(call[0][0]) for call in mock_print.call_args_list]
        assert any("❌ Approval Request" in call for call in calls)
        assert any("REJECTED" in call for call in calls)
        assert any("Not safe" in call for call in calls)
