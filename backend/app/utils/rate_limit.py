"""Rate limit handling utilities for Google Gemini API."""
import re
import time
import logging
from typing import Callable, TypeVar, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


def extract_wait_seconds_from_error(error: Exception) -> Optional[float]:
    """
    Extract wait time in seconds from Google API rate limit error messages.
    Checks both the main exception and wrapped exceptions (__cause__, __context__).
    
    Common formats:
    - "Please retry in X.XXXs" (Google API format)
    - "Please retry after X seconds"
    - "quota exceeded, retry after Xs"
    - "rate limit exceeded. Retry after X seconds"
    - Error details with retry_after field
    - retry_delay { seconds: X } in nested errors
    """
    # Collect all errors to check (original + wrapped exceptions)
    errors_to_check = [error]
    
    # Check __cause__ (chained exceptions in Python 3+)
    if hasattr(error, '__cause__') and error.__cause__:
        errors_to_check.append(error.__cause__)
    
    # Check __context__ (exception context)
    if hasattr(error, '__context__') and error.__context__:
        errors_to_check.append(error.__context__)
    
    # Check if args contain nested errors
    if hasattr(error, 'args') and error.args:
        for arg in error.args:
            if isinstance(arg, Exception):
                errors_to_check.append(arg)
    
    # Pattern 1: Google API specific format "Please retry in X.XXXs"
    # Also check for retry_delay { seconds: X }
    patterns = [
        r'please\s+retry\s+in\s+(\d+(?:\.\d+)?)\s*s',  # "Please retry in 21.130789183s"
        r'retry\s+in\s+(\d+(?:\.\d+)?)\s*s(?!econds)',  # "retry in X.XXs" (but not "seconds")
        r'retry\s+in\s+(\d+(?:\.\d+)?)\s*seconds?',  # "retry in X seconds"
        r'retry\s+after\s+(\d+(?:\.\d+)?)\s*seconds?',  # "retry after X seconds"
        r'retry\s+after\s+(\d+(?:\.\d+)?)\s*s(?!econds)',  # "retry after Xs" (but not "seconds")
        r'wait\s+(\d+(?:\.\d+)?)\s*seconds?',  # "wait X seconds"
        r'(\d+(?:\.\d+)?)\s*seconds?\s*to\s*retry',  # "X seconds to retry"
        r'(\d+(?:\.\d+)?)\s*s(?!econds)\s*[^\d]',  # "X.XXs" as standalone (handles decimal seconds)
        r'retry_delay\s*\{\s*seconds:\s*(\d+)',  # "retry_delay { seconds: 23 }"
        r'seconds:\s*(\d+)',  # "seconds: 23" (from retry_delay)
    ]
    
    # Check all errors in the chain
    for err in errors_to_check:
        error_str = str(err)
        error_str_lower = error_str.lower()
        
        # First, try to extract from retry_delay { seconds: X } format (multi-line)
        retry_delay_match = re.search(r'retry_delay\s*\{[^}]*seconds:\s*(\d+)', error_str, re.IGNORECASE | re.DOTALL)
        if retry_delay_match:
            try:
                wait_time = float(retry_delay_match.group(1))
                if 0.1 <= wait_time <= 3600:
                    logger.debug(f"Extracted wait time: {wait_time} seconds from retry_delay")
                    return wait_time
            except (ValueError, IndexError, AttributeError):
                pass
        
        # Then try other patterns (for "Please retry in X.XXXs")
        for pattern in patterns:
            match = re.search(pattern, error_str, re.IGNORECASE)
            if match:
                try:
                    wait_time = float(match.group(1))
                    # Sanity check: wait time should be reasonable (0.1 second to 1 hour)
                    # Allow sub-second waits (like 21.13 seconds)
                    if 0.1 <= wait_time <= 3600:
                        logger.debug(f"Extracted wait time: {wait_time} seconds from error message")
                        return wait_time
                except (ValueError, IndexError, AttributeError):
                    continue
    
    # Check if error has retry_after attribute (some API clients provide this)
    if hasattr(error, 'retry_after'):
        try:
            wait_time = float(error.retry_after)
            if 1 <= wait_time <= 3600:
                return wait_time
        except (ValueError, TypeError):
            pass
    
    # Check error details/response if available
    if hasattr(error, 'details'):
        details = str(error.details).lower()
        for pattern in patterns:
            match = re.search(pattern, details, re.IGNORECASE)
            if match:
                try:
                    wait_time = float(match.group(1))
                    if 1 <= wait_time <= 3600:
                        return wait_time
                except (ValueError, IndexError):
                    continue
    
    return None


def is_rate_limit_error(error: Exception) -> bool:
    """
    Check if an error is a rate limit/quota error.
    Checks both the main exception and wrapped exceptions (__cause__, __context__).
    This is critical because LangChain often wraps original exceptions.
    """
    # Collect all error messages and types to check (including wrapped exceptions)
    error_messages = []
    error_types = []
    errors_to_check = []
    
    # Main error
    errors_to_check.append(error)
    error_messages.append(str(error).lower())
    error_types.append(type(error).__name__.lower())
    
    # Check __cause__ (chained exceptions in Python 3+)
    if hasattr(error, '__cause__') and error.__cause__:
        errors_to_check.append(error.__cause__)
        error_messages.append(str(error.__cause__).lower())
        error_types.append(type(error.__cause__).__name__.lower())
    
    # Check __context__ (exception context)
    if hasattr(error, '__context__') and error.__context__:
        errors_to_check.append(error.__context__)
        error_messages.append(str(error.__context__).lower())
        error_types.append(type(error.__context__).__name__.lower())
    
    # Combine all text for pattern matching
    all_text = ' '.join(error_messages)
    all_types = ' '.join(error_types)
    
    # Check for Google API specific exception types
    if 'resourceexhausted' in all_types or 'ResourceExhausted' in str(type(error)):
        return True
    
    # Check error type patterns
    rate_limit_indicators = [
        'ratelimiterror',
        'rate_limit',
        'resource_exhausted',
        'quota_exceeded',
        '429',
        'too_many_requests',
        'exceeded.*quota',
        'quota.*limit',
    ]
    
    for indicator in rate_limit_indicators:
        if indicator in all_types:
            return True
        # Check in error message
        if re.search(indicator, all_text, re.IGNORECASE):
            return True
    
    # Check HTTP status code (main error and all wrapped errors)
    for err in errors_to_check:
        if hasattr(err, 'status_code'):
            if err.status_code == 429:
                return True
    
    # Check error code/message (Google API sometimes uses code attribute)
    for err in errors_to_check:
        if hasattr(err, 'code'):
            error_code_str = str(err.code).lower()
            if err.code == 429 or 'resource_exhausted' in error_code_str:
                return True
    
    # Check for specific Google API error message patterns
    quota_patterns = [
        r'exceeded.*quota',
        r'quota.*exceeded',
        r'429.*quota',
        r'rate.*limit.*exceeded',
    ]
    for pattern in quota_patterns:
        if re.search(pattern, all_text, re.IGNORECASE):
            return True
    
    return False


def with_rate_limit_retry(
    max_retries: int = 3,
    default_wait: float = 60.0,
    backoff_multiplier: float = 1.5,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to automatically retry on rate limit errors with wait time extraction.
    
    Args:
        max_retries: Maximum number of retry attempts
        default_wait: Default wait time in seconds if wait time cannot be extracted
        backoff_multiplier: Multiplier for exponential backoff on subsequent retries
    
    Usage:
        @with_rate_limit_retry(max_retries=3, default_wait=60.0)
        def my_api_call():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_error: Optional[Exception] = None
            wait_time = default_wait
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    
                    # Check if it's a rate limit error
                    if is_rate_limit_error(e):
                        # Try to extract wait time from error
                        extracted_wait = extract_wait_seconds_from_error(e)
                        
                        if extracted_wait:
                            wait_time = extracted_wait
                            logger.warning(
                                f"⚠️  Rate limit detected! Error message suggests waiting {wait_time:.2f} seconds. "
                                f"Retrying automatically... (attempt {attempt + 1}/{max_retries + 1})"
                            )
                        else:
                            # Use exponential backoff if we can't extract wait time
                            wait_time = default_wait * (backoff_multiplier ** attempt)
                            logger.warning(
                                f"⚠️  Rate limit detected but couldn't extract wait time from error. "
                                f"Using exponential backoff: waiting {wait_time:.2f} seconds. "
                                f"(attempt {attempt + 1}/{max_retries + 1})"
                            )
                        
                        # Log the error details for debugging
                        logger.info(
                            f"Rate limit error details: {type(e).__name__}: {str(e)[:200]}"
                        )
                        
                        # Wait before retry - log prominently
                        if attempt < max_retries:
                            logger.warning(
                                f"⏳ WAITING {wait_time:.2f} SECONDS before retry due to rate limit (Google API quota exceeded)..."
                            )
                            time.sleep(wait_time)
                            logger.info(
                                f"✅ Wait complete. Retrying request now (attempt {attempt + 2}/{max_retries + 1})..."
                            )
                            continue
                        else:
                            logger.error(
                                f"Rate limit retry exhausted after {max_retries + 1} attempts. "
                                f"Last error: {type(e).__name__}: {str(e)[:200]}"
                            )
                            raise
                    else:
                        # Not a rate limit error, re-raise immediately
                        raise
            
            # Should never reach here, but just in case
            if last_error:
                raise last_error
            raise RuntimeError("Unexpected error in rate limit retry logic")
        
        return wrapper
    return decorator

