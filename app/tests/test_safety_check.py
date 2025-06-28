"""Tests for the main safety check integration."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from app.safety.safety_check import SafetyCheck
from app.safety.models import ApprovalStatus, RiskLevel


class TestSafetyCheck:
    """Test cases for SafetyCheck integration."""
    
    @pytest.fixture
    def safety_check(self, tmp_path):
        """Create a safety check instance with temp audit dir."""
        return SafetyCheck(audit_log_dir=str(tmp_path / "audit_logs"))
    
    def test_validate_safe_command(self, safety_check):
        """Test validating a safe command."""
        is_safe, message, approval = safety_check.validate_command(
            command="gcloud projects list",
            user="test-user",
            dry_run=True
        )
        
        assert is_safe
        assert "COMMAND VALIDATED - Safe to execute" in message
        assert "Risk Level: LOW" in message
        assert "Type: read_only" in message
        assert approval is None  # No approval needed
    
    def test_validate_high_risk_command(self, safety_check):
        """Test validating a high-risk command."""
        is_safe, message, approval = safety_check.validate_command(
            command="gcloud projects remove-iam-policy-binding my-project --member='user:admin@example.com' --role='roles/owner'",
            user="test-user",
            dry_run=True
        )
        
        assert not is_safe
        assert "HIGH RISK DETECTED" in message
        assert "Removing IAM bindings can break service authentication" in message
        assert approval is not None
        assert approval.status == ApprovalStatus.PENDING
    
    def test_validate_critical_risk_command(self, safety_check):
        """Test validating a critical risk command."""
        is_safe, message, approval = safety_check.validate_command(
            command="firewall-cmd --permanent --remove-port=443/tcp",
            user="test-user",
            dry_run=True
        )
        
        assert not is_safe
        assert "CRITICAL RISK DETECTED" in message
        assert "firewall rules can block critical services" in message
        assert approval is not None
        assert approval.status == ApprovalStatus.PENDING
    
    def test_validate_with_dry_run_output(self, safety_check):
        """Test that dry-run simulation is included."""
        is_safe, message, approval = safety_check.validate_command(
            command="systemctl stop nginx",
            user="test-user",
            dry_run=True
        )
        
        assert "DRY-RUN SIMULATION" in message
        assert "[DRY-RUN]" in message
        assert "nginx" in message
    
    def test_validate_with_force_approval(self, safety_check):
        """Test forcing approval on safe commands."""
        is_safe, message, approval = safety_check.validate_command(
            command="echo 'Hello World'",
            user="test-user",
            dry_run=True,
            force_approval=True
        )
        
        assert not is_safe  # Requires approval
        assert approval is not None
        assert approval.status == ApprovalStatus.PENDING
    
    def test_execute_command_dry_run(self, safety_check):
        """Test executing command in dry-run mode."""
        success, result = safety_check.execute_command(
            command="rm -rf /tmp/test",
            user="test-user",
            dry_run=True
        )
        
        assert success
        assert "DRY-RUN MODE - Command not executed" in result
        assert "Risk Level: HIGH" in result
    
    def test_execute_command_requiring_approval(self, safety_check):
        """Test executing command that requires approval."""
        # First attempt without approval
        success, result = safety_check.execute_command(
            command="gsutil rm -r gs://production-bucket/",
            user="test-user",
            dry_run=False
        )
        
        assert not success
        assert "Command requires approval" in result
        assert "Approval ID:" in result
    
    def test_execute_command_with_approval(self, safety_check):
        """Test executing command with pre-approval."""
        # First create an approval request
        command = "firewall-cmd --remove-port=80/tcp"
        is_safe, message, approval = safety_check.validate_command(
            command=command,
            user="test-user"
        )
        
        assert approval is not None
        
        # Approve it
        approved = safety_check.approve_command(approval.id, "admin")
        assert approved
        
        # Now execute with approval
        success, result = safety_check.execute_command(
            command=command,
            user="test-user",
            approval_id=approval.id,
            dry_run=True  # Still dry-run for testing
        )
        
        assert success
        assert "DRY-RUN MODE" in result
    
    def test_approve_command(self, safety_check):
        """Test approving a command."""
        # Create approval request
        command = "rm -rf /data"
        is_safe, message, approval = safety_check.validate_command(
            command=command,
            user="test-user"
        )
        
        assert approval and approval.status == ApprovalStatus.PENDING
        
        # Approve it
        approved_request = safety_check.approve_command(approval.id, "admin-user")
        
        assert approved_request
        assert approved_request.status == ApprovalStatus.APPROVED
        assert approved_request.approved_by == "admin-user"
    
    def test_reject_command(self, safety_check):
        """Test rejecting a command."""
        # Create approval request
        command = "DROP TABLE users;"
        is_safe, message, approval = safety_check.validate_command(
            command=command,
            user="test-user"
        )
        
        assert approval and approval.status == ApprovalStatus.PENDING
        
        # Reject it
        rejected_request = safety_check.reject_command(
            approval.id,
            "admin-user",
            "Too dangerous for production"
        )
        
        assert rejected_request
        assert rejected_request.status == ApprovalStatus.REJECTED
        assert rejected_request.approved_by == "admin-user"
        assert rejected_request.rejection_reason == "Too dangerous for production"
    
    def test_get_pending_approvals(self, safety_check):
        """Test getting pending approvals."""
        # Create multiple approval requests
        commands = [
            "rm -rf /data",
            "firewall-cmd --remove-port=443/tcp",
            "gcloud projects delete my-project",
        ]
        
        pending_ids = []
        for cmd in commands:
            is_safe, message, approval = safety_check.validate_command(
                command=cmd,
                user="test-user"
            )
            if approval and approval.status == ApprovalStatus.PENDING:
                pending_ids.append(approval.id)
        
        # Get pending approvals
        pending = safety_check.get_pending_approvals()
        pending_request_ids = [req.id for req in pending]
        
        assert len(pending) >= len(pending_ids)
        assert all(req_id in pending_request_ids for req_id in pending_ids)
    
    def test_get_audit_report(self, safety_check):
        """Test generating audit report."""
        # Create some activity
        commands = [
            ("gcloud projects list", "user1"),
            ("rm -rf /tmp/test", "user2"),
            ("firewall-cmd --remove-port=80/tcp", "user1"),
            ("systemctl stop nginx", "user2"),
        ]
        
        for cmd, user in commands:
            safety_check.execute_command(
                command=cmd,
                user=user,
                dry_run=True
            )
        
        # Generate report
        now = datetime.utcnow()
        report = safety_check.get_audit_report(
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1)
        )
        
        assert "AUDIT REPORT" in report
        assert "Total Commands:" in report
        assert "Unique Users:" in report
        assert "RISK LEVEL DISTRIBUTION" in report
    
    def test_search_audit_logs(self, safety_check):
        """Test searching audit logs."""
        # Create some activity
        safety_check.execute_command(
            command="gcloud projects list",
            user="alice",
            dry_run=True
        )
        
        safety_check.execute_command(
            command="rm -rf /data",
            user="bob",
            dry_run=True
        )
        
        # Search by user
        alice_logs = safety_check.search_audit_logs(user="alice")
        assert len(alice_logs) >= 1
        assert all(log['executed_by'] == "alice" for log in alice_logs)
        
        # Search by risk level
        high_risk_logs = safety_check.search_audit_logs(risk_level="high")
        assert len(high_risk_logs) >= 1
        assert all(log['validation_result']['risk_level'] == "high" for log in high_risk_logs)
    
    def test_integration_workflow(self, safety_check):
        """Test complete workflow: validate, approve, execute."""
        command = "gcloud projects remove-iam-policy-binding my-project --member='user:test@example.com' --role='roles/viewer'"
        user = "developer"
        
        # Step 1: Validate command
        is_safe, message, approval = safety_check.validate_command(
            command=command,
            user=user,
            dry_run=True
        )
        
        assert not is_safe
        assert approval is not None
        assert "HIGH RISK DETECTED" in message
        
        # Step 2: Admin reviews and approves
        approved = safety_check.approve_command(approval.id, "admin")
        assert approved.status == ApprovalStatus.APPROVED
        
        # Step 3: Execute with approval
        success, result = safety_check.execute_command(
            command=command,
            user=user,
            approval_id=approval.id,
            dry_run=True  # Still dry-run for safety
        )
        
        assert success
        assert "DRY-RUN MODE" in result
        
        # Step 4: Check audit log
        logs = safety_check.search_audit_logs(user=user)
        assert len(logs) >= 2  # Validation + execution
        
        # Find the execution log
        execution_logs = [
            log for log in logs 
            if log['command'] == command and not log['dry_run']
        ]
        # In this test, all are dry-run, so check for any matching command
        matching_logs = [log for log in logs if log['command'] == command]
        assert len(matching_logs) >= 1