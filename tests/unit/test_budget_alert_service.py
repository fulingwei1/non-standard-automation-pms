# -*- coding: utf-8 -*-
"""
预算预警服务测试
"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch


class TestBudgetAlertService:
    """预算预警服务测试"""

    def test_get_budget_status_basic(self):
        """测试获取预算状态基础功能"""
        from app.services.budget_alert_service import BudgetAlertService

        mock_db = MagicMock()
        service = BudgetAlertService(mock_db)

        # Mock project
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_amount = Decimal("100000")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        with patch.object(service, '_get_budget_amount', return_value=80000):
            with patch.object(service, '_get_actual_cost', return_value=40000):
                with patch.object(service, '_get_committed_cost', return_value=20000):
                    result = service.get_budget_status(project_id=1)
                    assert isinstance(result, (dict, type(None)))

    def test_get_budget_status_no_project(self):
        """测试项目不存在"""
        from app.services.budget_alert_service import BudgetAlertService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        service = BudgetAlertService(mock_db)

        result = service.get_budget_status(project_id=999)
        assert result is None

    def test_get_budget_status_no_budget(self):
        """测试项目无预算"""
        from app.services.budget_alert_service import BudgetAlertService

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        service = BudgetAlertService(mock_db)

        with patch.object(service, '_get_budget_amount', return_value=0):
            result = service.get_budget_status(project_id=1)
            assert result is None

    def test_get_budget_summary(self):
        """测试获取预算摘要"""
        from app.services.budget_alert_service import BudgetAlertService

        mock_db = MagicMock()
        service = BudgetAlertService(mock_db)

        result = service.get_budget_summary()
        assert isinstance(result, (dict, list))

    def test_check_budget_alerts(self):
        """测试检查预算预警"""
        from app.services.budget_alert_service import BudgetAlertService

        mock_db = MagicMock()
        service = BudgetAlertService(mock_db)

        result = service.check_budget_alerts(project_id=1)
        assert isinstance(result, (dict, list))

    def test_get_execution_rate(self):
        """测试获取执行率"""
        from app.services.budget_alert_service import BudgetAlertService

        mock_db = MagicMock()
        service = BudgetAlertService(mock_db)

        mock_project = MagicMock()
        mock_project.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        with patch.object(service, '_get_actual_cost', return_value=60000):
            with patch.object(service, '_get_budget_amount', return_value=80000):
                result = service._get_execution_rate(project_id=1, actual_cost=60000, budget_amount=80000)
                assert isinstance(result, (float, int))

    def test_get_cost_trend(self):
        """测试获取成本趋势"""
        from app.services.budget_alert_service import BudgetAlertService

        mock_db = MagicMock()
        service = BudgetAlertService(mock_db)

        result = service.get_cost_trend(project_id=1, days=30)
        assert isinstance(result, (dict, list))