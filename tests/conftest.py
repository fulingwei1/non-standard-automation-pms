import sys
from unittest.mock import MagicMock

# Mock redis module before importing app
redis_mock = MagicMock()
sys.modules["redis"] = redis_mock
sys.modules["redis.exceptions"] = MagicMock()

import pytest
from typing import Generator
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
def admin_token(client: TestClient) -> str:
    """
    获取管理员 token
    注意：这里假设数据库中已经有了 admin 用户。
    如果是在隔离的测试环境中，应该先创建 admin 用户。
    由于目前我们没有隔离数据库，这里尝试直接登录。
    """
    login_data = {
        "username": "admin",
        "password": "admin123",  # 假设默认密码
    }
    r = client.post(f"{settings.API_V1_PREFIX}/auth/login", data=login_data)
    if r.status_code == 200:
        return r.json()["access_token"]
    else:
        # 如果登录失败，可能是因为数据库没有初始化或者密码不对
        # 这里我们可以选择跳过或者抛出错误
        # 为了健壮性，这里先返回 None，测试用例中再处理
        return None

@pytest.fixture(scope="module")
def normal_user_token(client: TestClient) -> str:
    """获取普通用户 token"""
    login_data = {
        "username": "user",
        "password": "user123",  # 假设默认密码
    }
    r = client.post(f"{settings.API_V1_PREFIX}/auth/login", data=login_data)
    if r.status_code == 200:
        return r.json()["access_token"]
    else:
        return None

@pytest.fixture(scope="module")
def sales_user_token(client: TestClient) -> str:
    """获取销售用户 token"""
    login_data = {
        "username": "sales",
        "password": "sales123",  # 假设默认密码
    }
    r = client.post(f"{settings.API_V1_PREFIX}/auth/login", data=login_data)
    if r.status_code == 200:
        return r.json()["access_token"]
    else:
        return None

@pytest.fixture(scope="module")
def finance_user_token(client: TestClient) -> str:
    """获取财务用户 token"""
    login_data = {
        "username": "finance",
        "password": "finance123",  # 假设默认密码
    }
    r = client.post(f"{settings.API_V1_PREFIX}/auth/login", data=login_data)
    if r.status_code == 200:
        return r.json()["access_token"]
    else:
        return None
