"""
Milestone API endpoints tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Test client for the FastAPI app"""
    return TestClient(app)


def test_milestone_endpoint_basic_access(client):
    """Test that milestone endpoint is accessible"""
    # Test GET /milestone endpoint (will likely require auth)
    response = client.get("/api/v1/milestone/")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_milestone_create_endpoint(client):
    """Test that milestone create endpoint is accessible"""
    response = client.post("/api/v1/milestone/", json={})
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_milestone_get_by_id_endpoint(client):
    """Test that milestone get by ID endpoint is accessible"""
    response = client.get("/api/v1/milestone/1")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_milestone_update_endpoint(client):
    """Test that milestone update endpoint is accessible"""
    response = client.put("/api/v1/milestone/1", json={})
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_milestone_delete_endpoint(client):
    """Test that milestone delete endpoint is accessible"""
    response = client.delete("/api/v1/milestone/1")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_milestone_search_endpoint(client):
    """Test that milestone search endpoint is accessible"""
    response = client.get("/api/v1/milestone/search")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_milestone_complete_endpoint(client):
    """Test that milestone complete endpoint is accessible"""
    response = client.post("/api/v1/milestone/1/complete")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404