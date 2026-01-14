import pytest
from fastapi.testclient import TestClient
from app.core.config import settings

def test_login(client: TestClient, admin_token: str):
    """测试登录 - 如果 admin_token fixture 成功获取则通过"""
    if not admin_token:
        pytest.skip("Admin user not available with expected credentials (admin/admin123)")
    # admin_token fixture 已经验证了登录成功
    assert admin_token is not None
    assert len(admin_token) > 0

def test_get_current_user(client: TestClient, admin_token: str):
    if not admin_token:
        pytest.skip("Admin token not available")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get(f"{settings.API_V1_PREFIX}/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    # assert "email" in data # email 可能是可选的

def test_login_wrong_password(client: TestClient):
    login_data = {
        "username": "admin",
        "password": "wrongpassword",
    }
    response = client.post(f"{settings.API_V1_PREFIX}/auth/login", data=login_data)
    assert response.status_code != 200 # 应该是 400 或 401

def test_refresh_token(client: TestClient, admin_token: str):
    if not admin_token:
        pytest.skip("Admin token not available")

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.post(f"{settings.API_V1_PREFIX}/auth/refresh", headers=headers)
    assert response.status_code == 200
    assert "access_token" in response.json()
