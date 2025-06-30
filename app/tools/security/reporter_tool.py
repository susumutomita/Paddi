"""Security reporter tool that wraps the existing reporter agent."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from app.reporter.agent_reporter import ReportGenerator
from app.tools.base import (
    BaseTool,
    ToolCategory,
    ToolExecutionContext,
    ToolMetadata,
    ToolPriority,
    ToolResult,
)


logger = logging.getLogger(__name__)


class SecurityReporterTool(BaseTool):
    """Tool for generating security audit reports."""

    def __init__(self):
        """Initialize the security reporter tool."""
        super().__init__()

    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="security_reporter",
            description="Generates security audit reports in multiple formats (Markdown, HTML, HonKit)",
            category=ToolCategory.SECURITY_AUDIT,
            priority=ToolPriority.MEDIUM,
            tags=["security", "report", "documentation", "markdown", "html", "honkit"],
            dependencies=["security_explainer"],
            parameters={
                "input_file": {
                    "type": "string",
                    "description": "Path to analysis findings JSON",
                    "required": False,
                    "default": "data/explained.json",
                },
                "output_dir": {
                    "type": "string",
                    "description": "Directory to save reports",
                    "required": False,
                    "default": "output",
                },
                "formats": {
                    "type": "array",
                    "description": "Report formats to generate",
                    "required": False,
                    "default": ["markdown", "html"],
                    "choices": ["markdown", "html", "honkit"],
                },
                "template": {
                    "type": "string",
                    "description": "Report template to use",
                    "required": False,
                    "default": "default",
                },
                "metadata": {
                    "type": "object",
                    "description": "Additional metadata for the report",
                    "required": False,
                },
            },
        )

    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        """Validate input parameters."""
        errors = []

        # Check if input file exists
        if "input_file" in params:
            input_path = Path(params["input_file"])
            if not input_path.exists():
                errors.append(f"Input file not found: {params['input_file']}")

        # Validate formats
        if "formats" in params:
            valid_formats = ["markdown", "html", "honkit"]
            if isinstance(params["formats"], list):
                for fmt in params["formats"]:
                    if fmt not in valid_formats:
                        errors.append(f"Invalid format: {fmt}. Must be one of {valid_formats}")
            else:
                errors.append("Formats must be a list")

        return errors

    def execute(self, context: ToolExecutionContext, **kwargs) -> ToolResult:
        """Execute the report generation."""
        try:
            # Extract parameters
            input_file = kwargs.get("input_file", "data/explained.json")
            output_dir = kwargs.get("output_dir", "output")
            formats = kwargs.get("formats", ["markdown", "html"])
            template = kwargs.get("template", "default")
            metadata = kwargs.get("metadata", {})

            logger.info(f"Generating security reports in formats: {formats}")

            # Initialize report generator
            generator = ReportGenerator(
                input_file=input_file,
                output_dir=output_dir,
            )

            # Load findings
            findings = generator.load_findings()
            
            # Add metadata if provided
            if metadata:
                generator.metadata.update(metadata)

            # Generate reports in requested formats
            generated_files = []
            
            if "markdown" in formats:
                md_path = generator.generate_markdown()
                generated_files.append(str(md_path))
                logger.info(f"Generated Markdown report: {md_path}")

            if "html" in formats:
                html_path = generator.generate_html()
                generated_files.append(str(html_path))
                logger.info(f"Generated HTML report: {html_path}")

            if "honkit" in formats:
                honkit_path = generator.generate_honkit()
                generated_files.append(str(honkit_path))
                logger.info(f"Generated HonKit report: {honkit_path}")

            # Calculate summary statistics
            high_count = sum(1 for f in findings if f.get("severity") == "HIGH")
            medium_count = sum(1 for f in findings if f.get("severity") == "MEDIUM")
            low_count = sum(1 for f in findings if f.get("severity") == "LOW")
            total_count = len(findings)

            return ToolResult(
                success=True,
                data={
                    "generated_files": generated_files,
                    "formats": formats,
                    "findings_summary": {
                        "total": total_count,
                        "high": high_count,
                        "medium": medium_count,
                        "low": low_count,
                    },
                    "output_dir": output_dir,
                },
                metadata={
                    "template": template,
                    "input_file": input_file,
                },
            )

        except FileNotFoundError as e:
            logger.error(f"Input file not found: {e}")
            return ToolResult(
                success=False,
                error=f"Input file not found: {e}. Run security_explainer tool first.",
            )
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"exception_type": type(e).__name__},
            )