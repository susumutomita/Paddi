#!/usr/bin/env python3
"""
Autonomous CLI for Paddi - Natural Language Interface

Provides a gemini-cli style interface for interacting with Paddi through natural language.
Supports both interactive and one-shot modes with special commands.
"""

import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt

from app.agents.orchestrator import MultiAgentCoordinator
from app.cli.paddi_cli import PaddiCLI

logger = logging.getLogger(__name__)
console = Console()


class SpecialCommand(Enum):
    """Special commands for the autonomous CLI."""

    EXIT = "/exit"
    CLEAR = "/clear"
    HELP = "/help"
    MODEL = "/model"
    HISTORY = "/history"
    RESET = "/reset"


@dataclass
class ConversationContext:
    """Context for maintaining conversation state."""

    history: List[Dict[str, str]]
    project_id: Optional[str] = None
    model: str = "gemini-1.5-flash"
    session_start: datetime = None
    last_command_result: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize session start time."""
        if self.session_start is None:
            self.session_start = datetime.now()


class NaturalLanguageParser:
    """Parse natural language commands to structured commands."""

    def __init__(self):
        """Initialize the parser."""
        self.command_patterns = {
            "audit": [
                "監査",
                "audit",
                "セキュリティチェック",
                "security check",
                "診断",
                "analyze security",
                "脆弱性を調べ",
            ],
            "collect": [
                "収集",
                "collect",
                "構成情報",
                "configuration",
                "データを取得",
                "gather data",
            ],
            "analyze": ["分析", "analyze", "解析", "explain", "リスクを説明", "risk analysis"],
            "report": ["レポート", "report", "報告書", "結果をまとめ", "summary", "サマリー"],
        }

    def parse_command(self, input_text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Parse natural language input to command and parameters.

        Returns:
            Tuple of (command, parameters)
        """
        input_lower = input_text.lower()

        # Extract project ID if mentioned
        project_id = self._extract_project_id(input_text)

        # Determine command type
        command = self._determine_command(input_lower)

        # Extract additional parameters
        params = {"project_id": project_id}

        # Check for specific flags
        if "mock" in input_lower or "テスト" in input_lower:
            params["use_mock"] = True
        if "実際の" in input_lower or "real" in input_lower:
            params["use_mock"] = False

        return command, params

    def _extract_project_id(self, text: str) -> Optional[str]:
        """Extract project ID from text."""
        # Look for patterns like "project xxx" or "プロジェクト xxx"
        import re

        patterns = [
            r"project[:\s]+([a-zA-Z0-9\-_]+)",
            r"プロジェクト[:\s]*([a-zA-Z0-9\-_]+)",
            r"project_id[:\s]+([a-zA-Z0-9\-_]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _determine_command(self, input_lower: str) -> str:
        """Determine the command type from input."""
        for command, patterns in self.command_patterns.items():
            if any(pattern in input_lower for pattern in patterns):
                return command

        # Default to using the orchestrator for complex requests
        return "ai_agent"


class AutonomousCLI:
    """Autonomous CLI interface for natural language interaction."""

    def __init__(self):
        """Initialize the autonomous CLI."""
        self.paddi_cli = PaddiCLI()
        self.coordinator = MultiAgentCoordinator()
        self.parser = NaturalLanguageParser()
        self.context = ConversationContext(history=[])

    def start_interactive(self):
        """Start interactive mode."""
        self._print_welcome()

        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold cyan]paddi[/bold cyan]")

                # Check for special commands
                if self._handle_special_command(user_input):
                    continue

                # Process the command
                self._process_command(user_input)

            except KeyboardInterrupt:
                console.print("\n\n[yellow]セッションを終了します。[/yellow]")
                break
            except Exception as e:
                logger.error(f"Error processing command: {e}")
                console.print(f"\n[red]エラーが発生しました: {e}[/red]")

    def execute_one_shot(self, command: str) -> Dict[str, Any]:
        """Execute a single command and return the result."""
        return self._process_command(command, one_shot=True)

    def _print_welcome(self):
        """Print welcome message."""
        console.print("\n[bold green]🤖 Paddi Autonomous CLI[/bold green]")
        console.print("自然言語でセキュリティ監査を実行できます。")
        console.print("ヘルプは [cyan]/help[/cyan] を入力してください。")
        console.print("終了するには [cyan]/exit[/cyan] を入力してください。\n")

    def _handle_special_command(self, input_text: str) -> bool:
        """
        Handle special commands.

        Returns:
            True if command was handled, False otherwise
        """
        input_lower = input_text.lower().strip()

        if input_lower == SpecialCommand.EXIT.value:
            console.print("\n[yellow]セッションを終了します。[/yellow]")
            sys.exit(0)

        elif input_lower == SpecialCommand.CLEAR.value:
            console.clear()
            return True

        elif input_lower == SpecialCommand.HELP.value:
            self._show_help()
            return True

        elif input_lower.startswith(SpecialCommand.MODEL.value):
            self._handle_model_command(input_text)
            return True

        elif input_lower == SpecialCommand.HISTORY.value:
            self._show_history()
            return True

        elif input_lower == SpecialCommand.RESET.value:
            self.context = ConversationContext(history=[])
            console.print("[green]コンテキストをリセットしました。[/green]")
            return True

        return False

    def _show_help(self):
        """Show help information."""
        help_text = """
# Paddi Autonomous CLI ヘルプ

## 使用例
- `GCPプロジェクト example-123 のセキュリティを監査して`
- `脆弱性をチェックして詳細なレポートを作成`
- `プロジェクトの構成情報を収集して`

## 特殊コマンド
- `/exit` - セッションを終了
- `/clear` - 画面をクリア
- `/help` - このヘルプを表示
- `/model <name>` - AIモデルを切り替え
- `/history` - 会話履歴を表示
- `/reset` - コンテキストをリセット

## サポートされるコマンド
- **監査**: セキュリティ監査を実行
- **収集**: GCP構成情報を収集
- **分析**: セキュリティリスクを分析
- **レポート**: 監査レポートを生成
        """
        console.print(Markdown(help_text))

    def _handle_model_command(self, input_text: str):
        """Handle model switching command."""
        parts = input_text.split()
        if len(parts) > 1:
            model_name = parts[1]
            self.context.model = model_name
            console.print(f"[green]モデルを {model_name} に切り替えました。[/green]")
        else:
            console.print(f"[cyan]現在のモデル: {self.context.model}[/cyan]")

    def _show_history(self):
        """Show conversation history."""
        if not self.context.history:
            console.print("[yellow]会話履歴はありません。[/yellow]")
            return

        console.print("\n[bold]会話履歴:[/bold]")
        for i, entry in enumerate(self.context.history, 1):
            console.print(f"\n[cyan]{i}. ユーザー:[/cyan] {entry['user']}")
            console.print(f"[green]   応答:[/green] {entry['response']}")

    def _process_command(self, user_input: str, one_shot: bool = False) -> Dict[str, Any]:
        """Process a natural language command."""
        # Add to history
        history_entry = {"user": user_input, "response": ""}

        try:
            # Parse the command
            command, params = self.parser.parse_command(user_input)

            # Use project_id from context if not specified
            if not params.get("project_id") and self.context.project_id:
                params["project_id"] = self.context.project_id

            # Execute the command
            if command == "ai_agent":
                # Use the orchestrator for complex natural language requests
                response = self.coordinator.process_complex_request(user_input)
                result = response
            else:
                # Execute specific command
                result = self._execute_paddi_command(command, params)

            # Update context
            self.context.last_command_result = result

            # Store project_id if found
            if params.get("project_id"):
                self.context.project_id = params["project_id"]

            # Format response
            response_text = self._format_response(result)
            history_entry["response"] = response_text

            # Display response (unless in one-shot mode)
            if not one_shot:
                console.print(f"\n{response_text}")

            return result

        except Exception as e:
            error_msg = f"エラー: {str(e)}"
            history_entry["response"] = error_msg

            if not one_shot:
                console.print(f"\n[red]{error_msg}[/red]")

            return {"success": False, "error": str(e)}

        finally:
            self.context.history.append(history_entry)

    def _execute_paddi_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific Paddi command."""
        # Map command to PaddiCLI method
        method_map = {
            "audit": self.paddi_cli.audit,
            "collect": self.paddi_cli.collect,
            "analyze": self.paddi_cli.analyze,
            "report": self.paddi_cli.report,
        }

        if command not in method_map:
            raise ValueError(f"Unknown command: {command}")

        # Execute the command
        method = method_map[command]

        # Filter out None values from params
        filtered_params = {k: v for k, v in params.items() if v is not None}

        # Execute and capture output
        # Note: In a real implementation, we'd capture stdout/stderr
        method(**filtered_params)

        return {
            "success": True,
            "command": command,
            "params": filtered_params,
            "message": f"{command} コマンドを実行しました。",
        }

    def _format_response(self, result: Dict[str, Any]) -> str:
        """Format the response for display."""
        if result.get("success"):
            response = (
                f"[green]✅ {result.get('message', 'コマンドが正常に実行されました。')}[/green]"
            )

            if result.get("summary"):
                response += f"\n\n{result['summary']}"

            if result.get("report_path"):
                response += f"\n\n📄 レポート: {result['report_path']}"

            return response
        else:
            return f"[red]❌ {result.get('message', 'コマンドの実行に失敗しました。')}[/red]"


def main():
    """Main entry point for the autonomous CLI."""
    import argparse

    parser = argparse.ArgumentParser(description="Paddi Autonomous CLI")
    parser.add_argument(
        "command",
        nargs="?",
        help="Natural language command to execute (optional for interactive mode)",
    )
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Start in interactive mode"
    )

    args = parser.parse_args()

    cli = AutonomousCLI()

    if args.command and not args.interactive:
        # One-shot mode
        result = cli.execute_one_shot(args.command)
        sys.exit(0 if result.get("success") else 1)
    else:
        # Interactive mode
        cli.start_interactive()


if __name__ == "__main__":
    main()
