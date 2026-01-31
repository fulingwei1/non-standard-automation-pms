# -*- coding: utf-8 -*-
"""
CostAlertService 综合单元测试

测试覆盖:
- check_budget_execution: 检查项目预算执行情况并生成预警
- check_all_projects_budget: 批量检查项目预算执行情况
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestCheckBudgetExecution:
    """测试 check_budget_execution 方法"""

    def test_returns_none_when_project_not_found(self):
        """测试项目不存在时返回None"""
        from app.services.cost_alert_service import CostAlertService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = CostAlertService.check_budget_execution(mock_db, 999)

        assert result is None

    def test_returns_none_when_no_budget(self):
        """测试无预算时返回None"""
        from app.services.cost_alert_service import CostAlertService

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        with patch('app.services.cost_alert_service.get_project_budget') as mock_get_budget:
            mock_get_budget.return_value = 0

            result = CostAlertService.check_budget_execution(mock_db, 1)

            assert result is None

    def test_returns_none_when_no_alert_needed(self):
        """测试无需预警时返回None"""
        from app.services.cost_alert_service import CostAlertService

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_name = "测试项目"
        mock_project.project_code = "PJ001"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        with patch('app.services.cost_alert_service.get_project_budget') as mock_get_budget, \
             patch('app.services.cost_alert_service.get_actual_cost') as mock_get_cost, \
             patch('app.services.cost_alert_service.get_or_create_alert_rule') as mock_get_rule, \
             patch('app.services.cost_alert_service.determine_alert_level') as mock_determine:

            mock_get_budget.return_value = 100000
            mock_get_cost.return_value = 50000  # 50% 执行率，不需要预警
            mock_get_rule.return_value = MagicMock()
            mock_determine.return_value = (None, None, None)

            result = CostAlertService.check_budget_execution(mock_db, 1)

            assert result is None

    def test_creates_alert_when_needed(self):
        """测试需要预警时创建记录"""
        from app.services.cost_alert_service import CostAlertService

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_name = "测试项目"
        mock_project.project_code = "PJ001"

        mock_alert_rule = MagicMock()
        mock_alert_record = MagicMock()

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        with patch('app.services.cost_alert_service.get_project_budget') as mock_get_budget, \
             patch('app.services.cost_alert_service.get_actual_cost') as mock_get_cost, \
             patch('app.services.cost_alert_service.get_or_create_alert_rule') as mock_get_rule, \
             patch('app.services.cost_alert_service.determine_alert_level') as mock_determine, \
             patch('app.services.cost_alert_service.find_existing_alert') as mock_find_existing, \
             patch('app.services.cost_alert_service.create_alert_record') as mock_create:

            mock_get_budget.return_value = 100000
            mock_get_cost.return_value = 120000  # 超支
            mock_get_rule.return_value = mock_alert_rule
            mock_determine.return_value = ("WARNING", "预算超支警告", "项目预算超支20%")
            mock_find_existing.return_value = None
            mock_create.return_value = mock_alert_record

            result = CostAlertService.check_budget_execution(mock_db, 1)

            mock_create.assert_called_once()
            assert result == mock_alert_record

    def test_updates_existing_alert(self):
        """测试更新现有预警"""
        from app.services.cost_alert_service import CostAlertService

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_name = "测试项目"
        mock_project.project_code = "PJ001"

        mock_alert_rule = MagicMock()
        mock_existing_alert = MagicMock()
        mock_existing_alert.alert_content = "旧内容"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        with patch('app.services.cost_alert_service.get_project_budget') as mock_get_budget, \
             patch('app.services.cost_alert_service.get_actual_cost') as mock_get_cost, \
             patch('app.services.cost_alert_service.get_or_create_alert_rule') as mock_get_rule, \
             patch('app.services.cost_alert_service.determine_alert_level') as mock_determine, \
             patch('app.services.cost_alert_service.find_existing_alert') as mock_find_existing:

            mock_get_budget.return_value = 100000
            mock_get_cost.return_value = 120000
            mock_get_rule.return_value = mock_alert_rule
            mock_determine.return_value = ("WARNING", "预算超支警告", "新内容")
            mock_find_existing.return_value = mock_existing_alert

            result = CostAlertService.check_budget_execution(mock_db, 1)

            assert result == mock_existing_alert
            assert mock_existing_alert.alert_content == "新内容"
            mock_db.add.assert_called_once_with(mock_existing_alert)

    def test_passes_trigger_source(self):
        """测试传递触发来源"""
        from app.services.cost_alert_service import CostAlertService

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_name = "测试项目"
        mock_project.project_code = "PJ001"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        with patch('app.services.cost_alert_service.get_project_budget') as mock_get_budget, \
             patch('app.services.cost_alert_service.get_actual_cost') as mock_get_cost, \
             patch('app.services.cost_alert_service.get_or_create_alert_rule') as mock_get_rule, \
             patch('app.services.cost_alert_service.determine_alert_level') as mock_determine, \
             patch('app.services.cost_alert_service.find_existing_alert') as mock_find_existing, \
             patch('app.services.cost_alert_service.create_alert_record') as mock_create:

            mock_get_budget.return_value = 100000
            mock_get_cost.return_value = 120000
            mock_get_rule.return_value = MagicMock()
            mock_determine.return_value = ("WARNING", "警告", "内容")
            mock_find_existing.return_value = None
            mock_create.return_value = MagicMock()

            CostAlertService.check_budget_execution(
                mock_db, 1, trigger_source="TIMESHEET", source_id=123
            )

            # 验证create_alert_record被调用时包含trigger_source和source_id
            call_args = mock_create.call_args
            assert call_args[0][-2] == "TIMESHEET"
            assert call_args[0][-1] == 123


class TestCheckAllProjectsBudget:
    """测试 check_all_projects_budget 方法"""

    def test_checks_specified_projects(self):
        """测试检查指定项目"""
        from app.services.cost_alert_service import CostAlertService

        mock_db = MagicMock()

        mock_project1 = MagicMock()
        mock_project1.id = 1
        mock_project1.project_code = "PJ001"

        mock_project2 = MagicMock()
        mock_project2.id = 2
        mock_project2.project_code = "PJ002"

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_project1, mock_project2]

        with patch.object(CostAlertService, 'check_budget_execution') as mock_check:
            mock_check.return_value = None

            result = CostAlertService.check_all_projects_budget(mock_db, project_ids=[1, 2])

            assert result['checked_count'] == 2
            assert mock_check.call_count == 2

    def test_checks_all_active_projects(self):
        """测试检查所有活跃项目"""
        from app.services.cost_alert_service import CostAlertService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.is_active = True

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_project]

        with patch.object(CostAlertService, 'check_budget_execution') as mock_check:
            mock_check.return_value = None

            result = CostAlertService.check_all_projects_budget(mock_db)

            assert result['checked_count'] == 1

    def test_counts_alerts(self):
        """测试统计预警数量"""
        from app.services.cost_alert_service import CostAlertService

        mock_db = MagicMock()

        mock_project1 = MagicMock()
        mock_project1.id = 1
        mock_project1.project_code = "PJ001"

        mock_project2 = MagicMock()
        mock_project2.id = 2
        mock_project2.project_code = "PJ002"

        mock_alert = MagicMock()
        mock_alert.id = 100
        mock_alert.alert_level = "WARNING"

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_project1, mock_project2]

        with patch.object(CostAlertService, 'check_budget_execution') as mock_check:
            # 第一个项目有预警，第二个没有
            mock_check.side_effect = [mock_alert, None]

            result = CostAlertService.check_all_projects_budget(mock_db, project_ids=[1, 2])

            assert result['checked_count'] == 2
            assert result['alert_count'] == 1
            assert len(result['projects']) == 1
            assert result['projects'][0]['project_id'] == 1
            assert result['projects'][0]['alert_level'] == "WARNING"

    def test_returns_empty_for_no_projects(self):
        """测试无项目时返回空"""
        from app.services.cost_alert_service import CostAlertService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = CostAlertService.check_all_projects_budget(mock_db, project_ids=[])

        assert result['checked_count'] == 0
        assert result['alert_count'] == 0
        assert result['projects'] == []

    def test_includes_project_details_in_result(self):
        """测试结果包含项目详情"""
        from app.services.cost_alert_service import CostAlertService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"

        mock_alert = MagicMock()
        mock_alert.id = 100
        mock_alert.alert_level = "CRITICAL"

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_project]

        with patch.object(CostAlertService, 'check_budget_execution') as mock_check:
            mock_check.return_value = mock_alert

            result = CostAlertService.check_all_projects_budget(mock_db, project_ids=[1])

            assert result['projects'][0]['project_id'] == 1
            assert result['projects'][0]['project_code'] == "PJ001"
            assert result['projects'][0]['alert_id'] == 100
            assert result['projects'][0]['alert_level'] == "CRITICAL"
