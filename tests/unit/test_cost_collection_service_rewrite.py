# -*- coding: utf-8 -*-
"""
成本自动归集服务单元测试 - 重写版本

目标：
1. 只mock外部依赖（db.query, db.add等数据库操作）
2. 测试核心业务逻辑
3. 达到70%+覆盖率

测试策略：
- 使用patch mock数据库模型查询
- mock外部服务（CostAlertService）
- 让业务逻辑真正执行
"""

import unittest
from unittest.mock import MagicMock, patch, call
from datetime import date, datetime
from decimal import Decimal

from app.services.cost_collection_service import CostCollectionService
from app.models.project import ProjectCost


class TestCollectFromPurchaseOrder(unittest.TestCase):
    """测试从采购订单归集成本"""

    @patch('app.services.cost_collection_service.CostAlertService')
    def test_collect_new_order_with_project(self, mock_alert):
        """测试新订单归集（有关联项目）"""
        # 准备数据库session mock
        db = MagicMock()
        
        # Mock采购订单
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.project_id = 100
        mock_order.order_no = "PO-001"
        mock_order.order_title = "采购测试材料"
        mock_order.total_amount = Decimal("5000.00")
        mock_order.tax_amount = Decimal("650.00")
        mock_order.order_date = date(2024, 1, 15)
        mock_order.created_at = datetime(2024, 1, 15, 10, 0, 0)
        
        # Mock项目
        mock_project = MagicMock()
        mock_project.id = 100
        mock_project.actual_cost = 10000.0
        
        # 配置db.query的返回值
        def query_side_effect(model):
            query_mock = MagicMock()
            if model.__name__ == 'PurchaseOrder':
                query_mock.filter().first.return_value = mock_order
            elif model.__name__ == 'ProjectCost':
                query_mock.filter().first.return_value = None  # 不存在成本记录
            elif model.__name__ == 'Project':
                query_mock.filter().first.return_value = mock_project
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        # 执行测试
        result = CostCollectionService.collect_from_purchase_order(
            db=db,
            order_id=1,
            created_by=10
        )
        
        # 验证结果（只验证业务逻辑执行了）
        self.assertIsNotNone(result)
        self.assertIsInstance(result, ProjectCost)
        
        # 验证数据库操作被调用
        self.assertTrue(db.add.called)
        self.assertEqual(db.add.call_count, 2)  # cost + project

    def test_collect_order_not_found(self):
        """测试订单不存在的情况"""
        db = MagicMock()
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model.__name__ == 'PurchaseOrder':
                query_mock.filter().first.return_value = None
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        result = CostCollectionService.collect_from_purchase_order(
            db=db,
            order_id=999
        )
        
        self.assertIsNone(result)

    def test_collect_order_without_project(self):
        """测试订单没有关联项目"""
        db = MagicMock()
        
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.project_id = None
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model.__name__ == 'PurchaseOrder':
                query_mock.filter().first.return_value = mock_order
            elif model.__name__ == 'ProjectCost':
                query_mock.filter().first.return_value = None
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        result = CostCollectionService.collect_from_purchase_order(
            db=db,
            order_id=1
        )
        
        self.assertIsNone(result)

    def test_collect_existing_cost_update(self):
        """测试更新已存在的成本记录"""
        db = MagicMock()
        
        # Mock采购订单
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.project_id = 100
        mock_order.total_amount = Decimal("6000.00")
        mock_order.tax_amount = Decimal("780.00")
        mock_order.created_at = datetime(2024, 1, 20, 10, 0, 0)
        
        # Mock已存在的成本记录
        mock_existing_cost = MagicMock()
        mock_existing_cost.amount = Decimal("5000.00")
        
        # Mock项目
        mock_project = MagicMock()
        mock_project.id = 100
        
        # Mock项目成本列表（用于重新计算）
        mock_costs = [mock_existing_cost]
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model.__name__ == 'PurchaseOrder':
                query_mock.filter().first.return_value = mock_order
            elif model.__name__ == 'ProjectCost':
                # 第一次查询返回existing_cost，第二次查询返回列表
                filter_mock = query_mock.filter()
                filter_mock.first.return_value = mock_existing_cost
                filter_mock.all.return_value = mock_costs
            elif model.__name__ == 'Project':
                query_mock.filter().first.return_value = mock_project
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        result = CostCollectionService.collect_from_purchase_order(
            db=db,
            order_id=1,
            cost_date=date(2024, 1, 20)
        )
        
        # 验证更新操作
        self.assertIsNotNone(result)
        self.assertEqual(mock_existing_cost.amount, Decimal("6000.00"))
        self.assertEqual(mock_existing_cost.cost_date, date(2024, 1, 20))


class TestCollectFromOutsourcingOrder(unittest.TestCase):
    """测试从外协订单归集成本"""

    @patch('app.services.cost_collection_service.CostAlertService')
    def test_collect_new_outsourcing_order(self, mock_alert):
        """测试新外协订单归集"""
        db = MagicMock()
        
        # Mock外协订单
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.project_id = 100
        mock_order.machine_id = 50
        mock_order.order_no = "OUT-001"
        mock_order.order_title = "外协加工"
        mock_order.total_amount = Decimal("8000.00")
        mock_order.tax_amount = Decimal("1040.00")
        mock_order.created_at = datetime(2024, 1, 15, 10, 0, 0)
        
        # Mock项目
        mock_project = MagicMock()
        mock_project.id = 100
        mock_project.actual_cost = 20000.0
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model.__name__ == 'OutsourcingOrder':
                query_mock.filter().first.return_value = mock_order
            elif model.__name__ == 'ProjectCost':
                query_mock.filter().first.return_value = None
            elif model.__name__ == 'Project':
                query_mock.filter().first.return_value = mock_project
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        result = CostCollectionService.collect_from_outsourcing_order(
            db=db,
            order_id=1,
            created_by=10
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, ProjectCost)
        self.assertTrue(db.add.called)

    def test_collect_outsourcing_order_not_found(self):
        """测试外协订单不存在"""
        db = MagicMock()
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model.__name__ == 'OutsourcingOrder':
                query_mock.filter().first.return_value = None
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        result = CostCollectionService.collect_from_outsourcing_order(
            db=db,
            order_id=999
        )
        
        self.assertIsNone(result)


class TestCollectFromEcn(unittest.TestCase):
    """测试从ECN变更归集成本"""

    @patch('app.services.cost_collection_service.CostAlertService')
    def test_collect_new_ecn_cost(self, mock_alert):
        """测试新ECN成本归集"""
        db = MagicMock()
        
        # Mock ECN
        mock_ecn = MagicMock()
        mock_ecn.id = 1
        mock_ecn.project_id = 100
        mock_ecn.machine_id = 50
        mock_ecn.ecn_no = "ECN-001"
        mock_ecn.ecn_title = "设计变更"
        mock_ecn.cost_impact = Decimal("3000.00")
        
        # Mock项目
        mock_project = MagicMock()
        mock_project.id = 100
        mock_project.actual_cost = 15000.0
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model.__name__ == 'Ecn':
                query_mock.filter().first.return_value = mock_ecn
            elif model.__name__ == 'ProjectCost':
                query_mock.filter().first.return_value = None
            elif model.__name__ == 'Project':
                query_mock.filter().first.return_value = mock_project
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        result = CostCollectionService.collect_from_ecn(
            db=db,
            ecn_id=1,
            created_by=10
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, ProjectCost)
        self.assertTrue(db.add.called)

    def test_collect_ecn_not_found(self):
        """测试ECN不存在"""
        db = MagicMock()
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model.__name__ == 'Ecn':
                query_mock.filter().first.return_value = None
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        result = CostCollectionService.collect_from_ecn(
            db=db,
            ecn_id=999
        )
        
        self.assertIsNone(result)

    def test_collect_ecn_zero_cost(self):
        """测试ECN成本影响为0"""
        db = MagicMock()
        
        mock_ecn = MagicMock()
        mock_ecn.id = 1
        mock_ecn.project_id = 100
        mock_ecn.cost_impact = Decimal("0")
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model.__name__ == 'Ecn':
                query_mock.filter().first.return_value = mock_ecn
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        result = CostCollectionService.collect_from_ecn(
            db=db,
            ecn_id=1
        )
        
        self.assertIsNone(result)

    def test_collect_ecn_negative_cost(self):
        """测试ECN成本影响为负数"""
        db = MagicMock()
        
        mock_ecn = MagicMock()
        mock_ecn.id = 1
        mock_ecn.cost_impact = Decimal("-500.00")
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model.__name__ == 'Ecn':
                query_mock.filter().first.return_value = mock_ecn
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        result = CostCollectionService.collect_from_ecn(
            db=db,
            ecn_id=1
        )
        
        self.assertIsNone(result)


class TestRemoveCostFromSource(unittest.TestCase):
    """测试删除成本记录"""

    def test_remove_existing_cost(self):
        """测试删除已存在的成本记录"""
        db = MagicMock()
        
        # Mock成本记录
        mock_cost = MagicMock()
        mock_cost.project_id = 100
        mock_cost.amount = Decimal("5000.00")
        
        # Mock项目
        mock_project = MagicMock()
        mock_project.id = 100
        mock_project.actual_cost = 15000.0
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model.__name__ == 'ProjectCost':
                query_mock.filter().first.return_value = mock_cost
            elif model.__name__ == 'Project':
                query_mock.filter().first.return_value = mock_project
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        result = CostCollectionService.remove_cost_from_source(
            db=db,
            source_module="PURCHASE",
            source_type="PURCHASE_ORDER",
            source_id=1
        )
        
        self.assertTrue(result)
        db.delete.assert_called_once_with(mock_cost)
        # 验证项目成本减少
        self.assertEqual(mock_project.actual_cost, 10000.0)

    def test_remove_cost_not_found(self):
        """测试删除不存在的成本记录"""
        db = MagicMock()
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model.__name__ == 'ProjectCost':
                query_mock.filter().first.return_value = None
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        result = CostCollectionService.remove_cost_from_source(
            db=db,
            source_module="PURCHASE",
            source_type="PURCHASE_ORDER",
            source_id=999
        )
        
        self.assertFalse(result)


class TestCollectFromBom(unittest.TestCase):
    """测试从BOM归集成本"""

    @patch('app.services.cost_collection_service.delete_obj')
    @patch('app.services.cost_collection_service.CostAlertService')
    def test_collect_new_bom_cost(self, mock_alert, mock_delete):
        """测试新BOM成本归集"""
        db = MagicMock()
        
        # Mock BOM
        mock_bom = MagicMock()
        mock_bom.id = 1
        mock_bom.project_id = 100
        mock_bom.machine_id = 50
        mock_bom.bom_no = "BOM-001"
        mock_bom.bom_name = "测试BOM"
        mock_bom.status = "RELEASED"
        mock_bom.total_amount = Decimal("12000.00")
        
        # Mock BOM items
        mock_items = [
            MagicMock(amount=Decimal("5000.00")),
            MagicMock(amount=Decimal("7000.00")),
        ]
        
        # Mock项目
        mock_project = MagicMock()
        mock_project.id = 100
        mock_project.actual_cost = 20000.0
        
        # 配置查询
        def query_side_effect(model):
            query_mock = MagicMock()
            model_name = model.__name__ if hasattr(model, '__name__') else str(model)
            
            if 'BomHeader' in model_name:
                query_mock.filter().first.return_value = mock_bom
            elif 'BomItem' in model_name:
                query_mock.filter().all.return_value = mock_items
            elif model_name == 'ProjectCost':
                query_mock.filter().first.return_value = None
            elif model_name == 'Project':
                query_mock.filter().first.return_value = mock_project
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        result = CostCollectionService.collect_from_bom(
            db=db,
            bom_id=1,
            created_by=10
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, ProjectCost)
        self.assertTrue(db.add.called)

    def test_collect_bom_not_found(self):
        """测试BOM不存在"""
        db = MagicMock()
        
        def query_side_effect(model):
            query_mock = MagicMock()
            model_name = model.__name__ if hasattr(model, '__name__') else str(model)
            if 'BomHeader' in model_name:
                query_mock.filter().first.return_value = None
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        with self.assertRaises(ValueError) as context:
            CostCollectionService.collect_from_bom(
                db=db,
                bom_id=999
            )
        
        self.assertIn("BOM不存在", str(context.exception))

    def test_collect_bom_without_project(self):
        """测试BOM没有关联项目"""
        db = MagicMock()
        
        mock_bom = MagicMock()
        mock_bom.id = 1
        mock_bom.project_id = None
        mock_bom.status = "RELEASED"
        
        def query_side_effect(model):
            query_mock = MagicMock()
            model_name = model.__name__ if hasattr(model, '__name__') else str(model)
            if 'BomHeader' in model_name:
                query_mock.filter().first.return_value = mock_bom
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        with self.assertRaises(ValueError) as context:
            CostCollectionService.collect_from_bom(
                db=db,
                bom_id=1
            )
        
        self.assertIn("未关联项目", str(context.exception))

    def test_collect_bom_not_released(self):
        """测试未发布的BOM"""
        db = MagicMock()
        
        mock_bom = MagicMock()
        mock_bom.id = 1
        mock_bom.project_id = 100
        mock_bom.status = "DRAFT"
        
        def query_side_effect(model):
            query_mock = MagicMock()
            model_name = model.__name__ if hasattr(model, '__name__') else str(model)
            if 'BomHeader' in model_name:
                query_mock.filter().first.return_value = mock_bom
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        with self.assertRaises(ValueError) as context:
            CostCollectionService.collect_from_bom(
                db=db,
                bom_id=1
            )
        
        self.assertIn("已发布", str(context.exception))

    @patch('app.services.cost_collection_service.delete_obj')
    def test_collect_bom_zero_amount(self, mock_delete):
        """测试BOM总金额为0"""
        db = MagicMock()
        
        mock_bom = MagicMock()
        mock_bom.id = 1
        mock_bom.project_id = 100
        mock_bom.status = "RELEASED"
        mock_bom.total_amount = None
        
        # Mock空的BOM items
        mock_items = []
        
        def query_side_effect(model):
            query_mock = MagicMock()
            model_name = model.__name__ if hasattr(model, '__name__') else str(model)
            
            if 'BomHeader' in model_name:
                query_mock.filter().first.return_value = mock_bom
            elif 'BomItem' in model_name:
                query_mock.filter().all.return_value = mock_items
            elif model_name == 'ProjectCost':
                query_mock.filter().first.return_value = None
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        result = CostCollectionService.collect_from_bom(
            db=db,
            bom_id=1
        )
        
        self.assertIsNone(result)


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""

    @patch('app.services.cost_collection_service.CostAlertService')
    def test_order_with_none_amounts(self, mock_alert):
        """测试订单金额为None的情况"""
        db = MagicMock()
        
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.project_id = 100
        mock_order.order_no = "PO-001"
        mock_order.total_amount = None
        mock_order.tax_amount = None
        mock_order.order_date = None
        mock_order.created_at = None
        
        mock_project = MagicMock()
        mock_project.id = 100
        mock_project.actual_cost = None
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model.__name__ == 'PurchaseOrder':
                query_mock.filter().first.return_value = mock_order
            elif model.__name__ == 'ProjectCost':
                query_mock.filter().first.return_value = None
            elif model.__name__ == 'Project':
                query_mock.filter().first.return_value = mock_project
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        result = CostCollectionService.collect_from_purchase_order(
            db=db,
            order_id=1
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, ProjectCost)
        self.assertTrue(db.add.called)

    @patch('app.services.cost_collection_service.CostAlertService')
    def test_project_actual_cost_none(self, mock_alert):
        """测试项目实际成本为None的情况"""
        db = MagicMock()
        
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.project_id = 100
        mock_order.order_no = "PO-001"
        mock_order.total_amount = Decimal("5000.00")
        mock_order.tax_amount = Decimal("650.00")
        mock_order.order_date = date(2024, 1, 15)
        mock_order.created_at = datetime(2024, 1, 15, 10, 0, 0)
        
        mock_project = MagicMock()
        mock_project.id = 100
        mock_project.actual_cost = None
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model.__name__ == 'PurchaseOrder':
                query_mock.filter().first.return_value = mock_order
            elif model.__name__ == 'ProjectCost':
                query_mock.filter().first.return_value = None
            elif model.__name__ == 'Project':
                query_mock.filter().first.return_value = mock_project
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        result = CostCollectionService.collect_from_purchase_order(
            db=db,
            order_id=1
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, ProjectCost)
        # 验证项目成本更新：None + 5000 = 5000
        self.assertEqual(mock_project.actual_cost, 5000.0)


if __name__ == "__main__":
    unittest.main()
