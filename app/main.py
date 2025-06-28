#!/usr/bin/env python3
"""
Main entry point for Paddi Python agents orchestration.
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

import fire

from app.collector.agent_collector import main as collector_main
from app.explainer.agent_explainer import main as explainer_main
from app.reporter.agent_reporter import main as reporter_main

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PaddiCLI:
    """Paddi CLI for cloud security audit automation."""

    def init(self, skip_run: bool = False, output: str = "output"):
        """
        Initialize Paddi with sample data for quick demonstration.

        Args:
            skip_run: Skip automatic pipeline execution
            output: Output directory for reports
        """
        logger.info("🚀 Welcome to Paddi!")

        # Ensure directories exist
        Path("data").mkdir(exist_ok=True)
        Path(output).mkdir(exist_ok=True)

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

        if not skip_run:
            logger.info("Running full audit pipeline with sample data...")
            self.audit(use_mock=True, output_dir=output)
        else:
            logger.info("✅ Paddi initialized. Run 'python main.py audit' to start.")

    def audit(
        self,
        project_id: str = "example-project-123",
        organization_id: Optional[str] = None,
        use_mock: bool = True,
        location: str = "us-central1",
        output_dir: str = "output",
        verbose: bool = False,
        ai_provider: str = None,
        ollama_model: str = None,
        ollama_endpoint: str = None,
    ):
        """
        Run complete audit pipeline.

        Args:
            project_id: GCP project ID
            organization_id: Optional organization ID
            use_mock: Use mock data instead of real GCP APIs
            location: GCP location for Vertex AI
            output_dir: Output directory for reports
            verbose: Enable verbose logging
            ai_provider: AI provider to use ('gemini' or 'ollama')
            ollama_model: Ollama model name (default: llama3)
            ollama_endpoint: Ollama API endpoint (default: http://localhost:11434)
        """
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        try:
            # Step 1: Collect
            logger.info("🔍 Starting security audit...")
            self.collect(project_id, organization_id, use_mock)

            # Step 2: Analyze
            self.analyze(project_id, location, use_mock, ai_provider, ollama_model, ollama_endpoint)

            # Step 3: Report
            self.report(output_dir=output_dir)

            logger.info("✅ Audit completed successfully!")
            logger.info("📊 Reports generated in: %s/", output_dir)

        except Exception as e:
            logger.error("❌ Audit pipeline failed: %s", e)
            if verbose:
                logger.exception("Full error trace:")
            sys.exit(1)

    def collect(
        self,
        project_id: str = "example-project-123",
        organization_id: Optional[str] = None,
        use_mock: bool = True,
    ):
        """
        Collect cloud configuration data.

        Args:
            project_id: GCP project ID
            organization_id: Optional organization ID
            use_mock: Use mock data instead of real GCP APIs
        """
        logger.info("✓ Collecting IAM policies and SCC findings...")

        try:
            collector_main(
                project_id=project_id,
                organization_id=organization_id,
                use_mock=use_mock,
            )

            # Load and display summary
            collected_path = Path("data/collected.json")
            if collected_path.exists():
                data = json.loads(collected_path.read_text(encoding="utf-8"))
                iam_count = len(data.get("iam_policies", []))
                scc_count = len(data.get("scc_findings", []))
                logger.info("  └─ Found %d IAM policies", iam_count)
                logger.info("  └─ Found %d SCC findings", scc_count)

        except Exception as e:
            logger.error("❌ Collection failed: %s", e)
            raise

    def analyze(
        self,
        project_id: str = "example-project-123",
        location: str = "us-central1",
        use_mock: bool = True,
        ai_provider: str = None,
        ollama_model: str = None,
        ollama_endpoint: str = None,
    ):
        """
        Analyze collected data with AI.

        Args:
            project_id: GCP project ID
            location: GCP location for Vertex AI
            use_mock: Use mock AI responses
            ai_provider: AI provider to use ('gemini' or 'ollama')
            ollama_model: Ollama model name (default: llama3)
            ollama_endpoint: Ollama API endpoint (default: http://localhost:11434)
        """
        import os
        provider = ai_provider or os.getenv('AI_PROVIDER', 'gemini')
        logger.info("✓ Analyzing with %s AI...", provider.capitalize())

        try:
            explainer_main(
                project_id=project_id,
                location=location,
                use_mock=use_mock,
                ai_provider=ai_provider,
                ollama_model=ollama_model,
                ollama_endpoint=ollama_endpoint,
            )

            # Load and display summary
            explained_path = Path("data/explained.json")
            if explained_path.exists():
                data = json.loads(explained_path.read_text(encoding="utf-8"))
                findings = data if isinstance(data, list) else []

                severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
                for finding in findings:
                    severity = finding.get("severity", "LOW")
                    if severity in severity_counts:
                        severity_counts[severity] += 1

                for severity, count in severity_counts.items():
                    if count > 0:
                        logger.info("  ├─ %s: %d issues", severity, count)

        except Exception as e:
            logger.error("❌ Analysis failed: %s", e)
            raise

    def report(
        self,
        formats: Optional[List[str]] = None,
        input_dir: str = "data",
        output_dir: str = "output",
        template_dir: str = "app/templates",
    ):
        """
        Generate audit reports.

        Args:
            formats: Report formats (markdown, html, honkit)
            input_dir: Input data directory
            output_dir: Output directory
            template_dir: Template directory
        """
        if formats is None:
            formats = ["markdown", "html"]

        logger.info("✓ Generating reports in formats: %s", ", ".join(formats))

        try:
            reporter_main(
                template_dir=template_dir,
                formats=formats,
                input_dir=input_dir,
                output_dir=output_dir,
            )

            logger.info("✓ Reports generated:")
            for fmt in formats:
                if fmt == "markdown":
                    logger.info("  • Markdown: %s/audit.md", output_dir)
                elif fmt == "html":
                    logger.info("  • HTML: %s/audit.html", output_dir)
                elif fmt == "honkit":
                    logger.info("  • HonKit: docs/")

        except Exception as e:
            logger.error("❌ Report generation failed: %s", e)
            raise


def main():
    """Main entry point."""
    fire.Fire(PaddiCLI)


if __name__ == "__main__":
    main()
