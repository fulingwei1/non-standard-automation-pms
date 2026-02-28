# -*- coding: utf-8 -*-
"""TimesheetQualityService 单元测试"""

import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch


class TestTimesheetQualityService:

    def _make_service(self):
        from app.services.timesheet_quality_service import TimesheetQualityService
        db = MagicMock()
        return TimesheetQualityService(db_session), db

    # ---------- detect_anomalies ----------

    def test_detect_anomalies_empty(self):
        """无工时记录时返回空列表"""
        svc, db = self._make_service()
        db.query.return_value.filter.return_value.all.return_value = []
        result = svc.detect_anomalies()
        assert result == []

    def test_detect_anomalies_excessive_daily(self):
        """单日工时 > 16 时应标记 EXCESSIVE_DAILY_HOURS"""
        svc, db = self._make_service()
        today = date(2025, 1, 6)
        ts1 = MagicMock(user_id=1, work_date=today, hours=10)
        ts2 = MagicMock(user_id=1, work_date=today, hours=8)  # 合计 18 > 16
        user = MagicMock(real_name="张三", username="zs")
        db.query.return_value.filter.return_value.all.return_value = [ts1, ts2]
        db.query.return_value.filter.return_value.first.return_value = user
        anomalies = svc.detect_anomalies()
        types = [a["type"] for a in anomalies]
        assert "EXCESSIVE_DAILY_HOURS" in types

    def test_detect_anomalies_normal_hours_no_anomaly(self):
        """正常工时（8小时）不产生异常"""
        svc, db = self._make_service()
        today = date(2025, 1, 6)  # Monday
        ts = MagicMock(user_id=1, work_date=today, hours=8)
        user = MagicMock(real_name="李四", username="ls")
        db.query.return_value.filter.return_value.all.return_value = [ts]
        db.query.return_value.filter.return_value.first.return_value = user
        anomalies = svc.detect_anomalies()
        daily_anomalies = [a for a in anomalies if a["type"] == "EXCESSIVE_DAILY_HOURS"]
        assert daily_anomalies == []

    def test_detect_anomalies_excessive_weekly(self):
        """单周工时 > 80 时应标记 EXCESSIVE_WEEKLY_HOURS"""
        svc, db = self._make_service()
        monday = date(2025, 1, 6)
        # 5 天各 17 小时 = 85 > 80
        timesheets = [MagicMock(user_id=1, work_date=monday + timedelta(days=i), hours=17) for i in range(5)]
        user = MagicMock(real_name="王五", username="ww")
        db.query.return_value.filter.return_value.all.return_value = timesheets
        db.query.return_value.filter.return_value.first.return_value = user
        anomalies = svc.detect_anomalies()
        weekly = [a for a in anomalies if a["type"] == "EXCESSIVE_WEEKLY_HOURS"]
        assert len(weekly) >= 1

    # ---------- check_work_log_completeness ----------

    def test_completeness_no_missing_logs(self):
        """所有工时都有日志时完整性=100%"""
        svc, db = self._make_service()
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = []
        result = svc.check_work_log_completeness()
        assert result["completeness_rate"] == 100
        assert result["missing_log_count"] == 0

    def test_completeness_with_missing_log(self):
        """有工时记录无日志时缺失数 > 0"""
        svc, db = self._make_service()
        today = date.today()
        # 模拟 distinct 查询返回 (work_date, user_id) 对
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = [
            (today, 1)
        ]
        # 第二次查询（WorkLog）返回 None
        db.query.return_value.filter.return_value.first.side_effect = [None, MagicMock(real_name="测试", username="test")]
        result = svc.check_work_log_completeness()
        assert result["missing_log_count"] == 1

    # ---------- validate_data_consistency ----------

    def test_validate_consistency_no_timesheets(self):
        """无工时记录时一致性=100%"""
        svc, db = self._make_service()
        db.query.return_value.filter.return_value.all.return_value = []
        result = svc.validate_data_consistency()
        assert result["consistency_rate"] == 100
        assert result["inconsistency_count"] == 0

    # ---------- check_labor_law_compliance ----------

    def test_compliance_within_limit(self):
        """加班 ≤ 36 小时时合规"""
        svc, db = self._make_service()
        ts = MagicMock(hours=8)
        db.query.return_value.filter.return_value.all.return_value = [ts] * 3  # 24 hours
        result = svc.check_labor_law_compliance(user_id=1, year=2025, month=1)
        assert result["is_compliant"] is True
        assert result["overtime_hours"] == 24

    def test_compliance_exceeds_limit(self):
        """加班 > 36 小时时违规"""
        svc, db = self._make_service()
        ts = MagicMock(hours=10)
        db.query.return_value.filter.return_value.all.return_value = [ts] * 5  # 50 hours
        result = svc.check_labor_law_compliance(user_id=1, year=2025, month=2)
        assert result["is_compliant"] is False
        assert result["violation_hours"] == pytest.approx(14, abs=1)

    def test_compliance_result_structure(self):
        """返回值包含所有必要字段"""
        svc, db = self._make_service()
        db.query.return_value.filter.return_value.all.return_value = []
        result = svc.check_labor_law_compliance(user_id=1, year=2025, month=3)
        for key in ("user_id", "year", "month", "overtime_hours", "max_allowed", "is_compliant"):
            assert key in result
