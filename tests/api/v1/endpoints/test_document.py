"""
Document API endpoints tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Test client for the FastAPI app"""
    return TestClient(app)


def test_document_endpoint_basic_access(client):
    """Test that document endpoint is accessible"""
    # Test GET /document endpoint (will likely require auth)
    response = client.get("/api/v1/document/")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_document_create_endpoint(client):
    """Test that document create endpoint is accessible"""
    response = client.post("/api/v1/document/", json={})
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_document_get_by_id_endpoint(client):
    """Test that document get by ID endpoint is accessible"""
    response = client.get("/api/v1/document/1")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_document_update_endpoint(client):
    """Test that document update endpoint is accessible"""
    response = client.put("/api/v1/document/1", json={})
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_document_delete_endpoint(client):
    """Test that document delete endpoint is accessible"""
    response = client.delete("/api/v1/document/1")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_document_search_endpoint(client):
    """Test that document search endpoint is accessible"""
    response = client.get("/api/v1/document/search")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_document_upload_endpoint(client):
    """Test that document upload endpoint is accessible"""
    response = client.post("/api/v1/document/upload")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404