# -*- coding: utf-8 -*-
"""工程师绩效空考核周期页面合同回归。"""

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_dashboard_and_collaboration_endpoints_return_empty_state_without_active_period(
    client: TestClient, db_session: Session, admin_token: str
):
    db_session.execute(text("UPDATE performance_period SET is_active = 0"))
    db_session.commit()

    headers = _auth_headers(admin_token)

    summary_response = client.get(
        f"{settings.API_V1_PREFIX}/engineer-performance/summary/company",
        headers=headers,
    )
    assert summary_response.status_code == 200, summary_response.text
    summary = summary_response.json()["data"]
    assert summary["period_id"] is None
    assert summary["total_engineers"] == 0
    assert summary["avg_score"] == 0
    assert summary["level_distribution"] == {}
    assert summary["by_job_type"] == {}

    pending_response = client.get(
        f"{settings.API_V1_PREFIX}/engineer-performance/collaboration/pending",
        headers=headers,
    )
    assert pending_response.status_code == 200, pending_response.text
    assert pending_response.json()["data"] == []

    matrix_response = client.get(
        f"{settings.API_V1_PREFIX}/engineer-performance/collaboration/matrix",
        headers=headers,
    )
    assert matrix_response.status_code == 200, matrix_response.text
    matrix = matrix_response.json()["data"]
    assert matrix["period_id"] is None
    assert matrix["matrix"] == {}
    assert matrix["details"] == []
