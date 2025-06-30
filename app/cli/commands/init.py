"""Initialize command implementation."""

import json
import logging
from pathlib import Path

from app.cli.base import Command, CommandContext

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
            from .audit import AuditCommand
            audit_cmd = AuditCommand()
            audit_cmd.execute(context)
        else:
            logger.info("✅ Paddi initialized. Run 'python main.py audit' to start.")