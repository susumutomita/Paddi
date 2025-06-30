"""Integration module for connecting tools with the existing CLI system."""

import logging
from typing import Any, Dict, List, Optional

from app.tools.base import ToolExecutionContext
from app.tools.factory import SingletonToolFactory
from app.tools.registry import DynamicToolRegistry


logger = logging.getLogger(__name__)


class ToolIntegration:
    """Integration class for connecting tools with the CLI system."""

    def __init__(self):
        """Initialize tool integration."""
        self._factory = SingletonToolFactory()
        self._registry = self._factory.registry
        
        # Initialize with default tool paths
        if isinstance(self._registry, DynamicToolRegistry):
            self._registry.add_tool_path("app/tools/security")
            self._registry.add_tool_path("app/tools/file_ops")
            self._registry.add_tool_path("app/tools/system")
            self._registry.add_tool_path("app/tools/data")
            self._registry.add_tool_path("app/tools/api")

    def discover_and_register_tools(self) -> List[str]:
        """Discover and register all available tools.
        
        Returns:
            List[str]: Names of discovered tools
        """
        if isinstance(self._registry, DynamicToolRegistry):
            discovered = self._registry.discover_tools()
            return [tool.name for tool in discovered]
        return []

    def execute_tool(
        self, 
        tool_name: str, 
        user_intent: Optional[str] = None,
        dry_run: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute a tool by name.
        
        Args:
            tool_name: Name of the tool to execute
            user_intent: Optional user intent for context
            dry_run: Whether to run in dry-run mode
            **kwargs: Tool-specific parameters
            
        Returns:
            Dict[str, Any]: Execution result
        """
        # Create execution context
        context = ToolExecutionContext(
            user_intent=user_intent,
            dry_run=dry_run
        )
        
        # Get tool
        tool = self._factory.create(tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found"
            }
        
        # Execute tool
        result = tool.run(context, **kwargs)
        
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "metadata": result.metadata,
            "execution_history": context.execution_history
        }

    def execute_tool_by_intent(
        self, 
        user_intent: str,
        dry_run: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute the best matching tool based on user intent.
        
        Args:
            user_intent: User's intent or task description
            dry_run: Whether to run in dry-run mode
            **kwargs: Tool-specific parameters
            
        Returns:
            Dict[str, Any]: Execution result
        """
        # Create execution context
        context = ToolExecutionContext(
            user_intent=user_intent,
            dry_run=dry_run
        )
        
        # Select best tool
        if isinstance(self._registry, DynamicToolRegistry):
            tool = self._registry.select_best_tool(user_intent, context)
            if not tool:
                return {
                    "success": False,
                    "error": f"No suitable tool found for intent: {user_intent}"
                }
            
            # Execute tool
            result = tool.run(context, **kwargs)
            
            return {
                "tool_used": tool.name,
                "success": result.success,
                "data": result.data,
                "error": result.error,
                "metadata": result.metadata,
                "execution_history": context.execution_history
            }
        else:
            return {
                "success": False,
                "error": "Dynamic tool selection not available"
            }

    def list_available_tools(self) -> List[Dict[str, Any]]:
        """List all available tools.
        
        Returns:
            List[Dict[str, Any]]: Tool information
        """
        tools = []
        for metadata in self._registry.list_tools():
            tools.append({
                "name": metadata.name,
                "description": metadata.description,
                "category": metadata.category.value,
                "priority": metadata.priority.value,
                "tags": metadata.tags,
                "parameters": metadata.parameters
            })
        return tools

    def search_tools(self, query: str) -> List[Dict[str, Any]]:
        """Search for tools matching a query.
        
        Args:
            query: Search query
            
        Returns:
            List[Dict[str, Any]]: Matching tools
        """
        tools = []
        for metadata in self._registry.search_tools(query):
            tools.append({
                "name": metadata.name,
                "description": metadata.description,
                "category": metadata.category.value,
                "tags": metadata.tags
            })
        return tools


# Global instance for easy access
tool_integration = ToolIntegration()