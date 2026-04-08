"""
Procurement API endpoints tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Test client for the FastAPI app"""
    return TestClient(app)


def test_procurement_endpoint_basic_access(client):
    """Test that procurement endpoint is accessible"""
    # Test GET /procurement endpoint (will likely require auth)
    response = client.get("/api/v1/procurement/")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_procurement_create_endpoint(client):
    """Test that procurement create endpoint is accessible"""
    response = client.post("/api/v1/procurement/", json={})
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_procurement_get_by_id_endpoint(client):
    """Test that procurement get by ID endpoint is accessible"""
    response = client.get("/api/v1/procurement/1")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_procurement_update_endpoint(client):
    """Test that procurement update endpoint is accessible"""
    response = client.put("/api/v1/procurement/1", json={})
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_procurement_delete_endpoint(client):
    """Test that procurement delete endpoint is accessible"""
    response = client.delete("/api/v1/procurement/1")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_procurement_search_endpoint(client):
    """Test that procurement search endpoint is accessible"""
    response = client.get("/api/v1/procurement/search")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_procurement_approve_endpoint(client):
    """Test that procurement approve endpoint is accessible"""
    response = client.post("/api/v1/procurement/1/approve")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404