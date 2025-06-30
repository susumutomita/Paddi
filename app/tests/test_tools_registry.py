"""Tests for tool registry."""

import pytest
from pathlib import Path
from app.tools.base import BaseTool, ToolCategory, ToolExecutionContext, ToolMetadata, ToolResult
from app.tools.registry import DynamicToolRegistry, ToolRegistry


class TestToolA(BaseTool):
    """Test tool A."""

    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="test_tool_a",
            description="Test tool A for testing",
            category=ToolCategory.CUSTOM,
            tags=["test", "sample"],
        )

    def validate_parameters(self, params: dict) -> list[str]:
        return []

    def execute(self, context: ToolExecutionContext, **kwargs) -> ToolResult:
        return ToolResult(success=True, data={"tool": "A"})


class TestToolB(BaseTool):
    """Test tool B."""

    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="test_tool_b",
            description="Another test tool for testing",
            category=ToolCategory.SYSTEM_MANAGEMENT,
            tags=["test", "system"],
        )

    def validate_parameters(self, params: dict) -> list[str]:
        return []

    def execute(self, context: ToolExecutionContext, **kwargs) -> ToolResult:
        return ToolResult(success=True, data={"tool": "B"})


class TestToolRegistry:
    """Test ToolRegistry functionality."""

    def test_register_tool(self):
        """Test registering tools."""
        registry = ToolRegistry()
        registry.register(TestToolA)

        assert "test_tool_a" in registry._tools
        assert registry._tools["test_tool_a"] == TestToolA

    def test_register_invalid_tool(self):
        """Test registering invalid tool."""
        registry = ToolRegistry()

        class NotATool:
            pass

        with pytest.raises(ValueError, match="must be a subclass of BaseTool"):
            registry.register(NotATool)

    def test_unregister_tool(self):
        """Test unregistering tools."""
        registry = ToolRegistry()
        registry.register(TestToolA)
        registry.unregister("test_tool_a")

        assert "test_tool_a" not in registry._tools

    def test_get_tool(self):
        """Test getting tool instances."""
        registry = ToolRegistry()
        registry.register(TestToolA)

        tool = registry.get_tool("test_tool_a")
        assert tool is not None
        assert isinstance(tool, TestToolA)
        assert tool.name == "test_tool_a"

        # Test singleton behavior
        tool2 = registry.get_tool("test_tool_a")
        assert tool is tool2

    def test_get_nonexistent_tool(self):
        """Test getting non-existent tool."""
        registry = ToolRegistry()
        tool = registry.get_tool("nonexistent")
        assert tool is None

    def test_list_tools(self):
        """Test listing tools."""
        registry = ToolRegistry()
        registry.register(TestToolA)
        registry.register(TestToolB)

        tools = registry.list_tools()
        assert len(tools) == 2

        tool_names = [t.name for t in tools]
        assert "test_tool_a" in tool_names
        assert "test_tool_b" in tool_names

    def test_list_tools_by_category(self):
        """Test listing tools by category."""
        registry = ToolRegistry()
        registry.register(TestToolA)
        registry.register(TestToolB)

        custom_tools = registry.list_tools(ToolCategory.CUSTOM)
        assert len(custom_tools) == 1
        assert custom_tools[0].name == "test_tool_a"

        system_tools = registry.list_tools(ToolCategory.SYSTEM_MANAGEMENT)
        assert len(system_tools) == 1
        assert system_tools[0].name == "test_tool_b"

    def test_search_tools(self):
        """Test searching tools."""
        registry = ToolRegistry()
        registry.register(TestToolA)
        registry.register(TestToolB)

        # Search by name
        results = registry.search_tools("tool_a")
        assert len(results) == 1
        assert results[0].name == "test_tool_a"

        # Search by description
        results = registry.search_tools("Another")
        assert len(results) == 1
        assert results[0].name == "test_tool_b"

        # Search by tags
        results = registry.search_tools("system")
        assert len(results) == 1
        assert results[0].name == "test_tool_b"

        # Search with no results
        results = registry.search_tools("nonexistent")
        assert len(results) == 0

    def test_clear_registry(self):
        """Test clearing registry."""
        registry = ToolRegistry()
        registry.register(TestToolA)
        registry.register(TestToolB)

        registry.clear()
        assert len(registry._tools) == 0
        assert len(registry._instances) == 0


class TestDynamicToolRegistry:
    """Test DynamicToolRegistry functionality."""

    def test_add_tool_path(self):
        """Test adding tool paths."""
        registry = DynamicToolRegistry()
        path = Path("/test/path")
        registry.add_tool_path(path)

        assert path in registry._tool_paths

    def test_select_best_tool_by_name(self):
        """Test selecting best tool by name match."""
        registry = DynamicToolRegistry()
        registry.register(TestToolA)
        registry.register(TestToolB)

        context = ToolExecutionContext()
        tool = registry.select_best_tool("I need test_tool_a", context)

        assert tool is not None
        assert tool.name == "test_tool_a"

    def test_select_best_tool_by_category(self):
        """Test selecting best tool by category keywords."""
        registry = DynamicToolRegistry()
        registry.register(TestToolA)
        registry.register(TestToolB)

        context = ToolExecutionContext()
        tool = registry.select_best_tool("manage system configuration", context)

        assert tool is not None
        assert tool.name == "test_tool_b"

    def test_select_best_tool_no_match(self):
        """Test selecting tool with no match."""
        registry = DynamicToolRegistry()
        context = ToolExecutionContext()
        tool = registry.select_best_tool("something unrelated", context)

        assert tool is None

    def test_execute_tool_chain(self):
        """Test executing tool chain."""
        registry = DynamicToolRegistry()
        registry.register(TestToolA)
        registry.register(TestToolB)

        context = ToolExecutionContext()
        results = registry.execute_tool_chain(
            ["test_tool_a", "test_tool_b"], context
        )

        assert len(results) == 2
        assert results[0].success is True
        assert results[0].data["tool"] == "A"
        assert results[1].success is True
        assert results[1].data["tool"] == "B"

    def test_execute_tool_chain_with_failure(self):
        """Test tool chain stops on failure."""
        registry = DynamicToolRegistry()
        registry.register(TestToolA)

        context = ToolExecutionContext()
        results = registry.execute_tool_chain(
            ["nonexistent", "test_tool_a"], context
        )

        assert len(results) == 1
        assert results[0].success is False
        assert "not found" in results[0].error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])