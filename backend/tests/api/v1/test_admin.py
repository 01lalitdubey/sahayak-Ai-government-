import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_admin_overview_unauthorized(client: AsyncClient):
    """Test that unauthorized users cannot access admin overview."""
    response = await client.get("/api/v1/admin/overview")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_admin_users_unauthorized(client: AsyncClient):
    """Test that unauthorized users cannot access admin users list."""
    response = await client.get("/api/v1/admin/users")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_admin_system_health_unauthorized(client: AsyncClient):
    """Test that unauthorized users cannot access system health."""
    response = await client.get("/api/v1/admin/system/health")
    assert response.status_code == 401

# Add more tests using mock admin token if available in the testing suite
