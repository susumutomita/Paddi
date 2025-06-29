"""Comprehensive audit logging for command execution."""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from app.safety.models import ApprovalRequest, AuditLogEntry, CommandValidation, ImpactAnalysis


class AuditLogger:
    """Logs all command execution attempts with full context."""

    def __init__(self, log_dir: Optional[Path] = None):
        """Initialize the audit logger."""
        if isinstance(log_dir, str):
            self.log_dir = Path(log_dir)
        else:
            self.log_dir = log_dir or Path("audit_logs")
        self.log_dir.mkdir(exist_ok=True)

        # Setup Python logger
        self.logger = logging.getLogger("safety.audit")

        # JSON log file (rotated daily in production)
        self.json_log_file = self.log_dir / f"audit_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"

        # In-memory cache for recent entries (in production, use database)
        self.recent_entries: List[AuditLogEntry] = []
        self.max_recent_entries = 1000

    def log_command_execution(
        self,
        command: str,
        executed_by: str,
        validation_result: CommandValidation,
        impact_analysis: Optional[ImpactAnalysis] = None,
        approval: Optional[ApprovalRequest] = None,
        execution_result: Optional[str] = None,
        execution_error: Optional[str] = None,
        dry_run: bool = False,
    ) -> AuditLogEntry:
        """Log a command execution attempt."""
        entry = AuditLogEntry(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            command=command,
            executed_by=executed_by,
            validation_result=validation_result,
            impact_analysis=impact_analysis,
            approval=approval,
            execution_result=execution_result,
            execution_error=execution_error,
            dry_run=dry_run,
        )

        # Write to JSON log
        self._write_json_log(entry)

        # Add to recent entries cache
        self.recent_entries.append(entry)
        if len(self.recent_entries) > self.max_recent_entries:
            self.recent_entries.pop(0)

        # Log to Python logger
        self._log_to_python_logger(entry)

        return entry

    def _write_json_log(self, entry: AuditLogEntry) -> None:
        """Write entry to JSON log file."""
        try:
            with open(self.json_log_file, "a", encoding="utf-8") as f:
                json.dump(entry.to_dict(), f)
                f.write("\n")
        except Exception as e:
            self.logger.error("Failed to write audit log: %s", e)

    def _log_to_python_logger(self, entry: AuditLogEntry) -> None:
        """Log entry using Python's logging system."""
        level = logging.WARNING
        if entry.validation_result.risk_level.value in ["high", "critical"]:
            level = logging.ERROR
        elif entry.validation_result.risk_level.value == "medium":
            level = logging.WARNING
        else:
            level = logging.INFO

        msg = (
            f"Command execution: user={entry.executed_by}, "
            f"risk={entry.validation_result.risk_level.value}, "
            f"type={entry.validation_result.command_type.value}, "
            f"dry_run={entry.dry_run}, "
            f"command={entry.command[:50]}..."
        )

        self.logger.log(level, msg)

    def get_recent_entries(self, limit: int = 100) -> List[AuditLogEntry]:
        """Get recent audit log entries."""
        return self.recent_entries[-limit:]

    def search_logs(
        self,
        user: Optional[str] = None,
        risk_level: Optional[str] = None,
        command_pattern: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        dry_run_only: Optional[bool] = None,
    ) -> List[AuditLogEntry]:
        """Search audit logs with filters."""
        results = []

        # Search in recent entries (in production, query database)
        for entry in self.recent_entries:
            if user and entry.executed_by != user:
                continue
            if risk_level and entry.validation_result.risk_level.value != risk_level:
                continue
            if command_pattern and command_pattern not in entry.command:
                continue
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue
            if dry_run_only is not None and entry.dry_run != dry_run_only:
                continue

            results.append(entry)

        return results

    def generate_audit_report(self, start_time: datetime, end_time: datetime) -> str:
        """Generate an audit report for a time period."""
        entries = self.search_logs(start_time=start_time, end_time=end_time)

        if not entries:
            return "No audit entries found for the specified period."

        # Calculate statistics
        stats = {
            "total_commands": len(entries),
            "unique_users": len(set(e.executed_by for e in entries)),
            "dry_run_commands": sum(1 for e in entries if e.dry_run),
            "actual_executions": sum(1 for e in entries if not e.dry_run),
            "failed_executions": sum(1 for e in entries if e.execution_error),
            "risk_levels": {},
            "command_types": {},
            "required_approvals": sum(1 for e in entries if e.approval),
            "auto_approved": sum(
                1 for e in entries if e.approval and e.approval.status.value == "auto_approved"
            ),
        }

        # Count by risk level
        for entry in entries:
            risk = entry.validation_result.risk_level.value
            stats["risk_levels"][risk] = stats["risk_levels"].get(risk, 0) + 1

        # Count by command type
        for entry in entries:
            cmd_type = entry.validation_result.command_type.value
            stats["command_types"][cmd_type] = stats["command_types"].get(cmd_type, 0) + 1

        # Generate report
        lines = [
            "=" * 80,
            f"AUDIT REPORT: {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')}",
            "=" * 80,
            "",
            "SUMMARY STATISTICS:",
            f"- Total Commands: {stats['total_commands']}",
            f"- Unique Users: {stats['unique_users']}",
            f"- Dry Run Commands: {stats['dry_run_commands']}",
            f"- Actual Executions: {stats['actual_executions']}",
            f"- Failed Executions: {stats['failed_executions']}",
            f"- Required Approvals: {stats['required_approvals']}",
            f"- Auto-Approved: {stats['auto_approved']}",
            "",
            "RISK LEVEL DISTRIBUTION:",
        ]

        for risk, count in sorted(stats["risk_levels"].items()):
            percentage = (count / stats["total_commands"]) * 100
            lines.append(f"- {risk.upper()}: {count} ({percentage:.1f}%)")

        lines.extend(
            [
                "",
                "COMMAND TYPE DISTRIBUTION:",
            ]
        )

        for cmd_type, count in sorted(stats["command_types"].items()):
            percentage = (count / stats["total_commands"]) * 100
            lines.append(f"- {cmd_type}: {count} ({percentage:.1f}%)")

        # High-risk commands
        high_risk_commands = [
            e for e in entries if e.validation_result.risk_level.value in ["high", "critical"]
        ]

        if high_risk_commands:
            lines.extend(
                [
                    "",
                    "HIGH-RISK COMMANDS:",
                ]
            )

            for entry in high_risk_commands[:10]:  # Show first 10
                lines.append(
                    f"- [{entry.timestamp.strftime('%Y-%m-%d %H:%M')}] "
                    f"{entry.executed_by}: {entry.command[:60]}..."
                )

            if len(high_risk_commands) > 10:
                lines.append(f"  ... and {len(high_risk_commands) - 10} more")

        # Failed executions
        failed_executions = [e for e in entries if e.execution_error]

        if failed_executions:
            lines.extend(
                [
                    "",
                    "FAILED EXECUTIONS:",
                ]
            )

            for entry in failed_executions[:5]:  # Show first 5
                lines.append(
                    f"- [{entry.timestamp.strftime('%Y-%m-%d %H:%M')}] "
                    f"{entry.executed_by}: {entry.execution_error}"
                )

            if len(failed_executions) > 5:
                lines.append(f"  ... and {len(failed_executions) - 5} more")

        lines.append("=" * 80)

        return "\n".join(lines)

    def export_logs(self, output_file: Path, file_format: str = "json") -> None:
        """Export audit logs to a file."""
        if file_format == "json":
            data = [entry.to_dict() for entry in self.recent_entries]
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        elif file_format == "csv":
            import csv

            with open(output_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "timestamp",
                        "id",
                        "user",
                        "command",
                        "risk_level",
                        "command_type",
                        "dry_run",
                        "approved",
                        "error",
                    ]
                )

                for entry in self.recent_entries:
                    writer.writerow(
                        [
                            entry.timestamp.isoformat(),
                            entry.id,
                            entry.executed_by,
                            entry.command,
                            entry.validation_result.risk_level.value,
                            entry.validation_result.command_type.value,
                            entry.dry_run,
                            bool(entry.approval),
                            entry.execution_error or "",
                        ]
                    )
        else:
            raise ValueError(f"Unsupported format: {file_format}")
