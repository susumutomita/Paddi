"""Interactive controller for user input during execution."""

import asyncio
import sys
from typing import Dict, List, Optional

from .progressive_executor import ExecutionControl, UserInputProvider


class InteractiveController(UserInputProvider):
    """Handles interactive user input during execution."""

    def __init__(self, auto_mode: bool = False):
        """Initialize interactive controller."""
        self.auto_mode = auto_mode
        self._input_queue: asyncio.Queue = asyncio.Queue()
        self._is_interactive = sys.stdin.isatty()

    async def get_confirmation(self, message: str) -> bool:
        """Get yes/no confirmation from user."""
        if self.auto_mode:
            return True

        if not self._is_interactive:
            return True

        while True:
            response = await self._get_input(f"{message} [Y/n]: ")
            response = response.strip().lower()

            if response in ["", "y", "yes"]:
                return True
            elif response in ["n", "no"]:
                return False
            else:
                print("無効な入力です。'y' または 'n' を入力してください。")

    async def get_choice(
        self, message: str, options: List[str]
    ) -> Optional[str]:
        """Get user choice from options."""
        if self.auto_mode and options:
            return options[0]

        if not self._is_interactive:
            return options[0] if options else None

        # Display options
        print(f"\n{message}")
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")

        while True:
            response = await self._get_input("選択してください (番号): ")
            try:
                choice_idx = int(response.strip()) - 1
                if 0 <= choice_idx < len(options):
                    return options[choice_idx]
                else:
                    print(f"1から{len(options)}の番号を入力してください。")
            except ValueError:
                # Try matching by text
                response_lower = response.strip().lower()
                for option in options:
                    if option.lower() == response_lower:
                        return option
                print("無効な入力です。番号または選択肢を入力してください。")

    async def get_control_input(self) -> ExecutionControl:
        """Get execution control input from user."""
        if self.auto_mode:
            return ExecutionControl.CONTINUE

        if not self._is_interactive:
            return ExecutionControl.CONTINUE

        # Non-blocking check for user input
        if self._has_pending_input():
            response = await self._get_input_nowait()
            if response:
                return self._parse_control_input(response)

        return ExecutionControl.CONTINUE

    def _parse_control_input(self, input_str: str) -> ExecutionControl:
        """Parse control input string."""
        input_lower = input_str.strip().lower()

        control_map = {
            "p": ExecutionControl.PAUSE,
            "pause": ExecutionControl.PAUSE,
            "s": ExecutionControl.SKIP,
            "skip": ExecutionControl.SKIP,
            "a": ExecutionControl.ABORT,
            "abort": ExecutionControl.ABORT,
            "d": ExecutionControl.DETAILS,
            "details": ExecutionControl.DETAILS,
            "r": ExecutionControl.RETRY,
            "retry": ExecutionControl.RETRY,
        }

        return control_map.get(input_lower, ExecutionControl.CONTINUE)

    async def _get_input(self, prompt: str) -> str:
        """Get input from user with prompt."""
        if sys.stdin.isatty():
            # Interactive terminal
            return await asyncio.get_event_loop().run_in_executor(
                None, input, prompt
            )
        else:
            # Non-interactive, read from stdin
            print(prompt, end="", flush=True)
            return await asyncio.get_event_loop().run_in_executor(
                None, sys.stdin.readline
            )

    def _has_pending_input(self) -> bool:
        """Check if there's pending input (non-blocking)."""
        # This is a simplified check - in practice, you might use select()
        # or other platform-specific methods
        return False

    async def _get_input_nowait(self) -> Optional[str]:
        """Get input without waiting (non-blocking)."""
        try:
            return self._input_queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

    def show_controls(self) -> None:
        """Display available controls to user."""
        if not self._is_interactive or self.auto_mode:
            return

        print("\n実行制御コマンド:")
        print("  [p] 一時停止")
        print("  [s] 現在のステップをスキップ")
        print("  [a] 実行を中止")
        print("  [d] 詳細を表示")
        print("  [Enter] 続行\n")


class DialogController(InteractiveController):
    """Enhanced controller with dialog-style interactions."""

    def __init__(self, auto_mode: bool = False):
        """Initialize dialog controller."""
        super().__init__(auto_mode)
        self.context: Dict[str, any] = {}

    async def show_step_details(
        self, step_info: Dict[str, any]
    ) -> Optional[str]:
        """Show detailed information about a step."""
        if self.auto_mode:
            return None

        print("\n" + "=" * 50)
        print(f"ステップ詳細: {step_info.get('description', 'N/A')}")
        print("=" * 50)

        for key, value in step_info.items():
            if key != "description":
                print(f"{key}: {value}")

        print("=" * 50 + "\n")

        return await self.get_choice(
            "次のアクションを選択してください:",
            ["続行", "スキップ", "中止", "設定を変更"],
        )

    async def get_settings_update(
        self, current_settings: Dict[str, any]
    ) -> Dict[str, any]:
        """Get updated settings from user."""
        if self.auto_mode:
            return current_settings

        print("\n現在の設定:")
        for key, value in current_settings.items():
            print(f"  {key}: {value}")

        updated_settings = current_settings.copy()

        while True:
            key = await self._get_input(
                "\n変更する設定名 (空欄で終了): "
            )
            if not key.strip():
                break

            if key in current_settings:
                value = await self._get_input(f"{key}の新しい値: ")
                updated_settings[key] = value
                print(f"✓ {key} を {value} に更新しました")
            else:
                print(f"設定 '{key}' は存在しません")

        return updated_settings

    async def show_error_dialog(
        self, error: Exception, context: Dict[str, any]
    ) -> str:
        """Show error dialog and get user action."""
        if self.auto_mode:
            return "retry"

        print("\n" + "!" * 50)
        print("エラーが発生しました")
        print("!" * 50)
        print(f"エラータイプ: {type(error).__name__}")
        print(f"エラーメッセージ: {str(error)}")

        if context:
            print("\nコンテキスト:")
            for key, value in context.items():
                print(f"  {key}: {value}")

        print("!" * 50 + "\n")

        return await self.get_choice(
            "どのように対処しますか？",
            ["再試行", "スキップ", "中止", "詳細を確認"],
        )