"""
Acceptance API endpoints tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Test client for the FastAPI app"""
    return TestClient(app)


def test_acceptance_endpoint_basic_access(client):
    """Test that acceptance endpoint is accessible"""
    # Test GET /acceptance endpoint (will likely require auth)
    response = client.get("/api/v1/acceptance/")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_acceptance_create_endpoint(client):
    """Test that acceptance create endpoint is accessible"""
    response = client.post("/api/v1/acceptance/", json={})
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_acceptance_get_by_id_endpoint(client):
    """Test that acceptance get by ID endpoint is accessible"""
    response = client.get("/api/v1/acceptance/1")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_acceptance_update_endpoint(client):
    """Test that acceptance update endpoint is accessible"""
    response = client.put("/api/v1/acceptance/1", json={})
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_acceptance_delete_endpoint(client):
    """Test that acceptance delete endpoint is accessible"""
    response = client.delete("/api/v1/acceptance/1")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_acceptance_search_endpoint(client):
    """Test that acceptance search endpoint is accessible"""
    response = client.get("/api/v1/acceptance/search")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404