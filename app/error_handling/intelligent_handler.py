"""Intelligent error handling with self-healing capabilities."""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type

from app.log.logger import get_logger
from app.memory.context_manager import ContextualMemory

logger = get_logger(__name__)


class ErrorCategory(Enum):
    """Categories of errors for classification."""

    API_LIMIT = "api_limit"
    PERMISSION = "permission"
    NETWORK = "network"
    RESOURCE = "resource"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class RecoveryStrategy(ABC):
    """Abstract base class for recovery strategies."""

    @abstractmethod
    async def execute(self, error: Exception, context: Dict[str, Any]) -> Any:
        """Execute the recovery strategy."""

    @abstractmethod
    def can_handle(self, error: Exception) -> bool:
        """Check if this strategy can handle the given error."""


class RetryWithBackoffStrategy(RecoveryStrategy):
    """Retry with exponential backoff strategy."""

    def __init__(self, max_retries: int = 3, initial_delay: float = 1.0):
        self.max_retries = max_retries
        self.initial_delay = initial_delay

    def can_handle(self, error: Exception) -> bool:
        """Check if error is retryable."""
        error_msg = str(error).lower()
        retryable_keywords = ["rate limit", "quota", "too many requests", "temporarily unavailable"]
        return any(keyword in error_msg for keyword in retryable_keywords)

    async def execute(self, error: Exception, context: Dict[str, Any]) -> Any:
        """Execute retry with exponential backoff."""
        operation = context.get("operation")
        if not operation:
            raise ValueError("No operation provided for retry")

        delay = self.initial_delay
        last_error = error

        for attempt in range(self.max_retries):
            try:
                logger.info(f"Retrying operation (attempt {attempt + 1}/{self.max_retries})")
                await asyncio.sleep(delay)
                return await operation()
            except Exception as e:
                last_error = e
                delay *= 2  # Exponential backoff
                logger.warning(f"Retry {attempt + 1} failed: {e}")

        raise last_error


class AlternativeAPIStrategy(RecoveryStrategy):
    """Use alternative API endpoints or services."""

    def __init__(self, alternatives: Dict[str, Callable]):
        self.alternatives = alternatives

    def can_handle(self, error: Exception) -> bool:
        """Check if we have alternatives for this error."""
        error_msg = str(error).lower()
        return "api" in error_msg or "endpoint" in error_msg

    async def execute(self, error: Exception, context: Dict[str, Any]) -> Any:
        """Try alternative APIs."""
        service_name = context.get("service_name", "default")
        
        if service_name in self.alternatives:
            alternative = self.alternatives[service_name]
            logger.info(f"Switching to alternative API for {service_name}")
            return await alternative(context)
        
        raise error


class ResourceOptimizationStrategy(RecoveryStrategy):
    """Optimize resource usage when hitting limits."""

    def can_handle(self, error: Exception) -> bool:
        """Check if error is resource-related."""
        error_msg = str(error).lower()
        resource_keywords = ["memory", "disk space", "cpu", "resource", "out of"]
        return any(keyword in error_msg for keyword in resource_keywords)

    async def execute(self, error: Exception, context: Dict[str, Any]) -> Any:
        """Optimize resources and retry."""
        # Clear caches if available
        if "memory_manager" in context:
            context["memory_manager"].clear_memory("short_term")
            logger.info("Cleared short-term memory to free resources")

        # Split large operations into smaller chunks
        if "data" in context and isinstance(context["data"], list):
            data = context["data"]
            chunk_size = len(data) // 2
            if chunk_size > 0:
                logger.info(f"Splitting operation into chunks of {chunk_size}")
                results = []
                for i in range(0, len(data), chunk_size):
                    chunk = data[i:i + chunk_size]
                    chunk_context = {**context, "data": chunk}
                    result = await context["operation"](chunk_context)
                    results.extend(result if isinstance(result, list) else [result])
                return results

        # If no optimization possible, re-raise
        raise error


class PermissionEscalationStrategy(RecoveryStrategy):
    """Handle permission errors by suggesting escalation."""

    def can_handle(self, error: Exception) -> bool:
        """Check if error is permission-related."""
        error_msg = str(error).lower()
        permission_keywords = ["permission", "forbidden", "unauthorized", "access denied"]
        return any(keyword in error_msg for keyword in permission_keywords)

    async def execute(self, error: Exception, context: Dict[str, Any]) -> Any:
        """Provide guidance for permission issues."""
        error_msg = str(error)
        
        # Extract required permissions if possible
        required_permissions = self._extract_permissions(error_msg)
        
        guidance = {
            "error_type": "permission",
            "message": "権限エラーが発生しました",
            "required_permissions": required_permissions,
            "suggestions": [
                "必要な権限を確認してください",
                "サービスアカウントに適切なロールを付与してください",
                f"推奨ロール: {', '.join(required_permissions)}" if required_permissions else "管理者に確認してください"
            ],
            "command_hint": "gcloud projects add-iam-policy-binding PROJECT_ID --member=SERVICE_ACCOUNT --role=ROLE"
        }
        
        logger.error(f"Permission error: {json.dumps(guidance, ensure_ascii=False, indent=2)}")
        return guidance

    def _extract_permissions(self, error_msg: str) -> List[str]:
        """Extract required permissions from error message."""
        # Common GCP permission patterns
        if "compute.instances" in error_msg:
            return ["roles/compute.instanceAdmin"]
        elif "storage.buckets" in error_msg:
            return ["roles/storage.admin"]
        elif "iam.serviceAccounts" in error_msg:
            return ["roles/iam.serviceAccountAdmin"]
        return []


class ErrorAnalysis:
    """Analysis result for an error."""

    def __init__(self, category: ErrorCategory, severity: str, root_cause: str, 
                 context: Dict[str, Any]):
        self.category = category
        self.severity = severity
        self.root_cause = root_cause
        self.context = context
        self.timestamp = datetime.now()


class IntelligentErrorHandler:
    """Intelligent error classification and analysis."""

    def __init__(self):
        self.error_patterns = {
            ErrorCategory.API_LIMIT: [
                "rate limit", "quota exceeded", "too many requests", "429"
            ],
            ErrorCategory.PERMISSION: [
                "permission denied", "forbidden", "unauthorized", "403", "access denied"
            ],
            ErrorCategory.NETWORK: [
                "connection", "timeout", "network", "dns", "unreachable"
            ],
            ErrorCategory.RESOURCE: [
                "memory", "disk", "cpu", "resource", "out of", "insufficient"
            ],
            ErrorCategory.AUTHENTICATION: [
                "authentication", "credentials", "token", "401", "unauthenticated"
            ],
            ErrorCategory.VALIDATION: [
                "invalid", "validation", "bad request", "400", "malformed"
            ],
            ErrorCategory.TIMEOUT: [
                "timeout", "deadline", "took too long", "time limit"
            ]
        }

    def analyze_error(self, error: Exception, context: Dict[str, Any]) -> ErrorAnalysis:
        """Analyze error and classify it."""
        error_msg = str(error).lower()
        error_type = type(error).__name__
        
        # Classify error
        category = self._classify_error(error_msg, error_type)
        
        # Determine severity
        severity = self._determine_severity(category, context)
        
        # Extract root cause
        root_cause = self._extract_root_cause(error, category)
        
        return ErrorAnalysis(
            category=category,
            severity=severity,
            root_cause=root_cause,
            context={
                **context,
                "error_type": error_type,
                "error_message": str(error)
            }
        )

    def _classify_error(self, error_msg: str, error_type: str) -> ErrorCategory:
        """Classify error into category."""
        for category, patterns in self.error_patterns.items():
            if any(pattern in error_msg for pattern in patterns):
                return category
        
        # Check error type for additional classification
        if "timeout" in error_type.lower():
            return ErrorCategory.TIMEOUT
        elif "permission" in error_type.lower():
            return ErrorCategory.PERMISSION
        
        return ErrorCategory.UNKNOWN

    def _determine_severity(self, category: ErrorCategory, context: Dict[str, Any]) -> str:
        """Determine error severity."""
        # Critical errors
        if category in [ErrorCategory.AUTHENTICATION, ErrorCategory.PERMISSION]:
            return "CRITICAL"
        
        # High severity
        if category in [ErrorCategory.RESOURCE, ErrorCategory.API_LIMIT]:
            return "HIGH"
        
        # Medium severity
        if category in [ErrorCategory.NETWORK, ErrorCategory.TIMEOUT]:
            # Network errors might be transient
            retry_count = context.get("retry_count", 0)
            if retry_count > 2:
                return "HIGH"
            return "MEDIUM"
        
        # Low severity
        if category == ErrorCategory.VALIDATION:
            return "LOW"
        
        return "MEDIUM"

    def _extract_root_cause(self, error: Exception, category: ErrorCategory) -> str:
        """Extract root cause from error."""
        error_msg = str(error)
        
        if category == ErrorCategory.API_LIMIT:
            if "quota" in error_msg.lower():
                return "API quota exceeded"
            return "Rate limit reached"
        
        elif category == ErrorCategory.PERMISSION:
            return f"Insufficient permissions: {error_msg}"
        
        elif category == ErrorCategory.NETWORK:
            if "timeout" in error_msg.lower():
                return "Network timeout"
            return "Network connectivity issue"
        
        elif category == ErrorCategory.RESOURCE:
            if "memory" in error_msg.lower():
                return "Out of memory"
            elif "disk" in error_msg.lower():
                return "Insufficient disk space"
            return "Resource exhaustion"
        
        return error_msg


class ExecutionContext:
    """Context for error handling and recovery."""

    def __init__(self, operation: Callable, **kwargs):
        self.operation = operation
        self.metadata = kwargs
        self.retry_count = 0
        self.start_time = datetime.now()
        self.error_history = []

    def add_error(self, error: Exception):
        """Add error to history."""
        self.error_history.append({
            "error": str(error),
            "type": type(error).__name__,
            "timestamp": datetime.now().isoformat()
        })


class SelfHealingSystem:
    """Main self-healing system that coordinates error handling and recovery."""

    def __init__(self, memory_manager: Optional[ContextualMemory] = None):
        self.error_handler = IntelligentErrorHandler()
        self.memory_manager = memory_manager or ContextualMemory()
        self.recovery_strategies = [
            RetryWithBackoffStrategy(),
            AlternativeAPIStrategy({}),  # Can be configured with alternatives
            ResourceOptimizationStrategy(),
            PermissionEscalationStrategy()
        ]
        self.healing_history = []

    async def handle_error(self, error: Exception, context: ExecutionContext) -> Any:
        """Handle error with self-healing capabilities."""
        logger.error(f"🔧 Self-healing system activated for error: {error}")
        
        # Add error to context
        context.add_error(error)
        
        # Analyze error
        error_analysis = self.error_handler.analyze_error(
            error, 
            {"retry_count": context.retry_count, **context.metadata}
        )
        
        logger.info(
            f"Error analysis - Category: {error_analysis.category.value}, "
            f"Severity: {error_analysis.severity}, "
            f"Root cause: {error_analysis.root_cause}"
        )
        
        # Check if we've seen this error before
        previous_solution = self.memory_manager.get_error_solution(
            error_analysis.root_cause
        )
        
        if previous_solution:
            logger.info(f"Found previous solution: {previous_solution}")
            # Try previous solution first
            try:
                return await self._apply_solution(previous_solution, context)
            except Exception as e:
                logger.warning(f"Previous solution failed: {e}")
        
        # Generate recovery strategies
        strategies = await self.generate_recovery_strategies(error_analysis)
        
        # Execute strategies
        for strategy in strategies:
            try:
                logger.info(f"Attempting recovery strategy: {type(strategy).__name__}")
                result = await strategy.execute(error, {
                    "operation": context.operation,
                    "memory_manager": self.memory_manager,
                    **context.metadata
                })
                
                # Record successful solution
                self.memory_manager.record_error(
                    error_analysis.root_cause,
                    f"{type(strategy).__name__}:{json.dumps(context.metadata)}"
                )
                
                self._record_healing(error_analysis, strategy, success=True)
                return result
                
            except Exception as e:
                logger.warning(f"Recovery strategy {type(strategy).__name__} failed: {e}")
                continue
        
        # All strategies failed - suggest alternatives
        alternatives = await self.suggest_alternatives(error_analysis)
        logger.error(f"All recovery strategies failed. Alternatives: {alternatives}")
        
        self._record_healing(error_analysis, None, success=False)
        raise error

    async def generate_recovery_strategies(self, 
                                         error_analysis: ErrorAnalysis) -> List[RecoveryStrategy]:
        """Generate applicable recovery strategies for the error."""
        applicable_strategies = []
        
        # Use a mock error for testing strategy selection
        mock_error = Exception(error_analysis.context.get("error_message", ""))
        
        for strategy in self.recovery_strategies:
            if strategy.can_handle(mock_error):
                applicable_strategies.append(strategy)
        
        # Prioritize based on error category
        if error_analysis.category == ErrorCategory.API_LIMIT:
            # Prioritize retry and alternative API
            applicable_strategies.sort(
                key=lambda s: 0 if isinstance(s, RetryWithBackoffStrategy) else 1
            )
        
        return applicable_strategies

    async def suggest_alternatives(self, error_analysis: ErrorAnalysis) -> Dict[str, Any]:
        """Suggest alternative approaches when all strategies fail."""
        suggestions = {
            "error_category": error_analysis.category.value,
            "severity": error_analysis.severity,
            "manual_interventions": [],
            "workarounds": [],
            "documentation_links": []
        }
        
        if error_analysis.category == ErrorCategory.API_LIMIT:
            suggestions["manual_interventions"].append(
                "API制限に達しました。15分後に再試行してください"
            )
            suggestions["workarounds"].append(
                "--rate-limitオプションを使用してリクエスト速度を制限"
            )
            
        elif error_analysis.category == ErrorCategory.PERMISSION:
            suggestions["manual_interventions"].append(
                "必要な権限を付与してください"
            )
            suggestions["documentation_links"].append(
                "https://cloud.google.com/iam/docs/understanding-roles"
            )
            
        elif error_analysis.category == ErrorCategory.RESOURCE:
            suggestions["workarounds"].append(
                "処理を小さなバッチに分割して実行"
            )
            suggestions["workarounds"].append(
                "不要なリソースをクリーンアップ"
            )
        
        return suggestions

    async def _apply_solution(self, solution: str, context: ExecutionContext) -> Any:
        """Apply a previously successful solution."""
        # Parse solution format: "StrategyName:metadata"
        parts = solution.split(":", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid solution format: {solution}")
        
        strategy_name, metadata_str = parts
        
        # Find matching strategy
        for strategy in self.recovery_strategies:
            if type(strategy).__name__ == strategy_name:
                # Apply with saved metadata
                saved_metadata = json.loads(metadata_str) if metadata_str else {}
                return await strategy.execute(
                    Exception("Retry with previous solution"),
                    {**context.metadata, **saved_metadata}
                )
        
        raise ValueError(f"Strategy not found: {strategy_name}")

    def _record_healing(self, error_analysis: ErrorAnalysis, 
                       strategy: Optional[RecoveryStrategy], success: bool):
        """Record healing attempt for analysis."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "error_category": error_analysis.category.value,
            "severity": error_analysis.severity,
            "root_cause": error_analysis.root_cause,
            "strategy": type(strategy).__name__ if strategy else "None",
            "success": success
        }
        
        self.healing_history.append(record)
        
        # Keep only recent history
        if len(self.healing_history) > 1000:
            self.healing_history = self.healing_history[-1000:]

    def get_healing_statistics(self) -> Dict[str, Any]:
        """Get statistics about healing attempts."""
        if not self.healing_history:
            return {"total_attempts": 0, "success_rate": 0}
        
        total = len(self.healing_history)
        successful = sum(1 for record in self.healing_history if record["success"])
        
        # Group by category
        by_category = {}
        for record in self.healing_history:
            category = record["error_category"]
            if category not in by_category:
                by_category[category] = {"total": 0, "successful": 0}
            by_category[category]["total"] += 1
            if record["success"]:
                by_category[category]["successful"] += 1
        
        return {
            "total_attempts": total,
            "successful_attempts": successful,
            "success_rate": successful / total if total > 0 else 0,
            "by_category": by_category,
            "recent_failures": [
                r for r in self.healing_history[-10:] if not r["success"]
            ]
        }