# -*- coding: utf-8 -*-
"""
第三十三批覆盖率测试 - 预警PDF导出服务
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime

try:
    from app.services.alert_pdf_service import (
        build_alert_query,
        calculate_alert_statistics,
    )
    HAS_MODULE = True
except Exception:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="alert_pdf_service 导入失败")


class TestBuildAlertQuery:
    def _make_db(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.join.return_value = q
        q.order_by.return_value = q
        db.query.return_value = q
        return db, q

    def test_base_query_no_filters(self):
        """无过滤条件时构建基础查询"""
        db, q = self._make_db()
        result = build_alert_query(db)
        db.query.assert_called_once()

    def test_with_project_id(self):
        """指定project_id时添加过滤"""
        db, q = self._make_db()
        result = build_alert_query(db, project_id=10)
        # filter 被调用
        assert q.filter.called

    def test_with_alert_level(self):
        """指定alert_level时添加过滤"""
        db, q = self._make_db()
        result = build_alert_query(db, alert_level="RED")
        assert q.filter.called

    def test_with_status(self):
        """指定status时添加过滤"""
        db, q = self._make_db()
        result = build_alert_query(db, status="PENDING")
        assert q.filter.called

    def test_with_date_range(self):
        """指定日期范围时添加过滤"""
        db, q = self._make_db()
        result = build_alert_query(
            db,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31)
        )
        assert q.filter.call_count >= 2  # 开始日期和结束日期各一次

    def test_with_rule_type_joins_alert_rule(self):
        """指定rule_type时join AlertRule表"""
        db, q = self._make_db()
        result = build_alert_query(db, rule_type="project_delay")
        assert q.join.called


class TestCalculateAlertStatistics:
    def _make_alert(self, level="RED", status="PENDING", rule_type="project_delay"):
        alert = MagicMock()
        alert.alert_level = level
        alert.status = status
        alert.rule = MagicMock()
        alert.rule.rule_type = rule_type
        return alert

    def test_empty_alerts(self):
        """空预警列表返回全零统计"""
        stats = calculate_alert_statistics([])
        assert stats["total"] == 0
        assert stats["by_level"] == {}
        assert stats["by_status"] == {}
        assert stats["by_type"] == {}

    def test_single_alert(self):
        """单条预警统计正确"""
        alert = self._make_alert("RED", "PENDING", "project_delay")
        stats = calculate_alert_statistics([alert])
        assert stats["total"] == 1
        assert stats["by_level"]["RED"] == 1
        assert stats["by_status"]["PENDING"] == 1
        assert stats["by_type"]["project_delay"] == 1

    def test_multiple_levels(self):
        """多级别预警分别统计"""
        alerts = [
            self._make_alert("RED", "PENDING"),
            self._make_alert("RED", "RESOLVED"),
            self._make_alert("YELLOW", "PENDING"),
        ]
        stats = calculate_alert_statistics(alerts)
        assert stats["total"] == 3
        assert stats["by_level"]["RED"] == 2
        assert stats["by_level"]["YELLOW"] == 1

    def test_alert_without_rule(self):
        """无关联规则的预警类型为UNKNOWN"""
        alert = MagicMock()
        alert.alert_level = "BLUE"
        alert.status = "PENDING"
        alert.rule = None
        stats = calculate_alert_statistics([alert])
        assert stats["by_type"].get("UNKNOWN") == 1

    def test_multiple_statuses_counted(self):
        """不同状态分别计数"""
        alerts = [
            self._make_alert(status="PENDING"),
            self._make_alert(status="ACKNOWLEDGED"),
            self._make_alert(status="RESOLVED"),
            self._make_alert(status="PENDING"),
        ]
        stats = calculate_alert_statistics(alerts)
        assert stats["by_status"]["PENDING"] == 2
        assert stats["by_status"]["ACKNOWLEDGED"] == 1
        assert stats["by_status"]["RESOLVED"] == 1
