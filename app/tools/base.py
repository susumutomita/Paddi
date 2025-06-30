"""Base interface for all tools in the Paddi system."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class ToolCategory(Enum):
    """Tool categories."""

    SECURITY_AUDIT = "security_audit"
    SYSTEM_MANAGEMENT = "system_management"
    DATA_PROCESSING = "data_processing"
    EXTERNAL_API = "external_api"
    FILE_OPERATION = "file_operation"
    MONITORING = "monitoring"
    REMEDIATION = "remediation"
    CUSTOM = "custom"


class ToolPriority(Enum):
    """Tool execution priority."""

    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    OPTIONAL = 5


@dataclass
class ToolMetadata:
    """Metadata for tool discovery and selection."""

    name: str
    description: str
    category: ToolCategory
    priority: ToolPriority = ToolPriority.MEDIUM
    version: str = "1.0.0"
    author: str = "Paddi System"
    tags: List[str] = None
    dependencies: List[str] = None
    parameters: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.tags is None:
            self.tags = []
        if self.dependencies is None:
            self.dependencies = []
        if self.parameters is None:
            self.parameters = {}


@dataclass
class ToolParameter:
    """Tool parameter definition."""

    name: str
    type: type
    description: str
    required: bool = True
    default: Any = None
    choices: List[Any] = None


class ToolExecutionContext:
    """Context for tool execution."""

    def __init__(
        self,
        user_intent: str = None,
        environment: Dict[str, Any] = None,
        config: Dict[str, Any] = None,
        dry_run: bool = False,
    ):
        """Initialize execution context."""
        self.user_intent = user_intent
        self.environment = environment or {}
        self.config = config or {}
        self.dry_run = dry_run
        self.execution_history: List[Dict[str, Any]] = []

    def add_execution_record(self, tool_name: str, result: Any, error: Optional[Exception] = None):
        """Add execution record to history."""
        self.execution_history.append({
            "tool_name": tool_name,
            "result": result,
            "error": str(error) if error else None,
            "timestamp": self._get_timestamp(),
        })

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()


@dataclass
class ToolResult:
    """Result from tool execution."""

    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.metadata is None:
            self.metadata = {}


class BaseTool(ABC):
    """Base class for all tools."""

    def __init__(self):
        """Initialize the tool."""
        self._metadata = self._get_metadata()

    @abstractmethod
    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata.

        Returns:
            ToolMetadata: Tool metadata including name, description, etc.
        """
        pass

    @abstractmethod
    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        """Validate input parameters.

        Args:
            params: Input parameters

        Returns:
            List[str]: List of validation errors (empty if valid)
        """
        pass

    @abstractmethod
    def execute(self, context: ToolExecutionContext, **kwargs) -> ToolResult:
        """Execute the tool.

        Args:
            context: Execution context
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult: Execution result
        """
        pass

    @property
    def metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return self._metadata

    @property
    def name(self) -> str:
        """Get tool name."""
        return self._metadata.name

    @property
    def description(self) -> str:
        """Get tool description."""
        return self._metadata.description

    @property
    def category(self) -> ToolCategory:
        """Get tool category."""
        return self._metadata.category

    def can_execute(self, context: ToolExecutionContext) -> bool:
        """Check if the tool can execute in the given context.

        Args:
            context: Execution context

        Returns:
            bool: True if tool can execute
        """
        return True

    def pre_execute(self, context: ToolExecutionContext, **kwargs) -> None:
        """Pre-execution hook.

        Args:
            context: Execution context
            **kwargs: Tool-specific parameters
        """
        pass

    def post_execute(self, context: ToolExecutionContext, result: ToolResult) -> None:
        """Post-execution hook.

        Args:
            context: Execution context
            result: Execution result
        """
        context.add_execution_record(self.name, result.data, None)

    def run(self, context: ToolExecutionContext, **kwargs) -> ToolResult:
        """Run the tool with full lifecycle.

        Args:
            context: Execution context
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult: Execution result
        """
        try:
            # Validate parameters
            errors = self.validate_parameters(kwargs)
            if errors:
                return ToolResult(
                    success=False,
                    error=f"Parameter validation failed: {', '.join(errors)}"
                )

            # Check if can execute
            if not self.can_execute(context):
                return ToolResult(
                    success=False,
                    error="Tool cannot execute in the current context"
                )

            # Pre-execution
            self.pre_execute(context, **kwargs)

            # Execute
            if context.dry_run:
                result = ToolResult(
                    success=True,
                    data={"dry_run": True, "would_execute": self.name},
                    metadata={"dry_run": True}
                )
            else:
                result = self.execute(context, **kwargs)

            # Post-execution
            self.post_execute(context, result)

            return result

        except Exception as e:
            error_result = ToolResult(
                success=False,
                error=str(e),
                metadata={"exception_type": type(e).__name__}
            )
            context.add_execution_record(self.name, None, e)
            return error_result


class CompositeTool(BaseTool):
    """Base class for tools that compose multiple sub-tools."""

    def __init__(self, tools: List[BaseTool] = None):
        """Initialize composite tool."""
        super().__init__()
        self._tools = tools or []

    def add_tool(self, tool: BaseTool) -> None:
        """Add a sub-tool."""
        self._tools.append(tool)

    def remove_tool(self, tool_name: str) -> None:
        """Remove a sub-tool by name."""
        self._tools = [t for t in self._tools if t.name != tool_name]

    @property
    def tools(self) -> List[BaseTool]:
        """Get list of sub-tools."""
        return self._tools