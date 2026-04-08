"""
Supplier API endpoints tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Test client for the FastAPI app"""
    return TestClient(app)


def test_supplier_endpoint_basic_access(client):
    """Test that supplier endpoint is accessible"""
    # Test GET /supplier endpoint (will likely require auth)
    response = client.get("/api/v1/supplier/")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_supplier_create_endpoint(client):
    """Test that supplier create endpoint is accessible"""
    response = client.post("/api/v1/supplier/", json={})
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_supplier_get_by_id_endpoint(client):
    """Test that supplier get by ID endpoint is accessible"""
    response = client.get("/api/v1/supplier/1")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_supplier_update_endpoint(client):
    """Test that supplier update endpoint is accessible"""
    response = client.put("/api/v1/supplier/1", json={})
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_supplier_delete_endpoint(client):
    """Test that supplier delete endpoint is accessible"""
    response = client.delete("/api/v1/supplier/1")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_supplier_search_endpoint(client):
    """Test that supplier search endpoint is accessible"""
    response = client.get("/api/v1/supplier/search")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_supplier_approve_endpoint(client):
    """Test that supplier approve endpoint is accessible"""
    response = client.post("/api/v1/supplier/1/approve")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404