# -*- coding: utf-8 -*-
"""
预警PDF导出服务单元测试
测试 app/services/alert_pdf_service.py
"""

from datetime import date, datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.alert import AlertRecord, AlertRule
from app.services.alert_pdf_service import (
    build_alert_query,
    calculate_alert_statistics,
)


class MockAlertRecord:
    """模拟 AlertRecord 类"""

    def __init__(
        self,
        alert_no: str,
        alert_level: str,
        alert_title: str = "测试预警",
        status: str = "PENDING",
        triggered_at: datetime = None,
        project_id: int = None,
        rule: object = None,
    ):
        self.alert_no = alert_no
        self.alert_level = alert_level
        self.alert_title = alert_title
        self.status = status
        self.triggered_at = triggered_at or datetime.now()
        self.project_id = project_id
        self.rule = rule


class MockAlertRule:
    """模拟 AlertRule 类"""

    def __init__(self, rule_type: str):
        self.rule_type = rule_type


class TestBuildAlertQuery:
    """测试 build_alert_query 函数"""

    def test_build_query_no_filters(self):
        """测试无过滤条件"""
        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_db.query.return_value.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        result = build_alert_query(mock_db)

        mock_db.query.assert_called_once()
        assert result == mock_query

    def test_build_query_with_project_id(self):
        """测试按项目ID过滤"""
        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_db.query.return_value.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        result = build_alert_query(mock_db, project_id=1)

        assert mock_query.filter.called

    def test_build_query_with_alert_level(self):
        """测试按预警级别过滤"""
        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_db.query.return_value.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        result = build_alert_query(mock_db, alert_level="WARNING")

        assert mock_query.filter.called

    def test_build_query_with_status(self):
        """测试按状态过滤"""
        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_db.query.return_value.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        result = build_alert_query(mock_db, status="RESOLVED")

        assert mock_query.filter.called

    def test_build_query_with_rule_type(self):
        """测试按规则类型过滤"""
        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_db.query.return_value.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        result = build_alert_query(mock_db, rule_type="SCHEDULE")

        assert mock_query.join.called

    def test_build_query_with_date_range(self):
        """测试按日期范围过滤"""
        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_db.query.return_value.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        start = date(2024, 1, 1)
        end = date(2024, 12, 31)

        result = build_alert_query(mock_db, start_date=start, end_date=end)

        # 应该调用2次filter（开始日期和结束日期）
        assert mock_query.filter.call_count >= 2

    def test_build_query_with_all_filters(self):
        """测试所有过滤条件"""
        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_db.query.return_value.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        result = build_alert_query(
            mock_db,
            project_id=1,
            alert_level="WARNING",
            status="PENDING",
            rule_type="COST",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )

        assert mock_query.filter.called
        assert mock_query.join.called


class TestCalculateAlertStatistics:
    """测试 calculate_alert_statistics 函数"""

    def test_empty_alerts(self):
        """测试空预警列表"""
        result = calculate_alert_statistics([])

        assert result["total"] == 0
        assert result["by_level"] == {}
        assert result["by_status"] == {}
        assert result["by_type"] == {}

    def test_single_alert(self):
        """测试单个预警"""
        rule = MockAlertRule("SCHEDULE")
        alert = MockAlertRecord(
            alert_no="ALT001",
            alert_level="WARNING",
            status="PENDING",
            rule=rule,
        )

        result = calculate_alert_statistics([alert])

        assert result["total"] == 1
        assert result["by_level"]["WARNING"] == 1
        assert result["by_status"]["PENDING"] == 1
        assert result["by_type"]["SCHEDULE"] == 1

    def test_multiple_alerts(self):
        """测试多个预警"""
        rule1 = MockAlertRule("SCHEDULE")
        rule2 = MockAlertRule("COST")

        alerts = [
            MockAlertRecord("ALT001", "WARNING", status="PENDING", rule=rule1),
            MockAlertRecord("ALT002", "WARNING", status="RESOLVED", rule=rule1),
            MockAlertRecord("ALT003", "CRITICAL", status="PENDING", rule=rule2),
            MockAlertRecord("ALT004", "CRITICAL", status="PENDING", rule=rule2),
            MockAlertRecord("ALT005", "INFO", status="RESOLVED", rule=rule1),
        ]

        result = calculate_alert_statistics(alerts)

        assert result["total"] == 5

        # 按级别统计
        assert result["by_level"]["WARNING"] == 2
        assert result["by_level"]["CRITICAL"] == 2
        assert result["by_level"]["INFO"] == 1

        # 按状态统计
        assert result["by_status"]["PENDING"] == 3
        assert result["by_status"]["RESOLVED"] == 2

        # 按类型统计
        assert result["by_type"]["SCHEDULE"] == 3
        assert result["by_type"]["COST"] == 2

    def test_alert_without_rule(self):
        """测试没有规则的预警"""
        alert = MockAlertRecord(
            alert_no="ALT001",
            alert_level="WARNING",
            status="PENDING",
            rule=None,  # 无规则
        )

        result = calculate_alert_statistics([alert])

        assert result["total"] == 1
        assert result["by_type"]["UNKNOWN"] == 1

    def test_mixed_alerts_with_and_without_rules(self):
        """测试混合有无规则的预警"""
        rule = MockAlertRule("SCHEDULE")

        alerts = [
            MockAlertRecord("ALT001", "WARNING", status="PENDING", rule=rule),
            MockAlertRecord("ALT002", "WARNING", status="PENDING", rule=None),
            MockAlertRecord("ALT003", "CRITICAL", status="PENDING", rule=rule),
        ]

        result = calculate_alert_statistics(alerts)

        assert result["total"] == 3
        assert result["by_type"]["SCHEDULE"] == 2
        assert result["by_type"]["UNKNOWN"] == 1


class TestPdfStyles:
    """测试 PDF 样式函数"""

    def test_get_pdf_styles_without_reportlab(self):
        """测试未安装 reportlab 时的错误处理"""
        from app.services.alert_pdf_service import get_pdf_styles

        # 如果 reportlab 未安装，应该抛出 ImportError
        # 如果已安装，应该返回样式
        try:
            title_style, heading_style, normal_style, styles = get_pdf_styles()
            assert title_style is not None
            assert heading_style is not None
            assert normal_style is not None
            assert styles is not None
        except ImportError as e:
            assert "reportlab" in str(e)


class TestBuildSummaryTable:
    """测试 build_summary_table 函数"""

    def test_build_summary_table_basic(self):
        """测试基本摘要表格构建"""
        from app.services.alert_pdf_service import build_summary_table

        statistics = {
            "total": 10,
            "by_level": {"WARNING": 5, "CRITICAL": 3, "INFO": 2},
            "by_status": {"PENDING": 6, "RESOLVED": 4},
        }

        try:
            table = build_summary_table(statistics)
            assert table is not None
        except ImportError:
            # reportlab 未安装，跳过测试
            pytest.skip("reportlab not installed")

    def test_build_summary_table_empty_statistics(self):
        """测试空统计数据"""
        from app.services.alert_pdf_service import build_summary_table

        statistics = {
            "total": 0,
            "by_level": {},
            "by_status": {},
        }

        try:
            table = build_summary_table(statistics)
            assert table is not None
        except ImportError:
            pytest.skip("reportlab not installed")


class TestBuildAlertListTables:
    """测试 build_alert_list_tables 函数"""

    def test_build_alert_list_tables_empty(self):
        """测试空预警列表"""
        from app.services.alert_pdf_service import build_alert_list_tables

        mock_db = MagicMock(spec=Session)

        try:
            tables = build_alert_list_tables(mock_db, [])
            assert tables == []
        except ImportError:
            pytest.skip("reportlab not installed")

    def test_build_alert_list_tables_with_alerts(self):
        """测试有预警的列表"""
        from app.services.alert_pdf_service import build_alert_list_tables

        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # 创建模拟预警
        mock_project = MagicMock()
        mock_project.project_name = "测试项目"

        alert = MagicMock()
        alert.alert_no = "ALT001"
        alert.alert_level = "WARNING"
        alert.alert_title = "测试预警标题"
        alert.project = mock_project
        alert.triggered_at = datetime.now()
        alert.status = "PENDING"
        alert.handler_id = None
        alert.acknowledged_by = None

        try:
            tables = build_alert_list_tables(mock_db, [alert])
            assert len(tables) >= 1
        except ImportError:
            pytest.skip("reportlab not installed")

    def test_build_alert_list_tables_pagination(self):
        """测试分页"""
        from app.services.alert_pdf_service import build_alert_list_tables

        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # 创建25个模拟预警（page_size=20，应该分2页）
        alerts = []
        for i in range(25):
            mock_project = MagicMock()
            mock_project.project_name = f"项目{i}"

            alert = MagicMock()
            alert.alert_no = f"ALT{i:03d}"
            alert.alert_level = "WARNING"
            alert.alert_title = f"预警{i}"
            alert.project = mock_project
            alert.triggered_at = datetime.now()
            alert.status = "PENDING"
            alert.handler_id = None
            alert.acknowledged_by = None
            alerts.append(alert)

        try:
            tables = build_alert_list_tables(mock_db, alerts, page_size=20)
            # 应该有表格+PageBreak
            assert len(tables) >= 2
        except ImportError:
            pytest.skip("reportlab not installed")
