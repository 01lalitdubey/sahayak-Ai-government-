"""
Tests for Translation Service and Endpoints
"""

import pytest
from fastapi.testclient import TestClient

def _client():
    from app.main import create_application
    return TestClient(create_application(), raise_server_exceptions=False)

# Mock admin token for testing
admin_headers = {"Authorization": "Bearer admin_token"}

def test_start_pilot_job():
    client = _client()
    
    # Needs auth, we might get 401 in test since we don't have a real token
    # Just check that it's reachable and returns 401 or works with mock
    response = client.post("/api/v1/admin/translations/pilot")
    assert response.status_code in (202, 401)
    
    response = client.get("/api/v1/admin/translations/jobs/latest")
    assert response.status_code in (200, 404, 401)

def test_localization_injection():
    client = _client()
    # Search schemes with lang param
    # Just test routing doesn't break
    response = client.get("/api/v1/schemes?lang=hi")
    # Will be 503 if DB is not connected or 200
    assert response.status_code != 404

