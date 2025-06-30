"""Explain command implementation."""

import logging

from app.cli.base import Command, CommandContext
from app.explainer.agent_explainer import main as explainer_main

logger = logging.getLogger(__name__)


class ExplainCommand(Command):
    """Analyze security risks using AI."""

    @property
    def name(self) -> str:
        return "explain"

    @property
    def description(self) -> str:
        return "Analyze security risks using AI"

    def execute(self, context: CommandContext) -> None:
        """Execute explain command."""
        logger.info("🔍 Analyzing security risks...")

        explainer_main(
            project_id=context.project_id,
            location=context.location,
            use_mock=context.use_mock,
            ai_provider=context.ai_provider,
            ollama_model=context.ollama_model,
            ollama_endpoint=context.ollama_endpoint,
        )