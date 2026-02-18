# -*- coding: utf-8 -*-
"""第九批: test_anomaly_detector_cov9.py - TimesheetAnomalyDetector 单元测试"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import date, timedelta
from decimal import Decimal

pytest.importorskip("app.services.timesheet_reminder.anomaly_detector")

from app.services.timesheet_reminder.anomaly_detector import TimesheetAnomalyDetector


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_reminder_manager():
    return MagicMock()


@pytest.fixture
def detector(mock_db, mock_reminder_manager):
    with patch("app.services.timesheet_reminder.anomaly_detector.TimesheetReminderManager", return_value=mock_reminder_manager):
        d = TimesheetAnomalyDetector(db=mock_db)
        d.reminder_manager = mock_reminder_manager
        return d


class TestTimesheetAnomalyDetectorInit:
    def test_init(self, detector, mock_db):
        assert detector.db is mock_db


class TestDetectDailyOver12:
    """测试单日工时超12小时检测"""

    def test_detect_no_anomalies(self, detector, mock_db):
        # Query returns no results over threshold
        mock_q = MagicMock()
        mock_db.query.return_value.filter.return_value.group_by.return_value.having.return_value.all.return_value = []
        result = detector.detect_daily_over_12(
            start_date=date.today() - timedelta(days=1),
            end_date=date.today()
        )
        assert isinstance(result, list)
        assert len(result) == 0

    def test_detect_with_user_id_filter(self, detector, mock_db):
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.having.return_value = mock_q
        mock_q.all.return_value = []
        mock_db.query.return_value.filter.return_value.group_by.return_value = mock_q
        result = detector.detect_daily_over_12(
            start_date=date.today() - timedelta(days=1),
            end_date=date.today(),
            user_id=1
        )
        assert isinstance(result, list)


class TestDetectDailyInvalid:
    """测试单日工时无效检测 (< 0 or > 24)"""

    def test_detect_daily_invalid_empty(self, detector, mock_db):
        mock_q = MagicMock()
        mock_db.query.return_value.filter.return_value.group_by.return_value.having.return_value.all.return_value = []
        result = detector.detect_daily_invalid(
            start_date=date.today() - timedelta(days=1),
            end_date=date.today()
        )
        assert isinstance(result, list)


class TestDetectWeeklyOver60:
    """测试周工时超60小时检测"""

    def test_detect_weekly_over_60_empty(self, detector, mock_db):
        mock_q = MagicMock()
        mock_db.query.return_value.filter.return_value.group_by.return_value.having.return_value.all.return_value = []
        result = detector.detect_weekly_over_60(
            start_date=date.today() - timedelta(days=7),
            end_date=date.today()
        )
        assert isinstance(result, list)


class TestDetectAllAnomalies:
    """测试检测所有异常"""

    def test_detect_all_anomalies_empty(self, detector):
        with patch.object(detector, "detect_daily_over_12", return_value=[]):
            with patch.object(detector, "detect_daily_invalid", return_value=[]):
                with patch.object(detector, "detect_weekly_over_60", return_value=[]):
                    with patch.object(detector, "detect_no_rest_7days", return_value=[]):
                        with patch.object(detector, "detect_progress_mismatch", return_value=[]):
                            result = detector.detect_all_anomalies()
                            assert isinstance(result, list)
                            assert len(result) == 0

    def test_detect_all_anomalies_with_dates(self, detector):
        mock_anomaly = MagicMock()
        with patch.object(detector, "detect_daily_over_12", return_value=[mock_anomaly]):
            with patch.object(detector, "detect_daily_invalid", return_value=[]):
                with patch.object(detector, "detect_weekly_over_60", return_value=[]):
                    with patch.object(detector, "detect_no_rest_7days", return_value=[]):
                        with patch.object(detector, "detect_progress_mismatch", return_value=[]):
                            result = detector.detect_all_anomalies(
                                start_date=date.today() - timedelta(days=7),
                                end_date=date.today()
                            )
                            assert len(result) == 1

    def test_detect_all_anomalies_with_user_id(self, detector):
        with patch.object(detector, "detect_daily_over_12", return_value=[]):
            with patch.object(detector, "detect_daily_invalid", return_value=[]):
                with patch.object(detector, "detect_weekly_over_60", return_value=[]):
                    with patch.object(detector, "detect_no_rest_7days", return_value=[]):
                        with patch.object(detector, "detect_progress_mismatch", return_value=[]):
                            result = detector.detect_all_anomalies(user_id=1)
                            assert isinstance(result, list)
