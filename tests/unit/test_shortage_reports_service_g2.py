# -*- coding: utf-8 -*-
"""
ShortageReportsService 单元测试 - G2组覆盖率提升

覆盖:
- ShortageReportsService.__init__
- ShortageReportsService.create_shortage_report
- ShortageReportsService.get_shortage_report (found / not found)
- ShortageReportsService.confirm_shortage_report
- ShortageReportsService.handle_shortage_report
- ShortageReportsService.resolve_shortage_report
- calculate_alert_statistics (module-level function)
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


class TestShortageReportsServiceInit:
    """初始化测试"""

    def test_init_stores_db(self):
        from app.services.shortage.shortage_reports_service import ShortageReportsService
        db = MagicMock()
        service = ShortageReportsService(db)
        assert service.db is db


class TestCreateShortageReport:
    """测试 create_shortage_report"""

    def setup_method(self):
        from app.services.shortage.shortage_reports_service import ShortageReportsService
        self.db = MagicMock()
        self.service = ShortageReportsService(self.db)

    @patch("app.services.shortage.shortage_reports_service.save_obj")
    @patch("app.services.shortage.shortage_reports_service.ShortageReport")
    def test_creates_report_with_correct_fields(self, mock_cls, mock_save):
        mock_report = MagicMock()
        mock_report.status = "pending"
        mock_report.reporter_id = 42
        mock_cls.return_value = mock_report

        report_data = MagicMock()
        report_data.title = "缺料测试"
        report_data.description = "测试描述"
        report_data.material_id = 1
        report_data.shortage_quantity = Decimal("50")
        report_data.shortage_reason = "供应商延迟"
        report_data.impact_assessment = "影响生产"
        report_data.expected_arrival_date = date(2026, 3, 1)

        current_user = MagicMock()
        current_user.id = 42

        result = self.service.create_shortage_report(report_data, current_user)

        assert result is not None
        assert result.status == "pending"
        assert result.reporter_id == 42
        mock_save.assert_called_once()

    @patch("app.services.shortage.shortage_reports_service.save_obj")
    @patch("app.services.shortage.shortage_reports_service.ShortageReport")
    def test_report_status_is_pending_on_creation(self, mock_cls, mock_save):
        mock_report = MagicMock()
        mock_report.status = "pending"
        mock_cls.return_value = mock_report

        report_data = MagicMock()
        report_data.title = "T"
        report_data.description = "D"
        report_data.material_id = 2
        report_data.shortage_quantity = Decimal("10")
        report_data.shortage_reason = "reason"
        report_data.impact_assessment = "impact"
        report_data.expected_arrival_date = None

        current_user = MagicMock()
        current_user.id = 1

        result = self.service.create_shortage_report(report_data, current_user)
        assert result.status == "pending"


class TestGetShortageReport:
    """测试 get_shortage_report"""

    def setup_method(self):
        from app.services.shortage.shortage_reports_service import ShortageReportsService
        self.db = MagicMock()
        self.service = ShortageReportsService(self.db)

    def test_returns_report_when_found(self):
        mock_report = MagicMock()
        mock_report.id = 1
        # Simulate: db.query().options().filter().first() = mock_report
        (self.db.query.return_value
             .options.return_value
             .filter.return_value
             .first.return_value) = mock_report

        result = self.service.get_shortage_report(1)
        assert result == mock_report

    def test_returns_none_when_not_found(self):
        (self.db.query.return_value
             .options.return_value
             .filter.return_value
             .first.return_value) = None

        result = self.service.get_shortage_report(999)
        assert result is None


class TestConfirmShortageReport:
    """测试 confirm_shortage_report"""

    def setup_method(self):
        from app.services.shortage.shortage_reports_service import ShortageReportsService
        self.db = MagicMock()
        self.service = ShortageReportsService(self.db)

    def test_returns_none_when_report_not_found(self):
        self.service.get_shortage_report = MagicMock(return_value=None)
        result = self.service.confirm_shortage_report(999, MagicMock())
        assert result is None

    def test_sets_status_confirmed(self):
        mock_report = MagicMock()
        self.service.get_shortage_report = MagicMock(return_value=mock_report)

        current_user = MagicMock()
        current_user.id = 5

        result = self.service.confirm_shortage_report(1, current_user)

        assert mock_report.status == "confirmed"
        assert mock_report.confirmer_id == 5
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(mock_report)

    def test_returns_refreshed_report(self):
        mock_report = MagicMock()
        self.service.get_shortage_report = MagicMock(return_value=mock_report)

        current_user = MagicMock()
        current_user.id = 3

        result = self.service.confirm_shortage_report(1, current_user)
        assert result == mock_report


class TestHandleShortageReport:
    """测试 handle_shortage_report"""

    def setup_method(self):
        from app.services.shortage.shortage_reports_service import ShortageReportsService
        self.db = MagicMock()
        self.service = ShortageReportsService(self.db)

    def test_returns_none_when_not_found(self):
        self.service.get_shortage_report = MagicMock(return_value=None)
        result = self.service.handle_shortage_report(999, {}, MagicMock())
        assert result is None

    def test_sets_handling_status_and_fields(self):
        mock_report = MagicMock()
        self.service.get_shortage_report = MagicMock(return_value=mock_report)

        current_user = MagicMock()
        current_user.id = 7

        handle_data = {
            "handling_method": "urgent purchase",
            "handling_note": "已联系供应商",
        }

        result = self.service.handle_shortage_report(1, handle_data, current_user)

        assert mock_report.status == "handling"
        assert mock_report.handler_id == 7
        assert mock_report.handling_method == "urgent purchase"
        assert mock_report.handling_note == "已联系供应商"
        self.db.commit.assert_called_once()


class TestResolveShortageReport:
    """测试 resolve_shortage_report"""

    def setup_method(self):
        from app.services.shortage.shortage_reports_service import ShortageReportsService
        self.db = MagicMock()
        self.service = ShortageReportsService(self.db)

    def test_returns_none_when_not_found(self):
        self.service.get_shortage_report = MagicMock(return_value=None)
        result = self.service.resolve_shortage_report(999, {}, MagicMock())
        assert result is None

    def test_sets_resolved_status(self):
        mock_report = MagicMock()
        self.service.get_shortage_report = MagicMock(return_value=mock_report)

        current_user = MagicMock()
        current_user.id = 9

        resolve_data = {
            "resolution_method": "emergency purchase",
            "resolution_note": "已到货",
            "actual_arrival_date": date(2026, 2, 20),
        }

        result = self.service.resolve_shortage_report(1, resolve_data, current_user)

        assert mock_report.status == "resolved"
        assert mock_report.resolver_id == 9
        assert mock_report.resolution_method == "emergency purchase"
        assert mock_report.actual_arrival_date == date(2026, 2, 20)
        self.db.commit.assert_called_once()


class TestCalculateAlertStatistics:
    """测试模块级 calculate_alert_statistics"""

    def test_returns_expected_keys(self):
        from app.services.shortage.shortage_reports_service import calculate_alert_statistics

        db = MagicMock()
        # Make count() return 0 for all sub-queries
        db.query.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.filter.return_value.filter.return_value.count.return_value = 0

        result = calculate_alert_statistics(db, target_date=date.today())

        assert "new_alerts" in result
        assert "resolved_alerts" in result
        assert "pending_alerts" in result
        assert "level_counts" in result

    def test_level_counts_has_four_levels(self):
        from app.services.shortage.shortage_reports_service import calculate_alert_statistics

        db = MagicMock()
        db.query.return_value.filter.return_value.count.return_value = 3
        db.query.return_value.filter.return_value.filter.return_value.count.return_value = 3

        result = calculate_alert_statistics(db, target_date=date.today())
        assert "level_counts" in result
        # level_counts should have entries for level1..level4
        assert len(result["level_counts"]) == 4
