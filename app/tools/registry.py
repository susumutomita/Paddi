"""Dynamic tool registry for discovering and managing tools."""

import importlib
import inspect
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type, Union

from app.tools.base import BaseTool, ToolCategory, ToolExecutionContext, ToolMetadata, ToolResult


logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing and discovering tools."""

    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, Type[BaseTool]] = {}
        self._instances: Dict[str, BaseTool] = {}

    def register(self, tool_class: Type[BaseTool], name: Optional[str] = None) -> None:
        """Register a tool class.

        Args:
            tool_class: Tool class to register
            name: Optional custom name (defaults to class metadata name)
        """
        if not issubclass(tool_class, BaseTool):
            raise ValueError(f"{tool_class} must be a subclass of BaseTool")

        # Create temporary instance to get metadata
        temp_instance = tool_class()
        tool_name = name or temp_instance.metadata.name

        if tool_name in self._tools:
            logger.warning(f"Tool '{tool_name}' is already registered. Overwriting.")

        self._tools[tool_name] = tool_class
        logger.info(f"Registered tool: {tool_name}")

    def unregister(self, name: str) -> None:
        """Unregister a tool.

        Args:
            name: Tool name to unregister
        """
        if name in self._tools:
            del self._tools[name]
            if name in self._instances:
                del self._instances[name]
            logger.info(f"Unregistered tool: {name}")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool instance by name.

        Args:
            name: Tool name

        Returns:
            BaseTool: Tool instance or None if not found
        """
        if name not in self._tools:
            return None

        if name not in self._instances:
            self._instances[name] = self._tools[name]()

        return self._instances[name]

    def list_tools(self, category: Optional[ToolCategory] = None) -> List[ToolMetadata]:
        """List all registered tools.

        Args:
            category: Optional category filter

        Returns:
            List[ToolMetadata]: List of tool metadata
        """
        tools = []
        for name, tool_class in self._tools.items():
            instance = self.get_tool(name)
            if instance:
                if category is None or instance.category == category:
                    tools.append(instance.metadata)
        return tools

    def search_tools(self, query: str) -> List[ToolMetadata]:
        """Search tools by name, description, or tags.

        Args:
            query: Search query

        Returns:
            List[ToolMetadata]: Matching tools
        """
        query_lower = query.lower()
        matching_tools = []

        for name, tool_class in self._tools.items():
            instance = self.get_tool(name)
            if instance:
                metadata = instance.metadata
                # Search in name, description, and tags
                if (
                    query_lower in metadata.name.lower()
                    or query_lower in metadata.description.lower()
                    or any(query_lower in tag.lower() for tag in metadata.tags)
                ):
                    matching_tools.append(metadata)

        return matching_tools

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        self._instances.clear()


class DynamicToolRegistry(ToolRegistry):
    """Dynamic tool registry with automatic discovery."""

    def __init__(self, tool_paths: Optional[List[Union[str, Path]]] = None):
        """Initialize dynamic tool registry.

        Args:
            tool_paths: List of paths to search for tools
        """
        super().__init__()
        self._tool_paths = [Path(p) for p in (tool_paths or [])]
        self._discovered_modules: List[str] = []

    def add_tool_path(self, path: Union[str, Path]) -> None:
        """Add a path to search for tools.

        Args:
            path: Path to add
        """
        path = Path(path)
        if path not in self._tool_paths:
            self._tool_paths.append(path)

    def discover_tools(self) -> List[ToolMetadata]:
        """Discover tools from configured paths.

        Returns:
            List[ToolMetadata]: List of discovered tool metadata
        """
        discovered_tools = []

        # Add tool paths to Python path
        for path in self._tool_paths:
            if path.exists() and str(path) not in sys.path:
                sys.path.insert(0, str(path))

        # Discover from tool paths
        for tool_path in self._tool_paths:
            if tool_path.exists() and tool_path.is_dir():
                discovered_tools.extend(self._discover_tools_in_directory(tool_path))

        # Discover from Python modules
        discovered_tools.extend(self._discover_tools_from_modules())

        # Discover from system commands
        discovered_tools.extend(self._discover_system_commands())

        return discovered_tools

    def _discover_tools_in_directory(self, directory: Path) -> List[ToolMetadata]:
        """Discover tools in a directory.

        Args:
            directory: Directory to search

        Returns:
            List[ToolMetadata]: Discovered tools
        """
        discovered = []

        for py_file in directory.rglob("*.py"):
            if py_file.name.startswith("_"):
                continue

            try:
                # Create module name from file path
                relative_path = py_file.relative_to(directory.parent)
                module_name = str(relative_path).replace(os.sep, ".").replace(".py", "")

                if module_name in self._discovered_modules:
                    continue

                # Import module
                module = importlib.import_module(module_name)
                self._discovered_modules.append(module_name)

                # Find tool classes
                for name, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, BaseTool)
                        and obj != BaseTool
                        and not inspect.isabstract(obj)
                    ):
                        try:
                            self.register(obj)
                            instance = self.get_tool(obj().metadata.name)
                            if instance:
                                discovered.append(instance.metadata)
                        except Exception as e:
                            logger.error(f"Failed to register tool {name}: {e}")

            except Exception as e:
                logger.error(f"Failed to import {py_file}: {e}")

        return discovered

    def _discover_tools_from_modules(self) -> List[ToolMetadata]:
        """Discover tools from already loaded modules.

        Returns:
            List[ToolMetadata]: Discovered tools
        """
        discovered = []

        for module_name, module in sys.modules.items():
            if module_name.startswith("app.tools.") and module:
                for name, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, BaseTool)
                        and obj != BaseTool
                        and not inspect.isabstract(obj)
                    ):
                        try:
                            # Check if already registered
                            temp_instance = obj()
                            if temp_instance.metadata.name not in self._tools:
                                self.register(obj)
                                discovered.append(temp_instance.metadata)
                        except Exception as e:
                            logger.debug(f"Skipping tool {name}: {e}")

        return discovered

    def _discover_system_commands(self) -> List[ToolMetadata]:
        """Discover system commands as tools.

        Returns:
            List[ToolMetadata]: Discovered system command tools
        """
        # This is a placeholder for system command discovery
        # In a real implementation, this would scan PATH for executables
        # and create wrapper tools for them
        return []

    def select_best_tool(
        self, user_intent: str, context: ToolExecutionContext
    ) -> Optional[BaseTool]:
        """Select the best tool for a given user intent.

        Args:
            user_intent: User's intent or task description
            context: Execution context

        Returns:
            BaseTool: Best matching tool or None
        """
        # Simple implementation - can be enhanced with AI/ML
        intent_lower = user_intent.lower()

        # First, try exact name match
        for name, tool_class in self._tools.items():
            if name.lower() in intent_lower:
                tool = self.get_tool(name)
                if tool and tool.can_execute(context):
                    return tool

        # Then, search by description and tags
        matching_tools = self.search_tools(user_intent)
        for metadata in matching_tools:
            tool = self.get_tool(metadata.name)
            if tool and tool.can_execute(context):
                return tool

        # Finally, try category-based selection
        category_keywords = {
            ToolCategory.SECURITY_AUDIT: ["security", "audit", "compliance", "vulnerability"],
            ToolCategory.SYSTEM_MANAGEMENT: ["system", "manage", "configure", "setup"],
            ToolCategory.DATA_PROCESSING: ["data", "process", "analyze", "transform"],
            ToolCategory.EXTERNAL_API: ["api", "external", "integration", "webhook"],
            ToolCategory.FILE_OPERATION: ["file", "read", "write", "copy", "move"],
            ToolCategory.MONITORING: ["monitor", "watch", "observe", "track"],
            ToolCategory.REMEDIATION: ["fix", "remediate", "repair", "resolve"],
        }

        for category, keywords in category_keywords.items():
            if any(keyword in intent_lower for keyword in keywords):
                category_tools = self.list_tools(category)
                if category_tools:
                    tool = self.get_tool(category_tools[0].name)
                    if tool and tool.can_execute(context):
                        return tool

        return None

    def execute_tool_chain(
        self, tool_names: List[str], context: ToolExecutionContext, **kwargs
    ) -> List[ToolResult]:
        """Execute a chain of tools in sequence.

        Args:
            tool_names: List of tool names to execute
            context: Execution context
            **kwargs: Parameters for all tools

        Returns:
            List[ToolResult]: Results from each tool
        """
        results = []

        for tool_name in tool_names:
            tool = self.get_tool(tool_name)
            if not tool:
                results.append(
                    ToolResult(
                        success=False,
                        error=f"Tool '{tool_name}' not found"
                    )
                )
                continue

            result = tool.run(context, **kwargs)
            results.append(result)

            # Stop chain if tool fails
            if not result.success:
                break

        return results