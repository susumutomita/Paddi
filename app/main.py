#!/usr/bin/env python3
"""
Main entry point for Paddi Python agents orchestration.
"""

import logging
from typing import List, Optional

import fire
from collector.agent_collector import main as collector_main
from explainer.agent_explainer import main as explainer_main
from reporter.agent_reporter import main as reporter_main

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_audit(
    project_id: str = "example-project",
    organization_id: Optional[str] = None,
    use_mock: bool = True,
    output_formats: Optional[List[str]] = None,
    location: str = "us-central1",
):
    """Run complete audit pipeline."""
    try:
        # Step 1: Collect
        logger.info("Step 1: Collecting GCP configuration...")
        collector_main(
            project_id=project_id,
            organization_id=organization_id,
            use_mock=use_mock,
        )

        # Step 2: Explain
        logger.info("Step 2: Analyzing security risks...")
        explainer_main(
            project_id=project_id,
            location=location,
            use_mock=use_mock,
        )

        # Step 3: Report
        logger.info("Step 3: Generating reports...")
        reporter_main(
            template_dir="app/templates",
            formats=output_formats or ["markdown", "html"],
        )

        logger.info(" Audit pipeline completed successfully!")

    except Exception as e:
        logger.error("Audit pipeline failed: %s", e)
        raise


if __name__ == "__main__":
    fire.Fire(run_audit)
