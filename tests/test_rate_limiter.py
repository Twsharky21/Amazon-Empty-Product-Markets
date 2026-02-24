"""Tests for rate_limiter module."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.rate_limiter import USER_AGENTS, RateLimiter


def test_user_agents_not_empty():
    assert len(USER_AGENTS) >= 10


def test_get_user_agent_returns_string():
    rl = RateLimiter()
    ua = rl.get_user_agent()
    assert isinstance(ua, str)
    assert len(ua) > 20


def test_get_user_agent_varies():
    rl = RateLimiter()
    agents = {rl.get_user_agent() for _ in range(50)}
    assert len(agents) > 1, "User agent rotation not working"


def test_record_success_resets_failures():
    rl = RateLimiter()
    rl.record_failure()
    rl.record_failure()
    assert rl.consecutive_failures == 2
    rl.record_success()
    assert rl.consecutive_failures == 0


def test_record_failure_increments():
    rl = RateLimiter()
    rl.record_failure()
    assert rl.consecutive_failures == 1
    rl.record_failure()
    assert rl.consecutive_failures == 2


def test_wait_respects_delay_range():
    rl = RateLimiter(min_delay=0.01, max_delay=0.05)
    start = time.time()
    rl.wait()
    elapsed = time.time() - start
    assert 0.005 <= elapsed <= 0.15  # generous upper bound


def test_backoff_increases_delay():
    rl = RateLimiter(min_delay=0.01, max_delay=0.02, max_backoff=1.0)
    rl.record_failure()
    rl.record_failure()
    rl.record_failure()
    start = time.time()
    rl.wait()
    elapsed = time.time() - start
    # With 3 failures and factor 2: 0.01 * 2^3 = 0.08 + some jitter
    assert elapsed >= 0.05
