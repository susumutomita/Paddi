"""Tool-related commands for Paddi CLI."""

import json
import logging
from typing import Optional

from app.cli.base import Command, CommandContext
from app.tools.integration import tool_integration


logger = logging.getLogger(__name__)


class ToolsCommand(Command):
    """Base command for tool operations."""

    @property
    def name(self) -> str:
        """Get command name."""
        return "tools"

    @property
    def description(self) -> str:
        """Get command description."""
        return "Manage and execute dynamic tools"


class ListToolsCommand(Command):
    """List available tools."""

    @property
    def name(self) -> str:
        """Get command name."""
        return "list-tools"

    @property
    def description(self) -> str:
        """Get command description."""
        return "List all available tools"

    def execute(self, context: CommandContext) -> None:
        """Execute command."""
        # Discover tools
        tool_integration.discover_and_register_tools()
        
        # List tools
        tools = tool_integration.list_available_tools()
        
        if not tools:
            print("No tools found. Make sure tools are in the correct directories.")
            return
        
        print(f"\n🔧 Available Tools ({len(tools)} found):")
        print("=" * 80)
        
        # Group by category
        by_category = {}
        for tool in tools:
            category = tool["category"]
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(tool)
        
        # Display by category
        for category, category_tools in sorted(by_category.items()):
            print(f"\n📂 {category.upper()}")
            print("-" * 40)
            for tool in sorted(category_tools, key=lambda x: x["name"]):
                print(f"  • {tool['name']:<20} - {tool['description']}")
                if tool.get("tags"):
                    print(f"    Tags: {', '.join(tool['tags'])}")


class SearchToolsCommand(Command):
    """Search for tools."""

    @property
    def name(self) -> str:
        """Get command name."""
        return "search-tools"

    @property
    def description(self) -> str:
        """Get command description."""
        return "Search for tools by query"

    def execute(self, context: CommandContext) -> None:
        """Execute command."""
        query = context.get("query", "")
        
        if not query:
            print("Please provide a search query with --query")
            return
        
        # Discover tools
        tool_integration.discover_and_register_tools()
        
        # Search tools
        tools = tool_integration.search_tools(query)
        
        if not tools:
            print(f"No tools found matching '{query}'")
            return
        
        print(f"\n🔍 Tools matching '{query}' ({len(tools)} found):")
        print("=" * 60)
        
        for tool in tools:
            print(f"\n• {tool['name']}")
            print(f"  Description: {tool['description']}")
            print(f"  Category: {tool['category']}")
            if tool.get("tags"):
                print(f"  Tags: {', '.join(tool['tags'])}")


class ExecuteToolCommand(Command):
    """Execute a specific tool."""

    @property
    def name(self) -> str:
        """Get command name."""
        return "execute-tool"

    @property
    def description(self) -> str:
        """Get command description."""
        return "Execute a specific tool by name"

    def execute(self, context: CommandContext) -> None:
        """Execute command."""
        tool_name = context.get("tool_name")
        
        if not tool_name:
            print("Please provide a tool name with --tool-name")
            return
        
        # Discover tools
        tool_integration.discover_and_register_tools()
        
        # Get tool parameters from context
        params = {}
        for key, value in context.items():
            if key not in ["tool_name", "dry_run", "verbose", "output_format"]:
                params[key] = value
        
        # Execute tool
        result = tool_integration.execute_tool(
            tool_name=tool_name,
            dry_run=context.get("dry_run", False),
            **params
        )
        
        # Display result
        if result["success"]:
            print(f"\n✅ Tool '{tool_name}' executed successfully")
            
            # Format output based on preference
            output_format = context.get("output_format", "json")
            if output_format == "json":
                print("\nResult:")
                print(json.dumps(result["data"], indent=2))
            else:
                print("\nResult:")
                print(result["data"])
                
            if result.get("metadata"):
                print("\nMetadata:")
                print(json.dumps(result["metadata"], indent=2))
        else:
            print(f"\n❌ Tool execution failed: {result['error']}")


class ExecuteByIntentCommand(Command):
    """Execute tool based on user intent."""

    @property
    def name(self) -> str:
        """Get command name."""
        return "tool-intent"

    @property
    def description(self) -> str:
        """Get command description."""
        return "Execute the best matching tool based on user intent"

    def execute(self, context: CommandContext) -> None:
        """Execute command."""
        intent = context.get("intent")
        
        if not intent:
            print("Please provide an intent with --intent")
            return
        
        # Discover tools
        tool_integration.discover_and_register_tools()
        
        # Get parameters from context
        params = {}
        for key, value in context.items():
            if key not in ["intent", "dry_run", "verbose"]:
                params[key] = value
        
        # Execute by intent
        result = tool_integration.execute_tool_by_intent(
            user_intent=intent,
            dry_run=context.get("dry_run", False),
            **params
        )
        
        # Display result
        if result["success"]:
            print(f"\n✅ Selected tool: {result['tool_used']}")
            print("Execution successful")
            
            if result.get("data"):
                print("\nResult:")
                print(json.dumps(result["data"], indent=2))
                
            if result.get("metadata"):
                print("\nMetadata:")
                print(json.dumps(result["metadata"], indent=2))
        else:
            print(f"\n❌ Execution failed: {result['error']}")

