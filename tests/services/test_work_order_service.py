# -*- coding: utf-8 -*-
"""工单服务单元测试"""
import sys
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

# Mock notification_handlers module to fix import issues
_mock_handlers = MagicMock()
sys.modules["app.services.notification_handlers"] = _mock_handlers
sys.modules["app.services.notification_handlers.email_handler"] = MagicMock()
sys.modules["app.services.notification_handlers.sms_handler"] = MagicMock()
sys.modules["app.services.notification_handlers.system_handler"] = MagicMock()
sys.modules["app.services.notification_handlers.wechat_handler"] = MagicMock()

from app.services.production.work_order_service import WorkOrderService


def _make_db():
    return MagicMock()


def _make_work_order(**kw):
    """创建模拟工单对象"""
    t = MagicMock()
    defaults = dict(
        id=1,
        work_order_no="WO20250405001",
        task_name="测试工单",
        task_type="ASSEMBLY",
        project_id=1,
        machine_id=1,
        production_plan_id=1,
        process_id=1,
        workshop_id=1,
        workstation_id=1,
        material_name="测试物料",
        specification="规格A",
        plan_qty=100,
        completed_qty=0,
        qualified_qty=0,
        defect_qty=0,
        standard_hours=Decimal("8.00"),
        actual_hours=Decimal("0.00"),
        plan_start_date=date(2025, 4, 1),
        plan_end_date=date(2025, 4, 10),
        actual_start_time=None,
        actual_end_time=None,
        assigned_to=1,
        assigned_at=None,
        assigned_by=None,
        status="PENDING",
        priority="NORMAL",
        progress=0,
        work_content="测试工作内容",
        remark="测试备注",
        created_by=1,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(t, k, v)
    return t


def _make_pagination(total=10, offset=0, limit=20):
    """创建模拟分页对象"""
    pag = MagicMock()
    pag.offset = offset
    pag.limit = limit
    pag.total = total
    pag.items = []
    pag.to_response = lambda items, total: {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit,
    }
    return pag


class TestWorkOrderService:
    """WorkOrderService 测试类"""

    def test_build_response_basic(self):
        """测试构建工单响应对象 - 基本字段"""
        db = MagicMock()
        service = WorkOrderService(db)

        order = _make_work_order()
        # Mock 查询返回 None
        db.query.return_value.filter.return_value.first.return_value = None

        response = service.build_response(order)

        assert response.id == 1
        assert response.work_order_no == "WO20250405001"
        assert response.task_name == "测试工单"
        assert response.status == "PENDING"
        assert response.plan_qty == 100

    def test_build_response_with_maps(self):
        """测试构建工单响应对象 - 使用名称映射"""
        db = MagicMock()
        service = WorkOrderService(db)

        order = _make_work_order()

        response = service.build_response(
            order,
            project_map={1: "测试项目"},
            machine_map={1: "测试机台"},
            workshop_map={1: "测试车间"},
            workstation_map={1: "测试工位"},
            process_map={1: "测试工序"},
            worker_map={1: "测试工人"},
        )

        assert response.project_name == "测试项目"
        assert response.machine_name == "测试机台"
        assert response.workshop_name == "测试车间"
        assert response.workstation_name == "测试工位"
        assert response.process_name == "测试工序"
        assert response.assigned_worker_name == "测试工人"

    def test_create_work_order_validation_dates(self):
        """测试创建工单 - 日期校验：结束日期早于开始日期"""
        from app.schemas.production import WorkOrderCreate
        from fastapi import HTTPException

        db = MagicMock()
        service = WorkOrderService(db)

        # Mock 查询返回
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_name = "测试项目"
        db.query.return_value.filter.return_value.first.side_effect = [
            mock_project,  # project
            None,  # machine
            None,  # production_plan
            None,  # workshop
            None,  # workstation
        ]

        order_in = WorkOrderCreate(
            task_name="测试工单",
            task_type="ASSEMBLY",
            project_id=1,
            plan_start_date=date(2025, 4, 10),
            plan_end_date=date(2025, 4, 1),  # 结束日期早于开始日期
        )

        with pytest.raises(HTTPException) as exc_info:
            service.create_work_order(order_in, current_user_id=1)

        assert exc_info.value.status_code == 400
        assert "不能早于" in exc_info.value.detail

    def test_get_work_order_not_found(self):
        """测试获取工单 - 工单不存在"""
        from app.utils.db_helpers import get_or_404
        from fastapi import HTTPException

        db = MagicMock()
        service = WorkOrderService(db)

        # 模拟 get_or_404 抛出异常
        with patch("app.services.production.work_order_service.get_or_404") as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="工单不存在")

            with pytest.raises(HTTPException) as exc_info:
                service.get_work_order(999)

            assert exc_info.value.status_code == 404

    def test_assign_work_order_wrong_status(self):
        """测试派工 - 工单状态不正确"""
        from app.schemas.production import WorkOrderAssignRequest
        from fastapi import HTTPException

        db = MagicMock()
        service = WorkOrderService(db)

        # 工单状态不是 PENDING
        order = _make_work_order(status="IN_PROGRESS")

        with patch(
            "app.services.production.work_order_service.get_or_404"
        ) as mock_get:
            mock_get.return_value = order

            assign_in = WorkOrderAssignRequest(assigned_to=1)

            with pytest.raises(HTTPException) as exc_info:
                service.assign_work_order(1, assign_in, current_user_id=1)

            assert exc_info.value.status_code == 400
            assert "派工" in exc_info.value.detail


    def test_list_work_orders_with_filters(self):
        """测试查询工单列表 - 验证方法存在"""
        db = MagicMock()
        service = WorkOrderService(db)
        
        # 验证方法存在
        assert hasattr(service, 'list_work_orders')
        assert callable(service.list_work_orders)


class TestWorkOrderServiceHelperMethods:
    """测试辅助方法"""

    def test_fetch_project_map(self):
        """测试批量获取项目映射"""
        db = MagicMock()
        service = WorkOrderService(db)

        # 模拟查询结果
        mock_result = [MagicMock(id=1, project_name="项目A")]
        db.query.return_value.filter.return_value.all.return_value = mock_result

        result = service._fetch_project_map([1])

        assert 1 in result
        assert result[1] == "项目A"

    def test_fetch_project_map_empty(self):
        """测试批量获取项目映射 - 空列表"""
        db = MagicMock()
        service = WorkOrderService(db)

        result = service._fetch_project_map([])

        assert result == {}

    def test_fetch_machine_map(self):
        """测试批量获取机台映射"""
        db = MagicMock()
        service = WorkOrderService(db)

        mock_result = [MagicMock(id=1, machine_name="机台A")]
        db.query.return_value.filter.return_value.all.return_value = mock_result

        result = service._fetch_machine_map([1])

        assert 1 in result
        assert result[1] == "机台A"

    def test_fetch_worker_map(self):
        """测试批量获取工人映射"""
        db = MagicMock()
        service = WorkOrderService(db)

        mock_result = [MagicMock(id=1, worker_name="工人A")]
        db.query.return_value.filter.return_value.all.return_value = mock_result

        result = service._fetch_worker_map([1])

        assert 1 in result
        assert result[1] == "工人A"