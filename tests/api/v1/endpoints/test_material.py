"""
Material API endpoints tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Test client for the FastAPI app"""
    return TestClient(app)


def test_material_endpoint_basic_access(client):
    """Test that material endpoint is accessible"""
    # Test GET /material endpoint (will likely require auth)
    response = client.get("/api/v1/material/")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_material_create_endpoint(client):
    """Test that material create endpoint is accessible"""
    response = client.post("/api/v1/material/", json={})
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_material_get_by_id_endpoint(client):
    """Test that material get by ID endpoint is accessible"""
    response = client.get("/api/v1/material/1")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_material_update_endpoint(client):
    """Test that material update endpoint is accessible"""
    response = client.put("/api/v1/material/1", json={})
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_material_delete_endpoint(client):
    """Test that material delete endpoint is accessible"""
    response = client.delete("/api/v1/material/1")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_material_search_endpoint(client):
    """Test that material search endpoint is accessible"""
    response = client.get("/api/v1/material/search")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_material_inventory_endpoint(client):
    """Test that material inventory endpoint is accessible"""
    response = client.get("/api/v1/material/inventory")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404