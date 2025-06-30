"""Tests for base tool interface."""

import pytest
from app.tools.base import (
    BaseTool,
    CompositeTool,
    ToolCategory,
    ToolExecutionContext,
    ToolMetadata,
    ToolParameter,
    ToolPriority,
    ToolResult,
)


class MockTool(BaseTool):
    """Mock tool for testing."""

    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="mock_tool",
            description="A mock tool for testing",
            category=ToolCategory.CUSTOM,
            priority=ToolPriority.MEDIUM,
            tags=["test", "mock"],
            parameters={
                "input": {
                    "type": "string",
                    "description": "Input parameter",
                    "required": True,
                },
                "optional": {
                    "type": "integer",
                    "description": "Optional parameter",
                    "required": False,
                    "default": 42,
                },
            },
        )

    def validate_parameters(self, params: dict) -> list[str]:
        """Validate parameters."""
        errors = []
        if "input" not in params:
            errors.append("Missing required parameter: input")
        if "optional" in params and not isinstance(params["optional"], int):
            errors.append("Parameter 'optional' must be an integer")
        return errors

    def execute(self, context: ToolExecutionContext, **kwargs) -> ToolResult:
        """Execute the tool."""
        input_value = kwargs.get("input", "")
        optional_value = kwargs.get("optional", 42)

        return ToolResult(
            success=True,
            data={
                "input": input_value,
                "optional": optional_value,
                "processed": f"Processed: {input_value}",
            },
            metadata={"tool": "mock", "version": "1.0.0"},
        )


class FailingTool(BaseTool):
    """Tool that always fails for testing."""

    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="failing_tool",
            description="A tool that always fails",
            category=ToolCategory.CUSTOM,
        )

    def validate_parameters(self, params: dict) -> list[str]:
        """Validate parameters."""
        return []

    def execute(self, context: ToolExecutionContext, **kwargs) -> ToolResult:
        """Execute the tool."""
        raise RuntimeError("This tool always fails")


class TestToolMetadata:
    """Test ToolMetadata dataclass."""

    def test_metadata_creation(self):
        """Test creating tool metadata."""
        metadata = ToolMetadata(
            name="test_tool",
            description="Test tool description",
            category=ToolCategory.SECURITY_AUDIT,
            priority=ToolPriority.HIGH,
        )

        assert metadata.name == "test_tool"
        assert metadata.description == "Test tool description"
        assert metadata.category == ToolCategory.SECURITY_AUDIT
        assert metadata.priority == ToolPriority.HIGH
        assert metadata.version == "1.0.0"
        assert metadata.author == "Paddi System"
        assert metadata.tags == []
        assert metadata.dependencies == []
        assert metadata.parameters == {}


class TestToolExecutionContext:
    """Test ToolExecutionContext class."""

    def test_context_creation(self):
        """Test creating execution context."""
        context = ToolExecutionContext(
            user_intent="test intent",
            environment={"key": "value"},
            config={"setting": True},
            dry_run=True,
        )

        assert context.user_intent == "test intent"
        assert context.environment == {"key": "value"}
        assert context.config == {"setting": True}
        assert context.dry_run is True
        assert context.execution_history == []

    def test_add_execution_record(self):
        """Test adding execution records."""
        context = ToolExecutionContext()
        context.add_execution_record("test_tool", {"result": "success"}, None)

        assert len(context.execution_history) == 1
        record = context.execution_history[0]
        assert record["tool_name"] == "test_tool"
        assert record["result"] == {"result": "success"}
        assert record["error"] is None
        assert "timestamp" in record


class TestBaseTool:
    """Test BaseTool functionality."""

    def test_tool_properties(self):
        """Test tool properties."""
        tool = MockTool()

        assert tool.name == "mock_tool"
        assert tool.description == "A mock tool for testing"
        assert tool.category == ToolCategory.CUSTOM
        assert tool.metadata.priority == ToolPriority.MEDIUM

    def test_successful_execution(self):
        """Test successful tool execution."""
        tool = MockTool()
        context = ToolExecutionContext()

        result = tool.run(context, input="test input", optional=100)

        assert result.success is True
        assert result.data["input"] == "test input"
        assert result.data["optional"] == 100
        assert result.data["processed"] == "Processed: test input"
        assert result.error is None

        # Check execution history
        assert len(context.execution_history) == 1
        assert context.execution_history[0]["tool_name"] == "mock_tool"

    def test_parameter_validation_failure(self):
        """Test parameter validation failure."""
        tool = MockTool()
        context = ToolExecutionContext()

        # Missing required parameter
        result = tool.run(context)

        assert result.success is False
        assert "Parameter validation failed" in result.error
        assert "Missing required parameter: input" in result.error

    def test_dry_run_execution(self):
        """Test dry-run execution."""
        tool = MockTool()
        context = ToolExecutionContext(dry_run=True)

        result = tool.run(context, input="test")

        assert result.success is True
        assert result.data["dry_run"] is True
        assert result.data["would_execute"] == "mock_tool"
        assert result.metadata["dry_run"] is True

    def test_execution_failure(self):
        """Test execution failure."""
        tool = FailingTool()
        context = ToolExecutionContext()

        result = tool.run(context)

        assert result.success is False
        assert "This tool always fails" in result.error
        assert result.metadata["exception_type"] == "RuntimeError"

        # Check execution history
        assert len(context.execution_history) == 1
        assert context.execution_history[0]["error"] == "This tool always fails"


class TestCompositeTool:
    """Test CompositeTool functionality."""

    def test_composite_tool_creation(self):
        """Test creating composite tool."""
        tool1 = MockTool()
        tool2 = FailingTool()

        composite = CompositeTool([tool1, tool2])

        assert len(composite.tools) == 2
        assert composite.tools[0] == tool1
        assert composite.tools[1] == tool2

    def test_add_remove_tools(self):
        """Test adding and removing tools."""
        composite = CompositeTool()
        tool = MockTool()

        # Add tool
        composite.add_tool(tool)
        assert len(composite.tools) == 1

        # Remove tool
        composite.remove_tool("mock_tool")
        assert len(composite.tools) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])