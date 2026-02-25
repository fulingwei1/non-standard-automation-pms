# -*- coding: utf-8 -*-
"""
工单服务单元测试

目标：
1. 只mock外部依赖（db.query, db.add, db.commit等）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 目标覆盖率: 70%+
"""

import unittest
from unittest.mock import MagicMock, patch, call
from datetime import datetime

from fastapi import HTTPException

from app.services.production.work_order_service import WorkOrderService
from app.models.production import (
    WorkOrder,
    Workshop,
    Workstation,
    ProcessDict,
    Worker,
    ProductionPlan,
)
from app.models.project import Project, Machine
from app.schemas.production import WorkOrderResponse


class TestWorkOrderService(unittest.TestCase):
    """工单服务测试套件"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = WorkOrderService(self.db)

    # ========== build_response() 测试 ==========

    def test_build_response_full_fields(self):
        """测试构建响应 - 所有字段都存在"""
        from datetime import date
        # 准备mock对象
        mock_order = MagicMock(spec=WorkOrder)
        mock_order.id = 1
        mock_order.work_order_no = "WO-2024-001"
        mock_order.task_name = "加工任务"
        mock_order.task_type = "加工"
        mock_order.project_id = 10
        mock_order.machine_id = 20
        mock_order.production_plan_id = 30
        mock_order.process_id = 40
        mock_order.workshop_id = 50
        mock_order.workstation_id = 60
        mock_order.assigned_to = 70
        mock_order.material_name = "钢板"
        mock_order.specification = "100x100"
        mock_order.plan_qty = 100
        mock_order.completed_qty = 50
        mock_order.qualified_qty = 45
        mock_order.defect_qty = 5
        mock_order.standard_hours = 10.5
        mock_order.actual_hours = 8.5
        mock_order.plan_start_date = date(2024, 1, 1)
        mock_order.plan_end_date = date(2024, 1, 10)
        mock_order.actual_start_time = datetime(2024, 1, 2, 8, 0)
        mock_order.actual_end_time = None
        mock_order.status = "IN_PROGRESS"
        mock_order.priority = "HIGH"  # 使用字符串类型
        mock_order.progress = 50
        mock_order.work_content = "详细加工内容"
        mock_order.remark = "备注信息"
        mock_order.created_at = datetime(2024, 1, 1, 10, 0)
        mock_order.updated_at = datetime(2024, 1, 2, 10, 0)

        # Mock关联查询
        mock_project = MagicMock(spec=Project)
        mock_project.project_name = "项目A"

        mock_machine = MagicMock(spec=Machine)
        mock_machine.machine_name = "机台1"

        mock_workshop = MagicMock(spec=Workshop)
        mock_workshop.workshop_name = "一车间"

        mock_workstation = MagicMock(spec=Workstation)
        mock_workstation.workstation_name = "工位1"

        mock_process = MagicMock(spec=ProcessDict)
        mock_process.process_name = "切割"

        mock_worker = MagicMock(spec=Worker)
        mock_worker.worker_name = "张三"

        # 设置query().filter().first()的返回值
        def query_side_effect(model):
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_query.filter.return_value = mock_filter

            if model == Project:
                mock_filter.first.return_value = mock_project
            elif model == Machine:
                mock_filter.first.return_value = mock_machine
            elif model == Workshop:
                mock_filter.first.return_value = mock_workshop
            elif model == Workstation:
                mock_filter.first.return_value = mock_workstation
            elif model == ProcessDict:
                mock_filter.first.return_value = mock_process
            elif model == Worker:
                mock_filter.first.return_value = mock_worker
            else:
                mock_filter.first.return_value = None

            return mock_query

        self.db.query.side_effect = query_side_effect

        # 执行
        response = self.service.build_response(mock_order)

        # 验证
        self.assertIsInstance(response, WorkOrderResponse)
        self.assertEqual(response.id, 1)
        self.assertEqual(response.work_order_no, "WO-2024-001")
        self.assertEqual(response.project_name, "项目A")
        self.assertEqual(response.machine_name, "机台1")
        self.assertEqual(response.workshop_name, "一车间")
        self.assertEqual(response.workstation_name, "工位1")
        self.assertEqual(response.process_name, "切割")
        self.assertEqual(response.assigned_worker_name, "张三")
        self.assertEqual(response.plan_qty, 100)
        self.assertEqual(response.completed_qty, 50)
        self.assertEqual(response.standard_hours, 10.5)

    def test_build_response_minimal_fields(self):
        """测试构建响应 - 最少字段"""
        mock_order = MagicMock(spec=WorkOrder)
        mock_order.id = 1
        mock_order.work_order_no = "WO-2024-002"
        mock_order.task_name = "简单任务"
        mock_order.task_type = "检查"
        mock_order.project_id = None
        mock_order.machine_id = None
        mock_order.production_plan_id = None
        mock_order.process_id = None
        mock_order.workshop_id = None
        mock_order.workstation_id = None
        mock_order.assigned_to = None
        mock_order.material_name = None
        mock_order.specification = None
        mock_order.plan_qty = None
        mock_order.completed_qty = None
        mock_order.qualified_qty = None
        mock_order.defect_qty = None
        mock_order.standard_hours = None
        mock_order.actual_hours = None
        mock_order.plan_start_date = None
        mock_order.plan_end_date = None
        mock_order.actual_start_time = None
        mock_order.actual_end_time = None
        mock_order.status = "PENDING"
        mock_order.priority = "NORMAL"  # 使用字符串类型
        mock_order.progress = None
        mock_order.work_content = None
        mock_order.remark = None
        mock_order.created_at = datetime.now()
        mock_order.updated_at = datetime.now()

        response = self.service.build_response(mock_order)

        self.assertEqual(response.id, 1)
        self.assertEqual(response.work_order_no, "WO-2024-002")
        self.assertIsNone(response.project_name)
        self.assertIsNone(response.machine_name)
        self.assertEqual(response.plan_qty, 0)
        self.assertEqual(response.completed_qty, 0)
        self.assertEqual(response.actual_hours, 0)
        self.assertEqual(response.progress, 0)

    def test_build_response_missing_related_entities(self):
        """测试构建响应 - 关联实体不存在"""
        mock_order = MagicMock(spec=WorkOrder)
        mock_order.id = 1
        mock_order.work_order_no = "WO-2024-003"
        mock_order.task_name = "任务"
        mock_order.task_type = "加工"
        mock_order.project_id = 999  # 不存在的项目
        mock_order.machine_id = 888  # 不存在的机台
        mock_order.workshop_id = 777
        mock_order.workstation_id = 666
        mock_order.process_id = 555
        mock_order.assigned_to = 444
        mock_order.production_plan_id = None
        mock_order.material_name = None
        mock_order.specification = None
        mock_order.plan_qty = None
        mock_order.completed_qty = None
        mock_order.qualified_qty = None
        mock_order.defect_qty = None
        mock_order.standard_hours = None
        mock_order.actual_hours = None
        mock_order.plan_start_date = None
        mock_order.plan_end_date = None
        mock_order.actual_start_time = None
        mock_order.actual_end_time = None
        mock_order.status = "PENDING"
        mock_order.priority = "NORMAL"  # 使用字符串类型
        mock_order.progress = None
        mock_order.work_content = None
        mock_order.remark = None
        mock_order.created_at = datetime.now()
        mock_order.updated_at = datetime.now()

        # Mock查询返回None
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = None
        mock_query.filter.return_value = mock_filter
        self.db.query.return_value = mock_query

        response = self.service.build_response(mock_order)

        # 验证所有关联名称都为None
        self.assertIsNone(response.project_name)
        self.assertIsNone(response.machine_name)
        self.assertIsNone(response.workshop_name)
        self.assertIsNone(response.workstation_name)
        self.assertIsNone(response.process_name)
        self.assertIsNone(response.assigned_worker_name)

    # ========== list_work_orders() 测试 ==========

    @patch("app.common.query_filters.apply_pagination")
    def test_list_work_orders_no_filters(self, mock_apply_pagination):
        """测试查询工单列表 - 无过滤条件"""
        mock_order1 = MagicMock(spec=WorkOrder)
        mock_order1.id = 1
        mock_order2 = MagicMock(spec=WorkOrder)
        mock_order2.id = 2

        # Mock查询链
        mock_query = MagicMock()
        mock_count = MagicMock(return_value=2)
        mock_order_by = MagicMock()

        mock_query.filter.return_value = mock_query
        mock_query.count = mock_count
        mock_query.order_by.return_value = mock_order_by

        mock_apply_pagination.return_value.all.return_value = [mock_order1, mock_order2]

        self.db.query.return_value = mock_query

        # Mock pagination - 使用真实的类行为
        class MockPagination:
            def __init__(self):
                self.offset = 0
                self.limit = 10
            
            def to_response(self, items, total):
                return {
                    "items": items,
                    "total": total,
                    "page": 1,
                    "page_size": 10,
                }
        
        mock_pagination = MockPagination()

        # 执行
        with patch.object(self.service, "build_response", side_effect=lambda x: f"response_{x.id}"):
            result = self.service.list_work_orders(mock_pagination)

        # 验证
        self.db.query.assert_called_once_with(WorkOrder)
        mock_count.assert_called_once()
        # 验证返回结果
        self.assertEqual(result["items"], ["response_1", "response_2"])
        self.assertEqual(result["total"], 2)

    @patch("app.common.query_filters.apply_pagination")
    def test_list_work_orders_with_filters(self, mock_apply_pagination):
        """测试查询工单列表 - 带过滤条件"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query

        mock_order = MagicMock(spec=WorkOrder)
        mock_order.id = 1
        mock_apply_pagination.return_value.all.return_value = [mock_order]

        self.db.query.return_value = mock_query

        mock_pagination = MagicMock()
        mock_pagination.offset = 0
        mock_pagination.limit = 10
        mock_pagination.to_response.return_value = {"items": [], "total": 1}

        # 执行 - 带所有过滤条件
        with patch.object(self.service, "build_response", return_value="response"):
            self.service.list_work_orders(
                mock_pagination,
                project_id=10,
                workshop_id=20,
                status="IN_PROGRESS",
                priority=3,
                assigned_to=30,
            )

        # 验证调用了5次filter（每个条件一次）
        self.assertEqual(mock_query.filter.call_count, 5)

    # ========== create_work_order() 测试 ==========

    @patch("app.api.v1.endpoints.production.utils.generate_work_order_no")
    @patch("app.utils.db_helpers.get_or_404")
    @patch("app.utils.db_helpers.save_obj")
    def test_create_work_order_success(self, mock_save_obj, mock_get_or_404, mock_generate_no):
        """测试创建工单 - 成功"""
        mock_generate_no.return_value = "WO-2024-NEW"

        # Mock workstation with matching workshop_id
        mock_workstation = MagicMock(spec=Workstation)
        mock_workstation.workshop_id = 50  # 匹配workshop_id

        # Mock验证成功
        mock_get_or_404.side_effect = [
            MagicMock(spec=Project),  # project
            MagicMock(spec=Machine),  # machine
            MagicMock(spec=ProductionPlan),  # plan
            MagicMock(spec=Workshop),  # workshop
            mock_workstation,  # workstation
        ]

        # Mock order_in
        mock_order_in = MagicMock()
        mock_order_in.project_id = 10
        mock_order_in.machine_id = 20
        mock_order_in.production_plan_id = 30
        mock_order_in.workshop_id = 50
        mock_order_in.workstation_id = 60
        mock_order_in.model_dump.return_value = {
            "task_name": "新任务",
            "task_type": "加工",
            "project_id": 10,
            "machine_id": 20,
            "production_plan_id": 30,
            "workshop_id": 50,
            "workstation_id": 60,
        }

        # Mock build_response
        mock_response = MagicMock(spec=WorkOrderResponse)
        with patch.object(self.service, "build_response", return_value=mock_response):
            result = self.service.create_work_order(mock_order_in, current_user_id=100)

        # 验证
        self.assertEqual(result, mock_response)
        mock_save_obj.assert_called_once()
        saved_order = mock_save_obj.call_args[0][1]
        self.assertEqual(saved_order.work_order_no, "WO-2024-NEW")
        self.assertEqual(saved_order.status, "PENDING")
        self.assertEqual(saved_order.progress, 0)
        self.assertEqual(saved_order.created_by, 100)

    @patch("app.api.v1.endpoints.production.utils.generate_work_order_no")
    @patch("app.utils.db_helpers.get_or_404")
    def test_create_work_order_invalid_project(self, mock_get_or_404, mock_generate_no):
        """测试创建工单 - 项目不存在"""
        # 第一次调用get_or_404就抛出异常（项目不存在）
        mock_get_or_404.side_effect = HTTPException(status_code=404, detail="项目不存在")

        mock_order_in = MagicMock()
        mock_order_in.project_id = 999
        mock_order_in.machine_id = None
        mock_order_in.production_plan_id = None
        mock_order_in.workshop_id = None
        mock_order_in.workstation_id = None

        with self.assertRaises(HTTPException) as context:
            self.service.create_work_order(mock_order_in, current_user_id=100)

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "项目不存在")
        # 验证只调用了一次get_or_404（在project验证时就失败了）
        mock_get_or_404.assert_called_once()

    @patch("app.api.v1.endpoints.production.utils.generate_work_order_no")
    @patch("app.utils.db_helpers.get_or_404")
    def test_create_work_order_workstation_wrong_workshop(self, mock_get_or_404, mock_generate_no):
        """测试创建工单 - 工位不属于该车间"""
        mock_get_or_404.side_effect = [
            None,  # project_id is None
            None,  # machine_id is None
            None,  # production_plan_id is None
            MagicMock(spec=Workshop),  # workshop
            MagicMock(spec=Workstation, workshop_id=999),  # workstation (不匹配)
        ]

        mock_order_in = MagicMock()
        mock_order_in.project_id = None
        mock_order_in.machine_id = None
        mock_order_in.production_plan_id = None
        mock_order_in.workshop_id = 50
        mock_order_in.workstation_id = 60

        with self.assertRaises(HTTPException) as context:
            self.service.create_work_order(mock_order_in, current_user_id=100)

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "工位不属于该车间")

    # ========== get_work_order() 测试 ==========

    @patch("app.utils.db_helpers.get_or_404")
    def test_get_work_order_success(self, mock_get_or_404):
        """测试获取工单详情 - 成功"""
        mock_order = MagicMock(spec=WorkOrder)
        mock_order.id = 1
        mock_order.work_order_no = "WO-2024-001"
        mock_order.task_name = "Test Task"
        mock_order.task_type = "MACHINING"
        mock_order.status = "PENDING"
        mock_order.priority = "NORMAL"
        mock_order.progress = 0
        mock_order.plan_qty = 10
        mock_order.completed_qty = 0
        mock_order.qualified_qty = 0
        mock_order.defect_qty = 0
        mock_order.actual_hours = 0
        mock_order.created_at = datetime.now()
        mock_order.updated_at = datetime.now()
        # 设置所有可选字段为None
        for attr in ['project_id', 'machine_id', 'production_plan_id', 'process_id',
                     'workshop_id', 'workstation_id', 'assigned_to', 'material_name',
                     'specification', 'standard_hours', 'plan_start_date', 'plan_end_date',
                     'actual_start_time', 'actual_end_time', 'work_content', 'remark']:
            setattr(mock_order, attr, None)
        
        mock_get_or_404.return_value = mock_order

        result = self.service.get_work_order(1)

        self.assertIsInstance(result, WorkOrderResponse)
        self.assertEqual(result.id, 1)
        mock_get_or_404.assert_called_once_with(self.db, WorkOrder, 1, detail="工单不存在")

    @patch("app.utils.db_helpers.get_or_404")
    def test_get_work_order_not_found(self, mock_get_or_404):
        """测试获取工单详情 - 不存在"""
        # get_or_404抛出HTTPException
        mock_get_or_404.side_effect = HTTPException(status_code=404, detail="工单不存在")

        with self.assertRaises(HTTPException) as context:
            self.service.get_work_order(999)

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "工单不存在")

    # ========== assign_work_order() 测试 ==========

    @patch("app.utils.db_helpers.save_obj")
    @patch("app.utils.db_helpers.get_or_404")
    def test_assign_work_order_success(self, mock_get_or_404, mock_save_obj):
        """测试单个派工 - 成功"""
        mock_order = MagicMock(spec=WorkOrder)
        mock_order.status = "PENDING"
        mock_order.workshop_id = 50
        mock_order.workstation_id = None  # 初始化工位ID

        mock_worker = MagicMock(spec=Worker)
        mock_workstation = MagicMock(spec=Workstation)
        mock_workstation.workshop_id = 50

        mock_get_or_404.side_effect = [
            mock_order,  # 工单
            mock_worker,  # 工人
            mock_workstation,  # 工位
        ]

        mock_assign_in = MagicMock()
        mock_assign_in.assigned_to = 70
        mock_assign_in.workstation_id = 60

        mock_response = MagicMock(spec=WorkOrderResponse)
        with patch.object(self.service, "build_response", return_value=mock_response):
            result = self.service.assign_work_order(1, mock_assign_in, current_user_id=100)

        # 验证
        self.assertEqual(result, mock_response)
        self.assertEqual(mock_order.assigned_to, 70)
        self.assertEqual(mock_order.status, "ASSIGNED")
        self.assertEqual(mock_order.assigned_by, 100)
        self.assertEqual(mock_order.workstation_id, 60)
        self.assertIsNotNone(mock_order.assigned_at)
        mock_save_obj.assert_called_once()

    @patch("app.utils.db_helpers.get_or_404")
    def test_assign_work_order_invalid_status(self, mock_get_or_404):
        """测试单个派工 - 工单状态不正确"""
        mock_order = MagicMock(spec=WorkOrder)
        mock_order.status = "IN_PROGRESS"

        mock_get_or_404.return_value = mock_order

        mock_assign_in = MagicMock()
        mock_assign_in.assigned_to = 70

        with self.assertRaises(HTTPException) as context:
            self.service.assign_work_order(1, mock_assign_in, current_user_id=100)

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "只有待派工状态的工单才能派工")

    @patch("app.utils.db_helpers.get_or_404")
    def test_assign_work_order_worker_not_found(self, mock_get_or_404):
        """测试单个派工 - 工人不存在"""
        mock_order = MagicMock(spec=WorkOrder)
        mock_order.status = "PENDING"

        # 第一次返回工单，第二次工人不存在抛出异常
        mock_get_or_404.side_effect = [
            mock_order,  # 工单存在
            HTTPException(status_code=404, detail="工人不存在"),  # 工人不存在
        ]

        mock_assign_in = MagicMock()
        mock_assign_in.assigned_to = 999
        mock_assign_in.workstation_id = None

        with self.assertRaises(HTTPException) as context:
            self.service.assign_work_order(1, mock_assign_in, current_user_id=100)

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "工人不存在")

    @patch("app.utils.db_helpers.get_or_404")
    def test_assign_work_order_workstation_wrong_workshop(self, mock_get_or_404):
        """测试单个派工 - 工位不属于该车间"""
        mock_order = MagicMock(spec=WorkOrder)
        mock_order.status = "PENDING"
        mock_order.workshop_id = 50

        mock_worker = MagicMock(spec=Worker)
        
        mock_workstation = MagicMock(spec=Workstation)
        mock_workstation.workshop_id = 999  # 不匹配工单的车间ID

        mock_get_or_404.side_effect = [
            mock_order,  # 工单
            mock_worker,  # 工人
            mock_workstation,  # 工位（workshop_id不匹配）
        ]

        mock_assign_in = MagicMock()
        mock_assign_in.assigned_to = 70
        mock_assign_in.workstation_id = 60

        with self.assertRaises(HTTPException) as context:
            self.service.assign_work_order(1, mock_assign_in, current_user_id=100)

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "工位不属于该车间")

    @patch("app.utils.db_helpers.save_obj")
    @patch("app.utils.db_helpers.get_or_404")
    def test_assign_work_order_without_workstation(self, mock_get_or_404, mock_save_obj):
        """测试单个派工 - 不指定工位"""
        mock_order = MagicMock(spec=WorkOrder)
        mock_order.status = "PENDING"
        mock_order.workshop_id = 50
        mock_order.workstation_id = None  # 初始值为None
        mock_order.assigned_to = None

        mock_worker = MagicMock(spec=Worker)

        mock_get_or_404.side_effect = [
            mock_order,
            mock_worker,
        ]

        mock_assign_in = MagicMock()
        mock_assign_in.assigned_to = 70
        mock_assign_in.workstation_id = None

        mock_response = MagicMock(spec=WorkOrderResponse)
        with patch.object(self.service, "build_response", return_value=mock_response):
            result = self.service.assign_work_order(1, mock_assign_in, current_user_id=100)

        self.assertEqual(result, mock_response)
        # 验证没有修改workstation_id（保持原值）
        self.assertIsNone(mock_order.workstation_id)

    # ========== batch_assign() 测试 ==========

    def test_batch_assign_all_success(self):
        """测试批量派工 - 全部成功"""
        # Mock两个待派工的工单
        mock_order1 = MagicMock(spec=WorkOrder)
        mock_order1.id = 1
        mock_order1.status = "PENDING"

        mock_order2 = MagicMock(spec=WorkOrder)
        mock_order2.id = 2
        mock_order2.status = "PENDING"

        mock_worker = MagicMock(spec=Worker)
        mock_worker.worker_name = "张三"

        mock_workstation = MagicMock(spec=Workstation)

        # 使用计数器跟踪调用
        call_counts = {"WorkOrder": 0, "Worker": 0, "Workstation": 0}

        # Mock查询
        def query_side_effect(model):
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_query.filter.return_value = mock_filter

            if model == WorkOrder:
                # 每次调用返回不同的工单
                call_counts["WorkOrder"] += 1
                if call_counts["WorkOrder"] == 1:
                    mock_filter.first.return_value = mock_order1
                else:
                    mock_filter.first.return_value = mock_order2
            elif model == Worker:
                call_counts["Worker"] += 1
                mock_filter.first.return_value = mock_worker
            elif model == Workstation:
                call_counts["Workstation"] += 1
                mock_filter.first.return_value = mock_workstation

            return mock_query

        self.db.query.side_effect = query_side_effect

        mock_assign_in = MagicMock()
        mock_assign_in.assigned_to = 70
        mock_assign_in.workstation_id = 60

        result = self.service.batch_assign([1, 2], mock_assign_in, current_user_id=100)

        # 验证
        self.assertEqual(result["data"]["success_count"], 2)
        self.assertEqual(len(result["data"]["failed_orders"]), 0)
        self.db.commit.assert_called_once()

    def test_batch_assign_order_not_found(self):
        """测试批量派工 - 工单不存在"""
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = None
        mock_query.filter.return_value = mock_filter
        self.db.query.return_value = mock_query

        mock_assign_in = MagicMock()
        mock_assign_in.assigned_to = 70
        mock_assign_in.workstation_id = None

        result = self.service.batch_assign([999], mock_assign_in, current_user_id=100)

        self.assertEqual(result["data"]["success_count"], 0)
        self.assertEqual(len(result["data"]["failed_orders"]), 1)
        self.assertEqual(result["data"]["failed_orders"][0]["reason"], "工单不存在")

    def test_batch_assign_invalid_status(self):
        """测试批量派工 - 工单状态不正确"""
        mock_order = MagicMock(spec=WorkOrder)
        mock_order.id = 1
        mock_order.status = "COMPLETED"

        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = mock_order
        mock_query.filter.return_value = mock_filter
        self.db.query.return_value = mock_query

        mock_assign_in = MagicMock()
        mock_assign_in.assigned_to = 70
        mock_assign_in.workstation_id = None

        result = self.service.batch_assign([1], mock_assign_in, current_user_id=100)

        self.assertEqual(result["data"]["success_count"], 0)
        self.assertEqual(len(result["data"]["failed_orders"]), 1)
        self.assertIn("不能派工", result["data"]["failed_orders"][0]["reason"])

    def test_batch_assign_worker_not_found(self):
        """测试批量派工 - 工人不存在"""
        mock_order = MagicMock(spec=WorkOrder)
        mock_order.id = 1
        mock_order.status = "PENDING"

        def query_side_effect(model):
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_query.filter.return_value = mock_filter

            if model == WorkOrder:
                mock_filter.first.return_value = mock_order
            elif model == Worker:
                mock_filter.first.return_value = None

            return mock_query

        self.db.query.side_effect = query_side_effect

        mock_assign_in = MagicMock()
        mock_assign_in.assigned_to = 999
        mock_assign_in.workstation_id = None

        result = self.service.batch_assign([1], mock_assign_in, current_user_id=100)

        self.assertEqual(result["data"]["success_count"], 0)
        self.assertEqual(len(result["data"]["failed_orders"]), 1)
        self.assertEqual(result["data"]["failed_orders"][0]["reason"], "工人不存在")

    def test_batch_assign_workstation_not_found(self):
        """测试批量派工 - 工位不存在"""
        mock_order = MagicMock(spec=WorkOrder)
        mock_order.id = 1
        mock_order.status = "PENDING"

        mock_worker = MagicMock(spec=Worker)
        mock_worker.worker_name = "张三"

        def query_side_effect(model):
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_query.filter.return_value = mock_filter

            if model == WorkOrder:
                mock_filter.first.return_value = mock_order
            elif model == Worker:
                mock_filter.first.return_value = mock_worker
            elif model == Workstation:
                mock_filter.first.return_value = None

            return mock_query

        self.db.query.side_effect = query_side_effect

        mock_assign_in = MagicMock()
        mock_assign_in.assigned_to = 70
        mock_assign_in.workstation_id = 999

        result = self.service.batch_assign([1], mock_assign_in, current_user_id=100)

        self.assertEqual(result["data"]["success_count"], 0)
        self.assertEqual(len(result["data"]["failed_orders"]), 1)
        self.assertEqual(result["data"]["failed_orders"][0]["reason"], "工位不存在")

    def test_batch_assign_partial_success(self):
        """测试批量派工 - 部分成功"""
        # 第一个工单成功，第二个工单状态错误
        mock_order1 = MagicMock(spec=WorkOrder)
        mock_order1.id = 1
        mock_order1.status = "PENDING"

        mock_order2 = MagicMock(spec=WorkOrder)
        mock_order2.id = 2
        mock_order2.status = "COMPLETED"

        mock_worker = MagicMock(spec=Worker)
        mock_worker.worker_name = "张三"

        def query_side_effect(model):
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_query.filter.return_value = mock_filter

            if model == WorkOrder:
                mock_filter.first.side_effect = [mock_order1, mock_order2]
            elif model == Worker:
                mock_filter.first.return_value = mock_worker

            return mock_query

        self.db.query.side_effect = query_side_effect

        mock_assign_in = MagicMock()
        mock_assign_in.assigned_to = 70
        mock_assign_in.workstation_id = None

        result = self.service.batch_assign([1, 2], mock_assign_in, current_user_id=100)

        self.assertEqual(result["data"]["success_count"], 1)
        self.assertEqual(len(result["data"]["failed_orders"]), 1)
        self.assertEqual(result["data"]["failed_orders"][0]["order_id"], 2)

    def test_batch_assign_exception_handling(self):
        """测试批量派工 - 异常处理"""
        mock_order = MagicMock(spec=WorkOrder)
        mock_order.id = 1
        mock_order.status = "PENDING"

        # Mock查询时抛出异常
        def query_side_effect(model):
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_query.filter.return_value = mock_filter

            if model == WorkOrder:
                mock_filter.first.return_value = mock_order
            elif model == Worker:
                raise Exception("数据库连接错误")

            return mock_query

        self.db.query.side_effect = query_side_effect

        mock_assign_in = MagicMock()
        mock_assign_in.assigned_to = 70
        mock_assign_in.workstation_id = None

        result = self.service.batch_assign([1], mock_assign_in, current_user_id=100)

        self.assertEqual(result["data"]["success_count"], 0)
        self.assertEqual(len(result["data"]["failed_orders"]), 1)
        self.assertIn("数据库连接错误", result["data"]["failed_orders"][0]["reason"])

    def test_batch_assign_only_worker(self):
        """测试批量派工 - 仅指定工人"""
        mock_order = MagicMock(spec=WorkOrder)
        mock_order.id = 1
        mock_order.status = "PENDING"

        mock_worker = MagicMock(spec=Worker)
        mock_worker.worker_name = "李四"

        def query_side_effect(model):
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_query.filter.return_value = mock_filter

            if model == WorkOrder:
                mock_filter.first.return_value = mock_order
            elif model == Worker:
                mock_filter.first.return_value = mock_worker

            return mock_query

        self.db.query.side_effect = query_side_effect

        mock_assign_in = MagicMock()
        mock_assign_in.assigned_to = 70
        mock_assign_in.workstation_id = None

        result = self.service.batch_assign([1], mock_assign_in, current_user_id=100)

        self.assertEqual(result["data"]["success_count"], 1)
        self.assertEqual(mock_order.assigned_to, 70)
        self.assertEqual(mock_order.assigned_to_name, "李四")


if __name__ == "__main__":
    unittest.main()
