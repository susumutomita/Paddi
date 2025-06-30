"""Security explainer tool that wraps the existing explainer agent."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from app.explainer.agent_explainer import SecurityRiskExplainer
from app.tools.base import (
    BaseTool,
    ToolCategory,
    ToolExecutionContext,
    ToolMetadata,
    ToolPriority,
    ToolResult,
)


logger = logging.getLogger(__name__)


class SecurityExplainerTool(BaseTool):
    """Tool for analyzing security risks using AI."""

    def __init__(self):
        """Initialize the security explainer tool."""
        super().__init__()

    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="security_explainer",
            description="Analyzes security configurations using AI to identify risks and provide recommendations",
            category=ToolCategory.SECURITY_AUDIT,
            priority=ToolPriority.HIGH,
            tags=["security", "ai", "analysis", "risk", "explainer", "gemini", "ollama"],
            dependencies=["security_collector"],
            parameters={
                "project_id": {
                    "type": "string",
                    "description": "GCP project ID for Vertex AI",
                    "required": False,
                },
                "location": {
                    "type": "string",
                    "description": "GCP region for Vertex AI",
                    "required": False,
                    "default": "asia-northeast1",
                },
                "use_mock": {
                    "type": "boolean",
                    "description": "Use mock responses instead of real LLM calls",
                    "required": False,
                    "default": False,
                },
                "input_file": {
                    "type": "string",
                    "description": "Path to configuration data",
                    "required": False,
                    "default": "data/collected.json",
                },
                "output_dir": {
                    "type": "string",
                    "description": "Directory to save analysis results",
                    "required": False,
                    "default": "data",
                },
                "ai_provider": {
                    "type": "string",
                    "description": "AI provider to use (gemini or ollama)",
                    "required": False,
                    "choices": ["gemini", "ollama"],
                },
                "ollama_model": {
                    "type": "string",
                    "description": "Ollama model name",
                    "required": False,
                },
                "ollama_endpoint": {
                    "type": "string",
                    "description": "Ollama API endpoint",
                    "required": False,
                },
                "project_path": {
                    "type": "string",
                    "description": "Path to project for context collection",
                    "required": False,
                },
            },
        )

    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        """Validate input parameters."""
        errors = []

        # Check if input file exists when not in dry run
        if "input_file" in params:
            input_path = Path(params["input_file"])
            if not input_path.exists():
                errors.append(f"Input file not found: {params['input_file']}")

        # Validate AI provider
        if "ai_provider" in params:
            if params["ai_provider"] not in ["gemini", "ollama", None]:
                errors.append(f"Invalid AI provider: {params['ai_provider']}")

        return errors

    def execute(self, context: ToolExecutionContext, **kwargs) -> ToolResult:
        """Execute the security analysis."""
        try:
            # Extract parameters
            project_id = kwargs.get("project_id")
            location = kwargs.get("location", "asia-northeast1")
            use_mock = kwargs.get("use_mock", False)
            input_file = kwargs.get("input_file", "data/collected.json")
            output_dir = kwargs.get("output_dir", "data")
            ai_provider = kwargs.get("ai_provider")
            ollama_model = kwargs.get("ollama_model")
            ollama_endpoint = kwargs.get("ollama_endpoint")
            project_path = kwargs.get("project_path")

            logger.info(f"Analyzing security risks using {ai_provider or 'default'} provider")

            # Initialize explainer
            explainer = SecurityRiskExplainer(
                project_id=project_id,
                location=location,
                use_mock=use_mock,
                input_file=input_file,
                output_dir=output_dir,
                ai_provider=ai_provider,
                ollama_model=ollama_model,
                ollama_endpoint=ollama_endpoint,
                project_path=project_path,
            )

            # Perform analysis
            findings = explainer.analyze()

            # Save findings
            output_path = explainer.save_findings(findings)

            # Calculate severity summary
            high_severity = sum(1 for f in findings if f.severity == "HIGH")
            medium_severity = sum(1 for f in findings if f.severity == "MEDIUM")
            low_severity = sum(1 for f in findings if f.severity == "LOW")

            # Prepare result data
            findings_data = [f.to_dict() for f in findings]

            return ToolResult(
                success=True,
                data={
                    "findings": findings_data,
                    "total": len(findings),
                    "high": high_severity,
                    "medium": medium_severity,
                    "low": low_severity,
                    "output_file": str(output_path),
                },
                metadata={
                    "ai_provider": ai_provider or "gemini",
                    "use_mock": use_mock,
                    "input_file": input_file,
                    "project_context": bool(project_path),
                },
            )

        except FileNotFoundError as e:
            logger.error(f"Input file not found: {e}")
            return ToolResult(
                success=False,
                error=f"Input file not found: {e}. Run security_collector tool first.",
            )
        except Exception as e:
            logger.error(f"Security analysis failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"exception_type": type(e).__name__},
            )

    def can_execute(self, context: ToolExecutionContext) -> bool:
        """Check if the tool can execute."""
        # Tool can always execute, but may use mock mode if dependencies are missing
        return True