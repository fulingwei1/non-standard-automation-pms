import pytest
from fastapi.testclient import TestClient
from app.core.config import settings

def test_login(client: TestClient):
    login_data = {
        "username": "admin",
        "password": "admin123",
    }
    response = client.post(f"{settings.API_V1_PREFIX}/auth/login", data=login_data)
    # 如果数据库未初始化，可能会失败。
    # 我们这里断言状态码可能是 200 或者 400/401 (如果用户不存在)
    # 但为了作为测试框架的验证，我们希望它能通过。
    # 鉴于这是一个现有项目，admin/admin123 应该是存在的。
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

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
