"""Concrete command implementations for Paddi CLI."""

import json
import logging
from pathlib import Path

from app.collector.agent_collector import main as collector_main
from app.explainer.agent_explainer import main as explainer_main
from app.reporter.agent_reporter import main as reporter_main

from .base import Command, CommandContext

logger = logging.getLogger(__name__)


class InitCommand(Command):
    """Initialize Paddi with sample data."""

    @property
    def name(self) -> str:
        return "init"

    @property
    def description(self) -> str:
        return "Initialize Paddi with sample data for quick demonstration"

    def execute(self, context: CommandContext) -> None:
        """Execute init command."""
        logger.info("🚀 Welcome to Paddi!")

        # Ensure directories exist
        Path("data").mkdir(exist_ok=True)
        Path(context.output_dir).mkdir(exist_ok=True)

        # Create sample data if it doesn't exist
        sample_data_path = Path("data/sample_collected.json")
        if not sample_data_path.exists():
            sample_data = {
                "project_id": "example-project-123",
                "timestamp": "2025-06-23T10:00:00Z",
                "iam_policies": [
                    {
                        "resource": "projects/example-project-123",
                        "bindings": [
                            {"role": "roles/owner", "members": ["user:admin@example.com"]}
                        ],
                    }
                ],
                "scc_findings": [
                    {
                        "name": "organizations/123/sources/456/findings/789",
                        "category": "PUBLIC_BUCKET",
                        "severity": "HIGH",
                    }
                ],
            }
            sample_data_path.write_text(json.dumps(sample_data, indent=2), encoding="utf-8")
            logger.info("✅ Created sample data")

        if not context.skip_run:
            logger.info("Running full audit pipeline with sample data...")
            audit_cmd = AuditCommand()
            audit_cmd.execute(context)
        else:
            logger.info("✅ Paddi initialized. Run 'python main.py audit' to start.")


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
