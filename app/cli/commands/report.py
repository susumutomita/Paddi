"""Report command implementation."""

import logging

from app.cli.base import Command, CommandContext
from app.reporter.agent_reporter import main as reporter_main

logger = logging.getLogger(__name__)


class ReportCommand(Command):
    """Generate security audit report."""

    @property
    def name(self) -> str:
        return "report"

    @property
    def description(self) -> str:
        return "Generate security audit report"

    def execute(self, context: CommandContext) -> None:
        """Execute report command."""
        logger.info("📝 Generating audit report...")

        reporter_main(output_dir=context.output_dir)