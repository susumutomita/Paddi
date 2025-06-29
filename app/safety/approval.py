"""Human approval workflow for high-risk commands."""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.safety.models import (
    ApprovalRequest,
    ApprovalStatus,
    CommandValidation,
    ImpactAnalysis,
    RiskLevel,
)


class ApprovalWorkflow:
    """Manages human approval workflow for commands."""

    def __init__(self):
        """Initialize the approval workflow."""
        # In production, this would use a database
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self.approval_history: List[ApprovalRequest] = []

        # Auto-approval rules
        self.auto_approval_rules = {
            "low_risk_readonly": lambda v, i: v.risk_level == RiskLevel.LOW
            and not i.data_loss_risk,
            "test_environment": lambda v, i: any("test" in r.lower() for r in i.affected_resources),
        }

        # Approval timeout (default: 1 hour)
        self.approval_timeout = timedelta(hours=1)

    def create_approval_request(
        self,
        command: str,
        validation: CommandValidation,
        impact: ImpactAnalysis,
        requested_by: str,
        force_approval: bool = False,
    ) -> ApprovalRequest:
        """Create a new approval request."""
        request_id = str(uuid.uuid4())

        # Check for auto-approval (skip if force_approval is True)
        if force_approval:
            status = ApprovalStatus.PENDING
        else:
            status = self._check_auto_approval(validation, impact)

        request = ApprovalRequest(
            id=request_id,
            command=command,
            validation=validation,
            impact_analysis=impact,
            requested_at=datetime.utcnow(),
            requested_by=requested_by,
            status=status,
            approved_by="system" if status == ApprovalStatus.AUTO_APPROVED else None,
            approved_at=datetime.utcnow() if status == ApprovalStatus.AUTO_APPROVED else None,
        )

        if status == ApprovalStatus.PENDING:
            self.pending_approvals[request_id] = request
        else:
            self.approval_history.append(request)

        return request

    def _check_auto_approval(
        self, validation: CommandValidation, impact: ImpactAnalysis
    ) -> ApprovalStatus:
        """Check if command qualifies for auto-approval."""
        for _, rule_func in self.auto_approval_rules.items():
            if rule_func(validation, impact):
                return ApprovalStatus.AUTO_APPROVED
        return ApprovalStatus.PENDING

    def approve_request(self, request_id: str, approver: str) -> Optional[ApprovalRequest]:
        """Approve a pending request."""
        request = self.pending_approvals.get(request_id)
        if not request:
            return None

        request.status = ApprovalStatus.APPROVED
        request.approved_by = approver
        request.approved_at = datetime.utcnow()

        # Move to history
        del self.pending_approvals[request_id]
        self.approval_history.append(request)

        return request

    def reject_request(
        self, request_id: str, rejector: str, reason: str
    ) -> Optional[ApprovalRequest]:
        """Reject a pending request."""
        request = self.pending_approvals.get(request_id)
        if not request:
            return None

        request.status = ApprovalStatus.REJECTED
        request.approved_by = rejector
        request.approved_at = datetime.utcnow()
        request.rejection_reason = reason

        # Move to history
        del self.pending_approvals[request_id]
        self.approval_history.append(request)

        return request

    def get_pending_approvals(self) -> List[ApprovalRequest]:
        """Get all pending approval requests."""
        # Check for expired requests
        self._expire_old_requests()
        return list(self.pending_approvals.values())

    def get_approval_by_id(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get an approval request by ID."""
        # Check pending
        if request_id in self.pending_approvals:
            return self.pending_approvals[request_id]

        # Check history
        for request in self.approval_history:
            if request.id == request_id:
                return request

        return None

    def _expire_old_requests(self) -> None:
        """Expire requests that have been pending too long."""
        now = datetime.utcnow()
        expired_ids = []

        for request_id, request in self.pending_approvals.items():
            if now - request.requested_at > self.approval_timeout:
                request.status = ApprovalStatus.REJECTED
                request.rejection_reason = "Request expired due to timeout"
                self.approval_history.append(request)
                expired_ids.append(request_id)

        # Remove expired requests
        for request_id in expired_ids:
            del self.pending_approvals[request_id]

    def format_approval_request(self, request: ApprovalRequest) -> str:
        """Format an approval request for display."""
        lines = [
            "=" * 60,
            f"APPROVAL REQUEST: {request.id}",
            "=" * 60,
            f"Status: {request.status.value.upper()}",
            f"Requested by: {request.requested_by}",
            f"Requested at: {request.requested_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            f"Command: {request.command}",
            "",
            "RISK ASSESSMENT:",
            f"- Risk Level: {request.validation.risk_level.value.upper()}",
            f"- Command Type: {request.validation.command_type.value.upper()}",
        ]

        if request.validation.risks:
            lines.append("- Risks:")
            for risk in request.validation.risks:
                lines.append(f"  • {risk}")

        if request.validation.warnings:
            lines.append("- Warnings:")
            for warning in request.validation.warnings:
                lines.append(f"  • {warning}")

        lines.extend(
            [
                "",
                "IMPACT ANALYSIS:",
                f"- Affected Resources: {len(request.impact_analysis.affected_resources)}",
            ]
        )

        for resource in request.impact_analysis.affected_resources[:5]:  # Show first 5
            lines.append(f"  • {resource}")

        if len(request.impact_analysis.affected_resources) > 5:
            remaining = len(request.impact_analysis.affected_resources) - 5
            lines.append(f"  • ... and {remaining} more")

        lines.extend(
            [
                f"- Affected Services: {', '.join(request.impact_analysis.affected_services)}",
                f"- Estimated Downtime: {request.impact_analysis.estimated_downtime or 'None'}",
                f"- Reversible: {'Yes' if request.impact_analysis.reversible else 'No'}",
                f"- Data Loss Risk: {'YES' if request.impact_analysis.data_loss_risk else 'No'}",
            ]
        )

        if request.impact_analysis.rollback_command:
            lines.extend(
                [
                    "",
                    "ROLLBACK COMMAND:",
                    request.impact_analysis.rollback_command,
                ]
            )

        if request.status != ApprovalStatus.PENDING:
            lines.extend(
                [
                    "",
                    "DECISION:",
                    f"- Status: {request.status.value}",
                    f"- Decided by: {request.approved_by}",
                    f"- Decided at: {self._format_decided_at(request)}",
                ]
            )

            if request.rejection_reason:
                lines.append(f"- Reason: {request.rejection_reason}")

        lines.append("=" * 60)

        return "\n".join(lines)

    def _format_decided_at(self, request: ApprovalRequest) -> str:
        """Format the decided at timestamp."""
        if request.approved_at:
            return request.approved_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        return "N/A"

    def get_approval_statistics(self) -> Dict[str, int]:
        """Get statistics about approvals."""
        stats = {
            "pending": len(self.pending_approvals),
            "approved": 0,
            "rejected": 0,
            "auto_approved": 0,
            "total": len(self.pending_approvals) + len(self.approval_history),
        }

        for request in self.approval_history:
            if request.status == ApprovalStatus.APPROVED:
                stats["approved"] += 1
            elif request.status == ApprovalStatus.REJECTED:
                stats["rejected"] += 1
            elif request.status == ApprovalStatus.AUTO_APPROVED:
                stats["auto_approved"] += 1

        return stats
