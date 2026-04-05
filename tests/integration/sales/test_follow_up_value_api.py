from datetime import date, datetime, timedelta
from types import SimpleNamespace

from app.core import security
from app.models.sales import Lead, LeadFollowUp


def test_follow_up_action_board_api(client, db_session, admin_auth_headers):
    owner = SimpleNamespace(id=99101, username="followup_api_owner")
    client.app.dependency_overrides[security.get_current_active_user] = lambda: owner
    now = datetime.now()

    try:
        db_session.add_all(
            [
                Lead(
                    lead_code="LD-API-001",
                    customer_name="超期接口客户",
                    owner_id=owner.id,
                    status="CONTACTED",
                    next_action_at=now - timedelta(days=1),
                    created_at=now - timedelta(days=7),
                    updated_at=now - timedelta(days=1),
                ),
                Lead(
                    lead_code="LD-API-002",
                    customer_name="临近接口客户",
                    owner_id=owner.id,
                    status="QUALIFIED",
                    next_action_at=now + timedelta(days=2),
                    created_at=now - timedelta(days=5),
                    updated_at=now,
                ),
            ]
        )
        db_session.commit()

        response = client.get(
            "/api/v1/sales/follow-up/reminders/action-board",
            params={"window_days": 3},
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        payload = response.json()
        overdue_codes = {item["entity_code"] for item in payload["data"]["overdue"]}
        upcoming_codes = {item["entity_code"] for item in payload["data"]["upcoming"]}

        assert payload["code"] == 200
        assert payload["data"]["overdue_count"] == 1
        assert payload["data"]["upcoming_count"] == 1
        assert overdue_codes == {"LD-API-001"}
        assert upcoming_codes == {"LD-API-002"}
    finally:
        client.app.dependency_overrides.pop(security.get_current_active_user, None)


def test_weekly_follow_up_report_api(client, db_session, admin_auth_headers):
    owner = SimpleNamespace(id=99102, username="followup_report_owner")
    client.app.dependency_overrides[security.get_current_active_user] = lambda: owner
    week_start = date(2030, 1, 7)

    try:
        lead_a = Lead(
            lead_code="LD-API-RPT-001",
            customer_name="报表客户A",
            owner_id=owner.id,
            status="CONTACTED",
            next_action_at=datetime(2030, 1, 8, 9, 0, 0),
            created_at=datetime(2030, 1, 6, 9, 0, 0),
            updated_at=datetime(2030, 1, 9, 9, 0, 0),
        )
        lead_b = Lead(
            lead_code="LD-API-RPT-002",
            customer_name="报表客户B",
            owner_id=owner.id,
            status="CONVERTED",
            next_action_at=None,
            created_at=datetime(2030, 1, 6, 9, 0, 0),
            updated_at=datetime(2030, 1, 10, 18, 0, 0),
        )
        db_session.add_all([lead_a, lead_b])
        db_session.flush()

        db_session.add_all(
            [
                LeadFollowUp(
                    lead_id=lead_a.id,
                    follow_up_type="CALL",
                    content="电话回访",
                    created_by=owner.id,
                    created_at=datetime(2030, 1, 8, 10, 0, 0),
                    updated_at=datetime(2030, 1, 8, 10, 0, 0),
                ),
                LeadFollowUp(
                    lead_id=lead_a.id,
                    follow_up_type="EMAIL",
                    content="发送资料",
                    created_by=owner.id,
                    created_at=datetime(2030, 1, 9, 14, 0, 0),
                    updated_at=datetime(2030, 1, 9, 14, 0, 0),
                ),
            ]
        )
        db_session.commit()

        response = client.get(
            "/api/v1/sales/follow-up/reports/weekly",
            params={"week_start": week_start.isoformat()},
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        payload = response.json()
        metrics = payload["data"]["metrics"]

        assert payload["code"] == 200
        assert payload["data"]["period_start"] == "2030-01-07"
        assert payload["data"]["period_end"] == "2030-01-13"
        assert metrics["follow_up_count"] == 2
        assert metrics["followed_lead_count"] == 1
        assert metrics["overdue_count"] == 0
        assert metrics["converted_lead_count"] == 1
        assert metrics["conversion_rate"] == 100.0
    finally:
        client.app.dependency_overrides.pop(security.get_current_active_user, None)
