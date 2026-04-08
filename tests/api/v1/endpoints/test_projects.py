"""
Project API endpoints tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Test client for the FastAPI app"""
    return TestClient(app)


def test_projects_endpoint_basic_access(client):
    """Test that projects endpoint is accessible"""
    # Test GET /projects endpoint (will likely require auth)
    response = client.get("/api/v1/projects/")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_projects_create_endpoint(client):
    """Test that projects create endpoint is accessible"""
    response = client.post("/api/v1/projects/", json={})
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_projects_get_by_id_endpoint(client):
    """Test that projects get by ID endpoint is accessible"""
    response = client.get("/api/v1/projects/1")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_projects_update_endpoint(client):
    """Test that projects update endpoint is accessible"""
    response = client.put("/api/v1/projects/1", json={})
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_projects_delete_endpoint(client):
    """Test that projects delete endpoint is accessible"""
    response = client.delete("/api/v1/projects/1")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_projects_search_endpoint(client):
    """Test that projects search endpoint is accessible"""
    response = client.get("/api/v1/projects/search")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404