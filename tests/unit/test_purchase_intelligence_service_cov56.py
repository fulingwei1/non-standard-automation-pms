# -*- coding: utf-8 -*-
"""
采购智能服务单元测试

测试 app/services/purchase_intelligence/service.py
目标覆盖率: 56%+
"""

import unittest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.models import (
    GoodsReceipt,
    Material,
    PurchaseOrder,
    PurchaseSuggestion,
    SupplierPerformance,
    SupplierQuotation,
    Vendor,
)
from app.schemas.purchase_intelligence import PurchaseSuggestionResponse
from app.services.purchase_intelligence import PurchaseIntelligenceService


class TestPurchaseIntelligenceService(unittest.TestCase):
    """采购智能服务测试类"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = PurchaseIntelligenceService(self.db)

    # ==================== 采购建议相关测试 ====================

    def test_get_purchase_suggestions_with_filters(self):
        """测试获取采购建议列表（带筛选条件）"""
        # Mock 数据
        mock_suggestion = MagicMock(spec=PurchaseSuggestion)
        mock_suggestion.id = 1
        mock_suggestion.material_id = 100
        mock_suggestion.status = 'PENDING'
        mock_suggestion.suggested_supplier_id = 10
        mock_suggestion.purchase_order_id = None

        # Mock 查询链
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_suggestion]

        self.db.query.return_value = mock_query

        # Mock 供应商查询
        mock_supplier = MagicMock(spec=Vendor)
        mock_supplier.supplier_name = "测试供应商"
        self.db.query.return_value.get.return_value = mock_supplier

        # 执行测试
        result = self.service.get_purchase_suggestions(
            status='PENDING',
            material_id=100,
            skip=0,
            limit=20,
        )

        # 验证
        self.assertEqual(len(result), 1)
        self.db.query.assert_called()

    def test_approve_purchase_suggestion_success(self):
        """测试批准采购建议（成功）"""
        # Mock 建议
        mock_suggestion = MagicMock(spec=PurchaseSuggestion)
        mock_suggestion.id = 1
        mock_suggestion.status = 'PENDING'

        self.db.query.return_value.get.return_value = mock_suggestion

        # 执行测试
        suggestion, message = self.service.approve_purchase_suggestion(
            suggestion_id=1,
            approved=True,
            user_id=1,
            review_note="测试批准",
        )

        # 验证
        self.assertEqual(suggestion.status, 'APPROVED')
        self.assertEqual(message, "采购建议已批准")
        self.db.commit.assert_called_once()

    def test_approve_purchase_suggestion_not_found(self):
        """测试批准采购建议（建议不存在）"""
        self.db.query.return_value.get.return_value = None

        # 执行测试并验证异常
        with self.assertRaises(ValueError) as ctx:
            self.service.approve_purchase_suggestion(
                suggestion_id=999,
                approved=True,
                user_id=1,
            )

        self.assertIn("不存在", str(ctx.exception))

    def test_approve_purchase_suggestion_invalid_status(self):
        """测试批准采购建议（状态不允许）"""
        # Mock 建议（已批准状态）
        mock_suggestion = MagicMock(spec=PurchaseSuggestion)
        mock_suggestion.status = 'APPROVED'

        self.db.query.return_value.get.return_value = mock_suggestion

        # 执行测试并验证异常
        with self.assertRaises(ValueError) as ctx:
            self.service.approve_purchase_suggestion(
                suggestion_id=1,
                approved=True,
                user_id=1,
            )

        self.assertIn("不允许审批", str(ctx.exception))

    # ==================== 供应商绩效相关测试 ====================

    def test_get_supplier_performance(self):
        """测试获取供应商绩效记录"""
        # Mock 绩效数据
        mock_performance = MagicMock(spec=SupplierPerformance)
        mock_performance.id = 1
        mock_performance.supplier_id = 10
        mock_performance.overall_score = Decimal('85.5')

        # Mock 查询链
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_performance]

        self.db.query.return_value = mock_query

        # 执行测试
        result = self.service.get_supplier_performance(
            supplier_id=10,
            evaluation_period='2024-01',
            limit=12,
        )

        # 验证
        self.assertEqual(len(result), 1)

    def test_evaluate_supplier_performance_supplier_not_found(self):
        """测试触发供应商绩效评估（供应商不存在）"""
        self.db.query.return_value.get.return_value = None

        # 执行测试并验证异常
        with self.assertRaises(ValueError) as ctx:
            self.service.evaluate_supplier_performance(
                supplier_id=999,
                evaluation_period='2024-01',
            )

        self.assertIn("供应商不存在", str(ctx.exception))

    # ==================== 报价相关测试 ====================

    def test_create_supplier_quotation_success(self):
        """测试创建供应商报价（成功）"""
        # Mock 供应商
        mock_supplier = MagicMock(spec=Vendor)
        mock_supplier.id = 10
        mock_supplier.supplier_code = 'SUP001'
        mock_supplier.supplier_name = '测试供应商'

        # Mock 物料
        mock_material = MagicMock(spec=Material)
        mock_material.id = 100
        mock_material.material_code = 'MAT001'
        mock_material.material_name = '测试物料'
        mock_material.specification = '规格A'

        # Mock 查询
        def query_side_effect(model):
            if model == Vendor:
                mock_query = MagicMock()
                mock_query.get.return_value = mock_supplier
                return mock_query
            elif model == Material:
                mock_query = MagicMock()
                mock_query.get.return_value = mock_material
                return mock_query
            else:
                # Mock SupplierQuotation 查询
                mock_query = MagicMock()
                mock_query.filter.return_value = mock_query
                mock_query.order_by.return_value = mock_query
                mock_query.first.return_value = None
                return mock_query

        self.db.query.side_effect = query_side_effect

        # 执行测试
        quotation = self.service.create_supplier_quotation(
            supplier_id=10,
            material_id=100,
            unit_price=100.0,
            currency='CNY',
            min_order_qty=10,
            lead_time_days=7,
            valid_from=date(2024, 1, 1),
            valid_to=date(2024, 12, 31),
            user_id=1,
        )

        # 验证
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    def test_create_supplier_quotation_material_not_found(self):
        """测试创建供应商报价（物料不存在）"""
        # Mock 供应商存在，物料不存在
        mock_supplier = MagicMock(spec=Vendor)

        def query_side_effect(model):
            if model == Vendor:
                mock_query = MagicMock()
                mock_query.get.return_value = mock_supplier
                return mock_query
            elif model == Material:
                mock_query = MagicMock()
                mock_query.get.return_value = None
                return mock_query

        self.db.query.side_effect = query_side_effect

        # 执行测试并验证异常
        with self.assertRaises(ValueError) as ctx:
            self.service.create_supplier_quotation(
                supplier_id=10,
                material_id=999,
                unit_price=100.0,
                currency='CNY',
                min_order_qty=10,
                lead_time_days=7,
                valid_from=date(2024, 1, 1),
                valid_to=date(2024, 12, 31),
                user_id=1,
            )

        self.assertIn("物料不存在", str(ctx.exception))

    # ==================== 订单跟踪相关测试 ====================

    def test_get_purchase_order_tracking_order_not_found(self):
        """测试获取采购订单跟踪记录（订单不存在）"""
        self.db.query.return_value.get.return_value = None

        # 执行测试并验证异常
        with self.assertRaises(ValueError) as ctx:
            self.service.get_purchase_order_tracking(order_id=999)

        self.assertIn("订单不存在", str(ctx.exception))

    # ==================== 辅助方法测试 ====================

    def test_generate_quotation_no_new_day(self):
        """测试生成报价单号（当天首个）"""
        # Mock 查询返回空
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None

        self.db.query.return_value = mock_query

        # 执行测试
        quotation_no = self.service._generate_quotation_no()

        # 验证格式 QT20240101XXXX
        self.assertTrue(quotation_no.startswith('QT'))
        self.assertEqual(len(quotation_no), 14)
        self.assertTrue(quotation_no.endswith('0001'))

    def test_generate_quotation_no_existing(self):
        """测试生成报价单号（已有单号）"""
        # Mock 已存在的报价单号
        mock_quotation = MagicMock()
        mock_quotation.quotation_no = 'QT202401010005'

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = mock_quotation

        self.db.query.return_value = mock_query

        # 执行测试
        quotation_no = self.service._generate_quotation_no()

        # 验证序号递增
        self.assertTrue(quotation_no.endswith('0006'))


if __name__ == '__main__':
    unittest.main()
