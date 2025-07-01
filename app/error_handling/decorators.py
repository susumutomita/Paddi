"""Decorators for easy integration of error handling into existing code."""

import asyncio
import functools
from typing import Any, Callable, Optional, Type, Union

from app.error_handling.intelligent_handler import ExecutionContext, SelfHealingSystem
from app.log.logger import get_logger
from app.memory.context_manager import ContextualMemory

logger = get_logger(__name__)


def with_self_healing(
    memory_manager: Optional[ContextualMemory] = None,
    max_retries: int = 3,
    error_types: Optional[list[Type[Exception]]] = None,
    fallback: Optional[Callable] = None
):
    """
    Decorator that adds self-healing capabilities to functions.
    
    Args:
        memory_manager: Optional memory manager for learning
        max_retries: Maximum number of retry attempts
        error_types: Specific error types to handle (None = handle all)
        fallback: Fallback function if all recovery fails
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            healing_system = SelfHealingSystem(memory_manager)
            
            # Create execution context
            async def operation():
                return await func(*args, **kwargs)
            
            context = ExecutionContext(
                operation=operation,
                function_name=func.__name__,
                args=args,
                kwargs=kwargs
            )
            
            try:
                return await operation()
            except Exception as e:
                # Check if we should handle this error type
                if error_types and not any(isinstance(e, et) for et in error_types):
                    raise
                
                try:
                    # Attempt self-healing
                    context.retry_count = 0
                    for attempt in range(max_retries):
                        try:
                            context.retry_count = attempt + 1
                            result = await healing_system.handle_error(e, context)
                            logger.info(f"Self-healing successful for {func.__name__}")
                            return result
                        except Exception as retry_error:
                            if attempt == max_retries - 1:
                                raise retry_error
                            logger.warning(f"Retry {attempt + 1} failed: {retry_error}")
                            
                except Exception as final_error:
                    # Use fallback if provided
                    if fallback:
                        logger.info(f"Using fallback for {func.__name__}")
                        return await fallback(*args, **kwargs)
                    raise final_error
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            healing_system = SelfHealingSystem(memory_manager)
            
            # Create execution context
            def operation():
                return func(*args, **kwargs)
            
            context = ExecutionContext(
                operation=operation,
                function_name=func.__name__,
                args=args,
                kwargs=kwargs
            )
            
            try:
                return operation()
            except Exception as e:
                # Check if we should handle this error type
                if error_types and not any(isinstance(e, et) for et in error_types):
                    raise
                
                try:
                    # For sync functions, we need to run async healing in event loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        # Convert sync operation to async
                        async def async_operation():
                            return operation()
                        
                        context.operation = async_operation
                        result = loop.run_until_complete(
                            healing_system.handle_error(e, context)
                        )
                        logger.info(f"Self-healing successful for {func.__name__}")
                        return result
                    finally:
                        loop.close()
                        
                except Exception as final_error:
                    # Use fallback if provided
                    if fallback:
                        logger.info(f"Using fallback for {func.__name__}")
                        return fallback(*args, **kwargs)
                    raise final_error
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def auto_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Simple retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_attempts}): {e}"
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts")
                        raise
            
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_attempts}): {e}"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts")
                        raise
            
            raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def handle_specific_errors(
    handlers: dict[Type[Exception], Callable[[Exception], Any]]
):
    """
    Decorator that handles specific exceptions with custom handlers.
    
    Args:
        handlers: Dictionary mapping exception types to handler functions
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Find matching handler
                for exc_type, handler in handlers.items():
                    if isinstance(e, exc_type):
                        if asyncio.iscoroutinefunction(handler):
                            return await handler(e)
                        else:
                            return handler(e)
                # No handler found, re-raise
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Find matching handler
                for exc_type, handler in handlers.items():
                    if isinstance(e, exc_type):
                        return handler(e)
                # No handler found, re-raise
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_errors(
    level: str = "ERROR",
    include_traceback: bool = True,
    notify: Optional[Callable[[Exception], None]] = None
):
    """
    Decorator that logs errors with optional notification.
    
    Args:
        level: Log level (ERROR, WARNING, etc.)
        include_traceback: Whether to include full traceback
        notify: Optional function to call for notifications
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                import traceback
                
                log_func = getattr(logger, level.lower(), logger.error)
                
                if include_traceback:
                    log_func(
                        f"Error in {func.__name__}: {e}\n"
                        f"Traceback:\n{traceback.format_exc()}"
                    )
                else:
                    log_func(f"Error in {func.__name__}: {e}")
                
                if notify:
                    try:
                        if asyncio.iscoroutinefunction(notify):
                            await notify(e)
                        else:
                            notify(e)
                    except Exception as notify_error:
                        logger.error(f"Notification failed: {notify_error}")
                
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                import traceback
                
                log_func = getattr(logger, level.lower(), logger.error)
                
                if include_traceback:
                    log_func(
                        f"Error in {func.__name__}: {e}\n"
                        f"Traceback:\n{traceback.format_exc()}"
                    )
                else:
                    log_func(f"Error in {func.__name__}: {e}")
                
                if notify:
                    try:
                        notify(e)
                    except Exception as notify_error:
                        logger.error(f"Notification failed: {notify_error}")
                
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator