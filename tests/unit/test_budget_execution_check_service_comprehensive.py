# -*- coding: utf-8 -*-
"""
budget_execution_check_service 综合单元测试

测试覆盖:
- get_project_budget: 获取项目预算金额
- get_actual_cost: 获取项目实际成本
- get_or_create_alert_rule: 获取或创建成本预警规则
- determine_alert_level: 判断预警级别
- find_existing_alert: 查找现有预警记录
- generate_alert_no: 生成预警编号
- create_alert_record: 创建预警记录
"""

from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest


class TestGetProjectBudget:
    """测试 get_project_budget 函数"""

    def test_returns_budget_from_approved_budget(self):
        """测试从已批准的预算中获取金额"""
        from app.services.budget_execution_check_service import get_project_budget

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.budget_amount = 100000

        mock_budget = MagicMock()
        mock_budget.total_amount = 150000

        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_budget

        result = get_project_budget(mock_db, 1, mock_project)

        assert result == 150000.0

    def test_returns_project_budget_when_no_approved_budget(self):
        """测试无已批准预算时返回项目预算"""
        from app.services.budget_execution_check_service import get_project_budget

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.budget_amount = 100000

        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = get_project_budget(mock_db, 1, mock_project)

        assert result == 100000.0

    def test_returns_zero_when_no_budget(self):
        """测试无预算时返回零"""
        from app.services.budget_execution_check_service import get_project_budget

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.budget_amount = None

        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = get_project_budget(mock_db, 1, mock_project)

        assert result == 0.0


class TestGetActualCost:
    """测试 get_actual_cost 函数"""

    def test_returns_project_actual_cost(self):
        """测试返回项目实际成本"""
        from app.services.budget_execution_check_service import get_actual_cost

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.actual_cost = 80000

        result = get_actual_cost(mock_db, 1, mock_project)

        assert result == 80000.0

    def test_calculates_cost_from_records_when_no_actual_cost(self):
        """测试无实际成本时从记录计算"""
        from app.services.budget_execution_check_service import get_actual_cost

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.actual_cost = None

        mock_cost1 = MagicMock()
        mock_cost1.amount = 30000
        mock_cost2 = MagicMock()
        mock_cost2.amount = 20000

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_cost1, mock_cost2]

        result = get_actual_cost(mock_db, 1, mock_project)

        assert result == 50000.0

    def test_handles_none_cost_amounts(self):
        """测试处理金额为None的成本记录"""
        from app.services.budget_execution_check_service import get_actual_cost

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.actual_cost = None

        mock_cost1 = MagicMock()
        mock_cost1.amount = 30000
        mock_cost2 = MagicMock()
        mock_cost2.amount = None

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_cost1, mock_cost2]

        result = get_actual_cost(mock_db, 1, mock_project)

        assert result == 30000.0


class TestGetOrCreateAlertRule:
    """测试 get_or_create_alert_rule 函数"""

    def test_returns_existing_rule(self):
        """测试返回现有规则"""
        from app.services.budget_execution_check_service import get_or_create_alert_rule

        mock_db = MagicMock()
        mock_rule = MagicMock()
        mock_rule.rule_code = 'COST_OVERRUN'

        mock_db.query.return_value.filter.return_value.first.return_value = mock_rule

        result = get_or_create_alert_rule(mock_db)

        assert result == mock_rule
        mock_db.add.assert_not_called()

    def test_creates_new_rule_when_not_exists(self):
        """测试不存在时创建新规则"""
        from app.services.budget_execution_check_service import get_or_create_alert_rule

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = get_or_create_alert_rule(mock_db)

        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        assert result.rule_code == 'COST_OVERRUN'
        assert result.rule_name == '成本超支预警'


class TestDetermineAlertLevel:
    """测试 determine_alert_level 函数"""

    def test_returns_urgent_for_severe_overrun(self):
        """测试严重超支返回紧急级别"""
        from app.services.budget_execution_check_service import determine_alert_level

        level, title, content = determine_alert_level(
            execution_rate=125,
            overrun_ratio=25,
            project_name="测试项目",
            project_code="PJ001",
            budget_amount=100000,
            actual_cost=125000
        )

        assert level == "URGENT"
        assert "严重超支" in title

    def test_returns_critical_for_moderate_overrun(self):
        """测试中度超支返回严重级别"""
        from app.services.budget_execution_check_service import determine_alert_level

        level, title, content = determine_alert_level(
            execution_rate=115,
            overrun_ratio=15,
            project_name="测试项目",
            project_code="PJ001",
            budget_amount=100000,
            actual_cost=115000
        )

        assert level == "CRITICAL"
        assert "超支" in title

    def test_returns_warning_for_minor_overrun(self):
        """测试轻度超支返回警告级别"""
        from app.services.budget_execution_check_service import determine_alert_level

        level, title, content = determine_alert_level(
            execution_rate=107,
            overrun_ratio=7,
            project_name="测试项目",
            project_code="PJ001",
            budget_amount=100000,
            actual_cost=107000
        )

        assert level == "WARNING"
        assert "超支" in title

    def test_returns_warning_for_near_budget(self):
        """测试接近预算返回警告级别"""
        from app.services.budget_execution_check_service import determine_alert_level

        level, title, content = determine_alert_level(
            execution_rate=95,
            overrun_ratio=0,
            project_name="测试项目",
            project_code="PJ001",
            budget_amount=100000,
            actual_cost=95000
        )

        assert level == "WARNING"
        assert "接近预算" in title

    def test_returns_info_for_high_execution_rate(self):
        """测试执行率较高返回提示级别"""
        from app.services.budget_execution_check_service import determine_alert_level

        level, title, content = determine_alert_level(
            execution_rate=85,
            overrun_ratio=0,
            project_name="测试项目",
            project_code="PJ001",
            budget_amount=100000,
            actual_cost=85000
        )

        assert level == "INFO"
        assert "执行率较高" in title

    def test_returns_none_for_normal_execution(self):
        """测试正常执行返回None"""
        from app.services.budget_execution_check_service import determine_alert_level

        level, title, content = determine_alert_level(
            execution_rate=50,
            overrun_ratio=0,
            project_name="测试项目",
            project_code="PJ001",
            budget_amount=100000,
            actual_cost=50000
        )

        assert level is None
        assert title is None
        assert content is None


class TestFindExistingAlert:
    """测试 find_existing_alert 函数"""

    def test_returns_existing_alert(self):
        """测试返回现有预警"""
        from app.services.budget_execution_check_service import find_existing_alert

        mock_db = MagicMock()
        mock_alert = MagicMock()
        mock_alert.id = 1

        mock_alert_rule = MagicMock()
        mock_alert_rule.id = 10

        mock_db.query.return_value.filter.return_value.first.return_value = mock_alert

        result = find_existing_alert(mock_db, 1, mock_alert_rule, "WARNING")

        assert result == mock_alert

    def test_returns_none_when_no_existing_alert(self):
        """测试无现有预警时返回None"""
        from app.services.budget_execution_check_service import find_existing_alert

        mock_db = MagicMock()
        mock_alert_rule = MagicMock()
        mock_alert_rule.id = 10

        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = find_existing_alert(mock_db, 1, mock_alert_rule, "WARNING")

        assert result is None


class TestGenerateAlertNo:
    """测试 generate_alert_no 函数"""

    def test_generates_first_alert_no(self):
        """测试生成第一个预警编号"""
        from app.services.budget_execution_check_service import generate_alert_no

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = generate_alert_no(mock_db)

        today = date.today().strftime("%Y%m%d")
        assert result == f'CO{today}0001'

    def test_increments_sequence_number(self):
        """测试递增序号"""
        from app.services.budget_execution_check_service import generate_alert_no

        mock_db = MagicMock()
        mock_existing = MagicMock()
        today = date.today().strftime("%Y%m%d")
        mock_existing.alert_no = f'CO{today}0005'

        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_existing

        result = generate_alert_no(mock_db)

        assert result == f'CO{today}0006'


class TestCreateAlertRecord:
    """测试 create_alert_record 函数"""

    def test_creates_alert_record(self):
        """测试创建预警记录"""
        from app.services.budget_execution_check_service import create_alert_record

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"

        mock_rule = MagicMock()
        mock_rule.id = 10

        # Mock generate_alert_no
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = create_alert_record(
            mock_db, mock_project, 1, mock_rule,
            "WARNING", "测试预警", "预警内容",
            100000, 90000, "COST", 123
        )

        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        assert result.alert_level == "WARNING"
        assert result.alert_title == "测试预警"
        assert result.target_id == 1

    def test_sets_correct_source_info(self):
        """测试设置正确的来源信息"""
        from app.services.budget_execution_check_service import create_alert_record

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"

        mock_rule = MagicMock()
        mock_rule.id = 10

        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = create_alert_record(
            mock_db, mock_project, 1, mock_rule,
            "WARNING", "测试预警", "预警内容",
            100000, 90000, "TIMESHEET", 456
        )

        assert result.source_module == "TIMESHEET"
        assert result.source_id == 456

    def test_uses_default_source_module(self):
        """测试使用默认来源模块"""
        from app.services.budget_execution_check_service import create_alert_record

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"

        mock_rule = MagicMock()
        mock_rule.id = 10

        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = create_alert_record(
            mock_db, mock_project, 1, mock_rule,
            "WARNING", "测试预警", "预警内容",
            100000, 90000, None, None
        )

        assert result.source_module == "COST"
