#!/usr/bin/env python3
"""
Main entry point for Paddi Python agents orchestration.
"""

import logging

import fire

from app.cli.paddi_cli import PaddiCLI

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    fire.Fire(PaddiCLI)


if __name__ == "__main__":
    main()
