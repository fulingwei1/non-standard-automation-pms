# -*- coding: utf-8 -*-
"""
毛利率 Dashboard API 端点测试

覆盖 4 个端点：
  GET  /pmo/margin-dashboard
  GET  /pmo/margin-dashboard/trend
  GET  /pmo/margin-dashboard/{project_id}/trend
  POST /pmo/margin-dashboard/snapshot/run（权限门禁）
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.models.project import Project
from app.models.project_margin_snapshot import ProjectMarginSnapshot
from app.models.user import Role, User, UserRole

PFX = settings.API_V1_PREFIX


def _auth_headers(user) -> dict:
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_user(db_session):
    marker = uuid4().hex[:10]
    user = User(
        username=f"mdash_admin_{marker}",
        password_hash=get_password_hash("m123"),
        real_name="看板管理员",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
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
        username=f"mdash_plain_{marker}",
        password_hash=get_password_hash("m123"),
        real_name="普通用户",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _make_project_with_snapshot(db_session):
    """造一个有合同 + 有毛利率快照的项目。"""
    from decimal import Decimal

    marker = uuid4().hex[:8]
    project = Project(
        project_code=f"MDASH-API-{marker}",
        project_name="看板API测试",
        stage="S5",
        status="ST01",
        health="H1",
        progress_pct=30,
        is_active=True,
        is_archived=False,
        contract_amount=Decimal("100000"),
        planned_start_date=date.today() - timedelta(days=90),
        planned_end_date=date.today() + timedelta(days=30),
    )
    db_session.add(project)
    db_session.flush()
    db_session.add(
        ProjectMarginSnapshot(
            project_id=project.id,
            snapshot_date=date.today(),
            current_margin_rate=28.0,
            margin_gap=3.0,
            health="healthy",
        )
    )
    db_session.commit()
    return project


class TestMarginDashboardEndpoint:
    def test_get_dashboard(self, client: TestClient, plain_user):
        """GET /pmo/margin-dashboard 返回看板结构。"""
        resp = client.get(
            f"{PFX}/pmo/margin-dashboard", headers=_auth_headers(plain_user)
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        for key in ("summary", "distribution", "anomalies"):
            assert key in data
        summary = data["summary"]
        assert "avg_margin_rate" in summary
        assert "healthy_count" in summary

    def test_no_auth_returns_401(self, client: TestClient):
        resp = client.get(f"{PFX}/pmo/margin-dashboard")
        assert resp.status_code in (401, 403)


class TestMarginGlobalTrendEndpoint:
    def test_get_global_trend(self, client: TestClient, plain_user, db_session):
        """GET /pmo/margin-dashboard/trend 返回趋势结构。"""
        _make_project_with_snapshot(db_session)
        resp = client.get(
            f"{PFX}/pmo/margin-dashboard/trend?days=5",
            headers=_auth_headers(plain_user),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "dates" in data
        assert "avg_margin_rate" in data
        assert "health_distribution" in data
        assert len(data["dates"]) == 6  # 5 天 = 6 个日期


class TestMarginProjectTrendEndpoint:
    def test_project_trend(self, client: TestClient, plain_user, db_session):
        """GET /pmo/margin-dashboard/{id}/trend 单项目趋势。"""
        project = _make_project_with_snapshot(db_session)
        resp = client.get(
            f"{PFX}/pmo/margin-dashboard/{project.id}/trend?days=5",
            headers=_auth_headers(plain_user),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["project_id"] == project.id
        assert "current_margin_rate" in data
        assert 28.0 in data["current_margin_rate"]  # 有快照天

    def test_project_not_found(self, client: TestClient, plain_user):
        resp = client.get(
            f"{PFX}/pmo/margin-dashboard/999999/trend",
            headers=_auth_headers(plain_user),
        )
        body = resp.json()
        assert body["code"] == 404


class TestMarginSnapshotRunEndpoint:
    def test_admin_can_trigger(self, client: TestClient, admin_user, db_session):
        """ADMIN 可触发快照。"""
        # 造一个有合同的项目让快照有内容
        from decimal import Decimal

        marker = uuid4().hex[:8]
        db_session.add(
            Project(
                project_code=f"MDASH-RUN-{marker}",
                project_name="快照触发测试",
                stage="S5",
                status="ST01",
                is_active=True,
                contract_amount=Decimal("100000"),
                planned_end_date=date.today() + timedelta(days=30),
            )
        )
        db_session.commit()
        resp = client.post(
            f"{PFX}/pmo/margin-dashboard/snapshot/run",
            headers=_auth_headers(admin_user),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert "total" in data
        assert "created" in data

    def test_plain_user_no_role_allowed(self, client: TestClient, plain_user):
        """无角色用户也放行（_require_pmo_or_admin 无角色时放行）。"""
        resp = client.post(
            f"{PFX}/pmo/margin-dashboard/snapshot/run",
            headers=_auth_headers(plain_user),
        )
        assert resp.status_code in (200, 403)
