import pytest
from fastapi import Request, HTTPException
from unittest.mock import Mock, AsyncMock, patch
from utils.rate_limit import RateLimiter, rate_limit


@pytest.mark.asyncio
async def test_rate_limiter_allows_under_limit():
    """Test that requests under the limit are allowed."""
    limiter = RateLimiter(max_requests=5, window_seconds=60)

    # Mock request and Redis
    request = Mock(spec=Request)
    request.client = Mock(host="192.168.1.1")
    request.app = Mock()

    redis_mock = AsyncMock()
    redis_mock.incr = AsyncMock(return_value=3)  # 3rd request
    redis_mock.expire = AsyncMock()
    request.app.state.redis = redis_mock

    # Should not raise exception
    await limiter.check_rate_limit(request, "test_endpoint")

    assert redis_mock.incr.called


@pytest.mark.asyncio
async def test_rate_limiter_blocks_over_limit():
    """Test that requests over the limit are blocked."""
    limiter = RateLimiter(max_requests=5, window_seconds=60)

    request = Mock(spec=Request)
    request.client = Mock(host="192.168.1.1")
    request.app = Mock()

    redis_mock = AsyncMock()
    redis_mock.incr = AsyncMock(return_value=6)  # Over limit
    redis_mock.expire = AsyncMock()
    request.app.state.redis = redis_mock

    with pytest.raises(HTTPException) as exc_info:
        await limiter.check_rate_limit(request, "test_endpoint")

    assert exc_info.value.status_code == 429
    assert "Demasiadas solicitudes" in exc_info.value.detail


@pytest.mark.asyncio
async def test_rate_limiter_sets_expiry_on_first_request():
    """Test that expiry is set on the first request."""
    limiter = RateLimiter(max_requests=5, window_seconds=60)

    request = Mock(spec=Request)
    request.client = Mock(host="192.168.1.1")
    request.app = Mock()

    redis_mock = AsyncMock()
    redis_mock.incr = AsyncMock(return_value=1)  # First request
    redis_mock.expire = AsyncMock()
    request.app.state.redis = redis_mock

    await limiter.check_rate_limit(request, "test_endpoint")

    assert redis_mock.expire.called
    redis_mock.expire.assert_called_once()


@pytest.mark.asyncio
async def test_rate_limiter_no_redis():
    """Test that rate limiter allows requests when Redis is not available."""
    limiter = RateLimiter(max_requests=5, window_seconds=60)

    request = Mock(spec=Request)
    request.client = Mock(host="192.168.1.1")
    request.app = Mock()
    request.app.state.redis = None  # No Redis

    # Should not raise exception even without Redis
    await limiter.check_rate_limit(request, "test_endpoint")


@pytest.mark.asyncio
async def test_rate_limiter_redis_error_continues():
    """Test that rate limiter continues on Redis errors."""
    limiter = RateLimiter(max_requests=5, window_seconds=60)

    request = Mock(spec=Request)
    request.client = Mock(host="192.168.1.1")
    request.app = Mock()

    redis_mock = AsyncMock()
    redis_mock.incr = AsyncMock(side_effect=Exception("Redis connection error"))
    request.app.state.redis = redis_mock

    # Should not raise exception even when Redis fails
    await limiter.check_rate_limit(request, "test_endpoint")


@pytest.mark.asyncio
async def test_rate_limiter_different_endpoints_separate_limits():
    """Test that different endpoints have separate rate limits."""
    limiter = RateLimiter(max_requests=5, window_seconds=60)

    request = Mock(spec=Request)
    request.client = Mock(host="192.168.1.1")
    request.app = Mock()

    redis_mock = AsyncMock()
    request.app.state.redis = redis_mock

    # Mock different counters for different endpoints
    call_count = {"endpoint1": 0, "endpoint2": 0}

    async def mock_incr(key):
        if "endpoint1" in key:
            call_count["endpoint1"] += 1
            return call_count["endpoint1"]
        else:
            call_count["endpoint2"] += 1
            return call_count["endpoint2"]

    redis_mock.incr = mock_incr
    redis_mock.expire = AsyncMock()

    # Both endpoints should have independent counters
    await limiter.check_rate_limit(request, "endpoint1")
    await limiter.check_rate_limit(request, "endpoint2")

    assert call_count["endpoint1"] == 1
    assert call_count["endpoint2"] == 1


def test_rate_limit_dependency_factory():
    """Test that the rate_limit dependency factory returns a callable."""
    dependency = rate_limit(max_requests=10, window_seconds=120, endpoint="test")

    assert callable(dependency)
