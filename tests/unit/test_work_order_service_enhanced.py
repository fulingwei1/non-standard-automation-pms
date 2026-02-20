# -*- coding: utf-8 -*-
"""
工单管理服务单元测试 - 增强版

覆盖 WorkOrderService 的核心业务逻辑
目标覆盖率: 60%+
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.services.production.work_order_service import WorkOrderService


class TestWorkOrderService(unittest.TestCase):
    """工单管理服务测试"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = WorkOrderService(self.db)

    # ==================== build_response 测试 ====================
    
    def test_build_response_with_all_relations(self):
        """测试构建工单响应 - 所有关联都存在"""
        # 准备工单数据
        order = MagicMock()
        order.id = 1
        order.work_order_no = "WO-001"
        order.task_name = "测试任务"
        order.task_type = "PRODUCTION"
        order.project_id = 10
        order.machine_id = 20
        order.production_plan_id = 30
        order.process_id = 40
        order.workshop_id = 50
        order.workstation_id = 60
        order.assigned_to = 70
        order.material_name = "钢板"
        order.specification = "500x300"
        order.plan_qty = 100
        order.completed_qty = 50
        order.qualified_qty = 48
        order.defect_qty = 2
        order.standard_hours = 80.0
        order.actual_hours = 40.5
        order.plan_start_date = datetime(2024, 1, 1)
        order.plan_end_date = datetime(2024, 1, 10)
        order.actual_start_time = datetime(2024, 1, 2)
        order.actual_end_time = None
        order.status = "IN_PROGRESS"
        order.priority = "HIGH"
        order.progress = 50
        order.work_content = "生产加工"
        order.remark = "备注信息"
        order.created_at = datetime(2024, 1, 1)
        order.updated_at = datetime(2024, 1, 2)

        # Mock 所有关联查询
        mock_project = MagicMock()
        mock_project.project_name = "项目A"
        
        mock_machine = MagicMock()
        mock_machine.machine_name = "机台X"
        
        mock_workshop = MagicMock()
        mock_workshop.workshop_name = "车间1"
        
        mock_workstation = MagicMock()
        mock_workstation.workstation_name = "工位1"
        
        mock_process = MagicMock()
        mock_process.process_name = "加工"
        
        mock_worker = MagicMock()
        mock_worker.worker_name = "张三"

        def mock_query_filter(model):
            mock_result = MagicMock()
            if model.__name__ == "Project":
                mock_result.filter.return_value.first.return_value = mock_project
            elif model.__name__ == "Machine":
                mock_result.filter.return_value.first.return_value = mock_machine
            elif model.__name__ == "Workshop":
                mock_result.filter.return_value.first.return_value = mock_workshop
            elif model.__name__ == "Workstation":
                mock_result.filter.return_value.first.return_value = mock_workstation
            elif model.__name__ == "ProcessDict":
                mock_result.filter.return_value.first.return_value = mock_process
            elif model.__name__ == "Worker":
                mock_result.filter.return_value.first.return_value = mock_worker
            return mock_result

        self.db.query.side_effect = mock_query_filter

        # 执行
        result = self.service.build_response(order)

        # 验证
        self.assertEqual(result.id, 1)
        self.assertEqual(result.work_order_no, "WO-001")
        self.assertEqual(result.project_name, "项目A")
        self.assertEqual(result.machine_name, "机台X")
        self.assertEqual(result.workshop_name, "车间1")
        self.assertEqual(result.workstation_name, "工位1")
        self.assertEqual(result.process_name, "加工")
        self.assertEqual(result.assigned_worker_name, "张三")
        self.assertEqual(result.status, "IN_PROGRESS")
        self.assertEqual(result.priority, "HIGH")
        self.assertEqual(result.plan_qty, 100)
        self.assertEqual(result.completed_qty, 50)

    def test_build_response_with_no_relations(self):
        """测试构建工单响应 - 无关联数据"""
        order = MagicMock()
        order.id = 2
        order.work_order_no = "WO-002"
        order.project_id = None
        order.machine_id = None
        order.workshop_id = None
        order.workstation_id = None
        order.process_id = None
        order.assigned_to = None
        order.plan_qty = None
        order.completed_qty = None
        order.qualified_qty = None
        order.defect_qty = None
        order.standard_hours = None
        order.actual_hours = None
        order.progress = None

        # 执行
        result = self.service.build_response(order)

        # 验证
        self.assertIsNone(result.project_name)
        self.assertIsNone(result.machine_name)
        self.assertIsNone(result.workshop_name)
        self.assertIsNone(result.workstation_name)
        self.assertIsNone(result.process_name)
        self.assertIsNone(result.assigned_worker_name)
        self.assertEqual(result.plan_qty, 0)
        self.assertEqual(result.completed_qty, 0)
        self.assertEqual(result.progress, 0)

    def test_build_response_with_null_standard_hours(self):
        """测试构建工单响应 - standard_hours 为 None"""
        order = MagicMock()
        order.standard_hours = None
        order.actual_hours = 10.5
        order.project_id = None
        order.machine_id = None
        order.workshop_id = None
        order.workstation_id = None
        order.process_id = None
        order.assigned_to = None

        result = self.service.build_response(order)

        self.assertIsNone(result.standard_hours)
        self.assertEqual(result.actual_hours, 10.5)

    # ==================== list_work_orders 测试 ====================
    
    def test_list_work_orders_no_filters(self):
        """测试查询工单列表 - 无过滤条件"""
        # Mock 分页对象
        pagination = MagicMock()
        pagination.offset = 0
        pagination.limit = 10
        pagination.to_response = MagicMock(return_value={"items": [], "total": 0})

        # Mock 查询
        mock_query = self.db.query.return_value
        mock_query.count.return_value = 0
        
        with patch("app.services.production.work_order_service.apply_pagination") as mock_paginate:
            mock_paginate.return_value.all.return_value = []

            # 执行
            result = self.service.list_work_orders(pagination)

            # 验证
            self.db.query.assert_called_once()
            pagination.to_response.assert_called_once()

    def test_list_work_orders_with_all_filters(self):
        """测试查询工单列表 - 所有过滤条件"""
        pagination = MagicMock()
        pagination.offset = 0
        pagination.limit = 10

        # Mock 工单
        order = MagicMock()
        mock_query = self.db.query.return_value
        mock_filter1 = mock_query.filter.return_value
        mock_filter2 = mock_filter1.filter.return_value
        mock_filter3 = mock_filter2.filter.return_value
        mock_filter4 = mock_filter3.filter.return_value
        mock_filter5 = mock_filter4.filter.return_value
        mock_filter5.count.return_value = 1

        with patch("app.services.production.work_order_service.apply_pagination") as mock_paginate:
            mock_order_by = mock_filter5.order_by.return_value
            mock_paginate.return_value.all.return_value = [order]

            with patch.object(self.service, "build_response", return_value=MagicMock()):
                pagination.to_response = MagicMock(return_value={"items": [{}], "total": 1})

                # 执行
                result = self.service.list_work_orders(
                    pagination,
                    project_id=1,
                    workshop_id=2,
                    status="PENDING",
                    priority="HIGH",
                    assigned_to=3,
                )

                # 验证过滤调用
                self.assertEqual(mock_query.filter.call_count, 5)

    # ==================== create_work_order 测试 ====================
    
    @patch("app.services.production.work_order_service.save_obj")
    @patch("app.services.production.work_order_service.get_or_404")
    def test_create_work_order_success(self, mock_get, mock_save):
        """测试创建工单成功"""
        # Mock 输入
        order_in = MagicMock()
        order_in.project_id = 1
        order_in.machine_id = 2
        order_in.production_plan_id = 3
        order_in.workshop_id = 4
        order_in.workstation_id = 5
        order_in.model_dump.return_value = {
            "task_name": "测试",
            "task_type": "PRODUCTION",
        }

        # Mock 工位验证
        mock_workstation = MagicMock()
        mock_workstation.workshop_id = 4

        def get_or_404_side_effect(db, model, id, detail):
            if model.__name__ == "Workstation":
                return mock_workstation
            return MagicMock()

        mock_get.side_effect = get_or_404_side_effect

        with patch("app.services.production.work_order_service.generate_work_order_no") as mock_gen:
            mock_gen.return_value = "WO-20240101-001"

            with patch("app.services.production.work_order_service.WorkOrder") as MockWorkOrder:
                mock_order = MagicMock()
                MockWorkOrder.return_value = mock_order

                with patch.object(self.service, "build_response", return_value=MagicMock()):
                    # 执行
                    result = self.service.create_work_order(order_in, current_user_id=100)

                    # 验证
                    mock_gen.assert_called_once_with(self.db)
                    mock_save.assert_called_once_with(self.db, mock_order)
                    self.assertEqual(mock_get.call_count, 4)

    @patch("app.services.production.work_order_service.get_or_404")
    def test_create_work_order_workstation_mismatch(self, mock_get):
        """测试创建工单 - 工位不属于车间"""
        order_in = MagicMock()
        order_in.project_id = None
        order_in.machine_id = None
        order_in.production_plan_id = None
        order_in.workshop_id = 4
        order_in.workstation_id = 5

        # Mock 工位属于不同车间
        mock_workstation = MagicMock()
        mock_workstation.workshop_id = 999

        def get_or_404_side_effect(db, model, id, detail):
            if model.__name__ == "Workstation":
                return mock_workstation
            return MagicMock()

        mock_get.side_effect = get_or_404_side_effect

        # 执行并验证异常
        with self.assertRaises(HTTPException) as context:
            self.service.create_work_order(order_in, current_user_id=100)

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("工位不属于该车间", context.exception.detail)

    # ==================== get_work_order 测试 ====================
    
    @patch("app.services.production.work_order_service.get_or_404")
    def test_get_work_order_success(self, mock_get):
        """测试获取工单详情成功"""
        mock_order = MagicMock()
        mock_get.return_value = mock_order

        with patch.object(self.service, "build_response", return_value=MagicMock()) as mock_build:
            # 执行
            result = self.service.get_work_order(order_id=1)

            # 验证
            mock_get.assert_called_once()
            mock_build.assert_called_once_with(mock_order)

    @patch("app.services.production.work_order_service.get_or_404")
    def test_get_work_order_not_found(self, mock_get):
        """测试获取不存在的工单"""
        mock_get.side_effect = HTTPException(status_code=404, detail="工单不存在")

        # 执行并验证异常
        with self.assertRaises(HTTPException) as context:
            self.service.get_work_order(order_id=999)

        self.assertEqual(context.exception.status_code, 404)

    # ==================== assign_work_order 测试 ====================
    
    @patch("app.services.production.work_order_service.save_obj")
    @patch("app.services.production.work_order_service.get_or_404")
    def test_assign_work_order_success(self, mock_get, mock_save):
        """测试工单派工成功"""
        # Mock 工单
        mock_order = MagicMock()
        mock_order.status = "PENDING"
        mock_order.workshop_id = 10

        # Mock 工人和工位
        mock_worker = MagicMock()
        mock_workstation = MagicMock()
        mock_workstation.workshop_id = 10

        def get_or_404_side_effect(db, model, id, detail=None):
            if model.__name__ == "WorkOrder":
                return mock_order
            elif model.__name__ == "Worker":
                return mock_worker
            elif model.__name__ == "Workstation":
                return mock_workstation
            return MagicMock()

        mock_get.side_effect = get_or_404_side_effect

        # Mock 派工输入
        assign_in = MagicMock()
        assign_in.assigned_to = 5
        assign_in.workstation_id = 6

        with patch.object(self.service, "build_response", return_value=MagicMock()):
            # 执行
            result = self.service.assign_work_order(
                order_id=1,
                assign_in=assign_in,
                current_user_id=100,
            )

            # 验证
            self.assertEqual(mock_order.assigned_to, 5)
            self.assertEqual(mock_order.workstation_id, 6)
            self.assertEqual(mock_order.status, "ASSIGNED")
            self.assertIsNotNone(mock_order.assigned_at)
            self.assertEqual(mock_order.assigned_by, 100)
            mock_save.assert_called_once_with(self.db, mock_order)

    @patch("app.services.production.work_order_service.get_or_404")
    def test_assign_work_order_invalid_status(self, mock_get):
        """测试派工失败 - 工单状态不是 PENDING"""
        mock_order = MagicMock()
        mock_order.status = "IN_PROGRESS"

        mock_get.return_value = mock_order

        assign_in = MagicMock()
        assign_in.assigned_to = 5

        # 执行并验证异常
        with self.assertRaises(HTTPException) as context:
            self.service.assign_work_order(
                order_id=1,
                assign_in=assign_in,
                current_user_id=100,
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("只有待派工状态", context.exception.detail)

    @patch("app.services.production.work_order_service.get_or_404")
    def test_assign_work_order_workstation_mismatch(self, mock_get):
        """测试派工失败 - 工位不属于车间"""
        mock_order = MagicMock()
        mock_order.status = "PENDING"
        mock_order.workshop_id = 10

        mock_worker = MagicMock()
        mock_workstation = MagicMock()
        mock_workstation.workshop_id = 999

        def get_or_404_side_effect(db, model, id, detail=None):
            if model.__name__ == "WorkOrder":
                return mock_order
            elif model.__name__ == "Worker":
                return mock_worker
            elif model.__name__ == "Workstation":
                return mock_workstation
            return MagicMock()

        mock_get.side_effect = get_or_404_side_effect

        assign_in = MagicMock()
        assign_in.assigned_to = 5
        assign_in.workstation_id = 6

        # 执行并验证异常
        with self.assertRaises(HTTPException) as context:
            self.service.assign_work_order(
                order_id=1,
                assign_in=assign_in,
                current_user_id=100,
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("工位不属于该车间", context.exception.detail)

    @patch("app.services.production.work_order_service.save_obj")
    @patch("app.services.production.work_order_service.get_or_404")
    def test_assign_work_order_without_workstation(self, mock_get, mock_save):
        """测试派工成功 - 不指定工位"""
        mock_order = MagicMock()
        mock_order.status = "PENDING"

        mock_worker = MagicMock()

        def get_or_404_side_effect(db, model, id, detail=None):
            if model.__name__ == "WorkOrder":
                return mock_order
            elif model.__name__ == "Worker":
                return mock_worker
            return MagicMock()

        mock_get.side_effect = get_or_404_side_effect

        assign_in = MagicMock()
        assign_in.assigned_to = 5
        assign_in.workstation_id = None

        with patch.object(self.service, "build_response", return_value=MagicMock()):
            # 执行
            result = self.service.assign_work_order(
                order_id=1,
                assign_in=assign_in,
                current_user_id=100,
            )

            # 验证
            self.assertEqual(mock_order.assigned_to, 5)
            self.assertEqual(mock_order.status, "ASSIGNED")

    # ==================== batch_assign 测试 ====================
    
    def test_batch_assign_all_success(self):
        """测试批量派工 - 全部成功"""
        # Mock 工单
        order1 = MagicMock()
        order1.id = 1
        order1.status = "PENDING"
        order1.workshop_id = 10

        order2 = MagicMock()
        order2.id = 2
        order2.status = "PENDING"
        order2.workshop_id = 10

        # Mock 工人和工位
        mock_worker = MagicMock()
        mock_worker.worker_name = "张三"

        mock_workstation = MagicMock()
        mock_workstation.workshop_id = 10

        def query_side_effect(model):
            mock_result = MagicMock()
            if model.__name__ == "WorkOrder":
                filter_result = MagicMock()
                filter_result.filter.return_value.first.side_effect = [order1, order2]
                mock_result.filter.return_value = filter_result
            elif model.__name__ == "Worker":
                mock_result.filter.return_value.first.return_value = mock_worker
            elif model.__name__ == "Workstation":
                mock_result.filter.return_value.first.return_value = mock_workstation
            return mock_result

        self.db.query.side_effect = query_side_effect

        assign_in = MagicMock()
        assign_in.assigned_to = 5
        assign_in.workstation_id = 6

        # 执行
        result = self.service.batch_assign(
            order_ids=[1, 2],
            assign_in=assign_in,
            current_user_id=100,
        )

        # 验证
        self.assertEqual(result["code"], 200)
        self.assertEqual(result["data"]["success_count"], 2)
        self.assertEqual(len(result["data"]["failed_orders"]), 0)
        self.db.commit.assert_called_once()

    def test_batch_assign_order_not_found(self):
        """测试批量派工 - 工单不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        assign_in = MagicMock()
        assign_in.assigned_to = 5

        # 执行
        result = self.service.batch_assign(
            order_ids=[999],
            assign_in=assign_in,
            current_user_id=100,
        )

        # 验证
        self.assertEqual(result["data"]["success_count"], 0)
        self.assertEqual(len(result["data"]["failed_orders"]), 1)
        self.assertIn("工单不存在", result["data"]["failed_orders"][0]["reason"])

    def test_batch_assign_invalid_status(self):
        """测试批量派工 - 工单状态不正确"""
        order = MagicMock()
        order.id = 1
        order.status = "COMPLETED"

        self.db.query.return_value.filter.return_value.first.return_value = order

        assign_in = MagicMock()
        assign_in.assigned_to = 5

        # 执行
        result = self.service.batch_assign(
            order_ids=[1],
            assign_in=assign_in,
            current_user_id=100,
        )

        # 验证
        self.assertEqual(result["data"]["success_count"], 0)
        self.assertEqual(len(result["data"]["failed_orders"]), 1)
        self.assertIn("不能派工", result["data"]["failed_orders"][0]["reason"])

    def test_batch_assign_worker_not_found(self):
        """测试批量派工 - 工人不存在"""
        order = MagicMock()
        order.id = 1
        order.status = "PENDING"

        def query_side_effect(model):
            mock_result = MagicMock()
            if model.__name__ == "WorkOrder":
                mock_result.filter.return_value.first.return_value = order
            elif model.__name__ == "Worker":
                mock_result.filter.return_value.first.return_value = None
            return mock_result

        self.db.query.side_effect = query_side_effect

        assign_in = MagicMock()
        assign_in.assigned_to = 999

        # 执行
        result = self.service.batch_assign(
            order_ids=[1],
            assign_in=assign_in,
            current_user_id=100,
        )

        # 验证
        self.assertEqual(result["data"]["success_count"], 0)
        self.assertEqual(len(result["data"]["failed_orders"]), 1)
        self.assertIn("工人不存在", result["data"]["failed_orders"][0]["reason"])

    def test_batch_assign_workstation_not_found(self):
        """测试批量派工 - 工位不存在"""
        order = MagicMock()
        order.id = 1
        order.status = "PENDING"

        mock_worker = MagicMock()
        mock_worker.worker_name = "张三"

        def query_side_effect(model):
            mock_result = MagicMock()
            if model.__name__ == "WorkOrder":
                mock_result.filter.return_value.first.return_value = order
            elif model.__name__ == "Worker":
                mock_result.filter.return_value.first.return_value = mock_worker
            elif model.__name__ == "Workstation":
                mock_result.filter.return_value.first.return_value = None
            return mock_result

        self.db.query.side_effect = query_side_effect

        assign_in = MagicMock()
        assign_in.assigned_to = 5
        assign_in.workstation_id = 999

        # 执行
        result = self.service.batch_assign(
            order_ids=[1],
            assign_in=assign_in,
            current_user_id=100,
        )

        # 验证
        self.assertEqual(result["data"]["success_count"], 0)
        self.assertEqual(len(result["data"]["failed_orders"]), 1)
        self.assertIn("工位不存在", result["data"]["failed_orders"][0]["reason"])

    def test_batch_assign_partial_success(self):
        """测试批量派工 - 部分成功"""
        order1 = MagicMock()
        order1.id = 1
        order1.status = "PENDING"

        order2 = MagicMock()
        order2.id = 2
        order2.status = "COMPLETED"  # 状态错误

        mock_worker = MagicMock()
        mock_worker.worker_name = "张三"

        call_count = [0]

        def query_side_effect(model):
            mock_result = MagicMock()
            if model.__name__ == "WorkOrder":
                def first_side_effect():
                    call_count[0] += 1
                    if call_count[0] == 1:
                        return order1
                    else:
                        return order2
                mock_result.filter.return_value.first.side_effect = first_side_effect
            elif model.__name__ == "Worker":
                mock_result.filter.return_value.first.return_value = mock_worker
            return mock_result

        self.db.query.side_effect = query_side_effect

        assign_in = MagicMock()
        assign_in.assigned_to = 5
        assign_in.workstation_id = None

        # 执行
        result = self.service.batch_assign(
            order_ids=[1, 2],
            assign_in=assign_in,
            current_user_id=100,
        )

        # 验证
        self.assertEqual(result["data"]["success_count"], 1)
        self.assertEqual(len(result["data"]["failed_orders"]), 1)
        self.assertEqual(result["data"]["failed_orders"][0]["order_id"], 2)

    def test_batch_assign_exception_handling(self):
        """测试批量派工 - 异常处理"""
        order = MagicMock()
        order.id = 1
        order.status = "PENDING"

        def query_side_effect(model):
            mock_result = MagicMock()
            if model.__name__ == "WorkOrder":
                mock_result.filter.return_value.first.return_value = order
            elif model.__name__ == "Worker":
                raise Exception("数据库错误")
            return mock_result

        self.db.query.side_effect = query_side_effect

        assign_in = MagicMock()
        assign_in.assigned_to = 5

        # 执行
        result = self.service.batch_assign(
            order_ids=[1],
            assign_in=assign_in,
            current_user_id=100,
        )

        # 验证
        self.assertEqual(result["data"]["success_count"], 0)
        self.assertEqual(len(result["data"]["failed_orders"]), 1)
        self.assertIn("数据库错误", result["data"]["failed_orders"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
