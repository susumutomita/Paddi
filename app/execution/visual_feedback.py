"""Visual feedback components for terminal UI."""

import os
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .feedback_manager import FeedbackLevel, FeedbackMessage
from .progressive_executor import (
    ExecutionPlan,
    ExecutionResult,
    ExecutionStep,
    ProgressListener,
)


@dataclass
class Theme:
    """Visual theme for terminal output."""

    # Progress bar characters
    progress_fill: str = "━"
    progress_empty: str = "━"
    progress_start: str = ""
    progress_end: str = ""

    # Status indicators
    success: str = "✅"
    error: str = "❌"
    warning: str = "⚠️"
    info: str = "ℹ️"
    running: str = "🔄"
    pending: str = "⏳"
    skipped: str = "⏭️"

    # Colors (ANSI escape codes)
    color_success: str = "\033[92m"  # Green
    color_error: str = "\033[91m"  # Red
    color_warning: str = "\033[93m"  # Yellow
    color_info: str = "\033[94m"  # Blue
    color_reset: str = "\033[0m"
    color_bold: str = "\033[1m"
    color_dim: str = "\033[2m"


class VisualFeedback(ProgressListener):
    """Visual feedback renderer for terminal."""

    def __init__(
        self,
        theme: Optional[Theme] = None,
        show_time: bool = True,
        show_memory: bool = False,
        compact_mode: bool = False,
    ):
        """Initialize visual feedback."""
        self.theme = theme or Theme()
        self.show_time = show_time
        self.show_memory = show_memory
        self.compact_mode = compact_mode
        self._terminal_width = self._get_terminal_width()
        self._current_plan: Optional[ExecutionPlan] = None
        self._start_time: Optional[float] = None
        self._last_update_time: float = 0
        self._update_interval: float = 0.1  # Update every 100ms

    def _get_terminal_width(self) -> int:
        """Get terminal width."""
        try:
            return os.get_terminal_size().columns
        except:
            return 80  # Default width

    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text if terminal supports it."""
        if not sys.stdout.isatty():
            return text
        return f"{color}{text}{self.theme.color_reset}"

    def _truncate_text(self, text: str, max_width: int) -> str:
        """Truncate text to fit terminal width."""
        if len(text) <= max_width:
            return text
        return text[: max_width - 3] + "..."

    def _render_progress_bar(
        self, current: int, total: int, width: int = 40
    ) -> str:
        """Render a progress bar."""
        if total == 0:
            percentage = 0
        else:
            percentage = current / total

        filled_width = int(width * percentage)
        empty_width = width - filled_width

        bar = (
            self.theme.progress_start
            + self.theme.progress_fill * filled_width
            + self.theme.progress_empty * empty_width
            + self.theme.progress_end
        )

        return f"{bar} {int(percentage * 100)}%"

    def _render_step_status(self, step: ExecutionStep) -> str:
        """Render step status with icon."""
        status_map = {
            "pending": (self.theme.pending, self.theme.color_dim),
            "running": (self.theme.running, self.theme.color_info),
            "completed": (self.theme.success, self.theme.color_success),
            "failed": (self.theme.error, self.theme.color_error),
            "skipped": (self.theme.skipped, self.theme.color_warning),
        }

        icon, color = status_map.get(
            step.status.value, (self.theme.info, self.theme.color_reset)
        )
        return self._colorize(icon, color)

    def _render_time_elapsed(self, seconds: float) -> str:
        """Render elapsed time in human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}分{secs}秒"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}時間{minutes}分"

    def _clear_line(self) -> None:
        """Clear current line in terminal."""
        if sys.stdout.isatty():
            print("\r" + " " * self._terminal_width + "\r", end="", flush=True)

    async def on_plan_start(self, plan: ExecutionPlan) -> None:
        """Handle plan start event."""
        self._current_plan = plan
        self._start_time = time.time()

        if not self.compact_mode:
            print("\n" + "=" * self._terminal_width)
            print(
                self._colorize(
                    f"🚀 {plan.name}", self.theme.color_bold
                )
            )
            if plan.description:
                print(f"   {plan.description}")
            print("=" * self._terminal_width + "\n")

    async def on_step_start(self, step: ExecutionStep) -> None:
        """Handle step start event."""
        current_time = time.time()
        if current_time - self._last_update_time < self._update_interval:
            return

        self._last_update_time = current_time

        if self.compact_mode:
            # Single line update
            self._clear_line()
            status = self._render_step_status(step)
            text = f"{status} {step.description}"
            print(self._truncate_text(text, self._terminal_width - 5), end="", flush=True)
        else:
            # Multi-line output
            print(f"{self._render_step_status(step)} {step.description}")

            if self.show_time and step.estimated_duration:
                print(
                    f"   予想時間: {self._render_time_elapsed(step.estimated_duration)}"
                )

    async def on_step_complete(
        self, step: ExecutionStep, result: ExecutionResult
    ) -> None:
        """Handle step completion event."""
        if self.compact_mode:
            self._clear_line()

        status_icon = self._render_step_status(step)
        duration_text = ""

        if self.show_time and hasattr(step, "_start_time"):
            duration = time.time() - step._start_time
            duration_text = f" ({self._render_time_elapsed(duration)})"

        if result.status.value == "completed":
            color = self.theme.color_success
            message = f"{status_icon} {step.description} 完了{duration_text}"
        elif result.status.value == "failed":
            color = self.theme.color_error
            message = f"{status_icon} {step.description} 失敗{duration_text}"
            if result.error:
                message += f"\n   エラー: {str(result.error)}"
        elif result.status.value == "skipped":
            color = self.theme.color_warning
            message = f"{status_icon} {step.description} スキップ"
        else:
            color = self.theme.color_reset
            message = f"{status_icon} {step.description}"

        print(self._colorize(message, color))

    async def on_plan_complete(self, plan: ExecutionPlan) -> None:
        """Handle plan completion event."""
        if not self._current_plan:
            return

        total_duration = time.time() - self._start_time if self._start_time else 0
        completed_steps = sum(
            1
            for step in plan.steps
            if step.status.value in ["completed", "skipped"]
        )
        failed_steps = sum(
            1 for step in plan.steps if step.status.value == "failed"
        )

        if not self.compact_mode:
            print("\n" + "=" * self._terminal_width)

        # Summary
        if failed_steps > 0:
            summary_icon = self.theme.error
            summary_color = self.theme.color_error
            summary_text = "実行完了（エラーあり）"
        else:
            summary_icon = self.theme.success
            summary_color = self.theme.color_success
            summary_text = "実行完了"

        print(
            self._colorize(
                f"{summary_icon} {summary_text}",
                summary_color + self.theme.color_bold,
            )
        )

        # Statistics
        print(f"\n📊 実行統計:")
        print(f"   完了: {completed_steps}/{len(plan.steps)} ステップ")
        if failed_steps > 0:
            print(
                self._colorize(
                    f"   失敗: {failed_steps} ステップ",
                    self.theme.color_error,
                )
            )
        print(f"   実行時間: {self._render_time_elapsed(total_duration)}")

        if not self.compact_mode:
            print("=" * self._terminal_width + "\n")

    async def on_error(self, step: ExecutionStep, error: Exception) -> None:
        """Handle error event."""
        if self.compact_mode:
            self._clear_line()

        print(
            self._colorize(
                f"{self.theme.error} エラー: {step.description}",
                self.theme.color_error + self.theme.color_bold,
            )
        )
        print(
            self._colorize(
                f"   {type(error).__name__}: {str(error)}",
                self.theme.color_error,
            )
        )

    def render_progress_summary(
        self, progress: Dict[str, any]
    ) -> str:
        """Render a progress summary."""
        lines = []

        # Header
        if progress.get("plan_name"):
            lines.append(
                self._colorize(
                    f"📋 {progress['plan_name']}",
                    self.theme.color_bold,
                )
            )

        # Progress bar
        completed = progress.get("completed_steps", 0)
        total = progress.get("total_steps", 0)
        if total > 0:
            bar = self._render_progress_bar(completed, total, width=30)
            lines.append(f"{bar} [{completed}/{total}ステップ]")

        # Time information
        if self.show_time:
            elapsed = progress.get("elapsed_time", 0)
            remaining = progress.get("estimated_remaining", 0)
            time_info = f"経過: {self._render_time_elapsed(elapsed)}"
            if remaining > 0:
                time_info += f" | 残り: {self._render_time_elapsed(remaining)}"
            lines.append(time_info)

        # Current step
        if progress.get("current_step"):
            lines.append(
                f"\n現在: {self.theme.running} {progress['current_step']}"
            )

        return "\n".join(lines)


class SpinnerFeedback:
    """Simple spinner for indicating activity."""

    def __init__(self, message: str = "処理中"):
        """Initialize spinner."""
        self.message = message
        self.chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.current = 0
        self._running = False

    def start(self) -> None:
        """Start spinner."""
        self._running = True
        self._animate()

    def stop(self) -> None:
        """Stop spinner."""
        self._running = False
        if sys.stdout.isatty():
            print("\r" + " " * (len(self.message) + 4) + "\r", end="", flush=True)

    def _animate(self) -> None:
        """Animate spinner."""
        import threading

        def run():
            while self._running:
                if sys.stdout.isatty():
                    char = self.chars[self.current]
                    print(f"\r{char} {self.message}", end="", flush=True)
                    self.current = (self.current + 1) % len(self.chars)
                time.sleep(0.1)

        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()