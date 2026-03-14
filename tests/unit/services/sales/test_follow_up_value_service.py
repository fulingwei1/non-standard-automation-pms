from datetime import date, datetime, timedelta
from typing import Optional

from app.models.sales import Lead, LeadFollowUp
from app.services.sales.follow_up_reminder_service import (
    FollowUpReminderService,
    ReminderType,
)


def _lead(
    code: str,
    owner_id: int,
    status: str,
    next_action_at: Optional[datetime],
    *,
    created_at: datetime,
    updated_at: Optional[datetime] = None,
    customer_name: Optional[str] = None,
) -> Lead:
    return Lead(
        lead_code=code,
        customer_name=customer_name or code,
        owner_id=owner_id,
        status=status,
        next_action_at=next_action_at,
        created_at=created_at,
        updated_at=updated_at or created_at,
    )


def test_get_due_action_digest_splits_overdue_and_upcoming(db_session):
    now = datetime.now()
    db_session.add_all(
        [
            _lead(
                "LD-DUE-001",
                owner_id=1,
                status="CONTACTED",
                next_action_at=now - timedelta(days=2),
                created_at=now - timedelta(days=10),
                customer_name="超期客户",
            ),
            _lead(
                "LD-SOON-001",
                owner_id=1,
                status="QUALIFIED",
                next_action_at=now + timedelta(days=2),
                created_at=now - timedelta(days=5),
                customer_name="临近客户",
            ),
            _lead(
                "LD-LATER-001",
                owner_id=1,
                status="NEW",
                next_action_at=now + timedelta(days=8),
                created_at=now - timedelta(days=3),
                customer_name="太远客户",
            ),
        ]
    )
    db_session.commit()

    service = FollowUpReminderService(db_session)
    digest = service.get_due_action_digest(user_id=1, window_days=3)

    assert digest["overdue_count"] == 1
    assert digest["upcoming_count"] == 1
    assert digest["total"] == 2
    assert digest["overdue"][0].type == ReminderType.OVERDUE_ACTION
    assert digest["upcoming"][0].type == ReminderType.UPCOMING_ACTION
    assert digest["overdue"][0].customer_name == "超期客户"
    assert digest["upcoming"][0].customer_name == "临近客户"


def test_get_weekly_follow_up_report_calculates_metrics(db_session):
    week_start = date(2026, 3, 9)
    base_dt = datetime(2026, 3, 9, 9, 0, 0)

    lead_overdue = _lead(
        "LD-RPT-001",
        owner_id=1,
        status="CONTACTED",
        next_action_at=datetime(2026, 3, 10, 10, 0, 0),
        created_at=base_dt - timedelta(days=2),
        updated_at=datetime(2026, 3, 11, 9, 0, 0),
        customer_name="跟进客户A",
    )
    lead_active = _lead(
        "LD-RPT-002",
        owner_id=1,
        status="QUALIFIED",
        next_action_at=datetime(2026, 3, 20, 10, 0, 0),
        created_at=base_dt - timedelta(days=1),
        updated_at=datetime(2026, 3, 12, 9, 0, 0),
        customer_name="跟进客户B",
    )
    lead_converted = _lead(
        "LD-RPT-003",
        owner_id=1,
        status="CONVERTED",
        next_action_at=None,
        created_at=base_dt - timedelta(days=4),
        updated_at=datetime(2026, 3, 12, 18, 0, 0),
        customer_name="已转化客户",
    )
    other_owner = _lead(
        "LD-RPT-004",
        owner_id=2,
        status="CONTACTED",
        next_action_at=datetime(2026, 3, 10, 10, 0, 0),
        created_at=base_dt - timedelta(days=2),
        updated_at=datetime(2026, 3, 11, 9, 0, 0),
        customer_name="别人的客户",
    )

    db_session.add_all([lead_overdue, lead_active, lead_converted, other_owner])
    db_session.flush()

    db_session.add_all(
        [
            LeadFollowUp(
                lead_id=lead_overdue.id,
                follow_up_type="CALL",
                content="首次电话",
                created_by=1,
                created_at=datetime(2026, 3, 10, 11, 0, 0),
                updated_at=datetime(2026, 3, 10, 11, 0, 0),
            ),
            LeadFollowUp(
                lead_id=lead_overdue.id,
                follow_up_type="EMAIL",
                content="补充资料",
                created_by=1,
                created_at=datetime(2026, 3, 11, 15, 0, 0),
                updated_at=datetime(2026, 3, 11, 15, 0, 0),
            ),
            LeadFollowUp(
                lead_id=lead_active.id,
                follow_up_type="MEETING",
                content="现场沟通",
                created_by=1,
                created_at=datetime(2026, 3, 12, 10, 0, 0),
                updated_at=datetime(2026, 3, 12, 10, 0, 0),
            ),
            LeadFollowUp(
                lead_id=other_owner.id,
                follow_up_type="CALL",
                content="不该计入",
                created_by=2,
                created_at=datetime(2026, 3, 12, 10, 0, 0),
                updated_at=datetime(2026, 3, 12, 10, 0, 0),
            ),
        ]
    )
    db_session.commit()

    service = FollowUpReminderService(db_session)
    report = service.get_weekly_follow_up_report(user_id=1, week_start=week_start)

    assert report["period_start"] == "2026-03-09"
    assert report["period_end"] == "2026-03-15"
    assert report["metrics"]["follow_up_count"] == 3
    assert report["metrics"]["followed_lead_count"] == 2
    assert report["metrics"]["overdue_count"] == 1
    assert report["metrics"]["converted_lead_count"] == 1
    assert report["metrics"]["conversion_rate"] == 50.0
    assert report["daily_breakdown"] == [
        {"date": "2026-03-10", "follow_up_count": 1},
        {"date": "2026-03-11", "follow_up_count": 1},
        {"date": "2026-03-12", "follow_up_count": 1},
    ]
