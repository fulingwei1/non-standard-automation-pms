# -*- coding: utf-8 -*-
"""Required-query read-only route regressions."""

from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.engineer_performance import EngineerProfile
from app.models.material import Material
from app.models.performance import PerformancePeriod
from app.models.project import Project
from app.models.user import User


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _admin_user(db: Session) -> User:
    return db.query(User).filter(User.username == "admin").first()


def test_project_status_material_search_and_reminders_do_not_500(
    client: TestClient, admin_token: str, db_session: Session
):
    admin = _admin_user(db_session)
    project = db_session.query(Project).first()
    suffix = uuid4().hex[:8]

    material = Material(
        material_code=f"RQ-MAT-{suffix}",
        material_name=f"必填查询测试物料-{suffix}",
        specification="required-query regression",
        current_stock=5,
        safety_stock=1,
        standard_price=10,
        unit="件",
        created_by=admin.id,
    )
    db_session.add(material)

    period = PerformancePeriod(
        period_code=f"RQ{suffix[:8].upper()}",
        period_name="必填查询回归周期",
        period_type="MONTHLY",
        start_date=date.today(),
        end_date=date.today(),
        status="ACTIVE",
        is_active=True,
    )
    db_session.add(period)

    if not db_session.query(EngineerProfile).filter(EngineerProfile.user_id == admin.id).first():
        db_session.add(
            EngineerProfile(
                user_id=admin.id,
                job_type="TEST",
                job_level="junior",
                job_start_date=date.today(),
            )
        )

    db_session.commit()
    headers = _auth_headers(admin_token)

    project_status = client.get(
        f"{settings.API_V1_PREFIX}/projects/status",
        params={"project_id": project.id},
        headers=headers,
        follow_redirects=False,
    )
    assert project_status.status_code == 200, project_status.text

    material_search = client.get(
        f"{settings.API_V1_PREFIX}/materials/search",
        params={"keyword": "必填查询测试物料"},
        headers=headers,
        follow_redirects=False,
    )
    assert material_search.status_code == 200, material_search.text
    assert any(
        item["material_code"] == material.material_code
        for item in material_search.json()["items"]
    )

    reminders = client.get(
        f"{settings.API_V1_PREFIX}/engineer-performance/data-integrity/reminders",
        params={"period_id": period.id},
        headers=headers,
        follow_redirects=False,
    )
    assert reminders.status_code == 200, reminders.text
    assert isinstance(reminders.json()["data"], list)


def test_strategy_review_routes_tolerate_legacy_json_lists(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    strategy_code = f"RQ-STR-{suffix}"

    db_session.execute(
        text(
            """
            INSERT INTO strategies (
                code,
                name,
                year,
                status,
                is_active,
                created_at,
                updated_at
            )
            VALUES (
                :code,
                :name,
                2026,
                'ACTIVE',
                1,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {"code": strategy_code, "name": "Required Query Strategy"},
    )
    strategy_id = db_session.execute(
        text("SELECT id FROM strategies WHERE code = :code"),
        {"code": strategy_code},
    ).scalar_one()
    db_session.execute(
        text(
            """
            INSERT INTO strategy_reviews (
                strategy_id,
                review_type,
                review_date,
                review_period,
                decisions,
                action_items,
                attendees,
                is_active,
                created_at,
                updated_at
            )
            VALUES (
                :strategy_id,
                'MONTHLY',
                CURRENT_DATE,
                '2026-06',
                '["保持当前方向"]',
                '["补齐周报数据"]',
                '["张三", "李四"]',
                1,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {"strategy_id": strategy_id},
    )
    db_session.commit()

    headers = _auth_headers(admin_token)
    response = client.get(
        f"{settings.API_V1_PREFIX}/strategy/reviews",
        params={"strategy_id": strategy_id},
        headers=headers,
        follow_redirects=False,
    )
    assert response.status_code == 200, response.text
    item = response.json()["items"][0]
    assert item["decisions"] == [{"content": "保持当前方向"}]
    assert item["action_items"] == [{"content": "补齐周报数据"}]
    assert item["attendees"] == []
    assert item["attendee_names"] == ["张三", "李四"]


def test_report_required_query_routes_return_successful_empty_reports(
    client: TestClient, admin_token: str
):
    headers = _auth_headers(admin_token)

    rd_personnel = client.get(
        f"{settings.API_V1_PREFIX}/report-center/rd-expense/rd-personnel",
        params={"year": 2026},
        headers=headers,
        follow_redirects=False,
    )
    assert rd_personnel.status_code == 200, rd_personnel.text

    rd_export = client.get(
        f"{settings.API_V1_PREFIX}/report-center/rd-expense/rd-export",
        params={"report_type": "auxiliary-ledger", "year": 2026, "format": "xlsx"},
        headers=headers,
        follow_redirects=False,
    )
    assert rd_export.status_code == 200, rd_export.text
    assert "spreadsheet" in rd_export.headers["content-type"]
    assert rd_export.content

    meeting_monthly = client.get(
        f"{settings.API_V1_PREFIX}/management-rhythm/reports-unified/meeting-monthly",
        params={"year": 2026, "month": 6},
        headers=headers,
        follow_redirects=False,
    )
    assert meeting_monthly.status_code == 200, meeting_monthly.text


def test_presale_required_period_routes_reject_invalid_period_without_500(
    client: TestClient, admin_token: str
):
    headers = _auth_headers(admin_token)

    # 2026-07-03 去重：/presale-analytics 重复前缀已下线，仅保留 /presales
    for prefix in ("/presales",):
        resource_waste = client.get(
            f"{settings.API_V1_PREFIX}{prefix}/resource-waste-analysis",
            params={"period": "测试"},
            headers=headers,
            follow_redirects=False,
        )
        assert resource_waste.status_code == 422, resource_waste.text

        ranking = client.get(
            f"{settings.API_V1_PREFIX}{prefix}/salesperson-ranking",
            params={"period": "测试"},
            headers=headers,
            follow_redirects=False,
        )
        assert ranking.status_code == 422, ranking.text
