# -*- coding: utf-8 -*-
"""缺料告警服务单元测试"""
import pytest
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch, PropertyMock
from fastapi import HTTPException

from app.services.shortage.shortage_alerts_service import ShortageAlertsService


def _make_db():
    return MagicMock()


def _make_user(uid=1, name="测试用户"):
    u = MagicMock()
    u.id = uid
    u.name = name
    return u


def _make_shortage(**kw):
    s = MagicMock()
    defaults = dict(
        id=1, material_id=10, material_code="M001", material_name="螺栓",
        shortage_quantity=100, required_date=date(2025, 6, 1),
        severity="high", status="pending", shortage_reason="供应商延期",
        project_id=1, machine_id=1,
        project=MagicMock(name="项目A"), machine=MagicMock(name="机器1"),
        assigned_user=MagicMock(name="张三"),
        acknowledged_by_user=None, resolved_by_user=None,
        acknowledged_at=None, acknowledgment_note=None,
        resolved_at=None, resolution_method=None, resolution_note=None,
        actual_arrival_date=None,
        created_at=datetime(2025, 5, 1, tzinfo=timezone.utc),
        updated_at=None,
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(s, k, v)
    return s


class TestGetShortageAlerts:
    def test_returns_paginated(self):
        db = _make_db()
        shortage = _make_shortage()
        q = db.query.return_value.options.return_value
        # chain filters
        for attr in ('filter', 'order_by'):
            setattr(q, attr, MagicMock(return_value=q))
        q.count.return_value = 1
        q.offset.return_value = q
        q.limit.return_value = q
        q.all.return_value = [shortage]

        with patch("app.services.shortage.shortage_alerts_service.apply_keyword_filter", return_value=q), \
             patch("app.services.shortage.shortage_alerts_service.get_pagination_params") as gpp, \
             patch("app.services.shortage.shortage_alerts_service.apply_pagination", return_value=q):
            pag = MagicMock(page=1, page_size=20, offset=0, limit=20)
            pag.pages_for_total.return_value = 1
            gpp.return_value = pag

            svc = ShortageAlertsService(db)
            result = svc.get_shortage_alerts()
            assert result.total == 1
            assert len(result.items) == 1


class TestGetShortageAlert:
    def test_found(self):
        db = _make_db()
        shortage = _make_shortage()
        db.query.return_value.options.return_value.filter.return_value.first.return_value = shortage
        svc = ShortageAlertsService(db)
        result = svc.get_shortage_alert(1)
        assert result["id"] == 1

    def test_not_found(self):
        db = _make_db()
        db.query.return_value.options.return_value.filter.return_value.first.return_value = None
        svc = ShortageAlertsService(db)
        assert svc.get_shortage_alert(999) is None


class TestAcknowledgeShortageAlert:
    def test_success(self):
        db = _make_db()
        shortage = _make_shortage(status="pending")
        db.query.return_value.filter.return_value.first.return_value = shortage
        user = _make_user()
        svc = ShortageAlertsService(db)
        with patch.object(svc, "_send_notification"):
            result = svc.acknowledge_shortage_alert(1, user, note="已确认")
        assert result is not None
        assert shortage.status == "acknowledged"
        db.commit.assert_called()

    def test_not_pending_raises(self):
        db = _make_db()
        shortage = _make_shortage(status="acknowledged")
        db.query.return_value.filter.return_value.first.return_value = shortage
        svc = ShortageAlertsService(db)
        with pytest.raises(HTTPException):
            svc.acknowledge_shortage_alert(1, _make_user())

    def test_not_found(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = ShortageAlertsService(db)
        assert svc.acknowledge_shortage_alert(1, _make_user()) is None


class TestUpdateShortageAlert:
    def test_updates_fields(self):
        db = _make_db()
        shortage = _make_shortage()
        db.query.return_value.filter.return_value.first.return_value = shortage
        svc = ShortageAlertsService(db)
        result = svc.update_shortage_alert(1, {"severity": "critical"}, _make_user())
        assert shortage.severity == "critical"
        assert result is not None

    def test_not_found(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = ShortageAlertsService(db)
        assert svc.update_shortage_alert(1, {}, _make_user()) is None


class TestAddFollowUp:
    def test_success(self):
        db = _make_db()
        shortage = _make_shortage()
        db.query.return_value.filter.return_value.first.return_value = shortage
        follow_up_mock = MagicMock(id=10)
        with patch("app.services.shortage.shortage_alerts_service.ArrivalFollowUp", return_value=follow_up_mock):
            svc = ShortageAlertsService(db)
            result = svc.add_follow_up(1, {"follow_up_type": "call", "description": "联系供应商"}, _make_user())
        assert result["follow_up_id"] == 10
        db.add.assert_called()

    def test_not_found_raises(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = ShortageAlertsService(db)
        with pytest.raises(HTTPException):
            svc.add_follow_up(999, {"follow_up_type": "call", "description": "test"}, _make_user())


class TestGetFollowUps:
    def test_returns_list(self):
        db = _make_db()
        fu = MagicMock(
            id=1, follow_up_type="call", description="desc",
            contact_person="李四", contact_method="phone",
            scheduled_time=None, status="pending",
            created_at=datetime(2025, 5, 1, tzinfo=timezone.utc),
            completed_at=None
        )
        # MagicMock(name=...) sets mock's internal name, not .name attribute
        created_by_user = MagicMock()
        created_by_user.name = "张三"
        fu.created_by_user = created_by_user
        db.query.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = [fu]

        # Patch joinedload so it doesn't validate the (missing) relationship
        with patch("app.services.shortage.shortage_alerts_service.joinedload", lambda *a, **k: MagicMock()):
            svc = ShortageAlertsService(db)
            result = svc.get_follow_ups(1)
        assert len(result) == 1
        assert result[0]["id"] == 1


class TestResolveShortageAlert:
    def test_success(self):
        db = _make_db()
        shortage = _make_shortage(status="acknowledged")
        db.query.return_value.filter.return_value.first.return_value = shortage
        svc = ShortageAlertsService(db)
        with patch.object(svc, "_send_notification"):
            result = svc.resolve_shortage_alert(1, {"resolution_method": "采购到货"}, _make_user())
        assert shortage.status == "resolved"
        assert result is not None


class TestGetStatisticsOverview:
    def test_returns_stats(self):
        db = _make_db()
        base_q = db.query.return_value.filter.return_value
        base_q.count.return_value = 10
        base_q.with_entities.return_value.group_by.return_value.all.return_value = []
        base_q.join.return_value.with_entities.return_value.group_by.return_value.all.return_value = []
        base_q.filter.return_value.with_entities.return_value.scalar.return_value = 7200
        base_q.filter.return_value.count.return_value = 2

        svc = ShortageAlertsService(db)
        result = svc.get_statistics_overview()
        assert "total_alerts" in result
        assert "period" in result


class TestGetDashboardData:
    def test_returns_dashboard(self):
        db = _make_db()
        # All counts return 0
        db.query.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.options.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        svc = ShortageAlertsService(db)
        result = svc.get_dashboard_data()
        assert "today_summary" in result
        assert "week_trend" in result
        assert "critical_alerts" in result
