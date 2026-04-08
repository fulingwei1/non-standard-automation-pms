"""
Dashboard API endpoints tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Test client for the FastAPI app"""
    return TestClient(app)


def test_dashboard_endpoint_basic_access(client):
    """Test that dashboard endpoint is accessible"""
    # Test GET /dashboard endpoint (will likely require auth)
    response = client.get("/api/v1/dashboard/")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_dashboard_create_endpoint(client):
    """Test that dashboard create endpoint is accessible"""
    response = client.post("/api/v1/dashboard/", json={})
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_dashboard_get_by_id_endpoint(client):
    """Test that dashboard get by ID endpoint is accessible"""
    response = client.get("/api/v1/dashboard/1")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_dashboard_update_endpoint(client):
    """Test that dashboard update endpoint is accessible"""
    response = client.put("/api/v1/dashboard/1", json={})
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_dashboard_delete_endpoint(client):
    """Test that dashboard delete endpoint is accessible"""
    response = client.delete("/api/v1/dashboard/1")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_dashboard_search_endpoint(client):
    """Test that dashboard search endpoint is accessible"""
    response = client.get("/api/v1/dashboard/search")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_dashboard_refresh_endpoint(client):
    """Test that dashboard refresh endpoint is accessible"""
    response = client.post("/api/v1/dashboard/1/refresh")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404