"""HTTP client with retry logic and rate limiting."""
import httpx
import time
from typing import Optional, Dict, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

# Rate limiting
_last_request_time: dict[str, float] = {}
_min_request_interval = 1.0  # Minimum seconds between requests per domain (increased to avoid rate limiting)


def get_client(timeout: Optional[float] = 30.0) -> httpx.Client:
    """
    Get HTTP client with retry logic.
    
    Args:
        timeout: Request timeout in seconds
    
    Returns:
        Configured httpx client
    """
    return httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers={
            "User-Agent": "DatasetPortal-Collector/1.0"
        }
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException, httpx.HTTPStatusError))
)
def make_request_with_retry(
    client: httpx.Client,
    method: str,
    url: str,
    headers: Optional[dict] = None,
    **kwargs
) -> httpx.Response:
    """
    Make HTTP request with retry logic and rate limiting.
    
    Args:
        client: HTTP client
        method: HTTP method
        url: Request URL
        **kwargs: Additional request parameters
    
    Returns:
        HTTP response
    """
    # Rate limiting
    domain = httpx.URL(url).host
    current_time = time.time()
    
    if domain in _last_request_time:
        time_since_last = current_time - _last_request_time[domain]
        if time_since_last < _min_request_interval:
            time.sleep(_min_request_interval - time_since_last)
    
    _last_request_time[domain] = time.time()
    
    # Merge headers if provided
    if headers:
        if "headers" in kwargs:
            kwargs["headers"].update(headers)
        else:
            kwargs["headers"] = headers
    
    # Make request
    try:
        response = client.request(method, url, **kwargs)
        # Only raise for 4xx and 5xx errors, not for 3xx (handled by follow_redirects)
        if response.status_code >= 400:
            response.raise_for_status()
        return response
    except httpx.HTTPStatusError as e:
        # Log error but let retry handle it
        if e.response.status_code == 429:  # Rate limit
            time.sleep(5)  # Wait longer for rate limit
        raise

