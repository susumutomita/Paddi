"""Tests for the intelligent error handling and self-healing system."""

import asyncio
import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.error_handling.decorators import (
    auto_retry,
    handle_specific_errors,
    log_errors,
    with_self_healing,
)
from app.error_handling.intelligent_handler import (
    ErrorAnalysis,
    ErrorCategory,
    ExecutionContext,
    IntelligentErrorHandler,
    RetryWithBackoffStrategy,
    SelfHealingSystem,
)
from app.error_handling.specific_handlers import (
    APILimitHandler,
    ErrorHandlerRegistry,
    NetworkErrorHandler,
    PermissionHandler,
    ResourceErrorHandler,
)
from app.memory.context_manager import ContextualMemory


class TestIntelligentErrorHandler:
    """Test intelligent error handler functionality."""

    def test_error_classification(self):
        """Test error classification."""
        handler = IntelligentErrorHandler()
        
        # Test API limit error
        error = Exception("Rate limit exceeded for API")
        analysis = handler.analyze_error(error, {})
        assert analysis.category == ErrorCategory.API_LIMIT
        assert analysis.severity == "HIGH"
        
        # Test permission error
        error = Exception("Permission denied: requires compute.instances.list")
        analysis = handler.analyze_error(error, {})
        assert analysis.category == ErrorCategory.PERMISSION
        assert analysis.severity == "CRITICAL"
        
        # Test network error
        error = Exception("Connection timeout to googleapis.com")
        analysis = handler.analyze_error(error, {})
        assert analysis.category == ErrorCategory.NETWORK
        assert analysis.severity == "MEDIUM"

    def test_severity_determination(self):
        """Test severity determination logic."""
        handler = IntelligentErrorHandler()
        
        # Test high retry count increases severity
        error = Exception("Network connection failed")
        analysis = handler.analyze_error(error, {"retry_count": 3})
        assert analysis.severity == "HIGH"
        
        # Test validation error has low severity
        error = Exception("Invalid request: bad parameter")
        analysis = handler.analyze_error(error, {})
        assert analysis.severity == "LOW"

    def test_root_cause_extraction(self):
        """Test root cause extraction."""
        handler = IntelligentErrorHandler()
        
        # Test quota error
        error = Exception("Quota exceeded for resource")
        analysis = handler.analyze_error(error, {})
        assert "quota" in analysis.root_cause.lower()
        
        # Test memory error
        error = Exception("Out of memory: cannot allocate")
        analysis = handler.analyze_error(error, {})
        assert "memory" in analysis.root_cause.lower()


class TestRecoveryStrategies:
    """Test recovery strategy implementations."""

    @pytest.mark.asyncio
    async def test_retry_with_backoff(self):
        """Test retry with exponential backoff."""
        strategy = RetryWithBackoffStrategy(max_retries=2, initial_delay=0.1)
        
        # Test retryable error
        error = Exception("Rate limit exceeded")
        assert strategy.can_handle(error)
        
        # Test successful retry
        call_count = 0
        async def failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return "success"
        
        context = {"operation": failing_operation}
        result = await strategy.execute(error, context)
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_all_attempts_fail(self):
        """Test retry when all attempts fail."""
        strategy = RetryWithBackoffStrategy(max_retries=2, initial_delay=0.01)
        
        async def always_failing():
            raise Exception("Permanent failure")
        
        context = {"operation": always_failing}
        with pytest.raises(Exception, match="Permanent failure"):
            await strategy.execute(Exception("Test"), context)


class TestSelfHealingSystem:
    """Test self-healing system integration."""

    @pytest.mark.asyncio
    async def test_handle_error_with_recovery(self):
        """Test error handling with successful recovery."""
        memory = ContextualMemory()
        healing_system = SelfHealingSystem(memory)
        
        # Create a context with retryable operation
        call_count = 0
        async def retryable_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Rate limit exceeded")
            return "recovered"
        
        context = ExecutionContext(operation=retryable_operation)
        error = Exception("Rate limit exceeded")
        
        result = await healing_system.handle_error(error, context)
        assert result == "recovered"
        
        # Check that solution was recorded
        solution = memory.get_error_solution("Rate limit reached")
        assert solution is not None

    @pytest.mark.asyncio
    async def test_handle_error_all_strategies_fail(self):
        """Test when all recovery strategies fail."""
        healing_system = SelfHealingSystem()
        
        async def always_failing():
            raise Exception("Unrecoverable error")
        
        context = ExecutionContext(operation=always_failing)
        error = Exception("Unrecoverable error")
        
        with pytest.raises(Exception, match="Unrecoverable"):
            await healing_system.handle_error(error, context)

    def test_healing_statistics(self):
        """Test healing statistics tracking."""
        healing_system = SelfHealingSystem()
        
        # Record some healing attempts
        analysis = ErrorAnalysis(
            category=ErrorCategory.API_LIMIT,
            severity="HIGH",
            root_cause="Rate limit",
            context={}
        )
        
        healing_system._record_healing(analysis, None, success=True)
        healing_system._record_healing(analysis, None, success=False)
        
        stats = healing_system.get_healing_statistics()
        assert stats["total_attempts"] == 2
        assert stats["successful_attempts"] == 1
        assert stats["success_rate"] == 0.5


class TestSpecificHandlers:
    """Test specific error handlers."""

    @pytest.mark.asyncio
    async def test_api_limit_handler(self):
        """Test API limit handler."""
        handler = APILimitHandler()
        
        error = Exception("429 Too Many Requests. Retry after 60")
        result = await handler.handle_rate_limit("gemini", error)
        
        assert result["action"] == "retry"
        assert result["wait_time"] == 60  # Extracted from error message

    @pytest.mark.asyncio
    async def test_permission_handler(self):
        """Test permission handler."""
        handler = PermissionHandler()
        
        error = Exception("Permission denied: requires compute.instances.list permission")
        result = await handler.handle_permission_error("compute", error)
        
        assert result["error_type"] == "permission"
        assert result["missing_permission"] == "compute.instances.list"
        assert len(result["required_roles"]) > 0
        assert len(result["fix_commands"]) > 0

    @pytest.mark.asyncio
    async def test_network_error_handler(self):
        """Test network error handler."""
        handler = NetworkErrorHandler()
        
        error = Exception("Connection timeout")
        result = await handler.handle_network_error(error)
        
        assert result["error_type"] == "network"
        assert "connectivity" in result
        assert result["retry_recommended"] is True

    @pytest.mark.asyncio
    async def test_resource_error_handler(self):
        """Test resource error handler."""
        handler = ResourceErrorHandler()
        
        error = Exception("Out of memory")
        result = await handler.handle_resource_error(error, {})
        
        assert result["error_type"] == "resource"
        assert result["resource"] == "memory"
        assert len(result["optimization_strategies"]) > 0


class TestDecorators:
    """Test error handling decorators."""

    @pytest.mark.asyncio
    async def test_with_self_healing_decorator(self):
        """Test self-healing decorator."""
        call_count = 0
        
        @with_self_healing(max_retries=2)
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary error")
            return "success"
        
        result = await flaky_function()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_auto_retry_decorator(self):
        """Test auto retry decorator."""
        attempt_count = 0
        
        @auto_retry(max_attempts=3, delay=0.01)
        async def retryable_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ValueError("Retry me")
            return "success"
        
        result = await retryable_function()
        assert result == "success"
        assert attempt_count == 3

    def test_handle_specific_errors_decorator(self):
        """Test specific error handler decorator."""
        def handle_value_error(e):
            return f"Handled: {e}"
        
        @handle_specific_errors({ValueError: handle_value_error})
        def may_fail(should_fail=False):
            if should_fail:
                raise ValueError("Test error")
            return "success"
        
        # Test normal execution
        assert may_fail() == "success"
        
        # Test error handling
        assert may_fail(should_fail=True) == "Handled: Test error"

    def test_log_errors_decorator(self):
        """Test error logging decorator."""
        with patch("app.error_handling.decorators.logger") as mock_logger:
            @log_errors(level="ERROR", include_traceback=False)
            def failing_function():
                raise RuntimeError("Test error")
            
            with pytest.raises(RuntimeError):
                failing_function()
            
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert "failing_function" in call_args
            assert "Test error" in call_args


class TestErrorHandlerRegistry:
    """Test error handler registry."""

    def test_get_handler(self):
        """Test getting specific handlers."""
        registry = ErrorHandlerRegistry()
        
        assert isinstance(registry.get_handler("api_limit"), APILimitHandler)
        assert isinstance(registry.get_handler("permission"), PermissionHandler)
        assert isinstance(registry.get_handler("network"), NetworkErrorHandler)
        assert isinstance(registry.get_handler("resource"), ResourceErrorHandler)
        assert registry.get_handler("unknown") is None

    @pytest.mark.asyncio
    async def test_handle_specific_error(self):
        """Test handling specific error types."""
        registry = ErrorHandlerRegistry()
        
        # Test API limit handling
        error = Exception("Rate limit exceeded")
        result = await registry.handle_specific_error(
            "api_limit", error, {"service": "gemini"}
        )
        assert result is not None
        assert result["action"] == "retry"


class TestIntegration:
    """Integration tests for error handling system."""

    @pytest.mark.asyncio
    async def test_end_to_end_error_recovery(self):
        """Test complete error handling flow."""
        memory = ContextualMemory()
        healing_system = SelfHealingSystem(memory)
        
        # Simulate a service with rate limit
        request_count = 0
        
        async def api_call():
            nonlocal request_count
            request_count += 1
            if request_count < 3:
                raise Exception("429 Rate limit exceeded")
            return {"data": "success"}
        
        @with_self_healing(memory_manager=memory)
        async def service_function():
            return await api_call()
        
        # First call should eventually succeed after retries
        result = await service_function()
        assert result == {"data": "success"}
        
        # Check that learning occurred
        assert len(memory.error_patterns) > 0
        assert len(memory.successful_solutions) > 0