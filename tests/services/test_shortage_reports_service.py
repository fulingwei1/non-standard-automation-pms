# -*- coding: utf-8 -*-
"""缺料报告服务单元测试"""
import pytest
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

from app.models.shortage import ShortageReport

# Patch relationship attributes that don't exist on the model class
# but are used in joinedload() calls in the service
for _attr in ('reporter', 'confirmer', 'handler', 'resolver'):
    if not hasattr(ShortageReport, _attr):
        setattr(ShortageReport, _attr, MagicMock())

from app.services.shortage.shortage_reports_service import (
    ShortageReportsService,
    calculate_alert_statistics,
    calculate_report_statistics,
    calculate_kit_statistics,
    calculate_arrival_statistics,
    calculate_response_time_statistics,
    calculate_stoppage_statistics,
    build_daily_report_data,
)


def _make_db():
    return MagicMock()


def _make_user(uid=1):
    u = MagicMock()
    u.id = uid
    return u


def _make_report(**kw):
    r = MagicMock()
    defaults = dict(
        id=1, title="缺料报告1", description="desc", status="pending",
        reporter=MagicMock(), confirmer=None, handler=None, resolver=None,
        created_at=datetime(2025, 5, 1, tzinfo=timezone.utc),
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(r, k, v)
    return r


class TestShortageReportsServiceGetList:
    def test_get_shortage_reports(self):
        db = _make_db()
        q = db.query.return_value.options.return_value
        for attr in ('filter', 'order_by'):
            setattr(q, attr, MagicMock(return_value=q))
        q.count.return_value = 0
        q.all.return_value = []

        with patch("app.services.shortage.shortage_reports_service.joinedload", lambda *a, **k: MagicMock()), \
             patch("app.services.shortage.shortage_reports_service.apply_keyword_filter", return_value=q), \
             patch("app.services.shortage.shortage_reports_service.get_pagination_params") as gpp, \
             patch("app.services.shortage.shortage_reports_service.apply_pagination", return_value=q):
            pag = MagicMock(page=1, page_size=20, offset=0, limit=20)
            pag.pages_for_total.return_value = 0
            gpp.return_value = pag

            svc = ShortageReportsService(db)
            result = svc.get_shortage_reports()
            assert result.total == 0


class TestCreateShortageReport:
    def test_create(self):
        db = _make_db()
        report_data = MagicMock(
            title="test", description="desc", material_id=1,
            shortage_quantity=10, shortage_reason="供应商", 
            impact_assessment="高", expected_arrival_date=date(2025, 7, 1)
        )
        svc = ShortageReportsService(db)
        with patch("app.services.shortage.shortage_reports_service.ShortageReport") as MockReport:
            instance = MagicMock()
            MockReport.return_value = instance
            result = svc.create_shortage_report(report_data, _make_user())
        db.add.assert_called_once()
        db.commit.assert_called_once()


class TestGetShortageReport:
    def test_found(self):
        db = _make_db()
        report = _make_report()
        db.query.return_value.options.return_value.filter.return_value.first.return_value = report
        svc = ShortageReportsService(db)
        with patch("app.services.shortage.shortage_reports_service.joinedload", lambda *a, **k: MagicMock()):
            assert svc.get_shortage_report(1) is report

    def test_not_found(self):
        db = _make_db()
        db.query.return_value.options.return_value.filter.return_value.first.return_value = None
        svc = ShortageReportsService(db)
        with patch("app.services.shortage.shortage_reports_service.joinedload", lambda *a, **k: MagicMock()):
            assert svc.get_shortage_report(999) is None


class TestConfirmShortageReport:
    def test_confirm(self):
        db = _make_db()
        report = _make_report(status="pending")
        svc = ShortageReportsService(db)
        with patch.object(svc, "get_shortage_report", return_value=report):
            result = svc.confirm_shortage_report(1, _make_user())
        assert report.status == "confirmed"
        db.commit.assert_called()

    def test_not_found(self):
        db = _make_db()
        svc = ShortageReportsService(db)
        with patch.object(svc, "get_shortage_report", return_value=None):
            assert svc.confirm_shortage_report(999, _make_user()) is None


class TestHandleShortageReport:
    def test_handle(self):
        db = _make_db()
        report = _make_report()
        svc = ShortageReportsService(db)
        with patch.object(svc, "get_shortage_report", return_value=report):
            result = svc.handle_shortage_report(1, {"handling_method": "加急采购"}, _make_user())
        assert report.status == "handling"


class TestResolveShortageReport:
    def test_resolve(self):
        db = _make_db()
        report = _make_report()
        svc = ShortageReportsService(db)
        with patch.object(svc, "get_shortage_report", return_value=report):
            result = svc.resolve_shortage_report(1, {"resolution_method": "到货"}, _make_user())
        assert report.status == "resolved"


# --- Module-level functions ---

class TestCalculateAlertStatistics:
    def test_basic(self):
        db = _make_db()
        base_q = db.query.return_value.filter.return_value
        base_q.count.return_value = 5
        base_q.filter.return_value.count.return_value = 2
        result = calculate_alert_statistics(db, date(2025, 5, 1))
        assert "new_alerts" in result
        assert "level_counts" in result


class TestCalculateReportStatistics:
    def test_basic(self):
        db = _make_db()
        db.query.return_value.filter.return_value.scalar.return_value = 3
        result = calculate_report_statistics(db, date(2025, 5, 1))
        assert "new_reports" in result


class TestCalculateKitStatistics:
    def test_no_checks(self):
        db = _make_db()
        db.query.return_value.filter.return_value.all.return_value = []
        result = calculate_kit_statistics(db, date(2025, 5, 1))
        assert result["total_work_orders"] == 0
        assert result["kit_rate"] == 0.0

    def test_with_checks(self):
        db = _make_db()
        k1 = MagicMock(kit_status="complete", kit_rate=0.95)
        k2 = MagicMock(kit_status="partial", kit_rate=0.5)
        db.query.return_value.filter.return_value.all.return_value = [k1, k2]
        result = calculate_kit_statistics(db, date(2025, 5, 1))
        assert result["total_work_orders"] == 2
        assert result["kit_complete_count"] == 1


class TestCalculateArrivalStatistics:
    def test_no_arrivals(self):
        db = _make_db()
        db.query.return_value.filter.return_value.scalar.return_value = 0
        result = calculate_arrival_statistics(db, date(2025, 5, 1))
        assert result["on_time_rate"] == 0.0

    def test_with_arrivals(self):
        db = _make_db()
        # expected=5, actual=4, delayed=1
        db.query.return_value.filter.return_value.scalar.side_effect = [5, 4, 1]
        result = calculate_arrival_statistics(db, date(2025, 5, 1))
        assert result["expected_arrivals"] == 5
        assert result["on_time_rate"] == 75.0


class TestCalculateResponseTimeStatistics:
    def test_no_alerts(self):
        db = _make_db()
        db.query.return_value.filter.return_value.all.return_value = []
        result = calculate_response_time_statistics(db, date(2025, 5, 1))
        assert result["avg_response_minutes"] == 0
        assert result["avg_resolve_hours"] == 0.0


class TestCalculateStoppageStatistics:
    def test_with_stop_impact(self):
        db = _make_db()
        alert = MagicMock()
        alert.alert_data = '{"impact_type": "stop", "estimated_delay_days": 2}'
        db.query.return_value.filter.return_value.all.return_value = [alert]
        result = calculate_stoppage_statistics(db, date(2025, 5, 1))
        assert result["stoppage_count"] == 1
        assert result["stoppage_hours"] == 48.0


class TestBuildDailyReportData:
    def test_combines_all(self):
        db = _make_db()
        with patch("app.services.shortage.shortage_reports_service.calculate_alert_statistics", return_value={"new_alerts": 1}), \
             patch("app.services.shortage.shortage_reports_service.calculate_report_statistics", return_value={"new_reports": 2}), \
             patch("app.services.shortage.shortage_reports_service.calculate_kit_statistics", return_value={"kit_rate": 0.9}), \
             patch("app.services.shortage.shortage_reports_service.calculate_arrival_statistics", return_value={"actual_arrivals": 3}), \
             patch("app.services.shortage.shortage_reports_service.calculate_response_time_statistics", return_value={"avg_response_minutes": 10}), \
             patch("app.services.shortage.shortage_reports_service.calculate_stoppage_statistics", return_value={"stoppage_count": 0}):
            result = build_daily_report_data(db, date(2025, 5, 1))
        assert result["new_alerts"] == 1
        assert result["new_reports"] == 2
        assert result["stoppage_count"] == 0
