# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 资源计划服务"""
from decimal import Decimal
from unittest.mock import MagicMock

import pytest


class TestResourcePlanServiceBusinessLogic:
    """资源计划服务业务逻辑测试"""

    def test_assign_employee(self):
        """测试分配员工"""
        try:
            from app.services.resource_plan_service import ResourcePlanService

            mock_db = MagicMock()
            plan = MagicMock()
            plan.project_id = 1
            plan.planned_start = None
            plan.planned_end = None
            plan.allocation_pct = Decimal("50")
            mock_db.query.return_value.filter.return_value.first.return_value = plan

            result = ResourcePlanService.assign_employee(mock_db, 1, 2)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_calculate_conflict_severity(self):
        """测试计算冲突严重性"""
        try:
            from app.services.resource_plan_service import ResourcePlanService

            result = ResourcePlanService.calculate_conflict_severity(Decimal("130"))

            assert result == "MEDIUM"
        except ImportError:
            pytest.skip("Module not found")
