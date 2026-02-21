# -*- coding: utf-8 -*-
"""
增强的AI报价单生成服务单元测试

测试覆盖：
- 报价单编号生成（多场景）
- 单个报价单生成（多场景）
- 三档报价方案生成（完整流程）
- 报价单更新（各字段更新）
- 报价单查询（存在/不存在）
- 报价单历史查询
- 版本管理
- 审批流程（通过/拒绝）
- 付款条款生成（三档）
- 价格计算（税费折扣）
- 边界条件和异常处理
"""

import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch, call

from app.services.presale_ai_quotation_service import AIQuotationGeneratorService
from app.models.presale_ai_quotation import QuotationType, QuotationStatus
from app.schemas.presale_ai_quotation import (
    QuotationGenerateRequest, QuotationUpdateRequest,
    QuotationItem, ThreeTierQuotationRequest
)


class TestAIQuotationGeneratorService(unittest.TestCase):
    """AI报价单生成服务测试基类"""
    
    def setUp(self):
        """测试前置设置"""
        self.db = MagicMock()
        self.service = AIQuotationGeneratorService(self.db)
        self.user_id = 1
        
    def tearDown(self):
        """测试后置清理"""
        self.db.reset_mock()


class TestInitialization(TestAIQuotationGeneratorService):
    """测试初始化"""
    
    def test_init_default_model(self):
        """测试默认AI模型"""
        service = AIQuotationGeneratorService(self.db)
        self.assertEqual(service.ai_model, "gpt-4")
        self.assertIs(service.db, self.db)
    
    def test_init_with_db(self):
        """测试数据库会话初始化"""
        self.assertIs(self.service.db, self.db)


class TestQuotationNumberGeneration(TestAIQuotationGeneratorService):
    """测试报价单编号生成"""
    
    @patch('app.services.presale_ai_quotation_service.datetime')
    def test_generate_quotation_number_first_today(self, mock_datetime):
        """测试生成当天第一个报价单编号"""
        mock_datetime.now.return_value = datetime(2026, 2, 21, 10, 0, 0)
        mock_query = self.db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.count.return_value = 0
        
        number = self.service.generate_quotation_number()
        
        self.assertEqual(number, "QT-20260221-0001")
        mock_datetime.now.assert_called_once()
    
    @patch('app.services.presale_ai_quotation_service.datetime')
    def test_generate_quotation_number_multiple_today(self, mock_datetime):
        """测试生成当天第N个报价单编号"""
        mock_datetime.now.return_value = datetime(2026, 2, 21, 15, 30, 0)
        mock_query = self.db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.count.return_value = 42
        
        number = self.service.generate_quotation_number()
        
        self.assertEqual(number, "QT-20260221-0043")
    
    @patch('app.services.presale_ai_quotation_service.datetime')
    def test_generate_quotation_number_format_padding(self, mock_datetime):
        """测试编号格式填充（9999+）"""
        mock_datetime.now.return_value = datetime(2026, 12, 31, 23, 59, 59)
        mock_query = self.db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.count.return_value = 9999
        
        number = self.service.generate_quotation_number()
        
        self.assertEqual(number, "QT-20261231-10000")


class TestGenerateQuotation(TestAIQuotationGeneratorService):
    """测试生成报价单"""
    
    def _create_quotation_request(self, quotation_type=QuotationType.STANDARD):
        """创建报价单请求辅助方法"""
        items = [
            QuotationItem(
                name="ERP系统",
                description="企业资源管理系统",
                quantity=Decimal("1"),
                unit="套",
                unit_price=Decimal("100000"),
                total_price=Decimal("100000"),
                category="软件开发"
            ),
            QuotationItem(
                name="培训服务",
                description="用户培训",
                quantity=Decimal("2"),
                unit="天",
                unit_price=Decimal("5000"),
                total_price=Decimal("10000"),
                category="服务"
            )
        ]
        
        return QuotationGenerateRequest(
            presale_ticket_id=1,
            customer_id=100,
            quotation_type=quotation_type,
            items=items,
            tax_rate=Decimal("0.13"),
            discount_rate=Decimal("0.05"),
            validity_days=30,
            notes="测试报价单"
        )
    
    @patch('app.services.presale_ai_quotation_service.save_obj')
    @patch('app.services.presale_ai_quotation_service.time')
    def test_generate_quotation_with_all_fields(self, mock_time, mock_save):
        """测试完整字段生成报价单"""
        mock_time.time.side_effect = [1000.0, 1002.5]
        self.service.generate_quotation_number = Mock(return_value="QT-20260221-0001")
        self.service._create_version_snapshot = Mock()
        
        request = self._create_quotation_request()
        request.payment_terms = "自定义付款条款"
        
        quotation = self.service.generate_quotation(request, self.user_id)
        
        # 验证计算
        self.assertEqual(quotation.subtotal, Decimal("110000"))
        self.assertEqual(quotation.tax, Decimal("14300"))  # 110000 * 0.13
        self.assertEqual(quotation.discount, Decimal("5500"))  # 110000 * 0.05
        self.assertEqual(quotation.total, Decimal("118800"))  # 110000 + 14300 - 5500
        
        # 验证基础字段
        self.assertEqual(quotation.quotation_number, "QT-20260221-0001")
        self.assertEqual(quotation.quotation_type, QuotationType.STANDARD)
        self.assertEqual(quotation.status, QuotationStatus.DRAFT)
        self.assertEqual(quotation.created_by, self.user_id)
        self.assertEqual(quotation.payment_terms, "自定义付款条款")
        self.assertEqual(quotation.validity_days, 30)
        self.assertEqual(quotation.notes, "测试报价单")
        
        # 验证时间
        self.assertEqual(quotation.generation_time, Decimal("2.5"))
        
        # 验证保存和版本快照
        mock_save.assert_called_once()
        self.service._create_version_snapshot.assert_called_once()
    
    @patch('app.services.presale_ai_quotation_service.save_obj')
    @patch('app.services.presale_ai_quotation_service.time')
    def test_generate_quotation_auto_payment_terms(self, mock_time, mock_save):
        """测试自动生成付款条款"""
        mock_time.time.side_effect = [1000.0, 1001.0]
        self.service.generate_quotation_number = Mock(return_value="QT-20260221-0002")
        self.service._create_version_snapshot = Mock()
        self.service._generate_payment_terms = Mock(return_value="AI生成的付款条款")
        
        request = self._create_quotation_request()
        request.payment_terms = None  # 不提供付款条款
        
        quotation = self.service.generate_quotation(request, self.user_id)
        
        self.assertEqual(quotation.payment_terms, "AI生成的付款条款")
        self.service._generate_payment_terms.assert_called_once_with(
            total=Decimal("118800"),
            quotation_type=QuotationType.STANDARD
        )
    
    @patch('app.services.presale_ai_quotation_service.save_obj')
    @patch('app.services.presale_ai_quotation_service.time')
    def test_generate_quotation_basic_type(self, mock_time, mock_save):
        """测试生成基础版报价单"""
        mock_time.time.side_effect = [1000.0, 1000.5]
        self.service.generate_quotation_number = Mock(return_value="QT-20260221-0003")
        self.service._create_version_snapshot = Mock()
        
        request = self._create_quotation_request(quotation_type=QuotationType.BASIC)
        quotation = self.service.generate_quotation(request, self.user_id)
        
        self.assertEqual(quotation.quotation_type, QuotationType.BASIC)
    
    @patch('app.services.presale_ai_quotation_service.save_obj')
    @patch('app.services.presale_ai_quotation_service.time')
    def test_generate_quotation_premium_type(self, mock_time, mock_save):
        """测试生成高级版报价单"""
        mock_time.time.side_effect = [1000.0, 1001.5]
        self.service.generate_quotation_number = Mock(return_value="QT-20260221-0004")
        self.service._create_version_snapshot = Mock()
        
        request = self._create_quotation_request(quotation_type=QuotationType.PREMIUM)
        quotation = self.service.generate_quotation(request, self.user_id)
        
        self.assertEqual(quotation.quotation_type, QuotationType.PREMIUM)
    
    @patch('app.services.presale_ai_quotation_service.save_obj')
    @patch('app.services.presale_ai_quotation_service.time')
    def test_generate_quotation_no_tax(self, mock_time, mock_save):
        """测试无税率报价单"""
        mock_time.time.side_effect = [1000.0, 1001.0]
        self.service.generate_quotation_number = Mock(return_value="QT-20260221-0005")
        self.service._create_version_snapshot = Mock()
        
        request = self._create_quotation_request()
        request.tax_rate = Decimal("0")
        
        quotation = self.service.generate_quotation(request, self.user_id)
        
        self.assertEqual(quotation.tax, Decimal("0"))
        self.assertEqual(quotation.total, Decimal("104500"))  # 110000 - 5500
    
    @patch('app.services.presale_ai_quotation_service.save_obj')
    @patch('app.services.presale_ai_quotation_service.time')
    def test_generate_quotation_no_discount(self, mock_time, mock_save):
        """测试无折扣报价单"""
        mock_time.time.side_effect = [1000.0, 1001.0]
        self.service.generate_quotation_number = Mock(return_value="QT-20260221-0006")
        self.service._create_version_snapshot = Mock()
        
        request = self._create_quotation_request()
        request.discount_rate = Decimal("0")
        
        quotation = self.service.generate_quotation(request, self.user_id)
        
        self.assertEqual(quotation.discount, Decimal("0"))
        self.assertEqual(quotation.total, Decimal("124300"))  # 110000 + 14300


class TestGenerateThreeTierQuotations(TestAIQuotationGeneratorService):
    """测试生成三档报价方案"""
    
    @patch.object(AIQuotationGeneratorService, 'generate_quotation')
    def test_generate_three_tier_quotations_complete(self, mock_generate):
        """测试完整三档报价生成"""
        # Mock返回值
        mock_basic = Mock(quotation_type=QuotationType.BASIC, total=Decimal("85000"))
        mock_standard = Mock(quotation_type=QuotationType.STANDARD, total=Decimal("180500"))
        mock_premium = Mock(quotation_type=QuotationType.PREMIUM, total=Decimal("315000"))
        mock_generate.side_effect = [mock_basic, mock_standard, mock_premium]
        
        # Mock内部方法
        self.service._generate_basic_items = Mock(return_value=[
            QuotationItem(
                name="基础ERP", description="基础功能", quantity=Decimal("1"),
                unit="套", unit_price=Decimal("80000"), total_price=Decimal("80000"),
                category="软件开发"
            )
        ])
        self.service._generate_standard_items = Mock(return_value=[
            QuotationItem(
                name="标准ERP", description="标准功能", quantity=Decimal("1"),
                unit="套", unit_price=Decimal("150000"), total_price=Decimal("150000"),
                category="软件开发"
            )
        ])
        self.service._generate_premium_items = Mock(return_value=[
            QuotationItem(
                name="高级ERP", description="高级功能", quantity=Decimal("1"),
                unit="套", unit_price=Decimal("250000"), total_price=Decimal("250000"),
                category="软件开发"
            )
        ])
        
        request = ThreeTierQuotationRequest(
            presale_ticket_id=1,
            customer_id=100,
            base_requirements="企业ERP系统需求"
        )
        
        basic, standard, premium = self.service.generate_three_tier_quotations(request, self.user_id)
        
        # 验证返回结果
        self.assertEqual(basic.quotation_type, QuotationType.BASIC)
        self.assertEqual(standard.quotation_type, QuotationType.STANDARD)
        self.assertEqual(premium.quotation_type, QuotationType.PREMIUM)
        
        # 验证调用次数
        self.assertEqual(mock_generate.call_count, 3)
        self.service._generate_basic_items.assert_called_once_with("企业ERP系统需求")
        self.service._generate_standard_items.assert_called_once()
        self.service._generate_premium_items.assert_called_once()
    
    def test_generate_basic_items(self):
        """测试生成基础版报价项"""
        items = self.service._generate_basic_items("ERP需求")
        
        self.assertIsInstance(items, list)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].name, "基础ERP系统")
        self.assertEqual(items[1].name, "系统部署与培训")
    
    def test_generate_standard_items(self):
        """测试生成标准版报价项"""
        basic_items = self.service._generate_basic_items("ERP需求")
        items = self.service._generate_standard_items("ERP需求", basic_items)
        
        self.assertIsInstance(items, list)
        self.assertGreater(len(items), len(basic_items))
        self.assertIn("标准ERP系统", items[0].name)
    
    def test_generate_premium_items(self):
        """测试生成高级版报价项"""
        basic_items = self.service._generate_basic_items("ERP需求")
        standard_items = self.service._generate_standard_items("ERP需求", basic_items)
        items = self.service._generate_premium_items("ERP需求", standard_items)
        
        self.assertIsInstance(items, list)
        self.assertGreater(len(items), len(standard_items))
        self.assertIn("高级ERP系统", items[0].name)


class TestUpdateQuotation(TestAIQuotationGeneratorService):
    """测试更新报价单"""
    
    def _create_mock_quotation(self):
        """创建模拟报价单"""
        mock_quotation = Mock()
        mock_quotation.id = 1
        mock_quotation.version = 1
        mock_quotation.subtotal = Decimal("100000")
        mock_quotation.tax = Decimal("13000")
        mock_quotation.discount = Decimal("5000")
        mock_quotation.total = Decimal("108000")
        mock_quotation.items = [
            {
                "name": "ERP系统",
                "quantity": "1",
                "unit_price": "100000",
                "total_price": "100000"
            }
        ]
        return mock_quotation
    
    def test_update_quotation_items(self):
        """测试更新报价项"""
        mock_quotation = self._create_mock_quotation()
        mock_query = self.db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_quotation
        
        self.service._create_version_snapshot = Mock()
        
        new_items = [
            QuotationItem(
                name="新ERP系统", description="升级版", quantity=Decimal("1"),
                unit="套", unit_price=Decimal("120000"), total_price=Decimal("120000"),
                category="软件开发"
            )
        ]
        
        request = QuotationUpdateRequest(items=new_items)
        quotation = self.service.update_quotation(1, request, self.user_id)
        
        self.assertEqual(quotation.subtotal, Decimal("120000"))
        self.assertEqual(quotation.version, 2)
        self.db.commit.assert_called_once()
    
    def test_update_quotation_tax_rate(self):
        """测试更新税率"""
        mock_quotation = self._create_mock_quotation()
        mock_query = self.db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_quotation
        
        self.service._create_version_snapshot = Mock()
        
        request = QuotationUpdateRequest(tax_rate=Decimal("0.06"))
        quotation = self.service.update_quotation(1, request, self.user_id)
        
        self.assertEqual(quotation.tax, Decimal("6000"))  # 100000 * 0.06
    
    def test_update_quotation_discount_rate(self):
        """测试更新折扣率"""
        mock_quotation = self._create_mock_quotation()
        mock_query = self.db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_quotation
        
        self.service._create_version_snapshot = Mock()
        
        request = QuotationUpdateRequest(discount_rate=Decimal("0.10"))
        quotation = self.service.update_quotation(1, request, self.user_id)
        
        self.assertEqual(quotation.discount, Decimal("10000"))  # 100000 * 0.10
    
    def test_update_quotation_validity_days(self):
        """测试更新有效期"""
        mock_quotation = self._create_mock_quotation()
        mock_query = self.db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_quotation
        
        self.service._create_version_snapshot = Mock()
        
        request = QuotationUpdateRequest(validity_days=60)
        quotation = self.service.update_quotation(1, request, self.user_id)
        
        self.assertEqual(quotation.validity_days, 60)
    
    def test_update_quotation_payment_terms(self):
        """测试更新付款条款"""
        mock_quotation = self._create_mock_quotation()
        mock_query = self.db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_quotation
        
        self.service._create_version_snapshot = Mock()
        
        request = QuotationUpdateRequest(payment_terms="新的付款条款")
        quotation = self.service.update_quotation(1, request, self.user_id)
        
        self.assertEqual(quotation.payment_terms, "新的付款条款")
    
    def test_update_quotation_status(self):
        """测试更新状态"""
        mock_quotation = self._create_mock_quotation()
        mock_query = self.db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_quotation
        
        self.service._create_version_snapshot = Mock()
        
        request = QuotationUpdateRequest(status=QuotationStatus.PENDING_APPROVAL)
        quotation = self.service.update_quotation(1, request, self.user_id)
        
        self.assertEqual(quotation.status, QuotationStatus.PENDING_APPROVAL)
    
    def test_update_quotation_not_found(self):
        """测试更新不存在的报价单"""
        mock_query = self.db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None
        
        request = QuotationUpdateRequest(notes="测试")
        
        with self.assertRaises(ValueError) as context:
            self.service.update_quotation(999, request, self.user_id)
        
        self.assertIn("not found", str(context.exception))
    
    def test_update_quotation_multiple_fields(self):
        """测试同时更新多个字段"""
        mock_quotation = self._create_mock_quotation()
        mock_query = self.db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_quotation
        
        self.service._create_version_snapshot = Mock()
        
        new_items = [
            QuotationItem(
                name="更新ERP", description="新版", quantity=Decimal("1"),
                unit="套", unit_price=Decimal("150000"), total_price=Decimal("150000"),
                category="软件开发"
            )
        ]
        
        request = QuotationUpdateRequest(
            items=new_items,
            tax_rate=Decimal("0.06"),
            discount_rate=Decimal("0.15"),
            validity_days=45,
            notes="批量更新"
        )
        
        quotation = self.service.update_quotation(1, request, self.user_id)
        
        self.assertEqual(quotation.subtotal, Decimal("150000"))
        self.assertEqual(quotation.tax, Decimal("9000"))  # 150000 * 0.06
        self.assertEqual(quotation.discount, Decimal("22500"))  # 150000 * 0.15
        self.assertEqual(quotation.validity_days, 45)
        self.assertEqual(quotation.notes, "批量更新")


class TestGetQuotation(TestAIQuotationGeneratorService):
    """测试获取报价单"""
    
    def test_get_quotation_exists(self):
        """测试获取存在的报价单"""
        mock_quotation = Mock()
        mock_query = self.db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_quotation
        
        quotation = self.service.get_quotation(1)
        
        self.assertIs(quotation, mock_quotation)
    
    def test_get_quotation_not_exists(self):
        """测试获取不存在的报价单"""
        mock_query = self.db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None
        
        quotation = self.service.get_quotation(999)
        
        self.assertIsNone(quotation)


class TestGetQuotationHistory(TestAIQuotationGeneratorService):
    """测试获取报价单历史"""
    
    def test_get_quotation_history_multiple(self):
        """测试获取多个历史记录"""
        mock_quotations = [Mock(), Mock(), Mock()]
        mock_query = self.db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_order.all.return_value = mock_quotations
        
        history = self.service.get_quotation_history(1)
        
        self.assertEqual(len(history), 3)
        self.assertEqual(history, mock_quotations)
    
    def test_get_quotation_history_empty(self):
        """测试获取空历史记录"""
        mock_query = self.db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_order.all.return_value = []
        
        history = self.service.get_quotation_history(999)
        
        self.assertEqual(len(history), 0)


class TestGetQuotationVersions(TestAIQuotationGeneratorService):
    """测试获取报价单版本"""
    
    def test_get_quotation_versions_multiple(self):
        """测试获取多个版本"""
        mock_versions = [Mock(version=3), Mock(version=2), Mock(version=1)]
        mock_query = self.db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_order.all.return_value = mock_versions
        
        versions = self.service.get_quotation_versions(1)
        
        self.assertEqual(len(versions), 3)
        self.assertEqual(versions, mock_versions)
    
    def test_get_quotation_versions_empty(self):
        """测试获取空版本列表"""
        mock_query = self.db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_order.all.return_value = []
        
        versions = self.service.get_quotation_versions(999)
        
        self.assertEqual(len(versions), 0)


class TestApproveQuotation(TestAIQuotationGeneratorService):
    """测试审批报价单"""
    
    @patch('app.services.presale_ai_quotation_service.datetime')
    def test_approve_quotation_approved(self, mock_datetime):
        """测试通过审批"""
        mock_datetime.now.return_value = datetime(2026, 2, 21, 10, 0, 0)
        
        mock_quotation = Mock()
        self.service.get_quotation = Mock(return_value=mock_quotation)
        
        approval = self.service.approve_quotation(
            quotation_id=1,
            approver_id=2,
            status="approved",
            comments="批准通过"
        )
        
        self.assertEqual(approval.quotation_id, 1)
        self.assertEqual(approval.approver_id, 2)
        self.assertEqual(approval.status, "approved")
        self.assertEqual(approval.comments, "批准通过")
        self.assertEqual(mock_quotation.status, QuotationStatus.APPROVED)
        self.db.add.assert_called_once_with(approval)
        self.db.commit.assert_called_once()
    
    @patch('app.services.presale_ai_quotation_service.datetime')
    def test_approve_quotation_rejected(self, mock_datetime):
        """测试拒绝审批"""
        mock_datetime.now.return_value = datetime(2026, 2, 21, 10, 0, 0)
        
        mock_quotation = Mock()
        self.service.get_quotation = Mock(return_value=mock_quotation)
        
        approval = self.service.approve_quotation(
            quotation_id=1,
            approver_id=2,
            status="rejected",
            comments="需要修改"
        )
        
        self.assertEqual(approval.status, "rejected")
        self.assertEqual(mock_quotation.status, QuotationStatus.REJECTED)
    
    def test_approve_quotation_not_found(self):
        """测试审批不存在的报价单"""
        self.service.get_quotation = Mock(return_value=None)
        
        with self.assertRaises(ValueError) as context:
            self.service.approve_quotation(999, 2, "approved")
        
        self.assertIn("not found", str(context.exception))
    
    @patch('app.services.presale_ai_quotation_service.datetime')
    def test_approve_quotation_no_comments(self, mock_datetime):
        """测试无审批意见"""
        mock_datetime.now.return_value = datetime(2026, 2, 21, 10, 0, 0)
        
        mock_quotation = Mock()
        self.service.get_quotation = Mock(return_value=mock_quotation)
        
        approval = self.service.approve_quotation(
            quotation_id=1,
            approver_id=2,
            status="approved"
        )
        
        self.assertIsNone(approval.comments)


class TestGeneratePaymentTerms(TestAIQuotationGeneratorService):
    """测试生成付款条款"""
    
    def test_generate_payment_terms_basic(self):
        """测试生成基础版付款条款"""
        total = Decimal("100000")
        terms = self.service._generate_payment_terms(total, QuotationType.BASIC)
        
        self.assertIn("¥100,000.00", terms)
        self.assertIn("一次性支付全款", terms)
    
    def test_generate_payment_terms_standard(self):
        """测试生成标准版付款条款"""
        total = Decimal("200000")
        terms = self.service._generate_payment_terms(total, QuotationType.STANDARD)
        
        self.assertIn("¥200,000.00", terms)
        self.assertIn("30%", terms)
        self.assertIn("40%", terms)
        self.assertIn("中期款", terms)
    
    def test_generate_payment_terms_premium(self):
        """测试生成高级版付款条款"""
        total = Decimal("500000")
        terms = self.service._generate_payment_terms(total, QuotationType.PREMIUM)
        
        self.assertIn("¥500,000.00", terms)
        self.assertIn("20%", terms)
        self.assertIn("中期款1", terms)
        self.assertIn("中期款2", terms)
    
    def test_generate_payment_terms_large_amount(self):
        """测试大金额格式化"""
        total = Decimal("1234567.89")
        terms = self.service._generate_payment_terms(total, QuotationType.PREMIUM)
        
        self.assertIn("¥1,234,567.89", terms)


class TestCreateVersionSnapshot(TestAIQuotationGeneratorService):
    """测试创建版本快照"""
    
    def test_create_version_snapshot(self):
        """测试创建版本快照"""
        mock_quotation = Mock()
        mock_quotation.id = 1
        mock_quotation.quotation_number = "QT-20260221-0001"
        mock_quotation.quotation_type = QuotationType.STANDARD
        mock_quotation.items = [{"name": "ERP"}]
        mock_quotation.subtotal = Decimal("100000")
        mock_quotation.tax = Decimal("13000")
        mock_quotation.discount = Decimal("5000")
        mock_quotation.total = Decimal("108000")
        mock_quotation.payment_terms = "付款条款"
        mock_quotation.validity_days = 30
        mock_quotation.status = QuotationStatus.DRAFT
        mock_quotation.version = 1
        
        self.service._create_version_snapshot(mock_quotation, self.user_id, "初始创建")
        
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        
        # 验证传入的版本对象
        call_args = self.db.add.call_args[0][0]
        self.assertEqual(call_args.quotation_id, 1)
        self.assertEqual(call_args.version, 1)
        self.assertEqual(call_args.changed_by, self.user_id)
        self.assertEqual(call_args.change_summary, "初始创建")
        self.assertIsInstance(call_args.snapshot_data, dict)


if __name__ == '__main__':
    unittest.main()
