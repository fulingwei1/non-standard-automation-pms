"""
Auth API endpoints tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.v1.endpoints.auth import router


@pytest.fixture
def client():
    """Test client for the FastAPI app"""
    return TestClient(app)


def test_auth_router_exists():
    """Test that auth router is properly imported and registered"""
    # This test ensures that the auth module can be imported without errors
    assert router is not None
    assert hasattr(router, 'routes')


def test_login_endpoint_exists(client):
    """Test that login endpoint is available"""
    # Test that we get a proper response structure even if authentication fails
    response = client.post("/api/v1/auth/login", json={
        "username": "test@example.com",
        "password": "testpass123"
    })
    # We expect either a proper auth response or validation error, not 404
    assert response.status_code in [200, 400, 401, 422]


def test_logout_endpoint_exists(client):
    """Test that logout endpoint is available"""
    # Test that the endpoint exists (may require auth header)
    response = client.post("/api/v1/auth/logout")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_change_password_endpoint_exists(client):
    """Test that change password endpoint is available"""
    # Test that the endpoint exists (will likely require auth and proper payload)
    response = client.put("/api/v1/auth/password")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_register_endpoint_exists(client):
    """Test that register endpoint is available"""
    response = client.post("/api/v1/auth/register")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404