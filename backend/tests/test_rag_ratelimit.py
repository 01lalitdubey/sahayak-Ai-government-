"""
RAG endpoint auth + rate-limit tests — Sahayak AI
=================================================
/rag/query and /rag/voice must reject anonymous callers and throttle
authenticated ones (each call spends Groq credits).
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_active_user
from app.core import config as config_module
from app.core.ratelimit import limiter
from app.database.database import get_db
from app.main import create_application


class _FakeUser:
    id = uuid.uuid4()
    is_active = True


def _client() -> TestClient:
    app = create_application()
    app.dependency_overrides[get_current_active_user] = lambda: _FakeUser()
    app.dependency_overrides[get_db] = lambda: None
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def _reset_limiter():
    limiter.reset()
    yield
    limiter.reset()


def test_rag_query_requires_auth():
    app = create_application()
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/api/v1/rag/query", json={"query": "hi", "language": "auto"})
    assert resp.status_code == 401


def test_rag_voice_requires_auth():
    app = create_application()
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/api/v1/rag/voice", files={"audio": ("a.webm", b"x", "audio/webm")})
    assert resp.status_code == 401


def test_rag_query_is_rate_limited(monkeypatch):
    monkeypatch.setattr(config_module.settings, "RAG_RATE_LIMIT", "3/minute")
    # Force the pipeline to fail fast so we exercise the limiter, not Groq.
    monkeypatch.setattr(config_module.settings, "GROQ_API_KEY", "", raising=False)
    client = _client()

    statuses = [
        client.post("/api/v1/rag/query", json={"query": "hi", "language": "auto"}).status_code
        for _ in range(5)
    ]
    # First 3 pass the limiter (then 503 RAG-disabled), the rest are 429.
    assert statuses.count(429) == 2, statuses
    assert 429 in statuses[3:]

    body = client.post("/api/v1/rag/query", json={"query": "hi", "language": "auto"}).json()
    assert body["success"] is False and body["status_code"] == 429
