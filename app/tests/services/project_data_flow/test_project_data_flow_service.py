# -*- coding: utf-8 -*-
"""
项目数据流通服务测试

测试 ProjectDataFlowService 的核心功能
"""

from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock, MagicMock, patch

import pytest
from sqlalchemy.orm import Session
from decimal import Decimal


class TestProjectDataFlowService:
    """项目数据流通服务测试类"""

    @pytest.fixture
    def mock_db_session(self):
        """创建模拟的数据库会话"""
        db = Mock(spec=Session)
        db.query = Mock(return_value=Mock())
        db.add = Mock()
        db.commit = Mock()
        db.flush = Mock()
        return db

    @pytest.fixture
    def service(self, mock_db_session):
        """创建项目数据流通服务实例"""
        from app.services.project_data_flow_service import ProjectDataFlowService
        return ProjectDataFlowService(mock_db_session)

    def test_create_work_orders_from_wbs_project_not_found(self, service, mock_db_session):
        """测试项目不存在时返回错误"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        # 执行测试
        result = service.create_work_orders_from_wbs(project_id=999)

        # 验证结果
        assert "error" in result
        assert result["error"] == "项目不存在"

    def test_create_work_orders_from_wbs_uses_current_task_and_work_order_models(
        self, service, mock_db_session
    ):
        """从当前项目任务模型生成生产工单，并写入真实 WorkOrder 字段"""
        from app.models.progress import Task
        from app.models.project import Project
        from app.models.production import WorkOrder

        project = SimpleNamespace(id=42, project_code="PRJ-42")
        task = SimpleNamespace(
            id=11,
            task_code="T-001",
            task_name="总装调试",
            stage="S5",
            plan_start=date(2026, 6, 8),
            plan_end=date(2026, 6, 12),
        )
        added = []

        def query(model):
            query_mock = MagicMock()
            if model is Project:
                query_mock.filter.return_value.first.return_value = project
            elif model is Task:
                query_mock.filter.return_value.all.return_value = [task]
            elif model is WorkOrder:
                query_mock.filter.return_value.first.return_value = None
            else:
                raise AssertionError(f"unexpected model queried: {model}")
            return query_mock

        mock_db_session.query.side_effect = query
        mock_db_session.add.side_effect = added.append

        result = service.create_work_orders_from_wbs(project_id=42)

        assert result == {
            "project_id": 42,
            "created_count": 1,
            "skipped_count": 0,
            "created_orders": ["WO-PRJ-42-T-001"],
        }
        assert len(added) == 1
        work_order = added[0]
        assert isinstance(work_order, WorkOrder)
        assert work_order.project_id == 42
        assert work_order.work_order_no == "WO-PRJ-42-T-001"
        assert work_order.task_name == "总装调试"
        assert work_order.task_type == "ASSEMBLY"
        assert work_order.plan_start_date == date(2026, 6, 8)
        assert work_order.plan_end_date == date(2026, 6, 12)
        assert "source_task_id" not in work_order.__dict__

    def test_transfer_to_after_sales_success(self, service, mock_db_session):
        """测试项目验收后成功转入售后服务"""
        from app.models.after_sales import AfterSalesMaintenance
        from app.models.project import Project

        project = SimpleNamespace(
            id=1,
            customer_id=100,
            warranty_start_date=date(2026, 8, 1),
            actual_end_date=None,
            planned_end_date=None,
        )

        def query(model):
            query_mock = MagicMock()
            if model is Project:
                query_mock.filter.return_value.first.return_value = project
            elif model is AfterSalesMaintenance:
                query_mock.filter.return_value.all.return_value = []
            else:
                raise AssertionError(f"unexpected model queried: {model}")
            return query_mock

        mock_db_session.query.side_effect = query

        # 执行测试
        result = service.transfer_to_after_sales(project_id=1)

        # 验证结果
        assert result["project_id"] == 1
        assert result["maintenance_created"] == 4
        assert len(result["maintenance_records"]) == 4
        assert "1 个月保养" in result["maintenance_records"]
        assert "3 个月保养" in result["maintenance_records"]
        assert "6 个月保养" in result["maintenance_records"]
        assert "12 个月保养" in result["maintenance_records"]
        # 验证添加了4条保养记录
        assert mock_db_session.add.call_count == 4

    def test_transfer_to_after_sales_project_not_found(self, service, mock_db_session):
        """测试项目不存在时返回错误"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        # 执行测试
        result = service.transfer_to_after_sales(project_id=999)

        # 验证结果
        assert "error" in result
        assert result["error"] == "项目不存在"

    def test_transfer_to_after_sales_schedules_regular_maintenance_from_warranty_start(
        self, service, mock_db_session
    ):
        """转售后时按质保开始日期生成定期保养计划日期"""
        from app.models.after_sales import AfterSalesMaintenance
        from app.models.project import Project

        project = SimpleNamespace(
            id=42,
            customer_id=100,
            warranty_start_date=date(2026, 8, 1),
            actual_end_date=date(2026, 7, 20),
            planned_end_date=date(2026, 7, 25),
        )
        added = []

        def query(model):
            query_mock = MagicMock()
            if model is Project:
                query_mock.filter.return_value.first.return_value = project
            elif model is AfterSalesMaintenance:
                query_mock.filter.return_value.all.return_value = []
            else:
                raise AssertionError(f"unexpected model queried: {model}")
            return query_mock

        mock_db_session.query.side_effect = query
        mock_db_session.add.side_effect = added.append

        result = service.transfer_to_after_sales(project_id=42)

        assert result["project_id"] == 42
        assert result["maintenance_created"] == 4
        assert result["skipped_existing"] == 0
        assert [item.scheduled_date for item in added] == [
            date(2026, 9, 1),
            date(2026, 11, 1),
            date(2027, 2, 1),
            date(2027, 8, 1),
        ]
        assert all(item.project_id == 42 for item in added)
        assert all(item.customer_id == 100 for item in added)
        assert all(item.maintenance_type == "REGULAR" for item in added)

    def test_transfer_to_after_sales_does_not_duplicate_regular_maintenance(
        self, service, mock_db_session
    ):
        """已有定期保养计划时不重复创建"""
        from app.models.after_sales import AfterSalesMaintenance
        from app.models.project import Project

        project = SimpleNamespace(
            id=42,
            customer_id=100,
            warranty_start_date=date(2026, 8, 1),
            actual_end_date=None,
            planned_end_date=None,
        )
        existing = [
            SimpleNamespace(maintenance_content="交付后 1 个月定期保养"),
            SimpleNamespace(maintenance_content="交付后 3 个月定期保养"),
            SimpleNamespace(maintenance_content="交付后 6 个月定期保养"),
            SimpleNamespace(maintenance_content="交付后 12 个月定期保养（质保期内）"),
        ]

        def query(model):
            query_mock = MagicMock()
            if model is Project:
                query_mock.filter.return_value.first.return_value = project
            elif model is AfterSalesMaintenance:
                query_mock.filter.return_value.all.return_value = existing
            else:
                raise AssertionError(f"unexpected model queried: {model}")
            return query_mock

        mock_db_session.query.side_effect = query

        result = service.transfer_to_after_sales(project_id=42)

        assert result == {
            "project_id": 42,
            "maintenance_created": 0,
            "maintenance_records": [],
            "skipped_existing": 4,
        }
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()

    def test_create_purchase_requests_from_bom_no_bom(self, service, mock_db_session):
        """测试项目无BOM时返回错误"""
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query

        # 执行测试
        result = service.create_purchase_requests_from_bom(project_id=1)

        # 验证结果
        assert "error" in result
        assert result["error"] == "项目无 BOM 数据"

    def test_create_purchase_requests_from_bom_writes_required_item_fields(
        self, service, mock_db_session
    ):
        """从 BOM 生成采购申请时写入真实采购明细必填字段"""
        from app.models.inventory_tracking import MaterialStock
        from app.models.material import BomHeader, BomItem
        from app.models.purchase import PurchaseRequest, PurchaseRequestItem

        bom = SimpleNamespace(id=501)
        bom_item = SimpleNamespace(
            id=9001,
            material_id=1001,
            material_code="M-001",
            material_name="伺服电机",
            specification="750W",
            unit="台",
            quantity=Decimal("5"),
            unit_price=Decimal("1200"),
            required_date=date(2026, 6, 20),
        )
        added = []

        def query(model):
            query_mock = MagicMock()
            if model is BomHeader:
                query_mock.filter.return_value.all.return_value = [bom]
            elif model is PurchaseRequest:
                query_mock.filter.return_value.first.return_value = None
            elif model is BomItem:
                query_mock.filter.return_value.all.return_value = [bom_item]
            elif model is MaterialStock or "coalesce" in str(model):
                query_mock.filter.return_value.scalar.return_value = Decimal("2")
            else:
                raise AssertionError(f"unexpected model queried: {model}")
            return query_mock

        def flush():
            for item in added:
                if isinstance(item, PurchaseRequest):
                    item.id = 700

        mock_db_session.query.side_effect = query
        mock_db_session.add.side_effect = added.append
        mock_db_session.flush.side_effect = flush

        result = service.create_purchase_requests_from_bom(project_id=42)

        assert result["project_id"] == 42
        assert result["request_id"] == 700
        assert result["total_materials"] == 1
        assert result["items_with_net_demand"] == 1

        request = next(item for item in added if isinstance(item, PurchaseRequest))
        assert request.project_id == 42
        assert request.source_type == "BOM"
        assert request.source_id == 501

        request_item = next(item for item in added if isinstance(item, PurchaseRequestItem))
        assert request_item.request_id == 700
        assert request_item.bom_item_id == 9001
        assert request_item.material_id == 1001
        assert request_item.material_code == "M-001"
        assert request_item.material_name == "伺服电机"
        assert request_item.specification == "750W"
        assert request_item.unit == "台"
        assert request_item.quantity == Decimal("3")
        assert request_item.unit_price == Decimal("1200")
        assert request_item.amount == Decimal("3600")
        assert request_item.required_date == date(2026, 6, 20)

    def test_create_purchase_requests_from_bom_returns_existing_request(
        self, service, mock_db_session
    ):
        """同一项目同一 BOM 已生成采购申请时不重复创建"""
        from app.models.material import BomHeader
        from app.models.purchase import PurchaseRequest

        bom = SimpleNamespace(id=501)
        existing_request = SimpleNamespace(
            id=700,
            request_no="PR-20260701-61",
            project_id=61,
            source_type="BOM",
            source_id=501,
        )

        def query(model):
            query_mock = MagicMock()
            if model is BomHeader:
                query_mock.filter.return_value.all.return_value = [bom]
            elif model is PurchaseRequest:
                query_mock.filter.return_value.first.return_value = existing_request
            else:
                raise AssertionError(f"unexpected model queried: {model}")
            return query_mock

        mock_db_session.query.side_effect = query

        result = service.create_purchase_requests_from_bom(project_id=61)

        assert result == {
            "project_id": 61,
            "request_no": "PR-20260701-61",
            "request_id": 700,
            "total_materials": 0,
            "items_with_net_demand": 0,
            "skipped_existing": True,
        }
        mock_db_session.add.assert_not_called()
        mock_db_session.flush.assert_not_called()
        mock_db_session.commit.assert_not_called()

    def test_create_delivery_schedule_project_not_found(self, service, mock_db_session):
        """测试项目不存在时返回错误"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        # 执行测试
        result = service.create_delivery_schedule_from_project(project_id=999, initiator_id=100)

        # 验证结果
        assert "error" in result
        assert result["error"] == "项目不存在"

    def test_create_delivery_schedule_from_project_uses_current_milestone_model(
        self, service, mock_db_session
    ):
        """从当前项目里程碑模型生成交付排产计划和任务"""
        from app.models.project import Project, ProjectMilestone
        from app.models.project_delivery import ProjectDeliverySchedule, ProjectDeliveryTask

        project = SimpleNamespace(id=42, project_name="包装线项目")
        milestone = SimpleNamespace(
            id=601,
            milestone_name="FAT 验收",
            planned_date=date(2026, 7, 1),
        )
        added = []

        def query(model):
            query_mock = MagicMock()
            if model is Project:
                query_mock.filter.return_value.first.return_value = project
            elif model is ProjectDeliverySchedule:
                query_mock.filter.return_value.first.return_value = None
            elif model is ProjectMilestone:
                query_mock.filter.return_value.order_by.return_value.all.return_value = [milestone]
            else:
                raise AssertionError(f"unexpected model queried: {model}")
            return query_mock

        def flush():
            for item in added:
                if isinstance(item, ProjectDeliverySchedule):
                    item.id = 800

        mock_db_session.query.side_effect = query
        mock_db_session.add.side_effect = added.append
        mock_db_session.flush.side_effect = flush

        result = service.create_delivery_schedule_from_project(project_id=42, initiator_id=100)

        assert result["project_id"] == 42
        assert result["schedule_id"] == 800
        assert result["tasks_created"] == 1

        schedule = next(item for item in added if isinstance(item, ProjectDeliverySchedule))
        assert schedule.schedule_name == "包装线项目 - 交付排产计划"
        assert schedule.project_id == 42
        assert schedule.initiator_id == 100
        assert schedule.is_active is True

        task = next(item for item in added if isinstance(item, ProjectDeliveryTask))
        assert task.schedule_id == 800
        assert task.task_no == "T001"
        assert task.task_type == "PRODUCTION"
        assert task.task_name == "FAT 验收"
        assert task.planned_start == date(2026, 7, 1)
        assert task.planned_end == date(2026, 7, 1)

    def test_create_delivery_schedule_returns_existing_active_schedule(
        self, service, mock_db_session
    ):
        """已有当前交付排产计划时不重复创建"""
        from app.models.project import Project
        from app.models.project_delivery import ProjectDeliverySchedule

        project = SimpleNamespace(id=42, project_name="包装线项目")
        existing_schedule = SimpleNamespace(
            id=800,
            schedule_no="PDS-2026-042",
            project_id=42,
            is_active=True,
        )

        def query(model):
            query_mock = MagicMock()
            if model is Project:
                query_mock.filter.return_value.first.return_value = project
            elif model is ProjectDeliverySchedule:
                query_mock.filter.return_value.first.return_value = existing_schedule
            else:
                raise AssertionError(f"unexpected model queried: {model}")
            return query_mock

        mock_db_session.query.side_effect = query

        result = service.create_delivery_schedule_from_project(project_id=42, initiator_id=100)

        assert result == {
            "project_id": 42,
            "schedule_id": 800,
            "schedule_no": "PDS-2026-042",
            "tasks_created": 0,
            "skipped_existing": True,
        }
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()
