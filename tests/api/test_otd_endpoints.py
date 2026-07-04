# -*- coding: utf-8 -*-
"""
OTD 项目交付智能体 - API 端点测试

验证 5 个端点的可访问性、返回结构和核心行为：
  GET  /otd/scan                  全量扫描
  GET  /otd/scan/{project_id}     单项目全景
  GET  /otd/metrics               7 核心指标
  GET  /otd/metrics/{project_id}  单项目指标
  POST /otd/scan/run              手动触发扫描（需权限）
"""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import create_access_token
from app.models.project import Project

# 路由前缀（与 test_pmo.py 一致，用 settings.API_V1_PREFIX）
PFX = settings.API_V1_PREFIX


def _auth_headers(user) -> dict:
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


def _make_project(db, stage="S2", **overrides):
    from uuid import uuid4

    marker = uuid4().hex[:8]
    defaults = dict(
        project_code=f"OTD-API-{marker}",
        project_name="OTD API 测试项目",
        stage=stage,
        status="ST01",
        health="H1",
        progress_pct=10,
        is_active=True,
        is_archived=False,
        planned_start_date=date.today() - timedelta(days=10),
        planned_end_date=date.today() + timedelta(days=120),
    )
    defaults.update(overrides)
    project = Project(**defaults)
    db.add(project)
    db.flush()
    return project


@pytest.fixture
def admin_user(db_session):
    """建一个带 ADMIN 角色的测试用户（用于 /scan/run 权限门禁）。

    必须用 get_password_hash（password_hash NOT NULL）+ UserRole 关联 + commit，
    这样 client（独立 session）才能查到用户和角色。
    用 uuid 用户名避免跨测试冲突。
    """
    from uuid import uuid4

    from app.core.security import get_password_hash
    from app.models.user import Role, User, UserRole

    marker = uuid4().hex[:10]
    user = User(
        username=f"otd_admin_{marker}",
        password_hash=get_password_hash("otd123"),
        real_name="OTD管理员",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    # ADMIN role 可能已被其他测试建过（跨文件共享 in-memory DB），先查后建
    role = db_session.query(Role).filter(Role.role_code == "ADMIN").first()
    if role is None:
        role = Role(role_code="ADMIN", role_name="管理员")
        db_session.add(role)
        db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    db_session.commit()  # 关键：提交到 in-memory DB，client 才能查到
    return user


@pytest.fixture
def plain_user(db_session):
    """无特殊角色的普通用户。用 uuid 用户名避免跨测试冲突。"""
    from uuid import uuid4

    from app.core.security import get_password_hash
    from app.models.user import User

    marker = uuid4().hex[:10]
    user = User(
        username=f"otd_plain_{marker}",
        password_hash=get_password_hash("otd123"),
        real_name="普通用户",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()  # 关键：提交
    return user


# ============================================================
# GET /otd/scan
# ============================================================


class TestOTDScanEndpoint:
    def test_scan_returns_200_with_structure(self, client: TestClient, plain_user):
        """GET /otd/scan 返回 200 且结构正确。"""
        resp = client.get(f"{PFX}/otd/scan", headers=_auth_headers(plain_user))
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["code"] == 200
        data = body["data"]
        # 核心字段存在
        for key in ("scanned", "with_risk", "high_or_critical", "alerts_created", "projects"):
            assert key in data, f"缺少字段 {key}"
        assert isinstance(data["projects"], list)
        # 默认 create_alerts=False，不应产预警
        assert data["alerts_created"] == 0

    def test_scan_with_create_alerts_param(self, client: TestClient, plain_user, db_session):
        """create_alerts=true 时允许产预警。"""
        _make_project(db_session, stage="S3")  # 在扫描范围内
        db_session.commit()  # 提交，client 才能查到
        resp = client.get(
            f"{PFX}/otd/scan?create_alerts=true", headers=_auth_headers(plain_user)
        )
        assert resp.status_code == 200
        assert "scanned" in resp.json()["data"]


# ============================================================
# GET /otd/scan/{project_id}
# ============================================================


class TestOTDScanProjectEndpoint:
    def test_single_project_scan(self, client: TestClient, plain_user, db_session):
        """GET /otd/scan/{id} 返回单项目全景。"""
        project = _make_project(db_session)
        db_session.commit()
        resp = client.get(
            f"{PFX}/otd/scan/{project.id}", headers=_auth_headers(plain_user)
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["project_id"] == project.id
        assert data["project_code"] == project.project_code
        assert "severity" in data
        assert "risk_items" in data
        assert isinstance(data["risk_items"], list)

    def test_nonexistent_project(self, client: TestClient, plain_user):
        """不存在的项目返回 LOW + meta 错误项。"""
        resp = client.get(f"{PFX}/otd/scan/999999", headers=_auth_headers(plain_user))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["severity"] == "LOW"
        assert any(it.get("dim") == "meta" for it in data["risk_items"])


# ============================================================
# GET /otd/metrics
# ============================================================


class TestOTDMetricsEndpoint:
    def test_metrics_returns_7_indicators(self, client: TestClient, plain_user):
        """GET /otd/metrics 返回 7 个核心指标。"""
        resp = client.get(f"{PFX}/otd/metrics", headers=_auth_headers(plain_user))
        assert resp.status_code == 200, resp.text
        metrics = resp.json()["data"]["metrics"]
        expected = {
            "on_time_delivery_rate",
            "delay_days",
            "rework_count",
            "change_count",
            "margin_deviation",
            "acceptance_cycle_days",
            "customer_complaint_rate",
        }
        assert set(metrics.keys()) == expected

    def test_metrics_with_date_range(self, client: TestClient, plain_user):
        """支持 start_date/end_date 参数。"""
        resp = client.get(
            f"{PFX}/otd/metrics?start_date=2026-01-01&end_date=2026-06-30",
            headers=_auth_headers(plain_user),
        )
        assert resp.status_code == 200
        win = resp.json()["data"]["window"]
        assert win["start"] == "2026-01-01"
        assert win["end"] == "2026-06-30"


class TestOTDProjectMetricsEndpoint:
    def test_project_metrics(self, client: TestClient, plain_user, db_session):
        """GET /otd/metrics/{id} 返回单项目指标。"""
        project = _make_project(db_session)
        db_session.commit()
        resp = client.get(
            f"{PFX}/otd/metrics/{project.id}", headers=_auth_headers(plain_user)
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["project_id"] == project.id
        assert "metrics" in data

    def test_project_metrics_not_found(self, client: TestClient, plain_user):
        """不存在的项目返回 404。"""
        resp = client.get(
            f"{PFX}/otd/metrics/999999", headers=_auth_headers(plain_user)
        )
        body = resp.json()
        assert body["code"] == 404


# ============================================================
# POST /otd/scan/run（权限门禁）
# ============================================================


class TestOTDScanRunEndpoint:
    def test_admin_can_trigger(self, client: TestClient, admin_user):
        """ADMIN 角色可触发手动扫描。"""
        resp = client.post(f"{PFX}/otd/scan/run", headers=_auth_headers(admin_user))
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert "scanned" in data
        assert "alerts_created" in data

    def test_plain_user_no_role_allowed(self, client: TestClient, plain_user):
        """无角色用户也应能触发（兼容：无角色配置时放行）。

        _require_pmo_or_admin 在无角色时放行（开发环境友好）。
        这里验证至少不会 500。
        """
        resp = client.post(f"{PFX}/otd/scan/run", headers=_auth_headers(plain_user))
        assert resp.status_code in (200, 403), resp.text


# ============================================================
# 未认证拒绝
# ============================================================


class TestOTDAuthRequired:
    def test_no_token_returns_401(self, client: TestClient):
        """无 token 访问应被拒。"""
        resp = client.get(f"{PFX}/otd/scan")
        assert resp.status_code in (401, 403)
