"""Main safety check system that integrates all safety components."""

from typing import List, Optional, Tuple

from app.safety.approval import ApprovalWorkflow
from app.safety.audit_logger import AuditLogger
from app.safety.dry_run import DryRunSimulator
from app.safety.impact_analyzer import ImpactAnalyzer
from app.safety.models import (
    ApprovalRequest,
    ApprovalStatus,
    CommandValidation,
    ImpactAnalysis,
    RiskLevel,
)
from app.safety.validator import SafetyValidator


class SafetyCheck:
    """Main safety check system for command validation and execution."""

    def __init__(self, audit_log_dir: Optional[str] = None):
        """Initialize the safety check system."""
        self.validator = SafetyValidator()
        self.dry_run_simulator = DryRunSimulator()
        self.impact_analyzer = ImpactAnalyzer()
        self.approval_workflow = ApprovalWorkflow()
        self.audit_logger = AuditLogger(audit_log_dir)

    def validate_command(
        self, command: str, user: str, dry_run: bool = True, force_approval: bool = False
    ) -> Tuple[bool, str, Optional[ApprovalRequest]]:
        """
        Validate a command and determine if it's safe to execute.

        Args:
            command: The command to validate
            user: The user requesting execution
            dry_run: Whether to simulate execution only
            force_approval: Force manual approval even for low-risk commands

        Returns:
            Tuple of (is_safe, message, approval_request)
        """
        # Step 1: Validate command
        validation = self.validator.validate_command(command)

        # Step 2: Analyze impact
        impact = self.impact_analyzer.analyze_impact(
            command, validation.command_type, validation.risk_level
        )

        # Step 3: Run dry-run simulation
        if dry_run or not validation.is_safe:
            dry_run_output = self.dry_run_simulator.simulate_command(
                command, validation.command_type
            )
            validation.dry_run_output = dry_run_output

        # Step 4: Check if approval is needed
        approval_request = None
        if validation.requires_approval or force_approval:
            approval_request = self.approval_workflow.create_approval_request(
                command, validation, impact, user, force_approval
            )

        # Step 5: Log the validation attempt
        self.audit_logger.log_command_execution(
            command=command,
            executed_by=user,
            validation_result=validation,
            impact_analysis=impact,
            approval=approval_request,
            dry_run=True,  # Initial validation is always dry-run
        )

        # Step 6: Generate response message
        message = self._generate_validation_message(validation, impact, approval_request, dry_run)

        # Determine if safe to proceed
        is_safe = (
            validation.is_safe and not validation.requires_approval and not force_approval
        ) or (
            approval_request
            and approval_request.status in [ApprovalStatus.APPROVED, ApprovalStatus.AUTO_APPROVED]
        )

        return is_safe, message, approval_request

    def execute_command(
        self, command: str, user: str, approval_id: Optional[str] = None, dry_run: bool = False
    ) -> Tuple[bool, str]:
        """
        Execute a command after validation.

        Args:
            command: The command to execute
            user: The user executing the command
            approval_id: ID of approval request if pre-approved
            dry_run: Whether to simulate execution only

        Returns:
            Tuple of (success, result_message)
        """
        # Validate command
        is_safe, validation_msg, approval_request = self.validate_command(command, user, dry_run)

        # Check approval if needed
        if approval_id:
            approval = self.approval_workflow.get_approval_by_id(approval_id)
            if not approval:
                return False, "Invalid approval ID"
            if approval.status != ApprovalStatus.APPROVED:
                return False, f"Approval status is {approval.status.value}, not approved"
            approval_request = approval

        # Check if safe to execute
        if not is_safe and not approval_request:
            return False, f"Command validation failed:\n{validation_msg}"

        if approval_request and approval_request.status == ApprovalStatus.PENDING:
            return False, (
                f"Command requires approval. Approval ID: {approval_request.id}\n"
                f"Use the approval workflow to approve/reject this command."
            )

        # Execute or simulate
        if dry_run:
            result = f"DRY-RUN MODE - Command not executed:\n{validation_msg}"
            success = True
        else:
            # In production, this would actually execute the command
            result = "Command execution would happen here (not implemented in safety demo)"
            success = True

        # Log execution
        validation = self.validator.validate_command(command)
        impact = self.impact_analyzer.analyze_impact(
            command, validation.command_type, validation.risk_level
        )

        self.audit_logger.log_command_execution(
            command=command,
            executed_by=user,
            validation_result=validation,
            impact_analysis=impact,
            approval=approval_request,
            execution_result=result if success else None,
            execution_error=result if not success else None,
            dry_run=dry_run,
        )

        return success, result

    def _generate_validation_message(
        self,
        validation: CommandValidation,
        impact: ImpactAnalysis,
        approval: Optional[ApprovalRequest],
        dry_run: bool,
    ) -> str:
        """Generate a detailed validation message."""
        lines = []

        # Header based on safety status
        lines.append(self._get_validation_header(validation))

        lines.extend(
            [
                "",
                f"Command: {validation.command}",
                f"Risk Level: {validation.risk_level.value.upper()}",
                f"Type: {validation.command_type.value}",
            ]
        )

        # Risks and warnings
        lines.extend(self._format_risks_and_warnings(validation))

        # Impact analysis
        lines.extend(self._format_impact_analysis(impact))

        # Dry-run output
        lines.extend(self._format_dry_run_output(validation, dry_run))

        # Safe alternatives
        lines.extend(self._format_safe_alternatives(validation))

        # Mitigation suggestions
        lines.extend(self._format_mitigation_suggestions(impact))

        # Approval status
        if approval:
            lines.extend(self._format_approval_status(approval))

        return "\n".join(lines)

    def _get_validation_header(self, validation: CommandValidation) -> str:
        """Get the appropriate header message based on validation status."""
        if validation.is_safe and not validation.requires_approval:
            return "✓ COMMAND VALIDATED - Safe to execute"
        if validation.risk_level == RiskLevel.CRITICAL:
            return "⚠️  CRITICAL RISK DETECTED - Manual review required"
        if validation.risk_level == RiskLevel.HIGH:
            return "⚠️  HIGH RISK DETECTED - Approval required"
        return "⚠️  COMMAND REQUIRES REVIEW"

    def _format_risks_and_warnings(self, validation: CommandValidation) -> List[str]:
        """Format risks and warnings section."""
        lines = []

        if validation.risks:
            lines.extend(["", "RISKS:"])
            for risk in validation.risks:
                lines.append(f"  ⚠️  {risk}")

        if validation.warnings:
            lines.extend(["", "WARNINGS:"])
            for warning in validation.warnings:
                lines.append(f"  ⚠️  {warning}")

        return lines

    def _format_impact_analysis(self, impact: ImpactAnalysis) -> List[str]:
        """Format impact analysis section."""
        lines = [
            "",
            "IMPACT ANALYSIS:",
            f"- Affected Resources: {len(impact.affected_resources)}",
            f"- Affected Services: {', '.join(impact.affected_services) or 'None'}",
            f"- Data Loss Risk: {'YES' if impact.data_loss_risk else 'No'}",
            f"- Reversible: {'Yes' if impact.reversible else 'No'}",
        ]

        if impact.estimated_downtime:
            lines.append(f"- Estimated Downtime: {impact.estimated_downtime}")

        # Rollback command
        if impact.rollback_command:
            lines.extend(
                [
                    "",
                    "ROLLBACK COMMAND:",
                    f"  {impact.rollback_command}",
                ]
            )

        return lines

    def _format_approval_status(self, approval: ApprovalRequest) -> List[str]:
        """Format approval status section."""
        lines = [
            "",
            "APPROVAL STATUS:",
            f"- Request ID: {approval.id}",
            f"- Status: {approval.status.value.upper()}",
        ]

        if approval.status == ApprovalStatus.AUTO_APPROVED:
            lines.append("- Auto-approved based on safety rules")
        elif approval.status == ApprovalStatus.PENDING:
            lines.append("- Awaiting manual approval")

        return lines

    def _format_dry_run_output(self, validation: CommandValidation, dry_run: bool) -> List[str]:
        """Format dry-run output section."""
        lines = []

        if dry_run and validation.dry_run_output:
            lines.extend(
                [
                    "",
                    "DRY-RUN SIMULATION:",
                    validation.dry_run_output,
                ]
            )

        return lines

    def _format_safe_alternatives(self, validation: CommandValidation) -> List[str]:
        """Format safe alternatives section."""
        lines = []

        alternatives = self.validator.get_safe_alternatives(validation.command)
        if alternatives:
            lines.extend(["", "SAFER ALTERNATIVES:"])
            for alt in alternatives:
                lines.append(f"  • {alt}")

        return lines

    def _format_mitigation_suggestions(self, impact: ImpactAnalysis) -> List[str]:
        """Format mitigation suggestions section."""
        lines = []

        mitigations = self.impact_analyzer.get_mitigation_suggestions(impact)
        if mitigations:
            lines.extend(["", "MITIGATION SUGGESTIONS:"])
            for mitigation in mitigations:
                lines.append(f"  • {mitigation}")

        return lines

    def get_pending_approvals(self) -> List[ApprovalRequest]:
        """Get all pending approval requests."""
        return self.approval_workflow.get_pending_approvals()

    def approve_command(self, approval_id: str, approver: str) -> Optional[ApprovalRequest]:
        """Approve a pending command."""
        return self.approval_workflow.approve_request(approval_id, approver)

    def reject_command(
        self, approval_id: str, rejector: str, reason: str
    ) -> Optional[ApprovalRequest]:
        """Reject a pending command."""
        return self.approval_workflow.reject_request(approval_id, rejector, reason)

    def get_audit_report(self, start_time, end_time) -> str:
        """Generate an audit report for the specified time period."""
        return self.audit_logger.generate_audit_report(start_time, end_time)

    def search_audit_logs(self, **kwargs) -> List[dict]:
        """Search audit logs with filters."""
        entries = self.audit_logger.search_logs(**kwargs)
        return [entry.to_dict() for entry in entries]
