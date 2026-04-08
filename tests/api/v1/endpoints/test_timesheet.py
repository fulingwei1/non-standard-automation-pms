"""
Timesheet API endpoints tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Test client for the FastAPI app"""
    return TestClient(app)


def test_timesheet_endpoint_basic_access(client):
    """Test that timesheet endpoint is accessible"""
    # Test GET /timesheet endpoint (will likely require auth)
    response = client.get("/api/v1/timesheet/")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_timesheet_create_endpoint(client):
    """Test that timesheet create endpoint is accessible"""
    response = client.post("/api/v1/timesheet/", json={})
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_timesheet_get_by_id_endpoint(client):
    """Test that timesheet get by ID endpoint is accessible"""
    response = client.get("/api/v1/timesheet/1")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_timesheet_update_endpoint(client):
    """Test that timesheet update endpoint is accessible"""
    response = client.put("/api/v1/timesheet/1", json={})
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_timesheet_delete_endpoint(client):
    """Test that timesheet delete endpoint is accessible"""
    response = client.delete("/api/v1/timesheet/1")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_timesheet_search_endpoint(client):
    """Test that timesheet search endpoint is accessible"""
    response = client.get("/api/v1/timesheet/search")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404


def test_timesheet_submit_endpoint(client):
    """Test that timesheet submit endpoint is accessible"""
    response = client.post("/api/v1/timesheet/1/submit")
    # Should not return 404, indicating the endpoint exists
    assert response.status_code != 404