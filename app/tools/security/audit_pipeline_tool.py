"""Composite tool for running complete security audit pipeline."""

import logging
from typing import Any, Dict, List

from app.tools.base import (
    CompositeTool,
    ToolCategory,
    ToolExecutionContext,
    ToolMetadata,
    ToolPriority,
    ToolResult,
)
from app.tools.security.collector_tool import SecurityCollectorTool
from app.tools.security.explainer_tool import SecurityExplainerTool
from app.tools.security.reporter_tool import SecurityReporterTool


logger = logging.getLogger(__name__)


class SecurityAuditPipelineTool(CompositeTool):
    """Composite tool that runs the complete security audit pipeline."""

    def __init__(self):
        """Initialize the audit pipeline tool."""
        # Initialize sub-tools
        tools = [
            SecurityCollectorTool(),
            SecurityExplainerTool(),
            SecurityReporterTool(),
        ]
        super().__init__(tools)

    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="security_audit_pipeline",
            description="Runs complete security audit pipeline: collect -> analyze -> report",
            category=ToolCategory.SECURITY_AUDIT,
            priority=ToolPriority.CRITICAL,
            tags=["security", "audit", "pipeline", "composite", "automated"],
            parameters={
                "provider": {
                    "type": "string",
                    "description": "Cloud provider (gcp, aws, azure, github, all)",
                    "required": False,
                    "default": "all",
                },
                "project_id": {
                    "type": "string",
                    "description": "GCP project ID",
                    "required": False,
                },
                "use_mock": {
                    "type": "boolean",
                    "description": "Use mock data for testing",
                    "required": False,
                    "default": False,
                },
                "output_dir": {
                    "type": "string",
                    "description": "Output directory for reports",
                    "required": False,
                    "default": "output",
                },
                "report_formats": {
                    "type": "array",
                    "description": "Report formats to generate",
                    "required": False,
                    "default": ["markdown", "html"],
                },
                "ai_provider": {
                    "type": "string",
                    "description": "AI provider for analysis",
                    "required": False,
                    "choices": ["gemini", "ollama"],
                },
            },
        )

    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        """Validate input parameters."""
        errors = []

        # Validate provider
        if "provider" in params:
            valid_providers = ["gcp", "aws", "azure", "github", "all"]
            if params["provider"] not in valid_providers:
                errors.append(f"Invalid provider: {params['provider']}")

        # Validate report formats
        if "report_formats" in params:
            valid_formats = ["markdown", "html", "honkit"]
            if isinstance(params["report_formats"], list):
                for fmt in params["report_formats"]:
                    if fmt not in valid_formats:
                        errors.append(f"Invalid format: {fmt}")
            else:
                errors.append("report_formats must be a list")

        return errors

    def execute(self, context: ToolExecutionContext, **kwargs) -> ToolResult:
        """Execute the complete audit pipeline."""
        try:
            results = {}
            
            # Extract common parameters
            use_mock = kwargs.get("use_mock", False)
            output_dir = kwargs.get("output_dir", "output")
            
            logger.info("Starting security audit pipeline...")

            # Step 1: Collect data
            logger.info("Step 1/3: Collecting security data...")
            collector = self.tools[0]  # SecurityCollectorTool
            collect_result = collector.run(
                context,
                provider=kwargs.get("provider", "all"),
                use_mock=use_mock,
                output_file="data/collected.json",
            )
            
            if not collect_result.success:
                return ToolResult(
                    success=False,
                    error=f"Collection failed: {collect_result.error}",
                    data={"step": "collect", "results": results},
                )
            
            results["collect"] = {
                "success": True,
                "items_collected": collect_result.metadata.get("items_collected", 0),
            }

            # Step 2: Analyze with AI
            logger.info("Step 2/3: Analyzing security risks...")
            explainer = self.tools[1]  # SecurityExplainerTool
            explain_result = explainer.run(
                context,
                project_id=kwargs.get("project_id"),
                use_mock=use_mock,
                input_file="data/collected.json",
                output_dir="data",
                ai_provider=kwargs.get("ai_provider"),
                ollama_model=kwargs.get("ollama_model"),
                ollama_endpoint=kwargs.get("ollama_endpoint"),
            )
            
            if not explain_result.success:
                return ToolResult(
                    success=False,
                    error=f"Analysis failed: {explain_result.error}",
                    data={"step": "explain", "results": results},
                )
            
            results["explain"] = {
                "success": True,
                "findings": explain_result.data.get("total", 0),
                "high": explain_result.data.get("high", 0),
                "medium": explain_result.data.get("medium", 0),
                "low": explain_result.data.get("low", 0),
            }

            # Step 3: Generate reports
            logger.info("Step 3/3: Generating reports...")
            reporter = self.tools[2]  # SecurityReporterTool
            report_result = reporter.run(
                context,
                input_file="data/explained.json",
                output_dir=output_dir,
                formats=kwargs.get("report_formats", ["markdown", "html"]),
            )
            
            if not report_result.success:
                return ToolResult(
                    success=False,
                    error=f"Report generation failed: {report_result.error}",
                    data={"step": "report", "results": results},
                )
            
            results["report"] = {
                "success": True,
                "generated_files": report_result.data.get("generated_files", []),
                "formats": report_result.data.get("formats", []),
            }

            # Pipeline completed successfully
            logger.info("Security audit pipeline completed successfully!")
            
            return ToolResult(
                success=True,
                data={
                    "pipeline_complete": True,
                    "results": results,
                    "summary": {
                        "items_collected": results["collect"]["items_collected"],
                        "findings_total": results["explain"]["findings"],
                        "high_severity": results["explain"]["high"],
                        "reports_generated": len(results["report"]["generated_files"]),
                    },
                },
                metadata={
                    "provider": kwargs.get("provider", "all"),
                    "use_mock": use_mock,
                    "ai_provider": kwargs.get("ai_provider", "gemini"),
                },
            )

        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                data={"results": results},
                metadata={"exception_type": type(e).__name__},
            )