"""Command registry for managing available commands."""

from typing import Dict, Type

from .base import Command
from .commands import (
    AuditCommand,
    CollectCommand,
    ExplainCommand,
    InitCommand,
    ReportCommand,
)


class CommandRegistry:
    """Registry for available commands."""

    def __init__(self):
        """Initialize command registry."""
        self._commands: Dict[str, Type[Command]] = {}
        self._register_default_commands()

    def _register_default_commands(self) -> None:
        """Register default commands."""
        self.register(InitCommand)
        self.register(AuditCommand)
        self.register(CollectCommand)
        self.register(ExplainCommand)
        self.register(ReportCommand)

    def register(self, command_class: Type[Command]) -> None:
        """Register a command class."""
        command = command_class()
        self._commands[command.name] = command_class

    def get_command(self, name: str) -> Type[Command]:
        """Get command class by name."""
        if name not in self._commands:
            raise ValueError(f"Unknown command: {name}")
        return self._commands[name]

    def list_commands(self) -> Dict[str, str]:
        """List all available commands with descriptions."""
        return {name: cmd_class().description for name, cmd_class in self._commands.items()}

    @property
    def command_names(self) -> list[str]:
        """Get list of command names."""
        return list(self._commands.keys())


# Global registry instance
registry = CommandRegistry()
