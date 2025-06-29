"""Tests for the approval workflow module."""

from datetime import datetime, timedelta

import pytest

from app.safety.approval import ApprovalWorkflow
from app.safety.models import (
    ApprovalStatus,
    CommandType,
    CommandValidation,
    ImpactAnalysis,
    RiskLevel,
)


class TestApprovalWorkflow:
    """Test cases for ApprovalWorkflow."""

    @pytest.fixture
    def workflow(self):
        """Create a workflow instance."""
        return ApprovalWorkflow()

    @pytest.fixture
    def sample_validation(self):
        """Create a sample validation result."""
        return CommandValidation(
            command="rm -rf /data",
            is_safe=False,
            risk_level=RiskLevel.HIGH,
            command_type=CommandType.DELETION,
            risks=["Permanent data deletion"],
            warnings=["Irreversible operation"],
            requires_approval=True,
        )

    @pytest.fixture
    def sample_impact(self):
        """Create a sample impact analysis."""
        return ImpactAnalysis(
            command="rm -rf /data",
            affected_resources=["/data directory"],
            affected_services=["storage"],
            estimated_downtime="Permanent",
            reversible=False,
            rollback_command=None,
            data_loss_risk=True,
        )

    def test_create_approval_request(self, workflow, sample_validation, sample_impact):
        """Test creating an approval request."""
        request = workflow.create_approval_request(
            command="rm -rf /data",
            validation=sample_validation,
            impact=sample_impact,
            requested_by="test-user",
        )

        assert request.id
        assert request.command == "rm -rf /data"
        assert request.requested_by == "test-user"
        assert request.status == ApprovalStatus.PENDING
        assert request.requested_at
        assert request in workflow.pending_approvals.values()

    def test_auto_approval_low_risk(self, workflow):
        """Test auto-approval for low-risk commands."""
        validation = CommandValidation(
            command="gcloud projects list",
            is_safe=True,
            risk_level=RiskLevel.LOW,
            command_type=CommandType.READ_ONLY,
            risks=[],
            warnings=[],
            requires_approval=False,
        )

        impact = ImpactAnalysis(
            command="gcloud projects list",
            affected_resources=[],
            affected_services=[],
            estimated_downtime=None,
            reversible=True,
            rollback_command=None,
            data_loss_risk=False,
        )

        request = workflow.create_approval_request(
            command="gcloud projects list",
            validation=validation,
            impact=impact,
            requested_by="test-user",
        )

        assert request.status == ApprovalStatus.AUTO_APPROVED
        assert request.approved_by == "system"
        assert request.approved_at
        assert request not in workflow.pending_approvals.values()
        assert request in workflow.approval_history

    def test_auto_approval_test_environment(self, workflow):
        """Test auto-approval for test environment resources."""
        validation = CommandValidation(
            command="rm test-file.txt",
            is_safe=False,
            risk_level=RiskLevel.MEDIUM,
            command_type=CommandType.DELETION,
            risks=["File deletion"],
            warnings=[],
            requires_approval=True,
        )

        impact = ImpactAnalysis(
            command="rm test-file.txt",
            affected_resources=["test-file.txt"],
            affected_services=[],
            estimated_downtime=None,
            reversible=False,
            rollback_command=None,
            data_loss_risk=True,
        )

        request = workflow.create_approval_request(
            command="rm test-file.txt",
            validation=validation,
            impact=impact,
            requested_by="test-user",
        )

        assert request.status == ApprovalStatus.AUTO_APPROVED

    def test_approve_request(self, workflow, sample_validation, sample_impact):
        """Test approving a request."""
        # Create pending request
        request = workflow.create_approval_request(
            command="rm -rf /data",
            validation=sample_validation,
            impact=sample_impact,
            requested_by="test-user",
        )

        assert request.status == ApprovalStatus.PENDING

        # Approve it
        approved = workflow.approve_request(request.id, "admin-user")

        assert approved
        assert approved.status == ApprovalStatus.APPROVED
        assert approved.approved_by == "admin-user"
        assert approved.approved_at
        assert request.id not in workflow.pending_approvals
        assert approved in workflow.approval_history

    def test_reject_request(self, workflow, sample_validation, sample_impact):
        """Test rejecting a request."""
        # Create pending request
        request = workflow.create_approval_request(
            command="rm -rf /data",
            validation=sample_validation,
            impact=sample_impact,
            requested_by="test-user",
        )

        # Reject it
        rejected = workflow.reject_request(request.id, "admin-user", "Too risky for production")

        assert rejected
        assert rejected.status == ApprovalStatus.REJECTED
        assert rejected.approved_by == "admin-user"
        assert rejected.approved_at
        assert rejected.rejection_reason == "Too risky for production"
        assert request.id not in workflow.pending_approvals
        assert rejected in workflow.approval_history

    def test_get_pending_approvals(self, workflow, sample_validation, sample_impact):
        """Test getting pending approvals."""
        # Create multiple requests
        requests = []
        for i in range(3):
            request = workflow.create_approval_request(
                command=f"command-{i}",
                validation=sample_validation,
                impact=sample_impact,
                requested_by=f"user-{i}",
            )
            if request.status == ApprovalStatus.PENDING:
                requests.append(request)

        pending = workflow.get_pending_approvals()
        assert len(pending) == len(requests)
        assert all(r.status == ApprovalStatus.PENDING for r in pending)

    def test_get_approval_by_id(self, workflow, sample_validation, sample_impact):
        """Test getting approval by ID."""
        # Create and approve a request
        request = workflow.create_approval_request(
            command="test-command",
            validation=sample_validation,
            impact=sample_impact,
            requested_by="test-user",
        )

        workflow.approve_request(request.id, "admin")

        # Should find in history
        found = workflow.get_approval_by_id(request.id)
        assert found
        assert found.id == request.id
        assert found.status == ApprovalStatus.APPROVED

        # Non-existent ID
        not_found = workflow.get_approval_by_id("non-existent-id")
        assert not_found is None

    def test_expire_old_requests(self, workflow, sample_validation, sample_impact):
        """Test expiration of old requests."""
        # Create an old request
        request = workflow.create_approval_request(
            command="old-command",
            validation=sample_validation,
            impact=sample_impact,
            requested_by="test-user",
        )

        # Manually set old timestamp
        request.requested_at = datetime.utcnow() - timedelta(hours=2)

        # Get pending approvals (triggers expiration)
        _ = workflow.get_pending_approvals()

        # Should be expired
        assert request.id not in workflow.pending_approvals
        assert any(
            r.id == request.id and r.status == ApprovalStatus.REJECTED
            for r in workflow.approval_history
        )

    def test_format_approval_request(self, workflow, sample_validation, sample_impact):
        """Test formatting approval request for display."""
        request = workflow.create_approval_request(
            command="rm -rf /important-data",
            validation=sample_validation,
            impact=sample_impact,
            requested_by="test-user",
        )

        formatted = workflow.format_approval_request(request)

        assert "APPROVAL REQUEST" in formatted
        assert request.id in formatted
        assert "rm -rf /important-data" in formatted
        assert "HIGH" in formatted
        assert "DELETION" in formatted
        assert "Permanent data deletion" in formatted
        assert "test-user" in formatted

    def test_get_approval_statistics(self, workflow, sample_validation, sample_impact):
        """Test getting approval statistics."""
        # Create various requests
        for i in range(5):
            request = workflow.create_approval_request(
                command=f"command-{i}",
                validation=sample_validation,
                impact=sample_impact,
                requested_by="test-user",
            )

            if i < 2 and request.status == ApprovalStatus.PENDING:
                workflow.approve_request(request.id, "admin")
            elif i < 4 and request.status == ApprovalStatus.PENDING:
                workflow.reject_request(request.id, "admin", "Not safe")

        stats = workflow.get_approval_statistics()

        assert stats["total"] > 0
        assert stats["pending"] >= 0
        assert stats["approved"] >= 0
        assert stats["rejected"] >= 0
        assert stats["auto_approved"] >= 0
        assert (
            stats["pending"] + stats["approved"] + stats["rejected"] + stats["auto_approved"]
        ) == stats["total"]
