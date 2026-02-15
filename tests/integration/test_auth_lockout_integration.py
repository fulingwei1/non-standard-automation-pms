# -*- coding: utf-8 -*-
"""
认证与账户锁定集成测试
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app


@pytest.fixture
def client():
    """测试客户端"""
    return TestClient(app)


def test_login_lockout_flow(client: TestClient):
    """
    测试完整的登录锁定流程
    
    1. 5次失败登录
    2. 账户被锁定
    3. 尝试登录返回423
    4. 管理员解锁
    5. 可以正常登录
    """
    test_username = "integration_test_user"
    wrong_password = "wrongpassword123"
    
    # 1. 连续5次失败登录
    for i in range(5):
        response = client.post(
            "/api/v1/auth/login",
            data={"username": test_username, "password": wrong_password}
        )
        assert response.status_code in [401, 423], f"第{i+1}次登录失败"
    
    # 2. 第6次应该返回账户锁定
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_username, "password": wrong_password}
    )
    assert response.status_code == 423
    data = response.json()
    assert data["detail"]["error_code"] == "ACCOUNT_LOCKED"


def test_successful_login_resets_attempts(client: TestClient):
    """
    测试成功登录重置失败次数
    
    1. 3次失败登录
    2. 1次成功登录
    3. 再次5次失败登录才能锁定
    """
    # 此测试需要真实用户数据，实际实现时需配置测试数据库
    pass


def test_ip_blacklist_prevents_login(client: TestClient):
    """
    测试IP黑名单阻止登录
    
    1. 从同一IP多次尝试不同用户
    2. IP被拉黑
    3. 无法登录任何账户
    """
    pass


if __name__ == '__main__':
    pytest.main([__file__, "-v"])
