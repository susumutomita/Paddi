"""Feedback manager for real-time progress updates."""

import asyncio
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Deque, Dict, List, Optional

from .progressive_executor import (
    ExecutionPlan,
    ExecutionResult,
    ExecutionStep,
    ProgressListener,
)


class FeedbackLevel(Enum):
    """Feedback message level."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"


@dataclass
class FeedbackMessage:
    """Represents a feedback message."""

    level: FeedbackLevel
    message: str
    timestamp: datetime
    step_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class StepMetrics:
    """Metrics for a step execution."""

    step_id: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration: Optional[float] = None
    memory_usage: Optional[float] = None
    error_count: int = 0


class FeedbackManager(ProgressListener):
    """Manages real-time feedback and progress updates."""

    def __init__(
        self,
        max_history: int = 100,
        callback: Optional[Callable[[FeedbackMessage], None]] = None,
    ):
        """Initialize feedback manager."""
        self.messages: Deque[FeedbackMessage] = deque(maxlen=max_history)
        self.metrics: Dict[str, StepMetrics] = {}
        self.callback = callback
        self._start_time: Optional[float] = None
        self._current_plan: Optional[ExecutionPlan] = None
        self._completed_steps = 0
        self._total_steps = 0

    def add_message(
        self,
        level: FeedbackLevel,
        message: str,
        step_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a feedback message."""
        feedback = FeedbackMessage(
            level=level,
            message=message,
            timestamp=datetime.now(),
            step_id=step_id,
            details=details,
        )
        self.messages.append(feedback)

        if self.callback:
            self.callback(feedback)

    async def on_plan_start(self, plan: ExecutionPlan) -> None:
        """Handle plan start event."""
        self._start_time = time.time()
        self._current_plan = plan
        self._completed_steps = 0
        self._total_steps = len(plan.steps)

        self.add_message(
            FeedbackLevel.INFO,
            f"🚀 {plan.name}を開始します",
            details={
                "plan_name": plan.name,
                "description": plan.description,
                "total_steps": self._total_steps,
            },
        )

    async def on_step_start(self, step: ExecutionStep) -> None:
        """Handle step start event."""
        self.metrics[step.id] = StepMetrics(
            step_id=step.id, start_time=time.time()
        )

        self.add_message(
            FeedbackLevel.INFO,
            f"🔄 {step.description}を実行中...",
            step_id=step.id,
            details={"estimated_duration": step.estimated_duration},
        )

    async def on_step_complete(
        self, step: ExecutionStep, result: ExecutionResult
    ) -> None:
        """Handle step completion event."""
        metrics = self.metrics.get(step.id)
        if metrics and metrics.start_time:
            metrics.end_time = time.time()
            metrics.duration = metrics.end_time - metrics.start_time

        self._completed_steps += 1

        if result.status.value == "completed":
            self.add_message(
                FeedbackLevel.SUCCESS,
                f"✅ {step.description}が完了しました",
                step_id=step.id,
                details={
                    "duration": metrics.duration if metrics else None,
                    "result": str(result.result)[:100]
                    if result.result
                    else None,
                },
            )
        elif result.status.value == "failed":
            if metrics:
                metrics.error_count += 1
            self.add_message(
                FeedbackLevel.ERROR,
                f"❌ {step.description}が失敗しました",
                step_id=step.id,
                details={"error": str(result.error) if result.error else None},
            )
        elif result.status.value == "skipped":
            self.add_message(
                FeedbackLevel.WARNING,
                f"⏭️ {step.description}をスキップしました",
                step_id=step.id,
            )

    async def on_plan_complete(self, plan: ExecutionPlan) -> None:
        """Handle plan completion event."""
        total_duration = (
            time.time() - self._start_time if self._start_time else 0
        )

        successful_steps = sum(
            1
            for step in plan.steps
            if step.status.value == "completed"
        )
        failed_steps = sum(
            1 for step in plan.steps if step.status.value == "failed"
        )

        self.add_message(
            FeedbackLevel.INFO,
            f"🎉 {plan.name}が完了しました",
            details={
                "total_duration": total_duration,
                "successful_steps": successful_steps,
                "failed_steps": failed_steps,
                "total_steps": self._total_steps,
            },
        )

    async def on_error(self, step: ExecutionStep, error: Exception) -> None:
        """Handle error event."""
        metrics = self.metrics.get(step.id)
        if metrics:
            metrics.error_count += 1

        self.add_message(
            FeedbackLevel.ERROR,
            f"⚠️ エラーが発生しました: {str(error)}",
            step_id=step.id,
            details={"error_type": type(error).__name__, "error": str(error)},
        )

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get progress summary."""
        if not self._current_plan:
            return {"status": "idle"}

        elapsed_time = (
            time.time() - self._start_time if self._start_time else 0
        )
        avg_step_duration = self._calculate_avg_step_duration()
        estimated_remaining = self._estimate_remaining_time(avg_step_duration)

        return {
            "plan_name": self._current_plan.name,
            "completed_steps": self._completed_steps,
            "total_steps": self._total_steps,
            "percentage": (
                (self._completed_steps / self._total_steps * 100)
                if self._total_steps > 0
                else 0
            ),
            "elapsed_time": elapsed_time,
            "estimated_remaining": estimated_remaining,
            "recent_messages": list(self.messages)[-5:],
        }

    def _calculate_avg_step_duration(self) -> float:
        """Calculate average step duration."""
        durations = [
            m.duration
            for m in self.metrics.values()
            if m.duration is not None
        ]
        return sum(durations) / len(durations) if durations else 0

    def _estimate_remaining_time(self, avg_duration: float) -> float:
        """Estimate remaining time."""
        remaining_steps = self._total_steps - self._completed_steps
        return remaining_steps * avg_duration if avg_duration > 0 else 0

    def get_step_metrics(self, step_id: str) -> Optional[StepMetrics]:
        """Get metrics for a specific step."""
        return self.metrics.get(step_id)

    def get_recent_messages(
        self, count: int = 10, level: Optional[FeedbackLevel] = None
    ) -> List[FeedbackMessage]:
        """Get recent messages."""
        messages = list(self.messages)[-count:]
        if level:
            messages = [m for m in messages if m.level == level]
        return messages

    def clear_history(self) -> None:
        """Clear message history."""
        self.messages.clear()
        self.metrics.clear()