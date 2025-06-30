"""Tool factory for creating tool instances."""

import logging
from typing import Any, Dict, Optional, Type

from app.tools.base import BaseTool
from app.tools.registry import DynamicToolRegistry, ToolRegistry


logger = logging.getLogger(__name__)


class ToolFactory:
    """Factory for creating tool instances."""

    def __init__(self, registry: Optional[ToolRegistry] = None):
        """Initialize tool factory.

        Args:
            registry: Tool registry (creates default if not provided)
        """
        self._registry = registry or DynamicToolRegistry()

    @property
    def registry(self) -> ToolRegistry:
        """Get the tool registry."""
        return self._registry

    def create(self, tool_name: str, config: Optional[Dict[str, Any]] = None) -> Optional[BaseTool]:
        """Create a tool instance.

        Args:
            tool_name: Name of the tool to create
            config: Optional configuration for the tool

        Returns:
            BaseTool: Tool instance or None if not found
        """
        tool = self._registry.get_tool(tool_name)
        if not tool:
            logger.error(f"Tool '{tool_name}' not found in registry")
            return None

        # If tool supports configuration, apply it
        if config and hasattr(tool, "configure"):
            tool.configure(config)

        return tool

    def create_from_class(
        self, tool_class: Type[BaseTool], config: Optional[Dict[str, Any]] = None
    ) -> BaseTool:
        """Create a tool instance from a class.

        Args:
            tool_class: Tool class
            config: Optional configuration

        Returns:
            BaseTool: Tool instance
        """
        if not issubclass(tool_class, BaseTool):
            raise ValueError(f"{tool_class} must be a subclass of BaseTool")

        tool = tool_class()

        # If tool supports configuration, apply it
        if config and hasattr(tool, "configure"):
            tool.configure(config)

        return tool

    def register_and_create(
        self,
        tool_class: Type[BaseTool],
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> BaseTool:
        """Register a tool class and create an instance.

        Args:
            tool_class: Tool class to register
            name: Optional custom name
            config: Optional configuration

        Returns:
            BaseTool: Tool instance
        """
        self._registry.register(tool_class, name)
        tool_name = name or tool_class().metadata.name
        return self.create(tool_name, config)

    def discover_and_create(
        self, tool_paths: Optional[list] = None
    ) -> Dict[str, BaseTool]:
        """Discover tools and create instances.

        Args:
            tool_paths: Optional paths to search for tools

        Returns:
            Dict[str, BaseTool]: Dictionary of tool name to instance
        """
        if isinstance(self._registry, DynamicToolRegistry):
            if tool_paths:
                for path in tool_paths:
                    self._registry.add_tool_path(path)
            self._registry.discover_tools()

        tools = {}
        for metadata in self._registry.list_tools():
            tool = self.create(metadata.name)
            if tool:
                tools[metadata.name] = tool

        return tools


class SingletonToolFactory(ToolFactory):
    """Singleton tool factory that ensures only one instance per tool."""

    _instance = None
    _tools_cache: Dict[str, BaseTool] = {}

    def __new__(cls):
        """Create or return singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def create(self, tool_name: str, config: Optional[Dict[str, Any]] = None) -> Optional[BaseTool]:
        """Create or get cached tool instance.

        Args:
            tool_name: Name of the tool
            config: Optional configuration

        Returns:
            BaseTool: Tool instance or None
        """
        if tool_name in self._tools_cache:
            return self._tools_cache[tool_name]

        tool = super().create(tool_name, config)
        if tool:
            self._tools_cache[tool_name] = tool

        return tool

    def clear_cache(self) -> None:
        """Clear the tools cache."""
        self._tools_cache.clear()