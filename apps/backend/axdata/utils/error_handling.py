"""Robust error handling with retry and circuit breaker."""
from __future__ import annotations
from typing import Any, Callable, Dict, Optional, Type
import time
import logging
from functools import wraps
from collections import defaultdict

logger = logging.getLogger(__name__)

# Circuit breaker state
_circuit_breaker_state: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
    "failures": 0,
    "last_failure": None,
    "state": "closed",  # closed, open, half_open
    "opened_at": None
})


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    retry_exceptions: tuple = (Exception,)
):
    """
    Decorator for retry with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        retry_exceptions: Tuple of exceptions to retry on
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except retry_exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_attempts}): {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                        delay = min(delay * exponential_base, max_delay)
                    else:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
            
            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: Type[Exception] = Exception
):
    """
    Circuit breaker decorator.
    
    Prevents calling a function if it has failed too many times recently.
    
    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before trying again (half-open state)
        expected_exception: Exception type to track
    """
    def decorator(func: Callable) -> Callable:
        func_id = f"{func.__module__}.{func.__name__}"
        state = _circuit_breaker_state[func_id]
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            
            # Check circuit state
            if state["state"] == "open":
                # Check if recovery timeout has passed
                if state["opened_at"] and (current_time - state["opened_at"]) >= recovery_timeout:
                    logger.info(f"Circuit breaker for {func_id} entering half-open state")
                    state["state"] = "half_open"
                    state["failures"] = 0
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker is open for {func_id}. "
                        f"Too many failures ({state['failures']}). "
                        f"Will retry after {recovery_timeout}s"
                    )
            
            # Try to call function
            try:
                result = func(*args, **kwargs)
                
                # Success: reset failures if in half-open, close circuit
                if state["state"] == "half_open":
                    logger.info(f"Circuit breaker for {func_id} closing (success in half-open)")
                    state["state"] = "closed"
                    state["failures"] = 0
                elif state["state"] == "closed":
                    # Reset failures on success
                    state["failures"] = 0
                
                return result
            
            except expected_exception as e:
                # Failure: increment counter
                state["failures"] += 1
                state["last_failure"] = current_time
                
                if state["failures"] >= failure_threshold:
                    state["state"] = "open"
                    state["opened_at"] = current_time
                    logger.error(
                        f"Circuit breaker for {func_id} opened after {state['failures']} failures. "
                        f"Will retry after {recovery_timeout}s"
                    )
                
                raise
        
        return wrapper
    return decorator


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


def reset_circuit_breaker(func_id: str):
    """Reset circuit breaker state for a function."""
    if func_id in _circuit_breaker_state:
        _circuit_breaker_state[func_id] = {
            "failures": 0,
            "last_failure": None,
            "state": "closed",
            "opened_at": None
        }
        logger.info(f"Circuit breaker reset for {func_id}")


def get_circuit_breaker_state(func_id: str) -> Dict[str, Any]:
    """Get current circuit breaker state."""
    return _circuit_breaker_state[func_id].copy()
