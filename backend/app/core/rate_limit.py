import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request, status

from app.core.config import get_settings

_attempts: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


def enforce_rate_limit(request: Request, *, bucket: str, limit: int, window_seconds: int) -> None:
    if get_settings().app_env.lower() not in {"production", "prod"}:
        return
    client_host = request.client.host if request.client else "unknown"
    key = f"{bucket}:{client_host}"
    now = time.monotonic()
    cutoff = now - window_seconds
    with _lock:
        attempts = _attempts[key]
        while attempts and attempts[0] <= cutoff:
            attempts.popleft()
        if len(attempts) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests",
                headers={"Retry-After": str(window_seconds)},
            )
        attempts.append(now)