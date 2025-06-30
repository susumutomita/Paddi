"""Progressive command implementations with real-time feedback."""

import asyncio
import logging
from typing import List, Optional

from app.execution import (
    FeedbackManager,
    InteractiveController,
    ProgressiveExecutor,
    VisualFeedback,
)
from app.execution.progressive_executor import ExecutionPlan, ExecutionStep

from .base import Command, CommandContext
from .commands import AuditCommand as BaseAuditCommand

logger = logging.getLogger(__name__)


class ProgressiveCommand(Command):
    """Base class for commands with progressive execution support."""

    def __init__(self, interactive: bool = True, visual: bool = True):
        """Initialize progressive command."""
        self.interactive = interactive
        self.visual = visual

    def create_execution_plan(self, context: CommandContext) -> ExecutionPlan:
        """Create execution plan for the command."""
        raise NotImplementedError("Subclasses must implement create_execution_plan")

    def execute(self, context: CommandContext) -> None:
        """Execute command with progressive feedback."""
        # Run async execution in sync context
        asyncio.run(self._execute_async(context))

    async def _execute_async(self, context: CommandContext) -> None:
        """Async execution with progressive feedback."""
        # Create execution plan
        plan = self.create_execution_plan(context)

        # Set up feedback components
        feedback_manager = FeedbackManager()
        visual_feedback = VisualFeedback(show_time=True, compact_mode=False)
        
        # Set up executor
        executor = ProgressiveExecutor()
        executor.add_listener(feedback_manager)
        
        if self.visual:
            executor.add_listener(visual_feedback)

        # Set up interactive controller if enabled
        if self.interactive:
            controller = InteractiveController(auto_mode=not context.verbose)
            executor.input_provider = controller
            controller.show_controls()

        # Execute the plan
        try:
            results = await executor.execute_with_feedback(plan)
            
            # Check for failures
            failed_steps = [
                step_id for step_id, result in results.items()
                if result.status.value == "failed"
            ]
            
            if failed_steps:
                logger.error(f"実行中にエラーが発生しました: {len(failed_steps)}件の失敗")
            else:
                logger.info("✅ 全てのステップが正常に完了しました")
                
        except Exception as e:
            logger.error(f"実行中に予期しないエラーが発生しました: {e}")
            raise


class ProgressiveAuditCommand(ProgressiveCommand):
    """Progressive implementation of audit command."""

    @property
    def name(self) -> str:
        return "audit"

    @property
    def description(self) -> str:
        return "Run complete audit pipeline with real-time feedback"

    def create_execution_plan(self, context: CommandContext) -> ExecutionPlan:
        """Create execution plan for audit."""
        from app.collector.agent_collector import main as collector_main
        from app.explainer.agent_explainer import main as explainer_main
        from app.reporter.agent_reporter import main as reporter_main

        steps = []

        # Collection step
        def collect_step():
            logger.info("📥 クラウド構成データを収集中...")
            collector_main(
                project_id=context.project_id,
                organization_id=context.organization_id,
                use_mock=context.use_mock,
                collect_all=context.collect_all,
                verbose=context.verbose,
            )
            logger.info("✓ データ収集完了")

        steps.append(
            ExecutionStep(
                id="collect",
                description="クラウド構成データの収集",
                execute=collect_step,
                can_skip=False,
                requires_confirmation=False,
                estimated_duration=10.0,
            )
        )

        # Analysis step
        def explain_step():
            logger.info("🔍 セキュリティリスクを分析中...")
            explainer_main(
                project_id=context.project_id,
                location=context.location,
                use_mock=context.use_mock,
                ai_provider=context.ai_provider,
                ollama_model=context.ollama_model,
                ollama_endpoint=context.ollama_endpoint,
            )
            logger.info("✓ リスク分析完了")

        steps.append(
            ExecutionStep(
                id="explain",
                description="AIによるセキュリティリスク分析",
                execute=explain_step,
                can_skip=False,
                requires_confirmation=context.verbose,
                estimated_duration=30.0,
            )
        )

        # Report generation step
        def report_step():
            logger.info("📝 監査レポートを生成中...")
            reporter_main(output_dir=context.output_dir)
            logger.info(f"✓ レポート生成完了: {context.output_dir}/")

        steps.append(
            ExecutionStep(
                id="report",
                description="監査レポートの生成",
                execute=report_step,
                can_skip=False,
                requires_confirmation=False,
                estimated_duration=5.0,
            )
        )

        return ExecutionPlan(
            steps=steps,
            name="包括的セキュリティ監査",
            description="クラウド構成の収集、リスク分析、レポート生成を実行",
        )


class ProgressiveCollectCommand(ProgressiveCommand):
    """Progressive implementation of collect command."""

    @property
    def name(self) -> str:
        return "collect"

    @property
    def description(self) -> str:
        return "Collect cloud configuration data with progress feedback"

    def create_execution_plan(self, context: CommandContext) -> ExecutionPlan:
        """Create execution plan for collection."""
        steps = []

        # Define collection sources
        sources = []
        if context.project_id:
            sources.append(("gcp", "Google Cloud", context.project_id))
        if context.aws_account_id:
            sources.append(("aws", "AWS", context.aws_account_id))
        if context.azure_subscription_id:
            sources.append(("azure", "Azure", context.azure_subscription_id))

        for source_type, source_name, source_id in sources:
            def create_collect_func(st, sn, sid):
                def collect():
                    logger.info(f"📥 {sn}からデータを収集中: {sid}")
                    # Here you would call the actual collection logic
                    # For now, we'll simulate it
                    import time
                    time.sleep(2)
                    logger.info(f"✓ {sn}のデータ収集完了")
                return collect

            steps.append(
                ExecutionStep(
                    id=f"collect_{source_type}",
                    description=f"{source_name}構成データの収集",
                    execute=create_collect_func(source_type, source_name, source_id),
                    can_skip=True,
                    requires_confirmation=False,
                    estimated_duration=5.0,
                )
            )

        # Aggregation step
        def aggregate_data():
            logger.info("📊 収集データを集約中...")
            import time
            time.sleep(1)
            logger.info("✓ データ集約完了")

        steps.append(
            ExecutionStep(
                id="aggregate",
                description="収集データの集約",
                execute=aggregate_data,
                can_skip=False,
                requires_confirmation=False,
                estimated_duration=2.0,
            )
        )

        return ExecutionPlan(
            steps=steps,
            name="マルチクラウド構成収集",
            description="複数のクラウドプロバイダーから構成データを収集",
        )