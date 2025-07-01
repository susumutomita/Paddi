#!/usr/bin/env python3
"""
Main entry point for Paddi Python agents orchestration.
"""

import logging
import sys

import fire

from app.cli.paddi_cli import PaddiCLI

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point with natural language support."""
    # Check if natural language command is provided
    if len(sys.argv) == 2 and not sys.argv[1].startswith("-"):
        # Single argument that doesn't start with dash - likely natural language
        natural_language_input = sys.argv[1]

        # Check if it's a known Fire command
        known_commands = [
            "init",
            "audit",
            "collect",
            "analyze",
            "explain",
            "report",
            "list_commands",
            "validate_command",
            "approve_command",
            "execute_remediation",
            "approve",
            "reject",
            "list_approvals",
            "chat",
            "ai_agent",
            "ai_audit",
            "langchain_audit",
            "recursive_audit",
            "audit_log",
            "safety_demo",
            "audit_logs",
        ]

        if natural_language_input not in known_commands:
            # This is a natural language command
            from app.agents.autonomous_cli import AutonomousCLI

            cli = AutonomousCLI()
            result = cli.execute_one_shot(natural_language_input)
            sys.exit(0 if result.get("success") else 1)

    # Otherwise, use normal Fire CLI
    fire.Fire(PaddiCLI)


if __name__ == "__main__":
    main()
