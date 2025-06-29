"""Tests for the audit logger module."""

import json
from datetime import datetime, timedelta

import pytest

from app.safety.audit_logger import AuditLogger
from app.safety.models import (
    CommandType,
    CommandValidation,
    ImpactAnalysis,
    RiskLevel,
)


class TestAuditLogger:
    """Test cases for AuditLogger."""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temporary directory for logs."""
        return tmp_path / "audit_logs"

    @pytest.fixture
    def logger(self, temp_dir):
        """Create a logger instance with temp directory."""
        return AuditLogger(log_dir=temp_dir)

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

    def test_log_command_execution(self, logger, sample_validation, sample_impact):
        """Test logging a command execution."""
        entry = logger.log_command_execution(
            command="rm -rf /data",
            executed_by="test-user",
            validation_result=sample_validation,
            impact_analysis=sample_impact,
            execution_result="Command executed successfully",
            dry_run=False,
        )

        assert entry.id
        assert entry.command == "rm -rf /data"
        assert entry.executed_by == "test-user"
        assert entry.validation_result == sample_validation
        assert entry.impact_analysis == sample_impact
        assert entry.execution_result == "Command executed successfully"
        assert not entry.dry_run
        assert entry in logger.recent_entries

    def test_json_log_file_creation(self, logger, temp_dir, sample_validation):
        """Test that JSON log files are created."""
        logger.log_command_execution(
            command="test command",
            executed_by="test-user",
            validation_result=sample_validation,
            dry_run=True,
        )

        # Check log file exists
        log_files = list(temp_dir.glob("audit_*.jsonl"))
        assert len(log_files) == 1

        # Check content
        with open(log_files[0], "r", encoding="utf-8") as f:
            line = f.readline()
            data = json.loads(line)
            assert data["command"] == "test command"
            assert data["executed_by"] == "test-user"

    def test_get_recent_entries(self, logger, sample_validation):
        """Test getting recent entries."""
        # Log multiple entries
        for i in range(10):
            logger.log_command_execution(
                command=f"command-{i}",
                executed_by="test-user",
                validation_result=sample_validation,
                dry_run=True,
            )

        # Get recent entries
        recent = logger.get_recent_entries(limit=5)
        assert len(recent) == 5
        assert recent[-1].command == "command-9"
        assert recent[0].command == "command-5"

    def test_search_logs_by_user(self, logger, sample_validation):
        """Test searching logs by user."""
        # Log entries for different users
        users = ["alice", "bob", "charlie"]
        for i, user in enumerate(users * 2):
            logger.log_command_execution(
                command=f"command-{i}",
                executed_by=user,
                validation_result=sample_validation,
                dry_run=True,
            )

        # Search for specific user
        alice_logs = logger.search_logs(user="alice")
        assert len(alice_logs) == 2
        assert all(log.executed_by == "alice" for log in alice_logs)

    def test_search_logs_by_risk_level(self, logger):
        """Test searching logs by risk level."""
        risk_levels = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]

        # Log entries with different risk levels
        for i, risk in enumerate(risk_levels * 2):
            validation = CommandValidation(
                command=f"command-{i}",
                is_safe=risk == RiskLevel.LOW,
                risk_level=risk,
                command_type=CommandType.UNKNOWN,
                risks=[],
                warnings=[],
                requires_approval=risk in [RiskLevel.HIGH, RiskLevel.CRITICAL],
            )

            logger.log_command_execution(
                command=f"command-{i}",
                executed_by="test-user",
                validation_result=validation,
                dry_run=True,
            )

        # Search for high risk
        high_risk_logs = logger.search_logs(risk_level="high")
        assert len(high_risk_logs) == 2
        assert all(log.validation_result.risk_level == RiskLevel.HIGH for log in high_risk_logs)

    def test_search_logs_by_time_range(self, logger, sample_validation):
        """Test searching logs by time range."""
        now = datetime.utcnow()

        # Create entries with different timestamps
        for i in range(5):
            entry = logger.log_command_execution(
                command=f"command-{i}",
                executed_by="test-user",
                validation_result=sample_validation,
                dry_run=True,
            )
            # Manually adjust timestamp for testing
            entry.timestamp = now - timedelta(hours=i)

        # Search last 2 hours
        recent_logs = logger.search_logs(start_time=now - timedelta(hours=2), end_time=now)

        # Should find entries 0, 1, 2 (within 2 hours)
        assert len(recent_logs) >= 3

    def test_search_logs_dry_run_filter(self, logger, sample_validation):
        """Test filtering by dry run status."""
        # Log mix of dry-run and actual executions
        for i in range(6):
            logger.log_command_execution(
                command=f"command-{i}",
                executed_by="test-user",
                validation_result=sample_validation,
                dry_run=(i % 2 == 0),
            )

        # Search dry-run only
        dry_run_logs = logger.search_logs(dry_run_only=True)
        assert len(dry_run_logs) == 3
        assert all(log.dry_run for log in dry_run_logs)

        # Search actual executions only
        actual_logs = logger.search_logs(dry_run_only=False)
        assert len(actual_logs) == 3
        assert all(not log.dry_run for log in actual_logs)

    def test_generate_audit_report(self, logger):
        """Test audit report generation."""
        now = datetime.utcnow()

        # Create various log entries
        risk_levels = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        command_types = [CommandType.READ_ONLY, CommandType.DELETION, CommandType.NETWORK]

        for i in range(10):
            validation = CommandValidation(
                command=f"command-{i}",
                is_safe=i < 5,
                risk_level=risk_levels[i % len(risk_levels)],
                command_type=command_types[i % len(command_types)],
                risks=["Test risk"] if i >= 5 else [],
                warnings=[],
                requires_approval=i >= 7,
            )

            logger.log_command_execution(
                command=f"command-{i}",
                executed_by=f"user-{i % 3}",
                validation_result=validation,
                execution_error="Error occurred" if i == 8 else None,
                dry_run=(i % 3 == 0),
            )

        # Generate report
        report = logger.generate_audit_report(
            start_time=now - timedelta(hours=1), end_time=now + timedelta(hours=1)
        )

        assert "AUDIT REPORT" in report
        assert "SUMMARY STATISTICS" in report
        assert "Total Commands: 10" in report
        assert "Unique Users: 3" in report
        assert "RISK LEVEL DISTRIBUTION" in report
        assert "COMMAND TYPE DISTRIBUTION" in report
        assert "HIGH-RISK COMMANDS" in report
        assert "FAILED EXECUTIONS" in report

    def test_export_logs_json(self, logger, temp_dir, sample_validation):
        """Test exporting logs to JSON."""
        # Create some log entries
        for i in range(3):
            logger.log_command_execution(
                command=f"command-{i}",
                executed_by="test-user",
                validation_result=sample_validation,
                dry_run=True,
            )

        # Export to JSON
        export_file = temp_dir / "export.json"
        logger.export_logs(export_file, file_format="json")

        assert export_file.exists()

        # Verify content
        with open(export_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert len(data) == 3
            assert all(isinstance(entry, dict) for entry in data)
            assert data[-1]["command"] == "command-2"

    def test_export_logs_csv(self, logger, temp_dir, sample_validation):
        """Test exporting logs to CSV."""
        # Create some log entries
        for i in range(3):
            logger.log_command_execution(
                command=f"command-{i}",
                executed_by="test-user",
                validation_result=sample_validation,
                dry_run=True,
            )

        # Export to CSV
        export_file = temp_dir / "export.csv"
        logger.export_logs(export_file, file_format="csv")

        assert export_file.exists()

        # Verify content
        with open(export_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 4  # Header + 3 entries
            assert "timestamp,id,user,command" in lines[0]

    def test_export_logs_invalid_format(self, logger, temp_dir):
        """Test exporting with invalid format raises error."""
        export_file = temp_dir / "export.txt"

        with pytest.raises(ValueError, match="Unsupported format"):
            logger.export_logs(export_file, file_format="invalid")
