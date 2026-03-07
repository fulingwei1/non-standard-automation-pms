from datetime import datetime

from fastapi.testclient import TestClient


def test_api_health_check(client: TestClient):
    """GET /api/health should be public and return health payload."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

    # Ensure timestamp is a valid ISO-8601 datetime string
    parsed = datetime.fromisoformat(data["timestamp"])
    assert isinstance(parsed, datetime)


def test_legacy_health_check_still_available(client: TestClient):
    """Existing /health endpoint should remain unchanged."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
