"""Simple in-memory sliding-window rate limiter.

Used to throttle expensive LLM endpoints (Claude calls cost real $).
Single-process only — if we scale horizontally swap for Redis later.

Usage:
    from services.rate_limit import enforce_rate_limit
    await enforce_rate_limit(request, key="summary", limit=20, window_s=60)
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

from fastapi import HTTPException, Request

# (endpoint_key, identifier) -> deque[timestamp_s]
_BUCKETS: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)


def _identifier(request: Request) -> str:
    """Authed user takes priority; else fall back to client IP."""
    user = getattr(request.state, "user", None)
    if user and isinstance(user, dict) and user.get("user_id"):
        return f"u:{user['user_id']}"
    fwd = request.headers.get("x-forwarded-for") or ""
    ip = fwd.split(",")[0].strip() or (request.client.host if request.client else "anon")
    return f"ip:{ip}"


async def enforce_rate_limit(
    request: Request,
    *,
    key: str,
    limit: int,
    window_s: int,
    user_id: str | None = None,
) -> None:
    """Raise 429 if the caller has exceeded `limit` calls in the last `window_s` seconds."""
    ident = f"u:{user_id}" if user_id else _identifier(request)
    bucket_key = (key, ident)
    bucket = _BUCKETS[bucket_key]
    now = time.monotonic()
    cutoff = now - window_s
    while bucket and bucket[0] < cutoff:
        bucket.popleft()
    if len(bucket) >= limit:
        retry_after = max(1, int(window_s - (now - bucket[0])))
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded ({limit}/{window_s}s). Retry in {retry_after}s.",
            headers={"Retry-After": str(retry_after)},
        )
    bucket.append(now)
