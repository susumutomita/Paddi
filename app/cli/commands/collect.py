"""Collect command implementation."""

import logging

from app.cli.base import Command, CommandContext
from app.collector.agent_collector import main as collector_main

logger = logging.getLogger(__name__)


class CollectCommand(Command):
    """Collect cloud configuration data."""

    @property
    def name(self) -> str:
        return "collect"

    @property
    def description(self) -> str:
        return "Collect cloud configuration data"

    def execute(self, context: CommandContext) -> None:
        """Execute collect command."""
        logger.info("📥 Collecting cloud configuration data...")

        collector_main(
            project_id=context.project_id,
            organization_id=context.organization_id,
            use_mock=context.use_mock,
            collect_all=context.collect_all,
            verbose=context.verbose,
        )