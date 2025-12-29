"""
Rate limiting middleware using Redis.
Provides DDoS protection and API abuse prevention.
"""
import time
import logging
from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

import redis.asyncio as redis

logger = logging.getLogger("rate-limiter")


class RateLimiter:
    """Redis-based rate limiter using sliding window algorithm."""
    
    def __init__(
        self,
        redis_url: str = "redis://redis:6379/0",
        default_limit: int = 100,
        default_window: int = 60,
    ):
        self.redis_url = redis_url
        self.default_limit = default_limit  # requests per window
        self.default_window = default_window  # window in seconds
        self._client: Optional[redis.Redis] = None
        
        # Endpoint-specific limits
        self.endpoint_limits = {
            # Auth endpoints - stricter limits
            "/api/auth/login": (10, 60),      # 10 per minute
            "/api/auth/signup": (5, 60),       # 5 per minute
            "/api/auth/forgot-password": (3, 60),  # 3 per minute
            
            # Call creation - moderate limits
            "/api/calls": (30, 60),            # 30 per minute
            
            # Regular endpoints
            "default": (100, 60),              # 100 per minute
        }
    
    async def connect(self) -> None:
        """Connect to Redis."""
        if self._client is None:
            try:
                self._client = redis.from_url(self.redis_url, decode_responses=True)
                await self._client.ping()
                logger.info("RateLimiter connected to Redis")
            except Exception as e:
                logger.warning(f"RateLimiter Redis connection failed: {e}")
                self._client = None
    
    async def is_allowed(self, key: str, limit: int, window: int) -> tuple[bool, int, int]:
        """
        Check if request is allowed under rate limit.
        
        Returns:
            (allowed, remaining, reset_time)
        """
        if self._client is None:
            await self.connect()
        
        if self._client is None:
            # Redis unavailable, allow request (fail open)
            return True, limit, 0
        
        try:
            now = int(time.time())
            window_key = f"ratelimit:{key}:{now // window}"
            
            # Increment counter
            count = await self._client.incr(window_key)
            
            # Set expiry on first request
            if count == 1:
                await self._client.expire(window_key, window + 1)
            
            remaining = max(0, limit - count)
            reset_time = (now // window + 1) * window
            
            return count <= limit, remaining, reset_time
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True, limit, 0  # Fail open
    
    def get_limit_for_path(self, path: str) -> tuple[int, int]:
        """Get rate limit configuration for a path."""
        # Check exact match
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]
        
        # Check prefix match
        for endpoint, limits in self.endpoint_limits.items():
            if endpoint != "default" and path.startswith(endpoint):
                return limits
        
        return self.endpoint_limits["default"]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""
    
    def __init__(self, app, rate_limiter: RateLimiter):
        super().__init__(app)
        self.limiter = rate_limiter
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/api/health"]:
            return await call_next(request)
        
        # Get client identifier (IP or user ID if authenticated)
        client_ip = request.client.host if request.client else "unknown"
        
        # Check for X-Forwarded-For header (behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        # Build rate limit key
        path = request.url.path
        limit, window = self.limiter.get_limit_for_path(path)
        key = f"{client_ip}:{path}"
        
        # Check rate limit
        allowed, remaining, reset_time = await self.limiter.is_allowed(key, limit, window)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for {client_ip} on {path}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(reset_time - int(time.time())),
                },
            )
        
        # Process request and add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response


# Create singleton instance
rate_limiter = RateLimiter()
