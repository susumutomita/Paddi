"""Security collector tool that wraps the existing collector agent."""

import json
import logging
from typing import Any, Dict, List

from app.collector.agent_collector import CollectorAgent
from app.tools.base import (
    BaseTool,
    ToolCategory,
    ToolExecutionContext,
    ToolMetadata,
    ToolPriority,
    ToolResult,
)


logger = logging.getLogger(__name__)


class SecurityCollectorTool(BaseTool):
    """Tool for collecting security data from cloud providers."""

    def __init__(self):
        """Initialize the security collector tool."""
        super().__init__()
        self._collector = CollectorAgent()

    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="security_collector",
            description="Collects security configuration and findings from cloud providers",
            category=ToolCategory.SECURITY_AUDIT,
            priority=ToolPriority.HIGH,
            tags=["security", "audit", "cloud", "compliance", "collector"],
            parameters={
                "provider": {
                    "type": "string",
                    "description": "Cloud provider (gcp, aws, azure, github)",
                    "required": False,
                    "default": "all",
                },
                "output_file": {
                    "type": "string",
                    "description": "Output file path",
                    "required": False,
                    "default": "data/collected.json",
                },
                "use_mock": {
                    "type": "boolean",
                    "description": "Use mock data instead of real API calls",
                    "required": False,
                    "default": False,
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
                errors.append(f"Invalid provider: {params['provider']}. Must be one of {valid_providers}")

        return errors

    def execute(self, context: ToolExecutionContext, **kwargs) -> ToolResult:
        """Execute the security collection."""
        try:
            # Extract parameters
            provider = kwargs.get("provider", "all")
            output_file = kwargs.get("output_file", "data/collected.json")
            use_mock = kwargs.get("use_mock", False)

            logger.info(f"Collecting security data for provider: {provider}")

            # Run the collector
            if provider == "all":
                # Collect from all providers
                all_data = {}
                for p in ["gcp", "aws", "azure", "github"]:
                    try:
                        if use_mock:
                            data = self._collector.collect_mock_data(p)
                        else:
                            data = self._collector.collect(p)
                        all_data[p] = data
                    except Exception as e:
                        logger.error(f"Failed to collect from {p}: {e}")
                        all_data[p] = {"error": str(e)}
                
                result_data = all_data
            else:
                # Collect from specific provider
                if use_mock:
                    result_data = self._collector.collect_mock_data(provider)
                else:
                    result_data = self._collector.collect(provider)

            # Save to file
            self._collector.save_to_file(result_data, output_file)

            return ToolResult(
                success=True,
                data=result_data,
                metadata={
                    "provider": provider,
                    "output_file": output_file,
                    "use_mock": use_mock,
                    "items_collected": self._count_items(result_data),
                },
            )

        except Exception as e:
            logger.error(f"Security collection failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"exception_type": type(e).__name__},
            )

    def _count_items(self, data: Any) -> int:
        """Count the number of items collected."""
        if isinstance(data, dict):
            count = 0
            for value in data.values():
                if isinstance(value, list):
                    count += len(value)
                elif isinstance(value, dict):
                    count += self._count_items(value)
                else:
                    count += 1
            return count
        elif isinstance(data, list):
            return len(data)
        else:
            return 1