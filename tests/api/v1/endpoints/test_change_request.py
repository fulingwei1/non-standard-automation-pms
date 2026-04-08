"""
Change Request API endpoints tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Test client for the FastAPI app"""
    return TestClient(app)


def test_change_request_endpoint_basic_access(client):
    """Test that change request endpoint is accessible"""
    # Test GET /change-request endpoint (will likely require auth)
    response = client.get("/api/v1/change-request/")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_change_request_create_endpoint(client):
    """Test that change request create endpoint is accessible"""
    response = client.post("/api/v1/change-request/", json={})
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_change_request_get_by_id_endpoint(client):
    """Test that change request get by ID endpoint is accessible"""
    response = client.get("/api/v1/change-request/1")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_change_request_update_endpoint(client):
    """Test that change request update endpoint is accessible"""
    response = client.put("/api/v1/change-request/1", json={})
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_change_request_delete_endpoint(client):
    """Test that change request delete endpoint is accessible"""
    response = client.delete("/api/v1/change-request/1")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_change_request_search_endpoint(client):
    """Test that change request search endpoint is accessible"""
    response = client.get("/api/v1/change-request/search")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_change_request_approve_endpoint(client):
    """Test that change request approve endpoint is accessible"""
    response = client.post("/api/v1/change-request/1/approve")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404