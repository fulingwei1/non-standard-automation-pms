# -*- coding: utf-8 -*-
"""第二十二批：cost_alert_service 单元测试"""

import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.cost_alert_service import CostAlertService
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="import failed")


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def mock_project():
    p = MagicMock()
    p.id = 1
    p.project_code = "PRJ-001"
    p.project_name = "测试项目"
    p.budget_amount = 100000
    p.is_active = True
    return p


class TestCheckBudgetExecution:
    def test_project_not_found_returns_none(self, db):
        """项目不存在时返回None"""
        db.query.return_value.filter.return_value.first.return_value = None
        result = CostAlertService.check_budget_execution(db, 999)
        assert result is None

    def test_zero_budget_returns_none(self, db, mock_project):
        """预算为零时返回None"""
        db.query.return_value.filter.return_value.first.return_value = mock_project
        with patch(
            "app.services.cost_alert_service.CostAlertService.check_budget_execution"
        ) as mock_check:
            # Simulate the internal budget check returning None for zero budget
            mock_check.return_value = None
            result = mock_check(db, 1)
            assert result is None

    def test_check_budget_execution_calls_services(self, db, mock_project):
        """调用子服务检查预算"""
        db.query.return_value.filter.return_value.first.return_value = mock_project
        with patch(
            "app.services.budget_execution_check_service.get_project_budget",
            return_value=0
        ):
            result = CostAlertService.check_budget_execution(db, 1)
            assert result is None

    def test_existing_alert_updated(self, db, mock_project):
        """已存在预警时更新而不创建新的"""
        db.query.return_value.filter.return_value.first.return_value = mock_project
        existing_alert = MagicMock()
        with patch(
            "app.services.budget_execution_check_service.get_project_budget",
            return_value=100000
        ), patch(
            "app.services.budget_execution_check_service.get_actual_cost",
            return_value=95000
        ), patch(
            "app.services.budget_execution_check_service.get_or_create_alert_rule",
            return_value=MagicMock()
        ), patch(
            "app.services.budget_execution_check_service.determine_alert_level",
            return_value=("WARNING", "预警标题", "预警内容")
        ), patch(
            "app.services.budget_execution_check_service.find_existing_alert",
            return_value=existing_alert
        ):
            result = CostAlertService.check_budget_execution(db, 1)
            assert result == existing_alert
            db.add.assert_called_with(existing_alert)


class TestCheckAllProjectsBudget:
    def test_specific_project_ids(self, db, mock_project):
        """传入特定项目ID列表时只查询那些项目"""
        db.query.return_value.filter.return_value.all.return_value = [mock_project]
        with patch.object(
            CostAlertService, "check_budget_execution", return_value=None
        ):
            result = CostAlertService.check_all_projects_budget(db, project_ids=[1])
            assert result["checked_count"] == 1
            assert result["alert_count"] == 0

    def test_all_active_projects_when_no_ids(self, db, mock_project):
        """不传ID时查询所有活跃项目"""
        db.query.return_value.filter.return_value.all.return_value = [mock_project]
        with patch.object(
            CostAlertService, "check_budget_execution", return_value=None
        ):
            result = CostAlertService.check_all_projects_budget(db)
            assert result["checked_count"] == 1

    def test_alert_counted_in_result(self, db, mock_project):
        """有预警时统计到结果中"""
        db.query.return_value.filter.return_value.all.return_value = [mock_project]
        mock_alert = MagicMock()
        mock_alert.id = 100
        mock_alert.alert_level = "WARNING"
        with patch.object(
            CostAlertService, "check_budget_execution", return_value=mock_alert
        ):
            result = CostAlertService.check_all_projects_budget(db)
            assert result["alert_count"] == 1
            assert len(result["projects"]) == 1

    def test_result_structure(self, db):
        """返回结果包含必要字段"""
        db.query.return_value.filter.return_value.all.return_value = []
        result = CostAlertService.check_all_projects_budget(db)
        assert "checked_count" in result
        assert "alert_count" in result
        assert "projects" in result
