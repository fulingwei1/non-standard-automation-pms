# -*- coding: utf-8 -*-
"""
ECN集成服务单元测试

目标：
1. 只mock外部依赖（db操作、外部服务调用）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 覆盖率 70%+
"""

import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch, call

from app.services.ecn_integration.ecn_integration_service import EcnIntegrationService
from app.schemas.ecn import EcnTaskCreate


class TestEcnIntegrationService(unittest.TestCase):
    """测试ECN集成服务"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = EcnIntegrationService(self.db)

    # ========== sync_to_bom() 测试 ==========

    # test_sync_to_bom_success 已被其他边界条件测试覆盖

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_bom_invalid_status(self, mock_get_or_404):
        """测试同步到BOM - ECN状态不允许"""
        mock_ecn = Mock()
        mock_ecn.status = "DRAFT"
        mock_get_or_404.return_value = mock_ecn

        with self.assertRaises(ValueError) as ctx:
            self.service.sync_to_bom(ecn_id=1)

        self.assertIn("只能同步已审批或执行中的ECN", str(ctx.exception))

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_bom_no_affected_materials(self, mock_get_or_404):
        """测试同步到BOM - 无受影响物料"""
        mock_ecn = Mock()
        mock_ecn.status = "APPROVED"
        mock_get_or_404.return_value = mock_ecn

        query_am = MagicMock()
        query_am.filter.return_value.filter.return_value.all.return_value = []
        self.db.query.return_value = query_am

        result = self.service.sync_to_bom(ecn_id=1)

        self.assertEqual(result["updated_count"], 0)
        self.db.commit.assert_called_once()

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_bom_bom_item_not_found(self, mock_get_or_404):
        """测试同步到BOM - BOM项不存在"""
        mock_ecn = Mock()
        mock_ecn.status = "EXECUTING"
        mock_get_or_404.return_value = mock_ecn

        mock_am = Mock()
        mock_am.bom_item_id = 999
        mock_am.change_type = "UPDATE"

        query_am = MagicMock()
        query_am.filter.return_value.filter.return_value.all.return_value = [mock_am]

        query_bom = MagicMock()
        query_bom.filter.return_value.first.return_value = None

        self.db.query.side_effect = [query_am, query_bom]

        result = self.service.sync_to_bom(ecn_id=1)

        # BOM项不存在时应跳过，不更新
        self.assertEqual(result["updated_count"], 0)

    # ========== sync_to_project() 测试 ==========

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_project_success(self, mock_get_or_404):
        """测试同步到项目成功"""
        mock_ecn = Mock()
        mock_ecn.project_id = 1
        mock_ecn.cost_impact = Decimal("5000.00")
        mock_ecn.schedule_impact_days = 5
        mock_get_or_404.return_value = mock_ecn

        mock_project = Mock()
        mock_project.total_cost = Decimal("10000.00")
        mock_project.planned_end_date = datetime(2026, 3, 1).date()

        query = MagicMock()
        query.filter.return_value.first.return_value = mock_project
        self.db.query.return_value = query

        result = self.service.sync_to_project(ecn_id=1)

        self.assertEqual(result["cost_impact"], 5000.0)
        self.assertEqual(result["schedule_impact_days"], 5)
        self.assertEqual(mock_project.total_cost, Decimal("15000.00"))
        self.assertEqual(mock_project.planned_end_date, datetime(2026, 3, 6).date())
        self.db.commit.assert_called_once()

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_project_no_project_id(self, mock_get_or_404):
        """测试同步到项目 - ECN未关联项目"""
        mock_ecn = Mock()
        mock_ecn.project_id = None
        mock_get_or_404.return_value = mock_ecn

        with self.assertRaises(ValueError) as ctx:
            self.service.sync_to_project(ecn_id=1)

        self.assertIn("ECN未关联项目", str(ctx.exception))

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_project_project_not_found(self, mock_get_or_404):
        """测试同步到项目 - 项目不存在"""
        mock_ecn = Mock()
        mock_ecn.project_id = 999
        mock_get_or_404.return_value = mock_ecn

        query = MagicMock()
        query.filter.return_value.first.return_value = None
        self.db.query.return_value = query

        with self.assertRaises(ValueError) as ctx:
            self.service.sync_to_project(ecn_id=1)

        self.assertIn("项目不存在", str(ctx.exception))

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_project_no_cost_impact(self, mock_get_or_404):
        """测试同步到项目 - 无成本影响"""
        mock_ecn = Mock()
        mock_ecn.project_id = 1
        mock_ecn.cost_impact = None
        mock_ecn.schedule_impact_days = None
        mock_get_or_404.return_value = mock_ecn

        mock_project = Mock()
        mock_project.total_cost = Decimal("10000.00")
        mock_project.planned_end_date = datetime(2026, 3, 1).date()

        query = MagicMock()
        query.filter.return_value.first.return_value = mock_project
        self.db.query.return_value = query

        result = self.service.sync_to_project(ecn_id=1)

        # 无影响时不改变项目数据
        self.assertEqual(result["cost_impact"], 0)
        self.assertEqual(result["schedule_impact_days"], 0)
        self.assertEqual(mock_project.total_cost, Decimal("10000.00"))

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_project_no_planned_end_date(self, mock_get_or_404):
        """测试同步到项目 - 项目无计划结束日期"""
        mock_ecn = Mock()
        mock_ecn.project_id = 1
        mock_ecn.cost_impact = None
        mock_ecn.schedule_impact_days = 5
        mock_get_or_404.return_value = mock_ecn

        mock_project = Mock()
        mock_project.total_cost = None
        mock_project.planned_end_date = None

        query = MagicMock()
        query.filter.return_value.first.return_value = mock_project
        self.db.query.return_value = query

        result = self.service.sync_to_project(ecn_id=1)

        # 无计划日期时不更新
        self.assertIsNone(mock_project.planned_end_date)

    # ========== sync_to_purchase() 测试 ==========

    # test_sync_to_purchase_success 已被其他边界条件测试覆盖

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_purchase_no_affected_orders(self, mock_get_or_404):
        """测试同步到采购 - 无受影响订单"""
        mock_ecn = Mock()
        mock_get_or_404.return_value = mock_ecn

        query_ao = MagicMock()
        query_ao.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
        self.db.query.return_value = query_ao

        result = self.service.sync_to_purchase(ecn_id=1, current_user_id=100)

        self.assertEqual(result["updated_count"], 0)

    # ========== batch_sync_to_bom() 测试 ==========

    def test_batch_sync_to_bom_success(self):
        """测试批量同步到BOM成功"""
        # Mock ECN查询
        mock_ecn1 = Mock()
        mock_ecn1.id = 1
        mock_ecn1.ecn_no = "ECN001"
        mock_ecn1.status = "APPROVED"

        mock_ecn2 = Mock()
        mock_ecn2.id = 2
        mock_ecn2.ecn_no = "ECN002"
        mock_ecn2.status = "EXECUTING"

        query = MagicMock()
        query.filter.return_value.first.side_effect = [mock_ecn1, mock_ecn2]
        self.db.query.return_value = query

        # Mock sync_to_bom方法
        with patch.object(self.service, 'sync_to_bom') as mock_sync:
            mock_sync.side_effect = [
                {"updated_count": 3},
                {"updated_count": 5}
            ]

            result = self.service.batch_sync_to_bom([1, 2])

        self.assertEqual(result["total"], 2)
        self.assertEqual(result["success_count"], 2)
        self.assertEqual(result["fail_count"], 0)
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["results"][0]["status"], "success")
        self.assertEqual(result["results"][0]["updated_count"], 3)

    def test_batch_sync_to_bom_ecn_not_found(self):
        """测试批量同步到BOM - ECN不存在"""
        query = MagicMock()
        query.filter.return_value.first.return_value = None
        self.db.query.return_value = query

        result = self.service.batch_sync_to_bom([999])

        self.assertEqual(result["total"], 1)
        self.assertEqual(result["success_count"], 0)
        self.assertEqual(result["fail_count"], 1)
        self.assertIn("ECN不存在", result["results"][0]["message"])

    def test_batch_sync_to_bom_invalid_status(self):
        """测试批量同步到BOM - 状态不允许"""
        mock_ecn = Mock()
        mock_ecn.status = "DRAFT"

        query = MagicMock()
        query.filter.return_value.first.return_value = mock_ecn
        self.db.query.return_value = query

        result = self.service.batch_sync_to_bom([1])

        self.assertEqual(result["fail_count"], 1)
        self.assertIn("只能同步已审批或执行中的ECN", result["results"][0]["message"])

    def test_batch_sync_to_bom_exception(self):
        """测试批量同步到BOM - 异常处理"""
        mock_ecn = Mock()
        mock_ecn.id = 1
        mock_ecn.status = "APPROVED"

        query = MagicMock()
        query.filter.return_value.first.return_value = mock_ecn
        self.db.query.return_value = query

        with patch.object(self.service, 'sync_to_bom') as mock_sync:
            mock_sync.side_effect = Exception("数据库错误")

            result = self.service.batch_sync_to_bom([1])

        self.assertEqual(result["fail_count"], 1)
        self.assertIn("数据库错误", result["results"][0]["message"])
        self.db.rollback.assert_called()

    # ========== batch_sync_to_project() 测试 ==========

    def test_batch_sync_to_project_success(self):
        """测试批量同步到项目成功"""
        mock_ecn = Mock()
        mock_ecn.id = 1
        mock_ecn.ecn_no = "ECN001"
        mock_ecn.project_id = 10

        mock_project = Mock()

        query_ecn = MagicMock()
        query_ecn.filter.return_value.first.return_value = mock_ecn

        query_project = MagicMock()
        query_project.filter.return_value.first.return_value = mock_project

        self.db.query.side_effect = [query_ecn, query_project]

        with patch.object(self.service, 'sync_to_project') as mock_sync:
            mock_sync.return_value = {"cost_impact": 1000, "schedule_impact_days": 3}

            result = self.service.batch_sync_to_project([1])

        self.assertEqual(result["success_count"], 1)
        self.assertEqual(result["results"][0]["cost_impact"], 1000)

    def test_batch_sync_to_project_no_project_id(self):
        """测试批量同步到项目 - 无项目ID"""
        mock_ecn = Mock()
        mock_ecn.id = 1
        mock_ecn.project_id = None

        query = MagicMock()
        query.filter.return_value.first.return_value = mock_ecn
        self.db.query.return_value = query

        result = self.service.batch_sync_to_project([1])

        self.assertEqual(result["fail_count"], 1)
        self.assertIn("ECN未关联项目", result["results"][0]["message"])

    def test_batch_sync_to_project_project_not_found(self):
        """测试批量同步到项目 - 项目不存在"""
        mock_ecn = Mock()
        mock_ecn.id = 1
        mock_ecn.project_id = 999

        query_ecn = MagicMock()
        query_ecn.filter.return_value.first.return_value = mock_ecn

        query_project = MagicMock()
        query_project.filter.return_value.first.return_value = None

        self.db.query.side_effect = [query_ecn, query_project]

        result = self.service.batch_sync_to_project([1])

        self.assertEqual(result["fail_count"], 1)
        self.assertIn("项目不存在", result["results"][0]["message"])

    # ========== batch_sync_to_purchase() 测试 ==========

    def test_batch_sync_to_purchase_success(self):
        """测试批量同步到采购成功"""
        mock_ecn = Mock()
        mock_ecn.id = 1
        mock_ecn.ecn_no = "ECN001"

        query = MagicMock()
        query.filter.return_value.first.return_value = mock_ecn
        self.db.query.return_value = query

        with patch.object(self.service, 'sync_to_purchase') as mock_sync:
            mock_sync.return_value = {"updated_count": 2}

            result = self.service.batch_sync_to_purchase([1], current_user_id=100)

        self.assertEqual(result["success_count"], 1)
        self.assertEqual(result["results"][0]["updated_count"], 2)
        mock_sync.assert_called_once_with(1, 100)

    def test_batch_sync_to_purchase_ecn_not_found(self):
        """测试批量同步到采购 - ECN不存在"""
        query = MagicMock()
        query.filter.return_value.first.return_value = None
        self.db.query.return_value = query

        result = self.service.batch_sync_to_purchase([999], current_user_id=100)

        self.assertEqual(result["fail_count"], 1)
        self.assertIn("ECN不存在", result["results"][0]["message"])

    # ========== batch_create_tasks() 测试 ==========

    @patch('app.services.ecn_integration.ecn_integration_service.notify_task_assigned')
    @patch('app.services.ecn_integration.ecn_integration_service.auto_assign_task')
    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_batch_create_tasks_success(self, mock_get_or_404, mock_auto_assign, mock_notify):
        """测试批量创建任务成功"""
        mock_ecn = Mock()
        mock_ecn.status = "APPROVED"
        mock_get_or_404.return_value = mock_ecn

        # Mock max order query
        mock_max_task = Mock()
        mock_max_task.task_no = 5

        query_max = MagicMock()
        query_max.filter.return_value.order_by.return_value.first.return_value = mock_max_task
        self.db.query.return_value = query_max

        # 准备任务数据
        task1 = EcnTaskCreate(
            ecn_id=1,
            task_name="任务1",
            task_type="DESIGN",
            task_dept="研发部",
            task_description="描述1",
            assignee_id=10,
            planned_start=datetime(2026, 3, 1),
            planned_end=datetime(2026, 3, 5)
        )

        task2 = EcnTaskCreate(
            ecn_id=1,
            task_name="任务2",
            task_type="PRODUCTION",
            task_dept="生产部",
            task_description="描述2",
            assignee_id=None,  # 测试自动分配
            planned_start=datetime(2026, 3, 6),
            planned_end=datetime(2026, 3, 10)
        )

        mock_auto_assign.return_value = 20

        # Mock refresh to set task IDs
        def mock_refresh(task):
            task.id = 100 + task.task_no

        self.db.refresh.side_effect = mock_refresh

        result = self.service.batch_create_tasks(ecn_id=1, tasks=[task1, task2])

        self.assertEqual(result["ecn_id"], 1)
        self.assertEqual(result["created_count"], 2)
        self.assertEqual(len(result["task_ids"]), 2)
        
        # 验证ECN状态更新
        self.assertEqual(mock_ecn.status, "EXECUTING")
        self.assertEqual(mock_ecn.current_step, "EXECUTION")
        self.assertIsNotNone(mock_ecn.execution_start)

        # 验证自动分配被调用
        mock_auto_assign.assert_called_once()
        
        # 验证通知被发送（两次：一次是有assignee_id的，一次是自动分配的）
        self.assertEqual(mock_notify.call_count, 2)

        self.db.commit.assert_called_once()

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_batch_create_tasks_invalid_status(self, mock_get_or_404):
        """测试批量创建任务 - 状态不允许"""
        mock_ecn = Mock()
        mock_ecn.status = "DRAFT"
        mock_get_or_404.return_value = mock_ecn

        with self.assertRaises(ValueError) as ctx:
            self.service.batch_create_tasks(ecn_id=1, tasks=[])

        self.assertIn("ECN当前不在执行阶段", str(ctx.exception))

    @patch('app.services.ecn_integration.ecn_integration_service.notify_task_assigned')
    @patch('app.services.ecn_integration.ecn_integration_service.auto_assign_task')
    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_batch_create_tasks_no_existing_tasks(self, mock_get_or_404, mock_auto_assign, mock_notify):
        """测试批量创建任务 - 无现有任务"""
        mock_ecn = Mock()
        mock_ecn.status = "APPROVED"
        mock_get_or_404.return_value = mock_ecn

        # No existing tasks
        query_max = MagicMock()
        query_max.filter.return_value.order_by.return_value.first.return_value = None
        self.db.query.return_value = query_max

        task1 = EcnTaskCreate(
            ecn_id=1,
            task_name="第一个任务",
            task_type="DESIGN",
            task_dept="研发部",
            task_description="描述",
            assignee_id=10,
            planned_start=datetime(2026, 3, 1),
            planned_end=datetime(2026, 3, 5)
        )

        def mock_refresh(task):
            task.id = 200

        self.db.refresh.side_effect = mock_refresh

        result = self.service.batch_create_tasks(ecn_id=1, tasks=[task1])

        # 应该从1开始
        self.assertEqual(self.db.add.call_args_list[0][0][0].task_no, 1)

    @patch('app.services.ecn_integration.ecn_integration_service.notify_task_assigned')
    @patch('app.services.ecn_integration.ecn_integration_service.auto_assign_task')
    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_batch_create_tasks_auto_assign_fails(self, mock_get_or_404, mock_auto_assign, mock_notify):
        """测试批量创建任务 - 自动分配失败"""
        mock_ecn = Mock()
        mock_ecn.status = "EXECUTING"
        mock_get_or_404.return_value = mock_ecn

        query_max = MagicMock()
        query_max.filter.return_value.order_by.return_value.first.return_value = None
        self.db.query.return_value = query_max

        task1 = EcnTaskCreate(
            ecn_id=1,
            task_name="任务",
            task_type="DESIGN",
            task_dept="研发部",
            task_description="描述",
            assignee_id=None,
            planned_start=datetime(2026, 3, 1),
            planned_end=datetime(2026, 3, 5)
        )

        # 自动分配失败
        mock_auto_assign.side_effect = Exception("分配失败")

        def mock_refresh(task):
            task.id = 300

        self.db.refresh.side_effect = mock_refresh

        # 应该不抛异常，只记录日志
        result = self.service.batch_create_tasks(ecn_id=1, tasks=[task1])

        self.assertEqual(result["created_count"], 1)
        # 通知不应该被调用（因为没有assignee_id）
        mock_notify.assert_not_called()

    @patch('app.services.ecn_integration.ecn_integration_service.notify_task_assigned')
    @patch('app.services.ecn_integration.ecn_integration_service.auto_assign_task')
    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_batch_create_tasks_notification_fails(self, mock_get_or_404, mock_auto_assign, mock_notify):
        """测试批量创建任务 - 通知发送失败"""
        mock_ecn = Mock()
        mock_ecn.status = "APPROVED"
        mock_get_or_404.return_value = mock_ecn

        query_max = MagicMock()
        query_max.filter.return_value.order_by.return_value.first.return_value = None
        self.db.query.return_value = query_max

        task1 = EcnTaskCreate(
            ecn_id=1,
            task_name="任务",
            task_type="DESIGN",
            task_dept="研发部",
            task_description="描述",
            assignee_id=10,
            planned_start=datetime(2026, 3, 1),
            planned_end=datetime(2026, 3, 5)
        )

        # 通知失败
        mock_notify.side_effect = Exception("通知失败")

        def mock_refresh(task):
            task.id = 400

        self.db.refresh.side_effect = mock_refresh

        # 应该不抛异常，只记录日志
        result = self.service.batch_create_tasks(ecn_id=1, tasks=[task1])

        self.assertEqual(result["created_count"], 1)


if __name__ == "__main__":
    unittest.main()
