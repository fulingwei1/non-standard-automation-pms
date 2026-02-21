# -*- coding: utf-8 -*-
"""
ECN集成服务增强单元测试
测试覆盖所有核心方法、边界条件和异常处理
"""

import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, call

from app.services.ecn_integration.ecn_integration_service import EcnIntegrationService
from app.schemas.ecn import EcnTaskCreate


class TestEcnIntegrationServiceSyncToBom(unittest.TestCase):
    """测试同步到BOM的功能"""

    def setUp(self):
        """设置测试环境"""
        self.db = MagicMock()
        self.service = EcnIntegrationService(self.db)

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_bom_success_update_quantity(self, mock_get_or_404):
        """测试成功同步BOM - 更新数量"""
        # 准备测试数据
        ecn = MagicMock()
        ecn.id = 1
        ecn.status = "APPROVED"
        mock_get_or_404.return_value = ecn

        # 模拟受影响的物料
        affected_material = MagicMock()
        affected_material.bom_item_id = 10
        affected_material.change_type = "UPDATE"
        affected_material.new_quantity = Decimal("100")
        affected_material.new_specification = None
        affected_material.material_id = None

        # 模拟BOM项
        bom_item = MagicMock()
        bom_item.id = 10
        bom_item.qty = 50.0

        self.db.query.return_value.filter.return_value.all.return_value = [affected_material]
        self.db.query.return_value.filter.return_value.first.return_value = bom_item

        # 执行同步
        result = self.service.sync_to_bom(1)

        # 验证结果
        self.assertEqual(result["updated_count"], 1)
        self.assertEqual(bom_item.qty, 100.0)
        self.assertEqual(affected_material.status, "PROCESSED")
        self.assertIsNotNone(affected_material.processed_at)
        self.db.commit.assert_called_once()

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_bom_success_update_specification(self, mock_get_or_404):
        """测试成功同步BOM - 更新规格"""
        ecn = MagicMock()
        ecn.status = "EXECUTING"
        mock_get_or_404.return_value = ecn

        affected_material = MagicMock()
        affected_material.bom_item_id = 10
        affected_material.change_type = "UPDATE"
        affected_material.new_quantity = None
        affected_material.new_specification = "新规格"
        affected_material.material_id = None

        bom_item = MagicMock()
        bom_item.specification = "旧规格"

        self.db.query.return_value.filter.return_value.all.return_value = [affected_material]
        self.db.query.return_value.filter.return_value.first.return_value = bom_item

        result = self.service.sync_to_bom(1)

        self.assertEqual(result["updated_count"], 1)
        self.assertEqual(bom_item.specification, "新规格")

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_bom_success_replace_material(self, mock_get_or_404):
        """测试成功同步BOM - 替换物料"""
        ecn = MagicMock()
        ecn.status = "APPROVED"
        mock_get_or_404.return_value = ecn

        affected_material = MagicMock()
        affected_material.bom_item_id = 10
        affected_material.change_type = "REPLACE"
        affected_material.new_quantity = None
        affected_material.new_specification = None
        affected_material.material_id = 999

        bom_item = MagicMock()
        bom_item.material_id = 123

        self.db.query.return_value.filter.return_value.all.return_value = [affected_material]
        self.db.query.return_value.filter.return_value.first.return_value = bom_item

        result = self.service.sync_to_bom(1)

        self.assertEqual(result["updated_count"], 1)
        self.assertEqual(bom_item.material_id, 999)

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_bom_invalid_status_draft(self, mock_get_or_404):
        """测试同步BOM失败 - ECN状态为草稿"""
        ecn = MagicMock()
        ecn.status = "DRAFT"
        mock_get_or_404.return_value = ecn

        with self.assertRaises(ValueError) as context:
            self.service.sync_to_bom(1)
        
        self.assertIn("只能同步已审批或执行中的ECN", str(context.exception))

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_bom_invalid_status_pending(self, mock_get_or_404):
        """测试同步BOM失败 - ECN状态为待审批"""
        ecn = MagicMock()
        ecn.status = "PENDING"
        mock_get_or_404.return_value = ecn

        with self.assertRaises(ValueError) as context:
            self.service.sync_to_bom(1)
        
        self.assertIn("只能同步已审批或执行中的ECN", str(context.exception))

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_bom_no_affected_materials(self, mock_get_or_404):
        """测试同步BOM - 没有待处理的受影响物料"""
        ecn = MagicMock()
        ecn.status = "APPROVED"
        mock_get_or_404.return_value = ecn

        self.db.query.return_value.filter.return_value.all.return_value = []

        result = self.service.sync_to_bom(1)

        self.assertEqual(result["updated_count"], 0)
        self.db.commit.assert_called_once()

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_bom_bom_item_not_found(self, mock_get_or_404):
        """测试同步BOM - BOM项不存在"""
        ecn = MagicMock()
        ecn.status = "APPROVED"
        mock_get_or_404.return_value = ecn

        affected_material = MagicMock()
        affected_material.bom_item_id = 10
        affected_material.change_type = "UPDATE"

        self.db.query.return_value.filter.return_value.all.return_value = [affected_material]
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.sync_to_bom(1)

        # BOM项不存在时，不会更新
        self.assertEqual(result["updated_count"], 0)


class TestEcnIntegrationServiceSyncToProject(unittest.TestCase):
    """测试同步到项目的功能"""

    def setUp(self):
        self.db = MagicMock()
        self.service = EcnIntegrationService(self.db)

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_project_success_with_cost_impact(self, mock_get_or_404):
        """测试成功同步到项目 - 包含成本影响"""
        ecn = MagicMock()
        ecn.id = 1
        ecn.project_id = 100
        ecn.cost_impact = Decimal("5000.00")
        ecn.schedule_impact_days = None
        mock_get_or_404.return_value = ecn

        project = MagicMock()
        project.id = 100
        project.total_cost = Decimal("100000.00")
        project.planned_end_date = None

        self.db.query.return_value.filter.return_value.first.return_value = project

        result = self.service.sync_to_project(1)

        self.assertEqual(result["cost_impact"], 5000.00)
        self.assertEqual(result["schedule_impact_days"], 0)
        self.assertEqual(project.total_cost, Decimal("105000.00"))
        self.db.commit.assert_called_once()

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_project_success_with_schedule_impact(self, mock_get_or_404):
        """测试成功同步到项目 - 包含工期影响"""
        ecn = MagicMock()
        ecn.project_id = 100
        ecn.cost_impact = None
        ecn.schedule_impact_days = 10
        mock_get_or_404.return_value = ecn

        project = MagicMock()
        project.total_cost = Decimal("100000.00")
        project.planned_end_date = datetime(2026, 3, 1)

        self.db.query.return_value.filter.return_value.first.return_value = project

        result = self.service.sync_to_project(1)

        self.assertEqual(result["cost_impact"], 0)
        self.assertEqual(result["schedule_impact_days"], 10)
        self.assertEqual(project.planned_end_date, datetime(2026, 3, 11))

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_project_no_project_id(self, mock_get_or_404):
        """测试同步到项目失败 - ECN未关联项目"""
        ecn = MagicMock()
        ecn.project_id = None
        mock_get_or_404.return_value = ecn

        with self.assertRaises(ValueError) as context:
            self.service.sync_to_project(1)
        
        self.assertIn("ECN未关联项目", str(context.exception))

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_project_project_not_found(self, mock_get_or_404):
        """测试同步到项目失败 - 项目不存在"""
        ecn = MagicMock()
        ecn.project_id = 100
        mock_get_or_404.return_value = ecn

        self.db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.sync_to_project(1)
        
        self.assertIn("项目不存在", str(context.exception))

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_project_project_cost_zero(self, mock_get_or_404):
        """测试同步到项目 - 项目初始成本为0"""
        ecn = MagicMock()
        ecn.project_id = 100
        ecn.cost_impact = Decimal("5000.00")
        ecn.schedule_impact_days = None
        mock_get_or_404.return_value = ecn

        project = MagicMock()
        project.total_cost = None
        project.planned_end_date = None

        self.db.query.return_value.filter.return_value.first.return_value = project

        result = self.service.sync_to_project(1)

        self.assertEqual(project.total_cost, Decimal("5000.00"))


class TestEcnIntegrationServiceSyncToPurchase(unittest.TestCase):
    """测试同步到采购的功能"""

    def setUp(self):
        self.db = MagicMock()
        self.service = EcnIntegrationService(self.db)

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_purchase_success_cancel(self, mock_get_or_404):
        """测试成功同步到采购 - 取消订单"""
        ecn = MagicMock()
        mock_get_or_404.return_value = ecn

        affected_order = MagicMock()
        affected_order.order_id = 200
        affected_order.action_type = "CANCEL"

        purchase_order = MagicMock()
        purchase_order.id = 200
        purchase_order.status = "CONFIRMED"

        self.db.query.return_value.filter.return_value.all.return_value = [affected_order]
        self.db.query.return_value.filter.return_value.first.return_value = purchase_order

        result = self.service.sync_to_purchase(1, current_user_id=999)

        self.assertEqual(result["updated_count"], 1)
        self.assertEqual(purchase_order.status, "CANCELLED")
        self.assertEqual(affected_order.status, "PROCESSED")
        self.assertEqual(affected_order.processed_by, 999)
        self.assertIsNotNone(affected_order.processed_at)

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_purchase_success_modify(self, mock_get_or_404):
        """测试成功同步到采购 - 修改订单"""
        ecn = MagicMock()
        mock_get_or_404.return_value = ecn

        affected_order = MagicMock()
        affected_order.order_id = 200
        affected_order.action_type = "MODIFY"

        purchase_order = MagicMock()
        self.db.query.return_value.filter.return_value.all.return_value = [affected_order]
        self.db.query.return_value.filter.return_value.first.return_value = purchase_order

        result = self.service.sync_to_purchase(1, current_user_id=999)

        self.assertEqual(result["updated_count"], 1)
        self.assertEqual(affected_order.status, "PROCESSED")

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_purchase_no_affected_orders(self, mock_get_or_404):
        """测试同步到采购 - 没有待处理的订单"""
        ecn = MagicMock()
        mock_get_or_404.return_value = ecn

        self.db.query.return_value.filter.return_value.all.return_value = []

        result = self.service.sync_to_purchase(1, current_user_id=999)

        self.assertEqual(result["updated_count"], 0)

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_purchase_order_not_found(self, mock_get_or_404):
        """测试同步到采购 - 采购订单不存在"""
        ecn = MagicMock()
        mock_get_or_404.return_value = ecn

        affected_order = MagicMock()
        affected_order.order_id = 200

        self.db.query.return_value.filter.return_value.all.return_value = [affected_order]
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.sync_to_purchase(1, current_user_id=999)

        self.assertEqual(result["updated_count"], 0)


class TestEcnIntegrationServiceBatchSync(unittest.TestCase):
    """测试批量同步功能"""

    def setUp(self):
        self.db = MagicMock()
        self.service = EcnIntegrationService(self.db)

    def test_batch_sync_to_bom_all_success(self):
        """测试批量同步BOM - 全部成功"""
        ecn1 = MagicMock()
        ecn1.id = 1
        ecn1.ecn_no = "ECN-001"
        ecn1.status = "APPROVED"

        ecn2 = MagicMock()
        ecn2.id = 2
        ecn2.ecn_no = "ECN-002"
        ecn2.status = "EXECUTING"

        def query_side_effect(*args):
            mock_query = MagicMock()
            if args[0].__name__ == 'Ecn':
                def filter_side_effect(*filter_args):
                    mock_filter = MagicMock()
                    mock_filter.first.side_effect = [ecn1, ecn2]
                    return mock_filter
                mock_query.filter.side_effect = filter_side_effect
            else:
                mock_query.filter.return_value.all.return_value = []
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.service.batch_sync_to_bom([1, 2])

        self.assertEqual(result["total"], 2)
        self.assertEqual(result["success_count"], 2)
        self.assertEqual(result["fail_count"], 0)
        self.assertEqual(len(result["results"]), 2)

    def test_batch_sync_to_bom_partial_success(self):
        """测试批量同步BOM - 部分成功（ECN不存在）"""
        # 第一个ECN不存在，第二个存在且状态正确
        ecn2 = MagicMock()
        ecn2.id = 2
        ecn2.ecn_no = "ECN-002"
        ecn2.status = "APPROVED"

        query_results = [None, ecn2, ecn2]  # 第一个查询返回None，后续查询返回ecn2
        query_idx = [0]

        def query_side_effect(*args):
            mock_query = MagicMock()
            if args[0].__name__ == 'Ecn':
                def filter_side_effect(*filter_args):
                    mock_filter = MagicMock()
                    result = query_results[min(query_idx[0], len(query_results) - 1)]
                    query_idx[0] += 1
                    mock_filter.first.return_value = result
                    return mock_filter
                mock_query.filter.side_effect = filter_side_effect
            else:
                # EcnAffectedMaterial查询
                mock_query.filter.return_value.all.return_value = []
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.service.batch_sync_to_bom([1, 2])

        self.assertEqual(result["total"], 2)
        self.assertEqual(result["success_count"], 1)
        self.assertEqual(result["fail_count"], 1)
        self.assertIn("ECN不存在", result["results"][0]["message"])

    def test_batch_sync_to_bom_ecn_not_found(self):
        """测试批量同步BOM - ECN不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.batch_sync_to_bom([999])

        self.assertEqual(result["total"], 1)
        self.assertEqual(result["success_count"], 0)
        self.assertEqual(result["fail_count"], 1)
        self.assertIn("ECN不存在", result["results"][0]["message"])

    def test_batch_sync_to_project_all_success(self):
        """测试批量同步项目 - 全部成功"""
        ecn = MagicMock()
        ecn.id = 1
        ecn.ecn_no = "ECN-001"
        ecn.project_id = 100
        ecn.cost_impact = Decimal("1000")
        ecn.schedule_impact_days = 5

        project = MagicMock()
        project.id = 100
        project.total_cost = Decimal("10000")
        project.planned_end_date = datetime(2026, 3, 1)

        def query_side_effect(*args):
            mock_query = MagicMock()
            mock_filter = MagicMock()
            if args[0].__name__ == 'Ecn':
                mock_filter.first.return_value = ecn
            elif args[0].__name__ == 'Project':
                mock_filter.first.return_value = project
            mock_query.filter.return_value = mock_filter
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.service.batch_sync_to_project([1])

        self.assertEqual(result["success_count"], 1)
        self.assertEqual(result["fail_count"], 0)

    def test_batch_sync_to_project_no_project_id(self):
        """测试批量同步项目 - ECN未关联项目"""
        ecn = MagicMock()
        ecn.id = 1
        ecn.project_id = None

        self.db.query.return_value.filter.return_value.first.return_value = ecn

        result = self.service.batch_sync_to_project([1])

        self.assertEqual(result["fail_count"], 1)
        self.assertIn("ECN未关联项目", result["results"][0]["message"])

    def test_batch_sync_to_purchase_all_success(self):
        """测试批量同步采购 - 全部成功"""
        ecn = MagicMock()
        ecn.id = 1
        ecn.ecn_no = "ECN-001"

        def query_side_effect(*args):
            mock_query = MagicMock()
            if args[0].__name__ == 'Ecn':
                mock_query.filter.return_value.first.return_value = ecn
            else:
                mock_query.filter.return_value.all.return_value = []
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.service.batch_sync_to_purchase([1], current_user_id=999)

        self.assertEqual(result["success_count"], 1)
        self.assertEqual(result["fail_count"], 0)


class TestEcnIntegrationServiceBatchCreateTasks(unittest.TestCase):
    """测试批量创建任务功能"""

    def setUp(self):
        self.db = MagicMock()
        self.service = EcnIntegrationService(self.db)

    @patch('app.services.ecn_integration.ecn_integration_service.notify_task_assigned')
    @patch('app.services.ecn_integration.ecn_integration_service.auto_assign_task')
    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_batch_create_tasks_success(self, mock_get_or_404, mock_auto_assign, mock_notify):
        """测试批量创建任务成功"""
        ecn = MagicMock()
        ecn.id = 1
        ecn.status = "APPROVED"
        mock_get_or_404.return_value = ecn

        # 模拟没有现有任务
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        tasks = [
            EcnTaskCreate(
                ecn_id=1,
                task_name="任务1",
                task_type="DESIGN",
                task_dept="工程部",
                task_description="描述1",
                assignee_id=100,
                planned_start=datetime(2026, 3, 1),
                planned_end=datetime(2026, 3, 10)
            ),
            EcnTaskCreate(
                ecn_id=1,
                task_name="任务2",
                task_type="PROCUREMENT",
                task_dept="采购部",
                task_description="描述2",
                assignee_id=200,
                planned_start=datetime(2026, 3, 5),
                planned_end=datetime(2026, 3, 15)
            )
        ]

        result = self.service.batch_create_tasks(1, tasks)

        self.assertEqual(result["ecn_id"], 1)
        self.assertEqual(result["created_count"], 2)
        self.assertEqual(len(result["task_ids"]), 2)
        self.assertEqual(ecn.status, "EXECUTING")
        self.assertIsNotNone(ecn.execution_start)
        self.db.commit.assert_called_once()

    @patch('app.services.ecn_integration.ecn_integration_service.notify_task_assigned')
    @patch('app.services.ecn_integration.ecn_integration_service.auto_assign_task')
    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_batch_create_tasks_with_existing_tasks(self, mock_get_or_404, mock_auto_assign, mock_notify):
        """测试批量创建任务 - 已存在任务"""
        ecn = MagicMock()
        ecn.status = "EXECUTING"
        mock_get_or_404.return_value = ecn

        # 模拟已存在的任务
        existing_task = MagicMock()
        existing_task.task_no = 5
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = existing_task

        tasks = [
            EcnTaskCreate(
                ecn_id=1,
                task_name="新任务",
                task_type="TESTING",
                task_dept="质量部",
                task_description="测试",
                assignee_id=300,
                planned_start=datetime(2026, 3, 1),
                planned_end=datetime(2026, 3, 10)
            )
        ]

        result = self.service.batch_create_tasks(1, tasks)

        self.assertEqual(result["created_count"], 1)
        # 新任务序号应该是6（从5开始的下一个）

    @patch('app.services.ecn_integration.ecn_integration_service.notify_task_assigned')
    @patch('app.services.ecn_integration.ecn_integration_service.auto_assign_task')
    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_batch_create_tasks_auto_assign(self, mock_get_or_404, mock_auto_assign, mock_notify):
        """测试批量创建任务 - 自动分配负责人"""
        ecn = MagicMock()
        ecn.status = "APPROVED"
        mock_get_or_404.return_value = ecn

        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        # 模拟自动分配返回用户ID
        mock_auto_assign.return_value = 888

        tasks = [
            EcnTaskCreate(
                ecn_id=1,
                task_name="无负责人任务",
                task_type="DESIGN",
                task_dept="工程部",
                task_description="需要自动分配",
                assignee_id=None,  # 没有指定负责人
                planned_start=datetime(2026, 3, 1),
                planned_end=datetime(2026, 3, 10)
            )
        ]

        result = self.service.batch_create_tasks(1, tasks)

        self.assertEqual(result["created_count"], 1)
        mock_auto_assign.assert_called_once()
        mock_notify.assert_called_once()

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_batch_create_tasks_invalid_status(self, mock_get_or_404):
        """测试批量创建任务失败 - ECN状态不允许"""
        ecn = MagicMock()
        ecn.status = "DRAFT"
        mock_get_or_404.return_value = ecn

        tasks = [
            EcnTaskCreate(
                ecn_id=1,
                task_name="任务",
                task_type="DESIGN",
                task_dept="工程部",
                task_description="描述",
                assignee_id=100,
                planned_start=datetime(2026, 3, 1),
                planned_end=datetime(2026, 3, 10)
            )
        ]

        with self.assertRaises(ValueError) as context:
            self.service.batch_create_tasks(1, tasks)
        
        self.assertIn("ECN当前不在执行阶段", str(context.exception))

    @patch('app.services.ecn_integration.ecn_integration_service.notify_task_assigned')
    @patch('app.services.ecn_integration.ecn_integration_service.auto_assign_task')
    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_batch_create_tasks_auto_assign_failure(self, mock_get_or_404, mock_auto_assign, mock_notify):
        """测试批量创建任务 - 自动分配失败但继续创建"""
        ecn = MagicMock()
        ecn.status = "APPROVED"
        mock_get_or_404.return_value = ecn

        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        # 模拟自动分配失败
        mock_auto_assign.side_effect = Exception("Auto assign failed")

        tasks = [
            EcnTaskCreate(
                ecn_id=1,
                task_name="任务",
                task_type="DESIGN",
                task_dept="工程部",
                task_description="描述",
                assignee_id=None,
                planned_start=datetime(2026, 3, 1),
                planned_end=datetime(2026, 3, 10)
            )
        ]

        # 应该仍然成功创建任务，只是没有负责人
        result = self.service.batch_create_tasks(1, tasks)
        self.assertEqual(result["created_count"], 1)

    @patch('app.services.ecn_integration.ecn_integration_service.notify_task_assigned')
    @patch('app.services.ecn_integration.ecn_integration_service.auto_assign_task')
    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_batch_create_tasks_notification_failure(self, mock_get_or_404, mock_auto_assign, mock_notify):
        """测试批量创建任务 - 通知发送失败但继续创建"""
        ecn = MagicMock()
        ecn.status = "APPROVED"
        mock_get_or_404.return_value = ecn

        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        # 模拟通知发送失败
        mock_notify.side_effect = Exception("Notification failed")

        tasks = [
            EcnTaskCreate(
                ecn_id=1,
                task_name="任务",
                task_type="DESIGN",
                task_dept="工程部",
                task_description="描述",
                assignee_id=100,
                planned_start=datetime(2026, 3, 1),
                planned_end=datetime(2026, 3, 10)
            )
        ]

        # 应该仍然成功创建任务
        result = self.service.batch_create_tasks(1, tasks)
        self.assertEqual(result["created_count"], 1)


class TestEcnIntegrationServiceEdgeCases(unittest.TestCase):
    """测试边界情况和特殊场景"""

    def setUp(self):
        self.db = MagicMock()
        self.service = EcnIntegrationService(self.db)

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_bom_multiple_materials(self, mock_get_or_404):
        """测试同步BOM - 多个受影响物料"""
        ecn = MagicMock()
        ecn.status = "APPROVED"
        mock_get_or_404.return_value = ecn

        materials = []
        bom_items = []
        for i in range(5):
            material = MagicMock()
            material.bom_item_id = i + 1
            material.change_type = "UPDATE"
            material.new_quantity = Decimal(str((i + 1) * 10))
            material.new_specification = None
            material.material_id = None
            materials.append(material)

            bom_item = MagicMock()
            bom_item.id = i + 1
            bom_items.append(bom_item)

        self.db.query.return_value.filter.return_value.all.return_value = materials
        self.db.query.return_value.filter.return_value.first.side_effect = bom_items

        result = self.service.sync_to_bom(1)

        self.assertEqual(result["updated_count"], 5)

    def test_batch_sync_to_bom_empty_list(self):
        """测试批量同步BOM - 空列表"""
        result = self.service.batch_sync_to_bom([])

        self.assertEqual(result["total"], 0)
        self.assertEqual(result["success_count"], 0)
        self.assertEqual(result["fail_count"], 0)
        self.assertEqual(len(result["results"]), 0)

    def test_batch_sync_to_project_empty_list(self):
        """测试批量同步项目 - 空列表"""
        result = self.service.batch_sync_to_project([])

        self.assertEqual(result["total"], 0)
        self.assertEqual(result["success_count"], 0)

    def test_batch_sync_to_purchase_empty_list(self):
        """测试批量同步采购 - 空列表"""
        result = self.service.batch_sync_to_purchase([], current_user_id=999)

        self.assertEqual(result["total"], 0)
        self.assertEqual(result["success_count"], 0)

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_project_both_impacts(self, mock_get_or_404):
        """测试同步到项目 - 同时有成本和工期影响"""
        ecn = MagicMock()
        ecn.project_id = 100
        ecn.cost_impact = Decimal("3000")
        ecn.schedule_impact_days = 7
        mock_get_or_404.return_value = ecn

        project = MagicMock()
        project.total_cost = Decimal("50000")
        project.planned_end_date = datetime(2026, 4, 1)

        self.db.query.return_value.filter.return_value.first.return_value = project

        result = self.service.sync_to_project(1)

        self.assertEqual(result["cost_impact"], 3000.0)
        self.assertEqual(result["schedule_impact_days"], 7)
        self.assertEqual(project.total_cost, Decimal("53000"))
        self.assertEqual(project.planned_end_date, datetime(2026, 4, 8))


if __name__ == '__main__':
    unittest.main()
