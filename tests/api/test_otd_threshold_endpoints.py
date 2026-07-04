# -*- coding: utf-8 -*-
"""
OTD 阈值配置 API 端点测试

- GET /otd/thresholds  返回当前配置（任意登录用户）
- PUT /otd/thresholds  更新配置（PMO/管理员）
- PUT 部分更新
- 权限：普通用户可读不可改（有角色时）
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.models.user import Role, User, UserRole

PFX = settings.API_V1_PREFIX


def _auth_headers(user) -> dict:
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_user(db_session):
    marker = uuid4().hex[:10]
    user = User(
        username=f"otd_thr_admin_{marker}",
        password_hash=get_password_hash("otd123"),
        real_name="阈值管理员",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    # ADMIN role 可能已被其他测试建过，先查后建（幂等）
    role = db_session.query(Role).filter(Role.role_code == "ADMIN").first()
    if role is None:
        role = Role(role_code="ADMIN", role_name="管理员")
        db_session.add(role)
        db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    db_session.commit()
    return user


@pytest.fixture
def plain_user(db_session):
    marker = uuid4().hex[:10]
    user = User(
        username=f"otd_thr_plain_{marker}",
        password_hash=get_password_hash("otd123"),
        real_name="普通用户",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


class TestGetThresholds:
    def test_get_returns_config_structure(self, client: TestClient, plain_user):
        """GET 返回完整配置结构（字段齐全、类型正确）。

        不硬断言具体数值——因为同 module 的 PUT 测试可能已改过默认值
        （in-memory DB 在 module scope 共享）。只验证结构和合理性。
        """
        resp = client.get(f"{PFX}/otd/thresholds", headers=_auth_headers(plain_user))
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        # 核心字段存在
        for key in (
            "scan_limit",
            "stages_in_delivery",
            "procurement_overdue_high_days",
            "open_items_high_count",
            "status_sets",
        ):
            assert key in data, f"缺少字段 {key}"
        # 类型合理
        assert isinstance(data["scan_limit"], int)
        assert isinstance(data["stages_in_delivery"], list)
        assert isinstance(data["status_sets"], dict)
        assert "issue_closed" in data["status_sets"]

    def test_get_no_auth_returns_401(self, client: TestClient):
        """无 token 拒绝。"""
        resp = client.get(f"{PFX}/otd/thresholds")
        assert resp.status_code in (401, 403)


class TestUpdateThresholds:
    def test_admin_can_update(self, client: TestClient, admin_user):
        """ADMIN 可更新，且立即生效。"""
        resp = client.put(
            f"{PFX}/otd/thresholds",
            headers=_auth_headers(admin_user),
            json={"procurement_overdue_high_days": 5, "open_items_high_count": 8},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["procurement_overdue_high_days"] == 5
        assert data["open_items_high_count"] == 8
        # 未改的字段保持默认
        assert data["procurement_overdue_medium_days"] == 7

    def test_update_partial_then_read(self, client: TestClient, admin_user):
        """PUT 后再 GET 值变了。"""
        client.put(
            f"{PFX}/otd/thresholds",
            headers=_auth_headers(admin_user),
            json={"margin_critical_threshold": -8},
        )
        resp = client.get(f"{PFX}/otd/thresholds", headers=_auth_headers(admin_user))
        assert resp.json()["data"]["margin_critical_threshold"] == -8

    def test_status_sets_update(self, client: TestClient, admin_user):
        """JSON 字段 status_sets 也能更新。"""
        new_sets = {
            "issue_closed": ["RESOLVED", "COMPLETED", "CLOSED", "DONE", "ARCHIVED"],
            "change_closed": ["COMPLETED", "CLOSED", "REJECTED"],
            "payment_pending": ["PENDING"],
            "milestone_completed": ["COMPLETED", "DONE"],
        }
        resp = client.put(
            f"{PFX}/otd/thresholds",
            headers=_auth_headers(admin_user),
            json={"status_sets": new_sets},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status_sets"] == new_sets
