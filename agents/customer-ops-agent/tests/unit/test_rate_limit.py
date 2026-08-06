"""Unit tests for the application-level rate limiter."""

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.rate_limit import (
    RateLimitMiddleware,
    add_rate_limit_middleware,
)


def _build_client(
    *,
    enabled: bool = True,
    requests_per_window: int = 2,
) -> tuple[TestClient, MagicMock]:
    """Create a small test application with rate limiting enabled."""
    app = FastAPI()
    event_logger = MagicMock()

    @app.post("/run")
    async def run_agent() -> dict[str, str]:
        return {"status": "success"}

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy"}

    app.add_middleware(
        RateLimitMiddleware,
        enabled=enabled,
        requests_per_window=requests_per_window,
        window_seconds=60,
        event_logger=event_logger,
    )
    return TestClient(app), event_logger


def test_requests_within_limit_are_allowed() -> None:
    """Allow requests until the configured limit is exhausted."""
    client, _ = _build_client()

    first = client.post("/run")
    second = client.post("/run")

    assert first.status_code == 200
    assert first.headers["X-RateLimit-Limit"] == "2"
    assert first.headers["X-RateLimit-Remaining"] == "1"

    assert second.status_code == 200
    assert second.headers["X-RateLimit-Remaining"] == "0"


def test_request_above_limit_returns_429() -> None:
    """Reject an additional request and include retry metadata."""
    client, event_logger = _build_client()

    client.post("/run")
    client.post("/run")
    rejected = client.post("/run")

    assert rejected.status_code == 429
    assert rejected.json()["detail"] == "Request rate limit exceeded."
    assert int(rejected.headers["Retry-After"]) > 0
    assert rejected.headers["X-RateLimit-Remaining"] == "0"

    event_logger.log_struct.assert_called_once()
    event = event_logger.log_struct.call_args.args[0]

    assert event["event_type"] == "RATE_LIMIT_REJECTED"
    assert event["http_method"] == "POST"
    assert event["path"] == "/run"
    assert len(event["client_hash"]) == 12
    assert event["client_hash"] != "testclient"
    assert "prompt" not in event
    assert "response" not in event
    assert event_logger.log_struct.call_args.kwargs["severity"] == "WARNING"


def test_health_requests_are_exempt() -> None:
    """Keep health checks available regardless of request volume."""
    client, event_logger = _build_client(requests_per_window=1)

    for _ in range(5):
        response = client.get("/health")
        assert response.status_code == 200
        assert "X-RateLimit-Limit" not in response.headers

    event_logger.log_struct.assert_not_called()


def test_disabled_rate_limit_allows_all_requests() -> None:
    """Allow all requests when rate limiting is disabled."""
    client, event_logger = _build_client(
        enabled=False,
        requests_per_window=1,
    )

    for _ in range(5):
        assert client.post("/run").status_code == 200

    event_logger.log_struct.assert_not_called()


def test_environment_limit_must_be_positive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject invalid rate-limit environment configuration."""
    monkeypatch.setenv("RATE_LIMIT_REQUESTS_PER_WINDOW", "0")
    app = FastAPI()

    with pytest.raises(
        ValueError,
        match="RATE_LIMIT_REQUESTS_PER_WINDOW must be a positive integer",
    ):
        add_rate_limit_middleware(app)
