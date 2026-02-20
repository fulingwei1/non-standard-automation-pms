# -*- coding: utf-8 -*-
"""
ECN集成服务单元测试
覆盖 EcnIntegrationService 的核心业务逻辑
"""

import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.ecn_integration import EcnIntegrationService


class TestEcnIntegrationService(unittest.TestCase):
    """ECN集成服务测试类"""

    def setUp(self):
        """测试前准备：创建模拟数据库会话"""
        self.db = MagicMock()
        self.service = EcnIntegrationService(self.db)

    def tearDown(self):
        """测试后清理"""
        self.db = None
        self.service = None

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_bom_success(self, mock_get_or_404):
        """测试成功同步ECN到BOM"""
        # 模拟ECN对象
        mock_ecn = MagicMock()
        mock_ecn.status = "APPROVED"
        mock_get_or_404.return_value = mock_ecn

        # 模拟受影响的物料
        mock_material1 = MagicMock()
        mock_material1.bom_item_id = 1
        mock_material1.change_type = "UPDATE"
        mock_material1.new_quantity = Decimal("10.5")
        mock_material1.new_specification = "新规格"

        mock_material2 = MagicMock()
        mock_material2.bom_item_id = 2
        mock_material2.change_type = "REPLACE"
        mock_material2.material_id = 999

        # 模拟BOM项目
        mock_bom_item1 = MagicMock()
        mock_bom_item1.id = 1
        mock_bom_item2 = MagicMock()
        mock_bom_item2.id = 2

        # 配置查询返回
        self.db.query.return_value.filter.return_value.all.return_value = [
            mock_material1, mock_material2
        ]
        self.db.query.return_value.filter.return_value.first.side_effect = [
            mock_bom_item1, mock_bom_item2
        ]

        # 执行同步
        result = self.service.sync_to_bom(1)

        # 验证结果
        self.assertEqual(result["updated_count"], 2)
        self.db.commit.assert_called_once()
        self.assertEqual(mock_material1.status, "PROCESSED")
        self.assertEqual(mock_material2.status, "PROCESSED")

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_bom_invalid_status(self, mock_get_or_404):
        """测试同步BOM时ECN状态无效"""
        # 模拟状态为DRAFT的ECN
        mock_ecn = MagicMock()
        mock_ecn.status = "DRAFT"
        mock_get_or_404.return_value = mock_ecn

        # 应该抛出 ValueError
        with self.assertRaises(ValueError) as context:
            self.service.sync_to_bom(1)
        
        self.assertIn("只能同步已审批或执行中的ECN", str(context.exception))

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_project_success(self, mock_get_or_404):
        """测试成功同步ECN到项目"""
        # 模拟ECN对象
        mock_ecn = MagicMock()
        mock_ecn.project_id = 100
        mock_ecn.cost_impact = Decimal("5000.00")
        mock_ecn.schedule_impact_days = 5
        mock_get_or_404.return_value = mock_ecn

        # 模拟项目对象
        mock_project = MagicMock()
        mock_project.id = 100
        mock_project.total_cost = Decimal("50000.00")
        mock_project.planned_end_date = datetime(2026, 3, 1)
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_project

        # 执行同步
        result = self.service.sync_to_project(1)

        # 验证结果
        self.assertEqual(result["cost_impact"], 5000.00)
        self.assertEqual(result["schedule_impact_days"], 5)
        self.assertEqual(mock_project.total_cost, Decimal("55000.00"))
        self.assertEqual(
            mock_project.planned_end_date, 
            datetime(2026, 3, 1) + timedelta(days=5)
        )
        self.db.commit.assert_called_once()

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_project_no_project_id(self, mock_get_or_404):
        """测试同步项目时ECN未关联项目"""
        # 模拟未关联项目的ECN
        mock_ecn = MagicMock()
        mock_ecn.project_id = None
        mock_get_or_404.return_value = mock_ecn

        # 应该抛出 ValueError
        with self.assertRaises(ValueError) as context:
            self.service.sync_to_project(1)
        
        self.assertIn("ECN未关联项目", str(context.exception))

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_sync_to_purchase_success(self, mock_get_or_404):
        """测试成功同步ECN到采购订单"""
        # 模拟ECN对象
        mock_ecn = MagicMock()
        mock_get_or_404.return_value = mock_ecn

        # 模拟受影响的订单
        mock_affected_order = MagicMock()
        mock_affected_order.order_id = 200
        mock_affected_order.action_type = "CANCEL"

        # 模拟采购订单
        mock_purchase_order = MagicMock()
        mock_purchase_order.id = 200
        mock_purchase_order.status = "PENDING"

        # 配置查询返回
        self.db.query.return_value.filter.return_value.all.return_value = [
            mock_affected_order
        ]
        self.db.query.return_value.filter.return_value.first.return_value = mock_purchase_order

        # 执行同步
        result = self.service.sync_to_purchase(1, current_user_id=10)

        # 验证结果
        self.assertEqual(result["updated_count"], 1)
        self.assertEqual(mock_purchase_order.status, "CANCELLED")
        self.assertEqual(mock_affected_order.status, "PROCESSED")
        self.assertEqual(mock_affected_order.processed_by, 10)
        self.db.commit.assert_called_once()

    def test_batch_sync_to_bom_mixed_results(self):
        """测试批量同步BOM（部分成功部分失败）"""
        # 模拟第一个ECN成功
        mock_ecn1 = MagicMock()
        mock_ecn1.id = 1
        mock_ecn1.ecn_no = "ECN-001"
        mock_ecn1.status = "APPROVED"

        # 模拟第二个ECN不存在
        # 模拟第三个ECN状态无效
        mock_ecn3 = MagicMock()
        mock_ecn3.id = 3
        mock_ecn3.status = "DRAFT"

        # 配置查询返回
        def query_side_effect(*args, **kwargs):
            mock_query = MagicMock()
            
            def filter_side_effect(*args, **kwargs):
                mock_filter = MagicMock()
                ecn_id_arg = str(args[0]) if args else ""
                
                if "ecn_id == 1" in ecn_id_arg or ".id == 1" in ecn_id_arg:
                    mock_filter.first.return_value = mock_ecn1
                    mock_filter.all.return_value = []
                elif "ecn_id == 2" in ecn_id_arg or ".id == 2" in ecn_id_arg:
                    mock_filter.first.return_value = None
                    mock_filter.all.return_value = []
                elif "ecn_id == 3" in ecn_id_arg or ".id == 3" in ecn_id_arg:
                    mock_filter.first.return_value = mock_ecn3
                    mock_filter.all.return_value = []
                return mock_filter
            
            mock_query.filter.side_effect = filter_side_effect
            return mock_query
        
        self.db.query.side_effect = query_side_effect

        # 执行批量同步
        result = self.service.batch_sync_to_bom([1, 2, 3])

        # 验证结果
        self.assertEqual(result["total"], 3)
        self.assertEqual(result["success_count"], 1)
        self.assertEqual(result["fail_count"], 2)
        self.assertEqual(len(result["results"]), 3)

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    @patch('app.services.ecn_integration.ecn_integration_service.auto_assign_task')
    @patch('app.services.ecn_integration.ecn_integration_service.notify_task_assigned')
    def test_batch_create_tasks_success(self, mock_notify, mock_auto_assign, mock_get_or_404):
        """测试批量创建ECN任务成功"""
        # 模拟ECN对象
        mock_ecn = MagicMock()
        mock_ecn.status = "APPROVED"
        mock_get_or_404.return_value = mock_ecn

        # 模拟任务创建数据
        from app.schemas.ecn import EcnTaskCreate
        task1 = MagicMock(spec=EcnTaskCreate)
        task1.task_name = "设计变更"
        task1.task_type = "DESIGN"
        task1.task_dept = "研发部"
        task1.task_description = "更新设计图纸"
        task1.assignee_id = None
        task1.planned_start = datetime(2026, 3, 1)
        task1.planned_end = datetime(2026, 3, 5)

        task2 = MagicMock(spec=EcnTaskCreate)
        task2.task_name = "BOM更新"
        task2.task_type = "BOM"
        task2.task_dept = "工艺部"
        task2.task_description = "更新BOM清单"
        task2.assignee_id = 20
        task2.planned_start = datetime(2026, 3, 6)
        task2.planned_end = datetime(2026, 3, 10)

        # 模拟自动分配返回
        mock_auto_assign.return_value = 15

        # 模拟没有现有任务
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        # 执行批量创建
        result = self.service.batch_create_tasks(1, [task1, task2])

        # 验证结果
        self.assertEqual(result["ecn_id"], 1)
        self.assertEqual(result["created_count"], 2)
        self.assertEqual(len(result["task_ids"]), 2)
        
        # 验证ECN状态更新为EXECUTING
        self.assertEqual(mock_ecn.status, "EXECUTING")
        self.assertEqual(mock_ecn.current_step, "EXECUTION")
        self.db.commit.assert_called_once()

    @patch('app.services.ecn_integration.ecn_integration_service.get_or_404')
    def test_batch_create_tasks_invalid_status(self, mock_get_or_404):
        """测试批量创建任务时ECN状态无效"""
        # 模拟状态为DRAFT的ECN
        mock_ecn = MagicMock()
        mock_ecn.status = "DRAFT"
        mock_get_or_404.return_value = mock_ecn

        # 应该抛出 ValueError
        with self.assertRaises(ValueError) as context:
            self.service.batch_create_tasks(1, [])
        
        self.assertIn("ECN当前不在执行阶段", str(context.exception))


if __name__ == "__main__":
    unittest.main()
