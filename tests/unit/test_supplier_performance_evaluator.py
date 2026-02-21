# -*- coding: utf-8 -*-
"""
供应商绩效评估服务单元测试

测试策略：
1. 只mock外部依赖（db.query, db.add, db.commit等数据库操作）
2. 让业务逻辑真正执行（不mock业务方法）
3. 覆盖主要方法和边界情况
4. 目标覆盖率：70%+
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch, call

from app.services.supplier_performance_evaluator import SupplierPerformanceEvaluator
from app.models import (
    Vendor,
    PurchaseOrder,
    GoodsReceipt,
    GoodsReceiptItem,
    SupplierPerformance,
)


class TestSupplierPerformanceEvaluatorCore(unittest.TestCase):
    """测试核心评估方法"""

    def setUp(self):
        """初始化测试环境"""
        self.mock_db = MagicMock()
        self.evaluator = SupplierPerformanceEvaluator(self.mock_db, tenant_id=1)

    # ========== evaluate_supplier() 主入口测试 ==========

    def test_evaluate_supplier_not_found(self):
        """测试供应商不存在的情况"""
        self.mock_db.query.return_value.get.return_value = None
        
        result = self.evaluator.evaluate_supplier(999, "2024-01")
        
        self.assertIsNone(result)
        self.mock_db.query.return_value.get.assert_called_once_with(999)

    def test_evaluate_supplier_invalid_period(self):
        """测试无效的评估期间格式"""
        mock_vendor = Mock(spec=Vendor)
        self.mock_db.query.return_value.get.return_value = mock_vendor
        
        result = self.evaluator.evaluate_supplier(1, "invalid-period")
        
        self.assertIsNone(result)

    def test_evaluate_supplier_success_with_orders(self):
        """测试成功评估有订单的供应商"""
        # Mock供应商
        mock_vendor = Mock(spec=Vendor)
        mock_vendor.id = 1
        mock_vendor.supplier_code = "SUP001"
        mock_vendor.supplier_name = "测试供应商"
        
        # Mock订单
        mock_order = Mock(spec=PurchaseOrder)
        mock_order.id = 1
        mock_order.total_amount = Decimal('10000')
        mock_order.order_date = date(2024, 1, 15)
        mock_order.required_date = date(2024, 1, 20)
        mock_order.promised_date = date(2024, 1, 20)
        mock_order.submitted_at = datetime(2024, 1, 15, 10, 0)
        mock_order.approved_at = datetime(2024, 1, 15, 14, 0)
        
        # Mock收货记录
        mock_receipt = Mock(spec=GoodsReceipt)
        mock_receipt.order_id = 1
        mock_receipt.receipt_date = date(2024, 1, 19)
        
        # Mock收货明细
        mock_receipt_item = Mock(spec=GoodsReceiptItem)
        mock_receipt_item.received_qty = Decimal('100')
        mock_receipt_item.qualified_qty = Decimal('95')
        mock_receipt_item.rejected_qty = Decimal('5')
        
        # 配置mock查询链
        def query_side_effect(model_or_func):
            mock_query = MagicMock()
            # 检查是否是func.avg() 或其他聚合函数
            if not isinstance(model_or_func, type):
                # 这是一个函数调用（如func.avg()），返回price_query_mock
                mock_query.join.return_value.filter.return_value.scalar.return_value = 100.0
                return mock_query
            
            if model_or_func == Vendor:
                mock_query.get.return_value = mock_vendor
            elif model_or_func == PurchaseOrder:
                mock_query.filter.return_value.all.return_value = [mock_order]
            elif model_or_func == SupplierPerformance:
                mock_query.filter.return_value.first.return_value = None
            elif model_or_func == GoodsReceipt:
                mock_query.filter.return_value.all.return_value = [mock_receipt]
            elif model_or_func == GoodsReceiptItem:
                mock_query.join.return_value.filter.return_value.all.return_value = [mock_receipt_item]
            return mock_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        # 执行评估
        result = self.evaluator.evaluate_supplier(1, "2024-01")
        
        # 验证结果
        self.assertIsNotNone(result)
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_evaluate_supplier_no_orders(self):
        """测试无订单的供应商"""
        mock_vendor = Mock(spec=Vendor)
        mock_vendor.id = 1
        mock_vendor.supplier_code = "SUP002"
        mock_vendor.supplier_name = "无订单供应商"
        
        def query_side_effect(model_or_func):
            mock_query = MagicMock()
            # 检查是否是func.avg() 或其他聚合函数
            if not isinstance(model_or_func, type):
                mock_query.join.return_value.filter.return_value.scalar.return_value = None
                return mock_query
            
            if model_or_func == Vendor:
                mock_query.get.return_value = mock_vendor
            elif model_or_func == PurchaseOrder:
                mock_query.filter.return_value.all.return_value = []
            elif model_or_func == SupplierPerformance:
                mock_query.filter.return_value.first.return_value = None
            return mock_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.evaluator.evaluate_supplier(1, "2024-01")
        
        self.assertIsNotNone(result)
        self.mock_db.add.assert_called_once()

    def test_evaluate_supplier_existing_record(self):
        """测试更新已存在的评估记录"""
        mock_vendor = Mock(spec=Vendor)
        mock_vendor.id = 1
        mock_vendor.supplier_code = "SUP003"
        mock_vendor.supplier_name = "现有记录供应商"
        
        mock_existing = Mock(spec=SupplierPerformance)
        mock_existing.id = 100
        
        def query_side_effect(model):
            mock_query = MagicMock()
            if model == Vendor:
                mock_query.get.return_value = mock_vendor
            elif model == PurchaseOrder:
                mock_query.filter.return_value.all.return_value = []
            elif model == SupplierPerformance:
                mock_query.filter.return_value.first.return_value = mock_existing
            return mock_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        # Mock价格查询
        price_query_mock = MagicMock()
        price_query_mock.join.return_value.filter.return_value.scalar.return_value = None
        
        original_query = self.mock_db.query
        def enhanced_query(model_or_func):
            if hasattr(model_or_func, '__name__') and 'avg' in str(model_or_func):
                return price_query_mock
            return original_query(model_or_func)
        
        self.mock_db.query = enhanced_query
        
        result = self.evaluator.evaluate_supplier(1, "2024-01")
        
        self.assertEqual(result, mock_existing)
        # 不应该调用add（因为是更新）
        self.mock_db.add.assert_not_called()

    def test_evaluate_supplier_december_period(self):
        """测试12月期间的日期计算"""
        mock_vendor = Mock(spec=Vendor)
        self.mock_db.query.return_value.get.return_value = mock_vendor
        
        def query_side_effect(model_or_func):
            mock_query = MagicMock()
            # 检查是否是func.avg() 或其他聚合函数
            if not isinstance(model_or_func, type):
                mock_query.join.return_value.filter.return_value.scalar.return_value = None
                return mock_query
            
            if model_or_func == Vendor:
                mock_query.get.return_value = mock_vendor
            elif model_or_func == PurchaseOrder:
                mock_query.filter.return_value.all.return_value = []
            elif model_or_func == SupplierPerformance:
                mock_query.filter.return_value.first.return_value = None
            return mock_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.evaluator.evaluate_supplier(1, "2024-12")
        
        self.assertIsNotNone(result)

    # ========== _calculate_delivery_metrics() 测试 ==========

    def test_delivery_metrics_no_orders(self):
        """测试无订单时的交货指标"""
        result = self.evaluator._calculate_delivery_metrics([], date(2024, 1, 1), date(2024, 1, 31))
        
        self.assertEqual(result['on_time_rate'], Decimal('0'))
        self.assertEqual(result['on_time_orders'], 0)
        self.assertEqual(result['late_orders'], 0)
        self.assertEqual(result['avg_delay_days'], Decimal('0'))

    def test_delivery_metrics_all_on_time(self):
        """测试全部准时交货"""
        mock_order = Mock(spec=PurchaseOrder)
        mock_order.id = 1
        mock_order.promised_date = date(2024, 1, 20)
        mock_order.required_date = None
        
        mock_receipt = Mock(spec=GoodsReceipt)
        mock_receipt.receipt_date = date(2024, 1, 19)
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_receipt]
        
        result = self.evaluator._calculate_delivery_metrics([mock_order], date(2024, 1, 1), date(2024, 1, 31))
        
        self.assertEqual(result['on_time_rate'], Decimal('100'))
        self.assertEqual(result['on_time_orders'], 1)
        self.assertEqual(result['late_orders'], 0)

    def test_delivery_metrics_with_late_orders(self):
        """测试有延迟订单"""
        mock_order = Mock(spec=PurchaseOrder)
        mock_order.id = 1
        mock_order.promised_date = date(2024, 1, 20)
        mock_order.required_date = None
        
        mock_receipt = Mock(spec=GoodsReceipt)
        mock_receipt.receipt_date = date(2024, 1, 25)  # 延迟5天
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_receipt]
        
        result = self.evaluator._calculate_delivery_metrics([mock_order], date(2024, 1, 1), date(2024, 1, 31))
        
        self.assertEqual(result['on_time_rate'], Decimal('0'))
        self.assertEqual(result['on_time_orders'], 0)
        self.assertEqual(result['late_orders'], 1)
        self.assertEqual(result['avg_delay_days'], Decimal('5'))

    def test_delivery_metrics_no_receipts(self):
        """测试无收货记录"""
        mock_order = Mock(spec=PurchaseOrder)
        mock_order.id = 1
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = self.evaluator._calculate_delivery_metrics([mock_order], date(2024, 1, 1), date(2024, 1, 31))
        
        self.assertEqual(result['on_time_rate'], Decimal('0'))
        self.assertEqual(result['on_time_orders'], 0)
        self.assertEqual(result['late_orders'], 0)

    def test_delivery_metrics_use_required_date(self):
        """测试使用要求交期（无承诺交期）"""
        mock_order = Mock(spec=PurchaseOrder)
        mock_order.id = 1
        mock_order.promised_date = None
        mock_order.required_date = date(2024, 1, 20)
        
        mock_receipt = Mock(spec=GoodsReceipt)
        mock_receipt.receipt_date = date(2024, 1, 19)
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_receipt]
        
        result = self.evaluator._calculate_delivery_metrics([mock_order], date(2024, 1, 1), date(2024, 1, 31))
        
        self.assertEqual(result['on_time_orders'], 1)

    def test_delivery_metrics_no_promised_date(self):
        """测试无承诺交期和要求交期"""
        mock_order = Mock(spec=PurchaseOrder)
        mock_order.id = 1
        mock_order.promised_date = None
        mock_order.required_date = None
        
        mock_receipt = Mock(spec=GoodsReceipt)
        mock_receipt.receipt_date = date(2024, 1, 19)
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_receipt]
        
        result = self.evaluator._calculate_delivery_metrics([mock_order], date(2024, 1, 1), date(2024, 1, 31))
        
        # 无交期时不计入统计
        self.assertEqual(result['on_time_orders'], 0)
        self.assertEqual(result['late_orders'], 0)

    def test_delivery_metrics_multiple_receipts(self):
        """测试多个收货记录取最早日期"""
        mock_order = Mock(spec=PurchaseOrder)
        mock_order.id = 1
        mock_order.promised_date = date(2024, 1, 20)
        mock_order.required_date = None
        
        mock_receipt1 = Mock(spec=GoodsReceipt)
        mock_receipt1.receipt_date = date(2024, 1, 25)
        
        mock_receipt2 = Mock(spec=GoodsReceipt)
        mock_receipt2.receipt_date = date(2024, 1, 19)  # 最早
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_receipt1, mock_receipt2]
        
        result = self.evaluator._calculate_delivery_metrics([mock_order], date(2024, 1, 1), date(2024, 1, 31))
        
        self.assertEqual(result['on_time_orders'], 1)  # 以最早日期为准

    # ========== _calculate_quality_metrics() 测试 ==========

    def test_quality_metrics_no_items(self):
        """测试无收货明细"""
        mock_order = Mock(spec=PurchaseOrder)
        mock_order.id = 1
        
        self.mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        
        result = self.evaluator._calculate_quality_metrics([mock_order], date(2024, 1, 1), date(2024, 1, 31))
        
        self.assertEqual(result['pass_rate'], Decimal('0'))
        self.assertEqual(result['total_qty'], Decimal('0'))
        self.assertEqual(result['qualified_qty'], Decimal('0'))
        self.assertEqual(result['rejected_qty'], Decimal('0'))

    def test_quality_metrics_all_qualified(self):
        """测试全部合格"""
        mock_order = Mock(spec=PurchaseOrder)
        mock_order.id = 1
        
        mock_item = Mock(spec=GoodsReceiptItem)
        mock_item.received_qty = Decimal('100')
        mock_item.qualified_qty = Decimal('100')
        mock_item.rejected_qty = Decimal('0')
        
        self.mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_item]
        
        result = self.evaluator._calculate_quality_metrics([mock_order], date(2024, 1, 1), date(2024, 1, 31))
        
        self.assertEqual(result['pass_rate'], Decimal('100'))
        self.assertEqual(result['total_qty'], Decimal('100'))
        self.assertEqual(result['qualified_qty'], Decimal('100'))

    def test_quality_metrics_with_rejects(self):
        """测试有不合格品"""
        mock_order = Mock(spec=PurchaseOrder)
        mock_order.id = 1
        
        mock_item = Mock(spec=GoodsReceiptItem)
        mock_item.received_qty = Decimal('100')
        mock_item.qualified_qty = Decimal('95')
        mock_item.rejected_qty = Decimal('5')
        
        self.mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_item]
        
        result = self.evaluator._calculate_quality_metrics([mock_order], date(2024, 1, 1), date(2024, 1, 31))
        
        self.assertEqual(result['pass_rate'], Decimal('95'))
        self.assertEqual(result['rejected_qty'], Decimal('5'))

    def test_quality_metrics_multiple_items(self):
        """测试多个收货明细汇总"""
        mock_order = Mock(spec=PurchaseOrder)
        mock_order.id = 1
        
        mock_item1 = Mock(spec=GoodsReceiptItem)
        mock_item1.received_qty = Decimal('100')
        mock_item1.qualified_qty = Decimal('95')
        mock_item1.rejected_qty = Decimal('5')
        
        mock_item2 = Mock(spec=GoodsReceiptItem)
        mock_item2.received_qty = Decimal('200')
        mock_item2.qualified_qty = Decimal('190')
        mock_item2.rejected_qty = Decimal('10')
        
        self.mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_item1, mock_item2]
        
        result = self.evaluator._calculate_quality_metrics([mock_order], date(2024, 1, 1), date(2024, 1, 31))
        
        self.assertEqual(result['total_qty'], Decimal('300'))
        self.assertEqual(result['qualified_qty'], Decimal('285'))
        self.assertEqual(result['rejected_qty'], Decimal('15'))
        self.assertEqual(result['pass_rate'], Decimal('95'))

    # ========== _calculate_price_competitiveness() 测试 ==========

    def test_price_competitiveness_no_data(self):
        """测试无价格数据"""
        mock_query = MagicMock()
        mock_query.join.return_value.filter.return_value.scalar.return_value = None
        self.mock_db.query.return_value = mock_query
        
        result = self.evaluator._calculate_price_competitiveness(1, date(2024, 1, 1), date(2024, 1, 31))
        
        self.assertEqual(result['competitiveness'], Decimal('50'))
        self.assertEqual(result['vs_market'], Decimal('0'))

    def test_price_competitiveness_below_market_20_percent(self):
        """测试价格低于市场20%以上"""
        # 第一次查询：供应商平均价格 = 80
        # 第二次查询：市场平均价格 = 100
        mock_query = MagicMock()
        mock_query.join.return_value.filter.return_value.scalar.side_effect = [80.0, 100.0]
        self.mock_db.query.return_value = mock_query
        
        result = self.evaluator._calculate_price_competitiveness(1, date(2024, 1, 1), date(2024, 1, 31))
        
        self.assertEqual(result['competitiveness'], Decimal('100'))
        self.assertEqual(result['vs_market'], Decimal('-20'))

    def test_price_competitiveness_below_market_10_percent(self):
        """测试价格低于市场10-20%"""
        mock_query = MagicMock()
        mock_query.join.return_value.filter.return_value.scalar.side_effect = [85.0, 100.0]
        self.mock_db.query.return_value = mock_query
        
        result = self.evaluator._calculate_price_competitiveness(1, date(2024, 1, 1), date(2024, 1, 31))
        
        self.assertEqual(result['competitiveness'], Decimal('90'))

    def test_price_competitiveness_below_market_5_percent(self):
        """测试价格低于市场0-10%"""
        mock_query = MagicMock()
        mock_query.join.return_value.filter.return_value.scalar.side_effect = [95.0, 100.0]
        self.mock_db.query.return_value = mock_query
        
        result = self.evaluator._calculate_price_competitiveness(1, date(2024, 1, 1), date(2024, 1, 31))
        
        self.assertEqual(result['competitiveness'], Decimal('80'))

    def test_price_competitiveness_above_market_5_percent(self):
        """测试价格高于市场0-10%"""
        mock_query = MagicMock()
        mock_query.join.return_value.filter.return_value.scalar.side_effect = [105.0, 100.0]
        self.mock_db.query.return_value = mock_query
        
        result = self.evaluator._calculate_price_competitiveness(1, date(2024, 1, 1), date(2024, 1, 31))
        
        self.assertEqual(result['competitiveness'], Decimal('60'))

    def test_price_competitiveness_above_market_15_percent(self):
        """测试价格高于市场10-20%"""
        mock_query = MagicMock()
        mock_query.join.return_value.filter.return_value.scalar.side_effect = [115.0, 100.0]
        self.mock_db.query.return_value = mock_query
        
        result = self.evaluator._calculate_price_competitiveness(1, date(2024, 1, 1), date(2024, 1, 31))
        
        self.assertEqual(result['competitiveness'], Decimal('40'))

    def test_price_competitiveness_above_market_25_percent(self):
        """测试价格高于市场20%以上"""
        mock_query = MagicMock()
        mock_query.join.return_value.filter.return_value.scalar.side_effect = [125.0, 100.0]
        self.mock_db.query.return_value = mock_query
        
        result = self.evaluator._calculate_price_competitiveness(1, date(2024, 1, 1), date(2024, 1, 31))
        
        self.assertEqual(result['competitiveness'], Decimal('20'))

    def test_price_competitiveness_no_market_data(self):
        """测试无市场价格数据"""
        # 第一次查询：供应商平均价格 = 100
        # 第二次查询：市场平均价格 = None
        mock_query = MagicMock()
        mock_query.join.return_value.filter.return_value.scalar.side_effect = [100.0, None]
        self.mock_db.query.return_value = mock_query
        
        result = self.evaluator._calculate_price_competitiveness(1, date(2024, 1, 1), date(2024, 1, 31))
        
        # 无市场数据时，vs_market应为0
        self.assertEqual(result['vs_market'], Decimal('0'))

    # ========== _calculate_response_speed() 测试 ==========

    def test_response_speed_no_orders(self):
        """测试无订单数据"""
        self.mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = self.evaluator._calculate_response_speed(1, date(2024, 1, 1), date(2024, 1, 31))
        
        self.assertEqual(result['score'], Decimal('50'))
        self.assertEqual(result['avg_hours'], Decimal('0'))

    def test_response_speed_within_4_hours(self):
        """测试4小时内响应"""
        mock_order = Mock(spec=PurchaseOrder)
        mock_order.submitted_at = datetime(2024, 1, 15, 10, 0)
        mock_order.approved_at = datetime(2024, 1, 15, 12, 0)  # 2小时
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_order]
        
        result = self.evaluator._calculate_response_speed(1, date(2024, 1, 1), date(2024, 1, 31))
        
        self.assertEqual(result['score'], Decimal('100'))
        self.assertEqual(result['avg_hours'], Decimal('2'))

    def test_response_speed_within_8_hours(self):
        """测试8小时内响应"""
        mock_order = Mock(spec=PurchaseOrder)
        mock_order.submitted_at = datetime(2024, 1, 15, 10, 0)
        mock_order.approved_at = datetime(2024, 1, 15, 16, 0)  # 6小时
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_order]
        
        result = self.evaluator._calculate_response_speed(1, date(2024, 1, 1), date(2024, 1, 31))
        
        self.assertEqual(result['score'], Decimal('90'))

    def test_response_speed_within_24_hours(self):
        """测试24小时内响应"""
        mock_order = Mock(spec=PurchaseOrder)
        mock_order.submitted_at = datetime(2024, 1, 15, 10, 0)
        mock_order.approved_at = datetime(2024, 1, 16, 8, 0)  # 22小时
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_order]
        
        result = self.evaluator._calculate_response_speed(1, date(2024, 1, 1), date(2024, 1, 31))
        
        self.assertEqual(result['score'], Decimal('80'))

    def test_response_speed_within_48_hours(self):
        """测试48小时内响应"""
        mock_order = Mock(spec=PurchaseOrder)
        mock_order.submitted_at = datetime(2024, 1, 15, 10, 0)
        mock_order.approved_at = datetime(2024, 1, 16, 20, 0)  # 34小时
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_order]
        
        result = self.evaluator._calculate_response_speed(1, date(2024, 1, 1), date(2024, 1, 31))
        
        self.assertEqual(result['score'], Decimal('60'))

    def test_response_speed_over_48_hours(self):
        """测试超过48小时"""
        mock_order = Mock(spec=PurchaseOrder)
        mock_order.submitted_at = datetime(2024, 1, 15, 10, 0)
        mock_order.approved_at = datetime(2024, 1, 18, 10, 0)  # 72小时
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_order]
        
        result = self.evaluator._calculate_response_speed(1, date(2024, 1, 1), date(2024, 1, 31))
        
        # 60 - (72-48)/24 * 5 = 60 - 5 = 55
        self.assertEqual(result['score'], Decimal('55'))

    def test_response_speed_very_slow(self):
        """测试极慢响应（不低于30分）"""
        mock_order = Mock(spec=PurchaseOrder)
        mock_order.submitted_at = datetime(2024, 1, 15, 10, 0)
        mock_order.approved_at = datetime(2024, 1, 25, 10, 0)  # 240小时
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_order]
        
        result = self.evaluator._calculate_response_speed(1, date(2024, 1, 1), date(2024, 1, 31))
        
        # 应该不低于30
        self.assertGreaterEqual(result['score'], Decimal('30'))

    def test_response_speed_multiple_orders(self):
        """测试多个订单取平均"""
        mock_order1 = Mock(spec=PurchaseOrder)
        mock_order1.submitted_at = datetime(2024, 1, 15, 10, 0)
        mock_order1.approved_at = datetime(2024, 1, 15, 12, 0)  # 2小时
        
        mock_order2 = Mock(spec=PurchaseOrder)
        mock_order2.submitted_at = datetime(2024, 1, 16, 10, 0)
        mock_order2.approved_at = datetime(2024, 1, 16, 16, 0)  # 6小时
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_order1, mock_order2]
        
        result = self.evaluator._calculate_response_speed(1, date(2024, 1, 1), date(2024, 1, 31))
        
        # 平均4小时
        self.assertEqual(result['avg_hours'], Decimal('4'))
        self.assertEqual(result['score'], Decimal('100'))

    # ========== _calculate_overall_score() 测试 ==========

    def test_overall_score_default_weights(self):
        """测试默认权重计算"""
        delivery_metrics = {'on_time_rate': Decimal('90')}
        quality_metrics = {'pass_rate': Decimal('95')}
        price_metrics = {'competitiveness': Decimal('80')}
        response_metrics = {'score': Decimal('85')}
        
        weight_config = {
            'on_time_delivery': Decimal('30'),
            'quality': Decimal('30'),
            'price': Decimal('20'),
            'response': Decimal('20'),
        }
        
        result = self.evaluator._calculate_overall_score(
            delivery_metrics, quality_metrics, price_metrics, response_metrics, weight_config
        )
        
        # 90*0.3 + 95*0.3 + 80*0.2 + 85*0.2 = 27 + 28.5 + 16 + 17 = 88.5
        self.assertEqual(result, Decimal('88.5'))

    def test_overall_score_custom_weights(self):
        """测试自定义权重"""
        delivery_metrics = {'on_time_rate': Decimal('80')}
        quality_metrics = {'pass_rate': Decimal('90')}
        price_metrics = {'competitiveness': Decimal('70')}
        response_metrics = {'score': Decimal('85')}
        
        weight_config = {
            'on_time_delivery': Decimal('40'),
            'quality': Decimal('40'),
            'price': Decimal('10'),
            'response': Decimal('10'),
        }
        
        result = self.evaluator._calculate_overall_score(
            delivery_metrics, quality_metrics, price_metrics, response_metrics, weight_config
        )
        
        # 80*0.4 + 90*0.4 + 70*0.1 + 85*0.1 = 32 + 36 + 7 + 8.5 = 83.5
        self.assertEqual(result, Decimal('83.5'))

    def test_overall_score_all_perfect(self):
        """测试全部满分"""
        delivery_metrics = {'on_time_rate': Decimal('100')}
        quality_metrics = {'pass_rate': Decimal('100')}
        price_metrics = {'competitiveness': Decimal('100')}
        response_metrics = {'score': Decimal('100')}
        
        weight_config = {
            'on_time_delivery': Decimal('25'),
            'quality': Decimal('25'),
            'price': Decimal('25'),
            'response': Decimal('25'),
        }
        
        result = self.evaluator._calculate_overall_score(
            delivery_metrics, quality_metrics, price_metrics, response_metrics, weight_config
        )
        
        self.assertEqual(result, Decimal('100'))

    # ========== _determine_rating() 测试 ==========

    def test_determine_rating_a_plus(self):
        """测试A+评级（>=90）"""
        self.assertEqual(self.evaluator._determine_rating(Decimal('95')), 'A+')
        self.assertEqual(self.evaluator._determine_rating(Decimal('90')), 'A+')

    def test_determine_rating_a(self):
        """测试A评级（>=80）"""
        self.assertEqual(self.evaluator._determine_rating(Decimal('85')), 'A')
        self.assertEqual(self.evaluator._determine_rating(Decimal('80')), 'A')

    def test_determine_rating_b(self):
        """测试B评级（>=70）"""
        self.assertEqual(self.evaluator._determine_rating(Decimal('75')), 'B')
        self.assertEqual(self.evaluator._determine_rating(Decimal('70')), 'B')

    def test_determine_rating_c(self):
        """测试C评级（>=60）"""
        self.assertEqual(self.evaluator._determine_rating(Decimal('65')), 'C')
        self.assertEqual(self.evaluator._determine_rating(Decimal('60')), 'C')

    def test_determine_rating_d(self):
        """测试D评级（<60）"""
        self.assertEqual(self.evaluator._determine_rating(Decimal('59')), 'D')
        self.assertEqual(self.evaluator._determine_rating(Decimal('0')), 'D')

    # ========== get_supplier_ranking() 测试 ==========

    def test_get_supplier_ranking(self):
        """测试获取供应商排名"""
        mock_performance1 = Mock(spec=SupplierPerformance)
        mock_performance1.overall_score = Decimal('95')
        
        mock_performance2 = Mock(spec=SupplierPerformance)
        mock_performance2.overall_score = Decimal('85')
        
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_performance1, mock_performance2
        ]
        
        result = self.evaluator.get_supplier_ranking("2024-01", limit=10)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].overall_score, Decimal('95'))

    def test_get_supplier_ranking_empty(self):
        """测试无排名数据"""
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        result = self.evaluator.get_supplier_ranking("2024-01")
        
        self.assertEqual(len(result), 0)

    # ========== batch_evaluate_all_suppliers() 测试 ==========

    def test_batch_evaluate_all_suppliers_success(self):
        """测试批量评估成功"""
        mock_vendor1 = Mock(spec=Vendor)
        mock_vendor1.id = 1
        mock_vendor1.supplier_code = "SUP001"
        mock_vendor1.status = "ACTIVE"
        mock_vendor1.vendor_type = "MATERIAL"
        
        mock_vendor2 = Mock(spec=Vendor)
        mock_vendor2.id = 2
        mock_vendor2.supplier_code = "SUP002"
        mock_vendor2.status = "ACTIVE"
        mock_vendor2.vendor_type = "MATERIAL"
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_vendor1, mock_vendor2]
        
        # Mock evaluate_supplier
        with patch.object(self.evaluator, 'evaluate_supplier') as mock_evaluate:
            mock_evaluate.return_value = Mock(spec=SupplierPerformance)
            
            result = self.evaluator.batch_evaluate_all_suppliers("2024-01")
            
            self.assertEqual(result, 2)
            self.assertEqual(mock_evaluate.call_count, 2)

    def test_batch_evaluate_all_suppliers_with_errors(self):
        """测试批量评估时部分失败"""
        mock_vendor1 = Mock(spec=Vendor)
        mock_vendor1.id = 1
        mock_vendor1.supplier_code = "SUP001"
        
        mock_vendor2 = Mock(spec=Vendor)
        mock_vendor2.id = 2
        mock_vendor2.supplier_code = "SUP002"
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_vendor1, mock_vendor2]
        
        # Mock evaluate_supplier，第一个成功，第二个失败
        with patch.object(self.evaluator, 'evaluate_supplier') as mock_evaluate:
            mock_evaluate.side_effect = [Mock(spec=SupplierPerformance), Exception("评估失败")]
            
            result = self.evaluator.batch_evaluate_all_suppliers("2024-01")
            
            # 只有一个成功
            self.assertEqual(result, 1)

    def test_batch_evaluate_all_suppliers_empty(self):
        """测试无供应商"""
        self.mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = self.evaluator.batch_evaluate_all_suppliers("2024-01")
        
        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
