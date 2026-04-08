"""
User API endpoints tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Test client for the FastAPI app"""
    return TestClient(app)


def test_users_endpoint_basic_access(client):
    """Test that users endpoint is accessible"""
    # Test GET /users endpoint (will likely require auth)
    response = client.get("/api/v1/users/")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_users_create_endpoint(client):
    """Test that users create endpoint is accessible"""
    response = client.post("/api/v1/users/", json={})
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_users_get_by_id_endpoint(client):
    """Test that users get by ID endpoint is accessible"""
    response = client.get("/api/v1/users/1")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_users_update_endpoint(client):
    """Test that users update endpoint is accessible"""
    response = client.put("/api/v1/users/1", json={})
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_users_delete_endpoint(client):
    """Test that users delete endpoint is accessible"""
    response = client.delete("/api/v1/users/1")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404