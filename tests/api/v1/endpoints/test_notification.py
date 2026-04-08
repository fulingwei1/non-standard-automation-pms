"""
Notification API endpoints tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Test client for the FastAPI app"""
    return TestClient(app)


def test_notification_endpoint_basic_access(client):
    """Test that notification endpoint is accessible"""
    # Test GET /notification endpoint (will likely require auth)
    response = client.get("/api/v1/notification/")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_notification_create_endpoint(client):
    """Test that notification create endpoint is accessible"""
    response = client.post("/api/v1/notification/", json={})
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_notification_get_by_id_endpoint(client):
    """Test that notification get by ID endpoint is accessible"""
    response = client.get("/api/v1/notification/1")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_notification_update_endpoint(client):
    """Test that notification update endpoint is accessible"""
    response = client.put("/api/v1/notification/1", json={})
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_notification_delete_endpoint(client):
    """Test that notification delete endpoint is accessible"""
    response = client.delete("/api/v1/notification/1")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_notification_search_endpoint(client):
    """Test that notification search endpoint is accessible"""
    response = client.get("/api/v1/notification/search")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_notification_send_endpoint(client):
    """Test that notification send endpoint is accessible"""
    response = client.post("/api/v1/notification/1/send")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404