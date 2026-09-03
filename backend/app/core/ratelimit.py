"""
Rate limiting — Sahayak AI
==========================
A single shared ``Limiter`` instance (slowapi / limits).

Requests are keyed by the caller's bearer token when present, falling back
to the client IP. On protected endpoints auth runs first, so the token key
is effectively per-user; the IP fallback only matters for unauthenticated
routes that opt in.

Wire-up lives in ``app.main``: ``app.state.limiter = limiter`` plus the
``RateLimitExceeded`` handler. Apply per-route with::

    from app.core.ratelimit import limiter

    @router.post("/thing")
    @limiter.limit(settings.SOME_RATE_LIMIT)
    async def thing(request: Request, ...):
        ...

The decorated function MUST take ``request: Request`` for slowapi to find
the limiter.
"""

from __future__ import annotations

import hashlib

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def _user_or_ip_key(request: Request) -> str:
    """Bearer-token hash if the request carries one, else the client IP."""
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer ") and len(auth) > 7:
        token = auth[7:].strip()
        if token:
            return "tok:" + hashlib.sha256(token.encode("utf-8")).hexdigest()[:32]
    return "ip:" + get_remote_address(request)


limiter = Limiter(key_func=_user_or_ip_key)
