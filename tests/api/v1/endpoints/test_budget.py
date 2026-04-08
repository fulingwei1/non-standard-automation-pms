"""
Budget API endpoints tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Test client for the FastAPI app"""
    return TestClient(app)


def test_budget_endpoint_basic_access(client):
    """Test that budget endpoint is accessible"""
    # Test GET /budget endpoint (will likely require auth)
    response = client.get("/api/v1/budget/")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_budget_create_endpoint(client):
    """Test that budget create endpoint is accessible"""
    response = client.post("/api/v1/budget/", json={})
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_budget_get_by_id_endpoint(client):
    """Test that budget get by ID endpoint is accessible"""
    response = client.get("/api/v1/budget/1")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_budget_update_endpoint(client):
    """Test that budget update endpoint is accessible"""
    response = client.put("/api/v1/budget/1", json={})
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_budget_delete_endpoint(client):
    """Test that budget delete endpoint is accessible"""
    response = client.delete("/api/v1/budget/1")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_budget_search_endpoint(client):
    """Test that budget search endpoint is accessible"""
    response = client.get("/api/v1/budget/search")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_budget_allocate_endpoint(client):
    """Test that budget allocate endpoint is accessible"""
    response = client.post("/api/v1/budget/1/allocate")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404