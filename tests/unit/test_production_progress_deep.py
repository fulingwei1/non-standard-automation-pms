# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 生产进度服务"""
from decimal import Decimal
from unittest.mock import MagicMock

import pytest


class TestProductionProgressServiceBusinessLogic:
    """生产进度服务业务逻辑测试"""

    def test_calculate_progress_deviation(self):
        """测试计算进度偏差"""
        try:
            from app.services.production_progress_service import ProductionProgressService

            mock_db = MagicMock()
            work_order = MagicMock()
            work_order.plan_start_date = None
            work_order.plan_end_date = None
            mock_db.query.return_value.filter.return_value.first.return_value = work_order
            service = ProductionProgressService(mock_db)

            result = service.calculate_progress_deviation(1, 50)

            assert isinstance(result, tuple)
            assert len(result) == 3
        except ImportError:
            pytest.skip("Module not found")

    def test_create_progress_log(self):
        """测试创建进度日志"""
        try:
            from app.services.production_progress_service import ProductionProgressService
            from app.schemas.production_progress import ProductionProgressLogCreate

            mock_db = MagicMock()
            work_order = MagicMock()
            work_order.id = 1
            work_order.status = "IN_PROGRESS"
            work_order.actual_hours = Decimal("0")
            work_order.workstation_id = 1
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                work_order,
                None,
                None,
            ]
            service = ProductionProgressService(mock_db)
            service.evaluate_alert_rules = MagicMock(return_value=[])
            service._update_workstation_status = MagicMock()

            log_data = ProductionProgressLogCreate(
                work_order_id=1,
                workstation_id=1,
                current_progress=50,
                completed_qty=10,
                qualified_qty=9,
                defect_qty=1,
                work_hours=Decimal("2"),
                status="IN_PROGRESS",
                note="test",
            )

            result = service.create_progress_log(log_data, user_id=1)

            assert result is not None
            assert mock_db.add.called
        except ImportError:
            pytest.skip("Module not found")
