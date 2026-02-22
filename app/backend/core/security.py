import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self._max_requests = max_requests
        self._window = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        window_start = now - self._window
        self._requests[key] = [t for t in self._requests[key] if t > window_start]
        if len(self._requests[key]) >= self._max_requests:
            return False
        self._requests[key].append(now)
        return True


rate_limiter = RateLimiter()
