# -*- coding: utf-8 -*-
"""follow_up_reminder_service 深度测试"""

from datetime import date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

from app.services.sales.follow_up_reminder_service import (
    FollowUpReminder,
    FollowUpReminderService,
    ReminderPriority,
    ReminderType,
)


class FakeQuery:
    def __init__(self, all_value=None, scalar_value=None):
        self._all_value = all_value or []
        self._scalar_value = scalar_value

    def options(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def outerjoin(self, *args, **kwargs):
        return self

    def join(self, *args, **kwargs):
        return self

    def group_by(self, *args, **kwargs):
        return self

    def subquery(self):
        return SimpleNamespace(c=SimpleNamespace(last_follow_up_at="last_follow_up_at", lead_id="lead_id"))

    def all(self):
        return self._all_value

    def scalar(self):
        return self._scalar_value


class TestFollowUpReminderServiceDeep:
    def _reminder(self, priority, days_overdue, rtype=ReminderType.NO_RECENT_FOLLOW_UP, next_action_at=None):
        return FollowUpReminder(
            type=rtype,
            priority=priority,
            entity_type="lead",
            entity_id=1,
            entity_code="L1",
            entity_name="客户A",
            customer_name="客户A",
            owner_id=1,
            owner_name="张三",
            message="msg",
            suggestion="do",
            days_overdue=days_overdue,
            last_follow_up_at=None,
            next_action_at=next_action_at,
            est_amount=None,
        )

    def test_get_reminders_for_user_sorting_filtering_and_limit(self):
        db = Mock()
        service = FollowUpReminderService(db)
        service._get_lead_overdue_reminders = Mock(return_value=[self._reminder(ReminderPriority.HIGH, 5, ReminderType.OVERDUE_ACTION)])
        service._get_lead_no_follow_up_reminders = Mock(return_value=[self._reminder(ReminderPriority.MEDIUM, 10)])
        service._get_opportunity_reminders = Mock(return_value=[self._reminder(ReminderPriority.URGENT, 2)])
        service._get_high_value_idle_reminders = Mock(return_value=[self._reminder(ReminderPriority.URGENT, 9, ReminderType.HIGH_VALUE_IDLE)])
        service._get_quote_expiring_reminders = Mock(return_value=[self._reminder(ReminderPriority.LOW, -2, ReminderType.QUOTE_EXPIRING)])

        recs = service.get_reminders_for_user(7, limit=3)
        filtered = service.get_reminders_for_user(7, include_types=[ReminderType.HIGH_VALUE_IDLE], limit=10)

        assert [r.priority for r in recs] == [ReminderPriority.URGENT, ReminderPriority.URGENT, ReminderPriority.HIGH]
        assert filtered[0].type == ReminderType.HIGH_VALUE_IDLE
        service._get_lead_overdue_reminders.assert_called_once_with(7)

    def test_get_lead_upcoming_reminders_priority_bands(self):
        now = datetime.now()
        lead1 = SimpleNamespace(id=1, lead_code="L1", customer_name="客户1", owner=SimpleNamespace(real_name="A"), status="NEW", next_action_at=now + timedelta(hours=12))
        lead2 = SimpleNamespace(id=2, lead_code="L2", customer_name="客户2", owner=None, status="CONTACTED", next_action_at=now + timedelta(hours=48))
        db = Mock()
        db.query.return_value = FakeQuery(all_value=[lead1, lead2])
        service = FollowUpReminderService(db)

        recs = service._get_lead_upcoming_reminders(1, window_days=3)

        assert len(recs) == 2
        assert recs[0].priority == ReminderPriority.HIGH
        assert recs[0].days_overdue == 0
        assert recs[1].priority == ReminderPriority.MEDIUM
        assert recs[1].days_overdue <= 0

    def test_priority_suggestion_digest_and_summary(self):
        service = FollowUpReminderService(Mock())

        assert service._calculate_priority(14, None) == ReminderPriority.URGENT
        assert service._calculate_priority(8, None) == ReminderPriority.HIGH
        assert service._calculate_priority(4, None) == ReminderPriority.MEDIUM
        assert service._calculate_priority(1, 600000.0) == ReminderPriority.URGENT
        assert "电话联系客户" in service._get_follow_up_suggestion("lead", "NEW")
        assert "准备报价方案" in service._get_follow_up_suggestion("opportunity", "PROPOSAL")
        assert service._get_follow_up_suggestion("other", "x") == "请跟进客户"

        overdue = [self._reminder(ReminderPriority.HIGH, 6, ReminderType.OVERDUE_ACTION)]
        upcoming = [self._reminder(ReminderPriority.LOW, -1, ReminderType.UPCOMING_ACTION, next_action_at=datetime.now() + timedelta(days=1))]
        service._get_lead_overdue_reminders = Mock(return_value=overdue)
        service._get_lead_upcoming_reminders = Mock(return_value=upcoming)
        digest = service.get_due_action_digest(1, window_days=3, limit=10)

        assert digest["overdue_count"] == 1
        assert digest["upcoming_count"] == 1
        assert digest["high_priority_count"] == 1
        assert digest["total"] == 2

        service.get_reminders_for_user = Mock(return_value=[
            self._reminder(ReminderPriority.URGENT, 5, ReminderType.OVERDUE_ACTION),
            self._reminder(ReminderPriority.HIGH, 4, ReminderType.NO_RECENT_FOLLOW_UP),
            self._reminder(ReminderPriority.MEDIUM, -2, ReminderType.QUOTE_EXPIRING),
            self._reminder(ReminderPriority.LOW, 1, ReminderType.HIGH_VALUE_IDLE),
        ])
        summary = service.get_summary(1)
        assert summary["total"] == 4
        assert summary["by_priority"]["urgent"] == 1
        assert summary["by_type"]["high_value_idle"] == 1
        assert summary["urgent_items"][0]["type"] == "overdue_action"

    def test_get_weekly_follow_up_report(self):
        db = Mock()
        daily_rows = [
            SimpleNamespace(follow_up_date="2026-04-06", follow_up_count=2),
            SimpleNamespace(follow_up_date="2026-04-08", follow_up_count=3),
        ]
        db.query.side_effect = [
            FakeQuery(scalar_value=5),
            FakeQuery(scalar_value=2),
            FakeQuery(scalar_value=1),
            FakeQuery(scalar_value=1),
            FakeQuery(all_value=daily_rows),
        ]
        service = FollowUpReminderService(db)

        report = service.get_weekly_follow_up_report(3, week_start=date(2026, 4, 6), week_end=date(2026, 4, 12))

        assert report["period_start"] == "2026-04-06"
        assert report["period_end"] == "2026-04-12"
        assert report["metrics"]["follow_up_count"] == 5
        assert report["metrics"]["followed_lead_count"] == 2
        assert report["metrics"]["overdue_count"] == 1
        assert report["metrics"]["converted_lead_count"] == 1
        assert report["metrics"]["conversion_rate"] == 50.0
        assert report["daily_breakdown"] == [
            {"date": "2026-04-06", "follow_up_count": 2},
            {"date": "2026-04-08", "follow_up_count": 3},
        ]
