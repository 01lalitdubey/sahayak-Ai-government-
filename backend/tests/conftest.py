"""
Shared pytest fixtures — Sahayak AI backend
"""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import create_application

# test_nllb_provider.py rebinds sys.modules['torch'] / sys.modules['transformers']
# at import time and never restores them, which breaks unrelated tests later in
# the session. Skip collecting it until it is rewritten with monkeypatch fixtures.
collect_ignore = ["test_nllb_provider.py"]


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """Async HTTP client bound to a fresh app instance (no live DB)."""
    app = create_application()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c
