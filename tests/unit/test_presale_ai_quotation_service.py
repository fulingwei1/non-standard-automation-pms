# -*- coding: utf-8 -*-
"""
AI报价单服务单元测试

目标：
1. 只mock外部依赖（db操作）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import datetime

from app.services.presale_ai_quotation_service import AIQuotationGeneratorService
from app.models.presale_ai_quotation import (
    PresaleAIQuotation, QuotationApproval, QuotationVersion,
    QuotationType, QuotationStatus
)
from app.schemas.presale_ai_quotation import (
    QuotationGenerateRequest, QuotationUpdateRequest,
    QuotationItem, ThreeTierQuotationRequest
)


class TestAIQuotationGeneratorService(unittest.TestCase):
    """AI报价单生成服务测试"""

    def setUp(self):
        """每个测试前的准备"""
        self.db = MagicMock()
        self.service = AIQuotationGeneratorService(self.db)
        self.user_id = 1

    # ========== generate_quotation_number() 测试 ==========

    def test_generate_quotation_number_first_of_day(self):
        """测试生成当天第一个报价单编号"""
        # Mock数据库查询返回0个已有报价单
        self.db.query.return_value.filter.return_value.count.return_value = 0
        
        number = self.service.generate_quotation_number()
        
        today = datetime.now().strftime("%Y%m%d")
        expected = f"QT-{today}-0001"
        self.assertEqual(number, expected)

    def test_generate_quotation_number_multiple_per_day(self):
        """测试生成当天第N个报价单编号"""
        # Mock已有5个报价单
        self.db.query.return_value.filter.return_value.count.return_value = 5
        
        number = self.service.generate_quotation_number()
        
        today = datetime.now().strftime("%Y%m%d")
        expected = f"QT-{today}-0006"
        self.assertEqual(number, expected)

    # ========== generate_quotation() 测试 ==========

    def test_generate_quotation_basic(self):
        """测试基础报价单生成"""
        # 准备测试数据
        items = [
            QuotationItem(
                name="产品A",
                description="描述A",
                quantity=Decimal("2"),
                unit="个",
                unit_price=Decimal("1000"),
                total_price=Decimal("2000"),
                category="硬件"
            ),
            QuotationItem(
                name="产品B",
                description="描述B",
                quantity=Decimal("1"),
                unit="套",
                unit_price=Decimal("3000"),
                total_price=Decimal("3000"),
                category="软件"
            )
        ]
        
        request = QuotationGenerateRequest(
            presale_ticket_id=101,
            customer_id=201,
            quotation_type=QuotationType.BASIC,
            items=items,
            tax_rate=Decimal("0.13"),
            discount_rate=Decimal("0"),
            validity_days=30,
            payment_terms="签订合同后一次性支付"
        )
        
        # Mock数据库操作
        self.db.query.return_value.filter.return_value.count.return_value = 0
        
        # 执行
        quotation = self.service.generate_quotation(request, self.user_id)
        
        # 验证
        self.assertIsInstance(quotation, PresaleAIQuotation)
        self.assertEqual(quotation.presale_ticket_id, 101)
        self.assertEqual(quotation.customer_id, 201)
        self.assertEqual(quotation.subtotal, Decimal("5000"))
        self.assertEqual(quotation.tax, Decimal("650"))  # 5000 * 0.13
        self.assertEqual(quotation.discount, Decimal("0"))
        self.assertEqual(quotation.total, Decimal("5650"))  # 5000 + 650 - 0
        self.assertEqual(quotation.status, QuotationStatus.DRAFT)
        self.assertEqual(quotation.created_by, self.user_id)
        self.assertEqual(quotation.payment_terms, "签订合同后一次性支付")
        
        # 验证数据库调用
        self.db.add.assert_called()
        self.db.commit.assert_called()

    def test_generate_quotation_with_discount(self):
        """测试带折扣的报价单生成"""
        items = [
            QuotationItem(
                name="产品",
                description="测试",
                quantity=Decimal("1"),
                unit="套",
                unit_price=Decimal("10000"),
                total_price=Decimal("10000"),
                category="软件"
            )
        ]
        
        request = QuotationGenerateRequest(
            presale_ticket_id=101,
            customer_id=201,
            quotation_type=QuotationType.STANDARD,
            items=items,
            tax_rate=Decimal("0.13"),
            discount_rate=Decimal("0.10"),  # 10%折扣
            validity_days=30
        )
        
        self.db.query.return_value.filter.return_value.count.return_value = 0
        
        quotation = self.service.generate_quotation(request, self.user_id)
        
        self.assertEqual(quotation.subtotal, Decimal("10000"))
        self.assertEqual(quotation.tax, Decimal("1300"))
        self.assertEqual(quotation.discount, Decimal("1000"))  # 10000 * 0.10
        self.assertEqual(quotation.total, Decimal("10300"))  # 10000 + 1300 - 1000

    def test_generate_quotation_auto_payment_terms(self):
        """测试自动生成付款条款"""
        items = [
            QuotationItem(
                name="产品",
                description="测试",
                quantity=Decimal("1"),
                unit="套",
                unit_price=Decimal("10000"),
                total_price=Decimal("10000"),
                category="软件"
            )
        ]
        
        # 不提供payment_terms
        request = QuotationGenerateRequest(
            presale_ticket_id=101,
            customer_id=201,
            quotation_type=QuotationType.PREMIUM,
            items=items,
            tax_rate=Decimal("0.13"),
            discount_rate=Decimal("0"),
            validity_days=30
        )
        
        self.db.query.return_value.filter.return_value.count.return_value = 0
        
        quotation = self.service.generate_quotation(request, self.user_id)
        
        # 验证自动生成了付款条款
        self.assertIsNotNone(quotation.payment_terms)
        self.assertIn("总金额", quotation.payment_terms)

    # ========== generate_three_tier_quotations() 测试 ==========

    def test_generate_three_tier_quotations(self):
        """测试生成三档报价"""
        request = ThreeTierQuotationRequest(
            presale_ticket_id=101,
            customer_id=201,
            base_requirements="需要一套ERP系统，包含基本的进销存功能"
        )
        
        self.db.query.return_value.filter.return_value.count.return_value = 0
        
        basic, standard, premium = self.service.generate_three_tier_quotations(
            request, self.user_id
        )
        
        # 验证三个报价单都生成了
        self.assertIsInstance(basic, PresaleAIQuotation)
        self.assertIsInstance(standard, PresaleAIQuotation)
        self.assertIsInstance(premium, PresaleAIQuotation)
        
        # 验证类型
        self.assertEqual(basic.quotation_type, QuotationType.BASIC)
        self.assertEqual(standard.quotation_type, QuotationType.STANDARD)
        self.assertEqual(premium.quotation_type, QuotationType.PREMIUM)
        
        # 验证价格递增
        self.assertLess(basic.total, standard.total)
        self.assertLess(standard.total, premium.total)
        
        # 验证折扣不同
        self.assertEqual(basic.discount, Decimal("0"))
        self.assertGreater(standard.discount, Decimal("0"))
        self.assertGreater(premium.discount, standard.discount)
        
        # 验证数据库调用次数（3个报价单 + 3个版本快照 = 6次commit）
        self.assertEqual(self.db.commit.call_count, 6)

    # ========== update_quotation() 测试 ==========

    def test_update_quotation_items(self):
        """测试更新报价项"""
        # 准备现有报价单
        existing_quotation = PresaleAIQuotation(
            id=1,
            presale_ticket_id=101,
            customer_id=201,
            quotation_number="QT-20260221-0001",
            quotation_type=QuotationType.BASIC,
            items=[],
            subtotal=Decimal("5000"),
            tax=Decimal("650"),
            discount=Decimal("0"),
            total=Decimal("5650"),
            payment_terms="测试",
            validity_days=30,
            status=QuotationStatus.DRAFT,
            created_by=1,
            version=1
        )
        
        self.db.query.return_value.filter.return_value.first.return_value = existing_quotation
        
        # 准备更新数据
        new_items = [
            QuotationItem(
                name="更新产品",
                description="更新描述",
                quantity=Decimal("1"),
                unit="套",
                unit_price=Decimal("8000"),
                total_price=Decimal("8000"),
                category="软件"
            )
        ]
        
        update_request = QuotationUpdateRequest(
            items=new_items,
            tax_rate=Decimal("0.13")
        )
        
        # 执行更新
        updated = self.service.update_quotation(1, update_request, self.user_id)
        
        # 验证
        self.assertEqual(updated.subtotal, Decimal("8000"))
        self.assertEqual(updated.tax, Decimal("1040"))  # 8000 * 0.13
        self.assertEqual(updated.total, Decimal("9040"))
        self.assertEqual(updated.version, 2)  # 版本号增加
        self.db.commit.assert_called()

    def test_update_quotation_status(self):
        """测试更新报价单状态"""
        existing_quotation = PresaleAIQuotation(
            id=1,
            presale_ticket_id=101,
            customer_id=201,
            quotation_number="QT-20260221-0001",
            quotation_type=QuotationType.BASIC,
            items=[],
            subtotal=Decimal("5000"),
            tax=Decimal("650"),
            discount=Decimal("0"),
            total=Decimal("5650"),
            payment_terms="测试",
            validity_days=30,
            status=QuotationStatus.DRAFT,
            created_by=1,
            version=1
        )
        
        self.db.query.return_value.filter.return_value.first.return_value = existing_quotation
        
        update_request = QuotationUpdateRequest(
            status=QuotationStatus.PENDING_APPROVAL
        )
        
        updated = self.service.update_quotation(1, update_request, self.user_id)
        
        self.assertEqual(updated.status, QuotationStatus.PENDING_APPROVAL)

    def test_update_quotation_not_found(self):
        """测试更新不存在的报价单"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        update_request = QuotationUpdateRequest(
            validity_days=60
        )
        
        with self.assertRaises(ValueError) as context:
            self.service.update_quotation(999, update_request, self.user_id)
        
        self.assertIn("not found", str(context.exception))

    def test_update_quotation_discount_rate(self):
        """测试更新折扣率"""
        existing_quotation = PresaleAIQuotation(
            id=1,
            presale_ticket_id=101,
            customer_id=201,
            quotation_number="QT-20260221-0001",
            quotation_type=QuotationType.BASIC,
            items=[],
            subtotal=Decimal("10000"),
            tax=Decimal("1300"),
            discount=Decimal("0"),
            total=Decimal("11300"),
            payment_terms="测试",
            validity_days=30,
            status=QuotationStatus.DRAFT,
            created_by=1,
            version=1
        )
        
        self.db.query.return_value.filter.return_value.first.return_value = existing_quotation
        
        update_request = QuotationUpdateRequest(
            discount_rate=Decimal("0.15")  # 15%折扣
        )
        
        updated = self.service.update_quotation(1, update_request, self.user_id)
        
        self.assertEqual(updated.discount, Decimal("1500"))  # 10000 * 0.15
        self.assertEqual(updated.total, Decimal("9800"))  # 10000 + 1300 - 1500

    # ========== get_quotation() 测试 ==========

    def test_get_quotation_exists(self):
        """测试获取存在的报价单"""
        mock_quotation = MagicMock(spec=PresaleAIQuotation)
        mock_quotation.id = 1
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_quotation
        
        result = self.service.get_quotation(1)
        
        self.assertEqual(result, mock_quotation)

    def test_get_quotation_not_exists(self):
        """测试获取不存在的报价单"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.get_quotation(999)
        
        self.assertIsNone(result)

    # ========== get_quotation_history() 测试 ==========

    def test_get_quotation_history(self):
        """测试获取报价单历史"""
        mock_quotations = [
            MagicMock(version=3),
            MagicMock(version=2),
            MagicMock(version=1)
        ]
        
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_quotations
        
        result = self.service.get_quotation_history(101)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result, mock_quotations)

    def test_get_quotation_history_empty(self):
        """测试获取空的报价单历史"""
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        result = self.service.get_quotation_history(101)
        
        self.assertEqual(len(result), 0)

    # ========== get_quotation_versions() 测试 ==========

    def test_get_quotation_versions(self):
        """测试获取报价单版本"""
        mock_versions = [
            MagicMock(version=2),
            MagicMock(version=1)
        ]
        
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_versions
        
        result = self.service.get_quotation_versions(1)
        
        self.assertEqual(len(result), 2)

    # ========== approve_quotation() 测试 ==========

    def test_approve_quotation_approved(self):
        """测试审批通过"""
        mock_quotation = PresaleAIQuotation(
            id=1,
            presale_ticket_id=101,
            customer_id=201,
            quotation_number="QT-20260221-0001",
            quotation_type=QuotationType.BASIC,
            items=[],
            subtotal=Decimal("5000"),
            tax=Decimal("650"),
            discount=Decimal("0"),
            total=Decimal("5650"),
            payment_terms="测试",
            validity_days=30,
            status=QuotationStatus.PENDING_APPROVAL,
            created_by=1,
            version=1
        )
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_quotation
        
        approval = self.service.approve_quotation(
            quotation_id=1,
            approver_id=2,
            status="approved",
            comments="同意"
        )
        
        # 验证审批记录
        self.assertIsInstance(approval, QuotationApproval)
        self.assertEqual(approval.quotation_id, 1)
        self.assertEqual(approval.approver_id, 2)
        self.assertEqual(approval.status, "approved")
        self.assertEqual(approval.comments, "同意")
        
        # 验证报价单状态更新
        self.assertEqual(mock_quotation.status, QuotationStatus.APPROVED)
        
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    def test_approve_quotation_rejected(self):
        """测试审批拒绝"""
        mock_quotation = PresaleAIQuotation(
            id=1,
            presale_ticket_id=101,
            customer_id=201,
            quotation_number="QT-20260221-0001",
            quotation_type=QuotationType.BASIC,
            items=[],
            subtotal=Decimal("5000"),
            tax=Decimal("650"),
            discount=Decimal("0"),
            total=Decimal("5650"),
            payment_terms="测试",
            validity_days=30,
            status=QuotationStatus.PENDING_APPROVAL,
            created_by=1,
            version=1
        )
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_quotation
        
        approval = self.service.approve_quotation(
            quotation_id=1,
            approver_id=2,
            status="rejected",
            comments="价格太高"
        )
        
        self.assertEqual(approval.status, "rejected")
        self.assertEqual(mock_quotation.status, QuotationStatus.REJECTED)

    def test_approve_quotation_not_found(self):
        """测试审批不存在的报价单"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.service.approve_quotation(
                quotation_id=999,
                approver_id=2,
                status="approved"
            )
        
        self.assertIn("not found", str(context.exception))

    # ========== _generate_payment_terms() 私有方法测试 ==========

    def test_generate_payment_terms_basic(self):
        """测试基础版付款条款生成"""
        terms = self.service._generate_payment_terms(
            total=Decimal("10000"),
            quotation_type=QuotationType.BASIC
        )
        
        self.assertIn("¥10,000.00", terms)
        self.assertIn("一次性支付", terms)

    def test_generate_payment_terms_standard(self):
        """测试标准版付款条款生成"""
        terms = self.service._generate_payment_terms(
            total=Decimal("50000"),
            quotation_type=QuotationType.STANDARD
        )
        
        self.assertIn("¥50,000.00", terms)
        self.assertIn("30%", terms)
        self.assertIn("40%", terms)

    def test_generate_payment_terms_premium(self):
        """测试高级版付款条款生成"""
        terms = self.service._generate_payment_terms(
            total=Decimal("100000"),
            quotation_type=QuotationType.PREMIUM
        )
        
        self.assertIn("¥100,000.00", terms)
        self.assertIn("20%", terms)
        self.assertIn("中期款1", terms)
        self.assertIn("中期款2", terms)

    # ========== _generate_basic_items() 私有方法测试 ==========

    def test_generate_basic_items(self):
        """测试生成基础版报价项"""
        items = self.service._generate_basic_items("需要一套基本的ERP系统")
        
        self.assertIsInstance(items, list)
        self.assertGreater(len(items), 0)
        
        for item in items:
            self.assertIsInstance(item, QuotationItem)
            self.assertIsNotNone(item.name)
            self.assertIsNotNone(item.total_price)
            self.assertGreater(item.total_price, 0)

    # ========== _generate_standard_items() 私有方法测试 ==========

    def test_generate_standard_items(self):
        """测试生成标准版报价项"""
        basic_items = self.service._generate_basic_items("测试需求")
        standard_items = self.service._generate_standard_items("测试需求", basic_items)
        
        self.assertIsInstance(standard_items, list)
        self.assertGreater(len(standard_items), len(basic_items))
        
        # 验证标准版价格更高
        basic_total = sum(item.total_price for item in basic_items)
        standard_total = sum(item.total_price for item in standard_items)
        self.assertGreater(standard_total, basic_total)

    # ========== _generate_premium_items() 私有方法测试 ==========

    def test_generate_premium_items(self):
        """测试生成高级版报价项"""
        basic_items = self.service._generate_basic_items("测试需求")
        standard_items = self.service._generate_standard_items("测试需求", basic_items)
        premium_items = self.service._generate_premium_items("测试需求", standard_items)
        
        self.assertIsInstance(premium_items, list)
        self.assertGreater(len(premium_items), len(standard_items))
        
        # 验证高级版价格更高
        standard_total = sum(item.total_price for item in standard_items)
        premium_total = sum(item.total_price for item in premium_items)
        self.assertGreater(premium_total, standard_total)

    # ========== _create_version_snapshot() 私有方法测试 ==========

    def test_create_version_snapshot(self):
        """测试创建版本快照"""
        quotation = PresaleAIQuotation(
            id=1,
            presale_ticket_id=101,
            customer_id=201,
            quotation_number="QT-20260221-0001",
            quotation_type=QuotationType.BASIC,
            items=[{"name": "产品A", "total_price": 1000}],
            subtotal=Decimal("1000"),
            tax=Decimal("130"),
            discount=Decimal("0"),
            total=Decimal("1130"),
            payment_terms="测试",
            validity_days=30,
            status=QuotationStatus.DRAFT,
            created_by=1,
            version=1
        )
        
        self.service._create_version_snapshot(quotation, self.user_id, "测试快照")
        
        # 验证调用了db.add和db.commit
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        
        # 验证添加的对象是QuotationVersion
        call_args = self.db.add.call_args[0][0]
        self.assertIsInstance(call_args, QuotationVersion)
        self.assertEqual(call_args.quotation_id, 1)
        self.assertEqual(call_args.version, 1)
        self.assertEqual(call_args.changed_by, self.user_id)
        self.assertEqual(call_args.change_summary, "测试快照")

    # ========== 边界情况测试 ==========

    def test_quotation_with_zero_items(self):
        """测试没有报价项的情况"""
        request = QuotationGenerateRequest(
            presale_ticket_id=101,
            customer_id=201,
            quotation_type=QuotationType.BASIC,
            items=[],  # 空列表
            tax_rate=Decimal("0.13"),
            discount_rate=Decimal("0"),
            validity_days=30
        )
        
        self.db.query.return_value.filter.return_value.count.return_value = 0
        
        quotation = self.service.generate_quotation(request, self.user_id)
        
        self.assertEqual(quotation.subtotal, Decimal("0"))
        self.assertEqual(quotation.total, Decimal("0"))

    def test_quotation_with_large_numbers(self):
        """测试大额报价单"""
        items = [
            QuotationItem(
                name="大型项目",
                description="大型企业级系统",
                quantity=Decimal("1"),
                unit="套",
                unit_price=Decimal("999999999.99"),
                total_price=Decimal("999999999.99"),
                category="软件"
            )
        ]
        
        request = QuotationGenerateRequest(
            presale_ticket_id=101,
            customer_id=201,
            quotation_type=QuotationType.PREMIUM,
            items=items,
            tax_rate=Decimal("0.13"),
            discount_rate=Decimal("0.10"),
            validity_days=30
        )
        
        self.db.query.return_value.filter.return_value.count.return_value = 0
        
        quotation = self.service.generate_quotation(request, self.user_id)
        
        # 验证大数计算正确
        self.assertIsInstance(quotation.total, Decimal)
        self.assertGreater(quotation.total, Decimal("900000000"))

    def test_update_quotation_with_all_fields(self):
        """测试同时更新所有字段"""
        existing_quotation = PresaleAIQuotation(
            id=1,
            presale_ticket_id=101,
            customer_id=201,
            quotation_number="QT-20260221-0001",
            quotation_type=QuotationType.BASIC,
            items=[],
            subtotal=Decimal("5000"),
            tax=Decimal("650"),
            discount=Decimal("0"),
            total=Decimal("5650"),
            payment_terms="旧条款",
            validity_days=30,
            status=QuotationStatus.DRAFT,
            created_by=1,
            version=1
        )
        
        self.db.query.return_value.filter.return_value.first.return_value = existing_quotation
        
        new_items = [
            QuotationItem(
                name="新产品",
                description="新描述",
                quantity=Decimal("1"),
                unit="套",
                unit_price=Decimal("6000"),
                total_price=Decimal("6000"),
                category="软件"
            )
        ]
        
        update_request = QuotationUpdateRequest(
            items=new_items,
            tax_rate=Decimal("0.06"),
            discount_rate=Decimal("0.05"),
            validity_days=60,
            payment_terms="新条款",
            status=QuotationStatus.PENDING_APPROVAL,
            notes="全面更新"
        )
        
        updated = self.service.update_quotation(1, update_request, self.user_id)
        
        # 验证所有字段都更新了
        self.assertEqual(updated.subtotal, Decimal("6000"))
        self.assertEqual(updated.tax, Decimal("360"))  # 6000 * 0.06
        self.assertEqual(updated.discount, Decimal("300"))  # 6000 * 0.05
        self.assertEqual(updated.total, Decimal("6060"))  # 6000 + 360 - 300
        self.assertEqual(updated.validity_days, 60)
        self.assertEqual(updated.payment_terms, "新条款")
        self.assertEqual(updated.status, QuotationStatus.PENDING_APPROVAL)
        self.assertEqual(updated.notes, "全面更新")
        self.assertEqual(updated.version, 2)


if __name__ == "__main__":
    unittest.main()
