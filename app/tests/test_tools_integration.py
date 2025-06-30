"""Tests for tool integration."""

import pytest
from app.tools.integration import ToolIntegration
from app.tools.base import BaseTool, ToolCategory, ToolExecutionContext, ToolMetadata, ToolResult


class MockIntegrationTool(BaseTool):
    """Mock tool for integration testing."""

    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="mock_integration_tool",
            description="Mock tool for integration testing",
            category=ToolCategory.CUSTOM,
            tags=["test", "integration", "mock"],
            parameters={
                "param1": {
                    "type": "string",
                    "description": "First parameter",
                    "required": True,
                },
                "param2": {
                    "type": "integer",
                    "description": "Second parameter",
                    "required": False,
                    "default": 10,
                },
            },
        )

    def validate_parameters(self, params: dict) -> list[str]:
        errors = []
        if "param1" not in params:
            errors.append("Missing required parameter: param1")
        return errors

    def execute(self, context: ToolExecutionContext, **kwargs) -> ToolResult:
        return ToolResult(
            success=True,
            data={
                "param1": kwargs.get("param1"),
                "param2": kwargs.get("param2", 10),
                "context_intent": context.user_intent,
            },
        )


class TestToolIntegration:
    """Test ToolIntegration functionality."""

    @pytest.fixture
    def integration(self):
        """Create tool integration instance."""
        integration = ToolIntegration()
        # Clear any existing tools
        integration._registry.clear()
        # Register test tool
        integration._registry.register(MockIntegrationTool)
        return integration

    def test_list_available_tools(self, integration):
        """Test listing available tools."""
        tools = integration.list_available_tools()

        assert len(tools) >= 1  # At least our mock tool
        mock_tool = next((t for t in tools if t["name"] == "mock_integration_tool"), None)
        assert mock_tool is not None
        assert mock_tool["description"] == "Mock tool for integration testing"
        assert mock_tool["category"] == "custom"
        assert "test" in mock_tool["tags"]

    def test_search_tools(self, integration):
        """Test searching tools."""
        # Search by name
        results = integration.search_tools("mock")
        assert len(results) >= 1
        assert any(t["name"] == "mock_integration_tool" for t in results)

        # Search by tag
        results = integration.search_tools("integration")
        assert len(results) >= 1
        assert any(t["name"] == "mock_integration_tool" for t in results)

        # Search with no results
        results = integration.search_tools("nonexistent_xyz")
        assert "mock_integration_tool" not in [t["name"] for t in results]

    def test_execute_tool_success(self, integration):
        """Test successful tool execution."""
        result = integration.execute_tool(
            tool_name="mock_integration_tool",
            user_intent="Test execution",
            param1="test_value",
            param2=42,
        )

        assert result["success"] is True
        assert result["data"]["param1"] == "test_value"
        assert result["data"]["param2"] == 42
        assert result["data"]["context_intent"] == "Test execution"
        assert len(result["execution_history"]) == 1

    def test_execute_tool_missing_params(self, integration):
        """Test tool execution with missing parameters."""
        result = integration.execute_tool(
            tool_name="mock_integration_tool",
            # Missing required param1
            param2=42,
        )

        assert result["success"] is False
        assert "Parameter validation failed" in result["error"]
        assert "Missing required parameter: param1" in result["error"]

    def test_execute_tool_not_found(self, integration):
        """Test executing non-existent tool."""
        result = integration.execute_tool(
            tool_name="nonexistent_tool",
            param1="test",
        )

        assert result["success"] is False
        assert "Tool 'nonexistent_tool' not found" in result["error"]

    def test_execute_tool_dry_run(self, integration):
        """Test dry-run execution."""
        result = integration.execute_tool(
            tool_name="mock_integration_tool",
            dry_run=True,
            param1="test_value",
        )

        assert result["success"] is True
        assert result["data"]["dry_run"] is True
        assert result["data"]["would_execute"] == "mock_integration_tool"
        assert result["metadata"]["dry_run"] is True

    def test_execute_tool_by_intent(self, integration):
        """Test executing tool by intent."""
        # Should match by name in intent
        result = integration.execute_tool_by_intent(
            user_intent="I need to use the mock_integration_tool",
            param1="test_value",
        )

        assert result["success"] is True
        assert result["tool_used"] == "mock_integration_tool"
        assert result["data"]["param1"] == "test_value"

    def test_execute_tool_by_intent_no_match(self, integration):
        """Test executing tool by intent with no match."""
        result = integration.execute_tool_by_intent(
            user_intent="Do something completely unrelated",
            param1="test",
        )

        assert result["success"] is False
        assert "No suitable tool found" in result["error"]

    def test_discover_and_register_tools(self, integration):
        """Test tool discovery process."""
        # This test verifies the discovery doesn't crash
        # In a real test, we'd create actual tool files in test directories
        discovered = integration.discover_and_register_tools()
        assert isinstance(discovered, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])