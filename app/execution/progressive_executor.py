"""Progressive execution engine for step-by-step task execution."""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union


class StepStatus(Enum):
    """Status of an execution step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    PAUSED = "paused"


class ExecutionControl(Enum):
    """User control options during execution."""

    CONTINUE = "continue"
    PAUSE = "pause"
    SKIP = "skip"
    ABORT = "abort"
    RETRY = "retry"
    DETAILS = "details"


@dataclass
class ExecutionStep:
    """Represents a single execution step."""

    id: str
    description: str
    execute: Callable[[], Any]
    can_skip: bool = True
    requires_confirmation: bool = False
    estimated_duration: Optional[float] = None
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[Exception] = None


@dataclass
class ExecutionResult:
    """Result of a step execution."""

    step_id: str
    status: StepStatus
    result: Optional[Any] = None
    error: Optional[Exception] = None
    requires_decision: bool = False
    options: Optional[List[str]] = None


@dataclass
class ExecutionPlan:
    """Execution plan containing all steps."""

    steps: List[ExecutionStep]
    name: str
    description: str


class ProgressListener(ABC):
    """Abstract base class for progress listeners."""

    @abstractmethod
    async def on_plan_start(self, plan: ExecutionPlan) -> None:
        """Called when execution plan starts."""
        pass

    @abstractmethod
    async def on_step_start(self, step: ExecutionStep) -> None:
        """Called when a step starts."""
        pass

    @abstractmethod
    async def on_step_complete(
        self, step: ExecutionStep, result: ExecutionResult
    ) -> None:
        """Called when a step completes."""
        pass

    @abstractmethod
    async def on_plan_complete(self, plan: ExecutionPlan) -> None:
        """Called when execution plan completes."""
        pass

    @abstractmethod
    async def on_error(self, step: ExecutionStep, error: Exception) -> None:
        """Called when an error occurs."""
        pass


class UserInputProvider(ABC):
    """Abstract base class for user input providers."""

    @abstractmethod
    async def get_confirmation(self, message: str) -> bool:
        """Get yes/no confirmation from user."""
        pass

    @abstractmethod
    async def get_choice(
        self, message: str, options: List[str]
    ) -> Optional[str]:
        """Get user choice from options."""
        pass

    @abstractmethod
    async def get_control_input(self) -> ExecutionControl:
        """Get execution control input from user."""
        pass


class ProgressiveExecutor:
    """Progressive executor for step-by-step task execution."""

    def __init__(
        self,
        listeners: Optional[List[ProgressListener]] = None,
        input_provider: Optional[UserInputProvider] = None,
    ):
        """Initialize the progressive executor."""
        self.listeners = listeners or []
        self.input_provider = input_provider
        self._current_plan: Optional[ExecutionPlan] = None
        self._is_paused = False
        self._is_aborted = False
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Not paused initially

    def add_listener(self, listener: ProgressListener) -> None:
        """Add a progress listener."""
        self.listeners.append(listener)

    def remove_listener(self, listener: ProgressListener) -> None:
        """Remove a progress listener."""
        if listener in self.listeners:
            self.listeners.remove(listener)

    async def _notify_plan_start(self, plan: ExecutionPlan) -> None:
        """Notify all listeners that plan is starting."""
        for listener in self.listeners:
            await listener.on_plan_start(plan)

    async def _notify_step_start(self, step: ExecutionStep) -> None:
        """Notify all listeners that step is starting."""
        for listener in self.listeners:
            await listener.on_step_start(step)

    async def _notify_step_complete(
        self, step: ExecutionStep, result: ExecutionResult
    ) -> None:
        """Notify all listeners that step completed."""
        for listener in self.listeners:
            await listener.on_step_complete(step, result)

    async def _notify_plan_complete(self, plan: ExecutionPlan) -> None:
        """Notify all listeners that plan completed."""
        for listener in self.listeners:
            await listener.on_plan_complete(plan)

    async def _notify_error(
        self, step: ExecutionStep, error: Exception
    ) -> None:
        """Notify all listeners of an error."""
        for listener in self.listeners:
            await listener.on_error(step, error)

    async def _execute_step(self, step: ExecutionStep) -> ExecutionResult:
        """Execute a single step."""
        try:
            # Check if confirmation required
            if step.requires_confirmation and self.input_provider:
                confirmed = await self.input_provider.get_confirmation(
                    f"Execute step: {step.description}?"
                )
                if not confirmed:
                    step.status = StepStatus.SKIPPED
                    return ExecutionResult(
                        step_id=step.id,
                        status=StepStatus.SKIPPED,
                    )

            step.status = StepStatus.RUNNING
            await self._notify_step_start(step)

            # Execute the step
            if asyncio.iscoroutinefunction(step.execute):
                result = await step.execute()
            else:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, step.execute
                )

            step.status = StepStatus.COMPLETED
            step.result = result

            return ExecutionResult(
                step_id=step.id,
                status=StepStatus.COMPLETED,
                result=result,
            )

        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = e
            await self._notify_error(step, e)
            return ExecutionResult(
                step_id=step.id,
                status=StepStatus.FAILED,
                error=e,
            )

    async def _wait_for_pause(self) -> None:
        """Wait if execution is paused."""
        await self._pause_event.wait()

    async def pause(self) -> None:
        """Pause execution."""
        self._is_paused = True
        self._pause_event.clear()

    async def resume(self) -> None:
        """Resume execution."""
        self._is_paused = False
        self._pause_event.set()

    async def abort(self) -> None:
        """Abort execution."""
        self._is_aborted = True
        self.resume()  # Resume to exit wait

    async def execute_with_feedback(
        self, plan: ExecutionPlan
    ) -> Dict[str, ExecutionResult]:
        """Execute plan with feedback."""
        self._current_plan = plan
        self._is_aborted = False
        results = {}

        await self._notify_plan_start(plan)

        for i, step in enumerate(plan.steps):
            # Check if aborted
            if self._is_aborted:
                break

            # Wait if paused
            await self._wait_for_pause()

            # Check for user control input
            if self.input_provider:
                control = await self.input_provider.get_control_input()

                if control == ExecutionControl.PAUSE:
                    await self.pause()
                    await self._wait_for_pause()
                elif control == ExecutionControl.SKIP and step.can_skip:
                    step.status = StepStatus.SKIPPED
                    results[step.id] = ExecutionResult(
                        step_id=step.id,
                        status=StepStatus.SKIPPED,
                    )
                    continue
                elif control == ExecutionControl.ABORT:
                    await self.abort()
                    break

            # Execute the step
            result = await self._execute_step(step)
            results[step.id] = result

            await self._notify_step_complete(step, result)

            # Handle step failure
            if result.status == StepStatus.FAILED and self.input_provider:
                choice = await self.input_provider.get_choice(
                    f"Step '{step.description}' failed. What would you like to do?",
                    ["retry", "skip", "abort"],
                )
                if choice == "retry":
                    result = await self._execute_step(step)
                    results[step.id] = result
                elif choice == "skip":
                    step.status = StepStatus.SKIPPED
                elif choice == "abort":
                    await self.abort()
                    break

        await self._notify_plan_complete(plan)
        return results

    def get_progress(self) -> Dict[str, Any]:
        """Get current execution progress."""
        if not self._current_plan:
            return {"status": "idle"}

        completed = sum(
            1
            for step in self._current_plan.steps
            if step.status
            in [StepStatus.COMPLETED, StepStatus.SKIPPED, StepStatus.FAILED]
        )
        total = len(self._current_plan.steps)

        return {
            "status": "paused" if self._is_paused else "running",
            "completed": completed,
            "total": total,
            "percentage": (completed / total * 100) if total > 0 else 0,
            "current_step": next(
                (
                    step.description
                    for step in self._current_plan.steps
                    if step.status == StepStatus.RUNNING
                ),
                None,
            ),
        }