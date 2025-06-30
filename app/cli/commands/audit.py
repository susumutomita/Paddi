"""Audit command implementation."""

import logging

from app.cli.base import Command, CommandContext
from .collect import CollectCommand
from .explain import ExplainCommand
from .report import ReportCommand

logger = logging.getLogger(__name__)


class AuditCommand(Command):
    """Run complete audit pipeline."""

    @property
    def name(self) -> str:
        return "audit"

    @property
    def description(self) -> str:
        return "Run complete audit pipeline (collect + explain + report)"

    def execute(self, context: CommandContext) -> None:
        """Execute audit command."""
        logger.info("🔐 Starting complete security audit...")

        # Run all steps in sequence
        collect_cmd = CollectCommand()
        explain_cmd = ExplainCommand()
        report_cmd = ReportCommand()

        collect_cmd.execute(context)
        explain_cmd.execute(context)
        report_cmd.execute(context)

        logger.info("✅ Audit complete! Check %s/ for results.", context.output_dir)