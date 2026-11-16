"""Access control and bounded, per-process admission for the hosted demonstration.

The counters are intentionally not described as a global spending budget: serverless
replicas and cold starts have separate state. The secret access code is the primary
barrier against anonymous paid model calls. No uploaded content is stored here.
"""

import hmac
import math
import threading
import time
from collections import deque
from contextlib import asynccontextmanager

from .config import Settings
from .errors import AppError


class DemoAccess:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._lock = threading.Lock()
        self._started: deque[float] = deque()
        self._active = 0

    def authorize(self, authorization: str) -> None:
        if not self.settings.public_demo:
            return
        if not self.settings.demo_access_configured:
            raise AppError(
                "demo_unavailable",
                "Live analysis is unavailable. You can still preview logs and open saved examples.",
                503,
            )
        expected = self.settings.demo_access_code.strip().encode("utf-8")
        supplied = authorization.removeprefix("Bearer ").encode("utf-8")
        if not authorization.startswith("Bearer ") or not hmac.compare_digest(supplied, expected):
            raise AppError(
                "demo_access_required",
                "Enter a valid demo access code to run live AI analysis.",
                401,
                {"WWW-Authenticate": "Bearer"},
            )

    @asynccontextmanager
    async def admit(self):
        if not self.settings.public_demo:
            yield
            return
        now = time.monotonic()
        with self._lock:
            while self._started and now - self._started[0] >= 60:
                self._started.popleft()
            if len(self._started) >= self.settings.demo_requests_per_minute:
                retry = max(1, math.ceil(60 - (now - self._started[0])))
                raise AppError(
                    "demo_rate_limited",
                    "This demo is receiving too many analyses. Please try again shortly.",
                    429,
                    {"Retry-After": str(retry)},
                )
            if self._active >= self.settings.demo_max_concurrent:
                raise AppError(
                    "demo_busy",
                    "Another analysis is running. Please try again shortly.",
                    429,
                    {"Retry-After": "5"},
                )
            self._started.append(now)
            self._active += 1
        try:
            yield
        finally:
            with self._lock:
                self._active -= 1
