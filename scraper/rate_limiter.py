"""
Rate Limiter — Manages request pacing, User-Agent rotation, and backoff.
"""

import logging
import random
import time

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 OPR/110.0.0.0",
]


class RateLimiter:
    """
    Controls request pacing with random delays, exponential backoff on
    failures, and rotating User-Agent strings.
    """

    def __init__(
        self,
        min_delay: float = 1.0,
        max_delay: float = 3.0,
        max_backoff: float = 60.0,
        backoff_factor: float = 2.0,
    ):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_backoff = max_backoff
        self.backoff_factor = backoff_factor
        self._consecutive_failures = 0

    def get_user_agent(self) -> str:
        """Return a randomly selected User-Agent string."""
        return random.choice(USER_AGENTS)

    def wait(self) -> None:
        """Sleep for an appropriate duration based on current failure state."""
        if self._consecutive_failures > 0:
            backoff = min(
                self.min_delay * (self.backoff_factor ** self._consecutive_failures),
                self.max_backoff,
            )
            delay = backoff + random.uniform(0, 1)
            logger.warning(
                "Backoff delay: %.1fs (consecutive failures: %d)",
                delay,
                self._consecutive_failures,
            )
        else:
            delay = random.uniform(self.min_delay, self.max_delay)

        time.sleep(delay)

    def record_success(self) -> None:
        """Reset failure counter on success."""
        self._consecutive_failures = 0

    def record_failure(self) -> None:
        """Increment failure counter for backoff calculation."""
        self._consecutive_failures += 1
        logger.warning("Failure recorded. Consecutive failures: %d", self._consecutive_failures)

    @property
    def consecutive_failures(self) -> int:
        return self._consecutive_failures
