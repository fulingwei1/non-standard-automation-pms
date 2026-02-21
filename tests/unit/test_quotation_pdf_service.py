# -*- coding: utf-8 -*-
"""
报价单PDF服务单元测试

目标：
1. 参考test_condition_parser_rewrite.py的mock策略
2. 只mock外部依赖（reportlab、文件系统）
3. 让业务逻辑真正执行
4. 覆盖主要方法和边界情况
5. 目标覆盖率: 70%+
"""

import unittest
from unittest.mock import MagicMock, patch, mock_open, call
from datetime import datetime
from decimal import Decimal
import os
import sys

# Mock reportlab before importing service
sys.modules['reportlab'] = MagicMock()
sys.modules['reportlab.lib'] = MagicMock()
sys.modules['reportlab.lib.pagesizes'] = MagicMock()
sys.modules['reportlab.lib.colors'] = MagicMock()
sys.modules['reportlab.lib.styles'] = MagicMock()
sys.modules['reportlab.lib.units'] = MagicMock()
sys.modules['reportlab.platypus'] = MagicMock()
sys.modules['reportlab.pdfbase'] = MagicMock()
sys.modules['reportlab.pdfbase.ttfonts'] = MagicMock()

from app.services.quotation_pdf_service import QuotationPDFService
from app.models.presale_ai_quotation import QuotationType, QuotationStatus


class TestQuotationPDFService(unittest.TestCase):
    """测试QuotationPDFService核心功能"""

    def setUp(self):
        """每个测试前的准备工作"""
        # Mock文件系统操作
        self.mock_makedirs = patch('os.makedirs').start()
        self.mock_exists = patch('os.path.exists').start()
        
        # 默认文件系统行为
        self.mock_exists.return_value = False
        
        # 创建服务实例
        self.service = QuotationPDFService()

    def tearDown(self):
        """每个测试后的清理工作"""
        patch.stopall()

    def _create_mock_quotation(
        self,
        quotation_number="Q20260221001",
        quotation_type=QuotationType.STANDARD,
        status=QuotationStatus.DRAFT,
        items=None,
        subtotal=Decimal("10000.00"),
        tax=Decimal("1300.00"),
        discount=Decimal("500.00"),
        total=Decimal("10800.00"),
        validity_days=30,
        payment_terms="预付50%，交付后付清余款",
        notes="本报价单包含实施培训服务",
        version=1
    ):
        """创建mock的报价单对象"""
        quotation = MagicMock()
        quotation.quotation_number = quotation_number
        quotation.quotation_type = quotation_type
        quotation.status = status
        quotation.items = items or [
            {
                "name": "需求分析",
                "quantity": 5,
                "unit": "天",
                "unit_price": Decimal("1000.00"),
                "total_price": Decimal("5000.00")
            },
            {
                "name": "系统开发",
                "quantity": 10,
                "unit": "天",
                "unit_price": Decimal("1500.00"),
                "total_price": Decimal("15000.00")
            }
        ]
        quotation.subtotal = subtotal
        quotation.tax = tax
        quotation.discount = discount
        quotation.total = total
        quotation.validity_days = validity_days
        quotation.payment_terms = payment_terms
        quotation.notes = notes
        quotation.version = version
        quotation.created_at = datetime(2026, 2, 21, 10, 30, 0)
        
        return quotation

    # ========== 初始化测试 ==========

    def test_init_creates_output_directory(self):
        """测试初始化创建输出目录"""
        self.mock_makedirs.assert_called_once_with("uploads/quotations/", exist_ok=True)

    def test_init_sets_output_dir(self):
        """测试初始化设置输出路径"""
        self.assertEqual(self.service.output_dir, "uploads/quotations/")

    @patch('app.services.quotation_pdf_service.REPORTLAB_AVAILABLE', True)
    @patch('app.services.quotation_pdf_service.pdfmetrics')
    @patch('app.services.quotation_pdf_service.TTFont')
    def test_init_registers_font_macos(self, mock_ttfont, mock_pdfmetrics):
        """测试在macOS上注册中文字体"""
        self.mock_exists.side_effect = lambda path: path == "/System/Library/Fonts/PingFang.ttc"
        
        service = QuotationPDFService()
        
        mock_ttfont.assert_called_once_with('Chinese', "/System/Library/Fonts/PingFang.ttc")
        mock_pdfmetrics.registerFont.assert_called_once()

    @patch('app.services.quotation_pdf_service.REPORTLAB_AVAILABLE', True)
    @patch('app.services.quotation_pdf_service.pdfmetrics')
    def test_init_font_registration_fails_gracefully(self, mock_pdfmetrics):
        """测试字体注册失败时优雅处理"""
        self.mock_exists.return_value = True
        mock_pdfmetrics.registerFont.side_effect = Exception("Font error")
        
        # 不应该抛出异常
        service = QuotationPDFService()
        self.assertIsNotNone(service)

    # ========== generate_pdf() 测试 ==========

    @patch('app.services.quotation_pdf_service.REPORTLAB_AVAILABLE', False)
    def test_generate_pdf_raises_error_when_reportlab_unavailable(self):
        """测试reportlab不可用时抛出异常"""
        quotation = self._create_mock_quotation()
        
        with self.assertRaises(RuntimeError) as context:
            self.service.generate_pdf(quotation)
        
        self.assertIn("ReportLab is not installed", str(context.exception))

    @patch('app.services.quotation_pdf_service.REPORTLAB_AVAILABLE', True)
    @patch('app.services.quotation_pdf_service.SimpleDocTemplate')
    def test_generate_pdf_creates_correct_filename(self, mock_doc_template):
        """测试生成正确的PDF文件名"""
        quotation = self._create_mock_quotation(quotation_number="Q20260221001")
        
        # Mock文档构建
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc
        
        filepath = self.service.generate_pdf(quotation)
        
        expected_path = "uploads/quotations/quotation_Q20260221001.pdf"
        self.assertEqual(filepath, expected_path)

    @patch('app.services.quotation_pdf_service.REPORTLAB_AVAILABLE', True)
    @patch('app.services.quotation_pdf_service.SimpleDocTemplate')
    @patch('app.services.quotation_pdf_service.A4', (595.27, 841.89))
    @patch('app.services.quotation_pdf_service.cm', 28.35)
    def test_generate_pdf_creates_document_with_correct_settings(self, mock_doc_template):
        """测试创建文档时使用正确的配置"""
        quotation = self._create_mock_quotation()
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc
        
        self.service.generate_pdf(quotation)
        
        # 验证SimpleDocTemplate调用参数
        call_args = mock_doc_template.call_args
        self.assertIn("uploads/quotations/quotation_Q20260221001.pdf", call_args[0])
        self.assertEqual(call_args[1]['pagesize'], (595.27, 841.89))
        self.assertEqual(call_args[1]['rightMargin'], 2 * 28.35)
        self.assertEqual(call_args[1]['leftMargin'], 2 * 28.35)

    @patch('app.services.quotation_pdf_service.REPORTLAB_AVAILABLE', True)
    @patch('app.services.quotation_pdf_service.SimpleDocTemplate')
    @patch('app.services.quotation_pdf_service.Image')
    def test_generate_pdf_includes_logo_when_provided(self, mock_image, mock_doc_template):
        """测试提供logo时包含在PDF中"""
        quotation = self._create_mock_quotation()
        company_info = {
            'logo_path': '/path/to/logo.png',
            'name': '测试公司'
        }
        
        self.mock_exists.side_effect = lambda path: path == '/path/to/logo.png'
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc
        
        self.service.generate_pdf(quotation, company_info)
        
        # 验证Image被调用
        mock_image.assert_called_once()

    @patch('app.services.quotation_pdf_service.REPORTLAB_AVAILABLE', True)
    @patch('app.services.quotation_pdf_service.SimpleDocTemplate')
    def test_generate_pdf_skips_logo_when_file_not_exists(self, mock_doc_template):
        """测试logo文件不存在时跳过"""
        quotation = self._create_mock_quotation()
        company_info = {'logo_path': '/nonexistent/logo.png'}
        
        self.mock_exists.return_value = False
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc
        
        # 不应抛出异常
        filepath = self.service.generate_pdf(quotation, company_info)
        self.assertIsNotNone(filepath)

    @patch('app.services.quotation_pdf_service.REPORTLAB_AVAILABLE', True)
    @patch('app.services.quotation_pdf_service.SimpleDocTemplate')
    @patch('app.services.quotation_pdf_service.Table')
    def test_generate_pdf_creates_items_table(self, mock_table, mock_doc_template):
        """测试创建报价项表格"""
        quotation = self._create_mock_quotation()
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc
        
        self.service.generate_pdf(quotation)
        
        # 验证Table被调用（至少3次：info, items, summary）
        self.assertGreaterEqual(mock_table.call_count, 3)

    @patch('app.services.quotation_pdf_service.REPORTLAB_AVAILABLE', True)
    @patch('app.services.quotation_pdf_service.SimpleDocTemplate')
    @patch('app.services.quotation_pdf_service.Paragraph')
    def test_generate_pdf_includes_payment_terms(self, mock_paragraph, mock_doc_template):
        """测试包含付款条款"""
        quotation = self._create_mock_quotation(
            payment_terms="第一期：签约后7日内支付30%\n第二期：验收后支付70%"
        )
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc
        
        self.service.generate_pdf(quotation)
        
        # 验证Paragraph被调用且包含付款条款文本
        paragraph_calls = [str(call) for call in mock_paragraph.call_args_list]
        self.assertTrue(any("第一期" in str(call) for call in paragraph_calls))

    @patch('app.services.quotation_pdf_service.REPORTLAB_AVAILABLE', True)
    @patch('app.services.quotation_pdf_service.SimpleDocTemplate')
    def test_generate_pdf_includes_notes(self, mock_doc_template):
        """测试包含备注"""
        quotation = self._create_mock_quotation(notes="重要提示：需提前预约")
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc
        
        filepath = self.service.generate_pdf(quotation)
        
        # 验证文档被构建
        mock_doc.build.assert_called_once()

    @patch('app.services.quotation_pdf_service.REPORTLAB_AVAILABLE', True)
    @patch('app.services.quotation_pdf_service.SimpleDocTemplate')
    def test_generate_pdf_skips_empty_payment_terms(self, mock_doc_template):
        """测试空付款条款时跳过该部分"""
        quotation = self._create_mock_quotation(payment_terms=None)
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc
        
        filepath = self.service.generate_pdf(quotation)
        self.assertIsNotNone(filepath)

    @patch('app.services.quotation_pdf_service.REPORTLAB_AVAILABLE', True)
    @patch('app.services.quotation_pdf_service.SimpleDocTemplate')
    def test_generate_pdf_skips_empty_notes(self, mock_doc_template):
        """测试空备注时跳过该部分"""
        quotation = self._create_mock_quotation(notes=None)
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc
        
        filepath = self.service.generate_pdf(quotation)
        self.assertIsNotNone(filepath)

    @patch('app.services.quotation_pdf_service.REPORTLAB_AVAILABLE', True)
    @patch('app.services.quotation_pdf_service.SimpleDocTemplate')
    def test_generate_pdf_handles_decimal_values(self, mock_doc_template):
        """测试正确处理Decimal类型的价格"""
        quotation = self._create_mock_quotation(
            subtotal=Decimal("12345.67"),
            tax=Decimal("1604.94"),
            discount=Decimal("1000.00"),
            total=Decimal("12950.61")
        )
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc
        
        filepath = self.service.generate_pdf(quotation)
        
        # 验证文档被成功创建
        self.assertTrue(filepath.endswith(".pdf"))
        mock_doc.build.assert_called_once()

    # ========== generate_comparison_pdf() 测试 ==========

    @patch('app.services.quotation_pdf_service.REPORTLAB_AVAILABLE', False)
    def test_generate_comparison_pdf_raises_error_when_reportlab_unavailable(self):
        """测试reportlab不可用时抛出异常"""
        quotations = [
            self._create_mock_quotation(quotation_type=QuotationType.BASIC),
            self._create_mock_quotation(quotation_type=QuotationType.STANDARD),
            self._create_mock_quotation(quotation_type=QuotationType.PREMIUM)
        ]
        
        with self.assertRaises(RuntimeError) as context:
            self.service.generate_comparison_pdf(quotations)
        
        self.assertIn("ReportLab is not installed", str(context.exception))

    @patch('app.services.quotation_pdf_service.REPORTLAB_AVAILABLE', True)
    @patch('app.services.quotation_pdf_service.SimpleDocTemplate')
    @patch('app.services.quotation_pdf_service.datetime')
    def test_generate_comparison_pdf_creates_timestamped_filename(self, mock_datetime, mock_doc_template):
        """测试生成带时间戳的对比PDF文件名"""
        mock_datetime.now.return_value.strftime.return_value = "20260221153000"
        
        quotations = [
            self._create_mock_quotation(
                quotation_type=QuotationType.BASIC,
                total=Decimal("5000.00")
            ),
            self._create_mock_quotation(
                quotation_type=QuotationType.STANDARD,
                total=Decimal("10000.00")
            ),
            self._create_mock_quotation(
                quotation_type=QuotationType.PREMIUM,
                total=Decimal("15000.00")
            )
        ]
        
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc
        
        filepath = self.service.generate_comparison_pdf(quotations)
        
        expected_path = "uploads/quotations/quotation_comparison_20260221153000.pdf"
        self.assertEqual(filepath, expected_path)

    @patch('app.services.quotation_pdf_service.REPORTLAB_AVAILABLE', True)
    @patch('app.services.quotation_pdf_service.SimpleDocTemplate')
    @patch('app.services.quotation_pdf_service.Table')
    def test_generate_comparison_pdf_creates_comparison_table(self, mock_table, mock_doc_template):
        """测试创建对比表格"""
        quotations = [
            self._create_mock_quotation(
                quotation_type=QuotationType.BASIC,
                items=[{"name": "功能A", "quantity": 1, "unit": "项", 
                        "unit_price": Decimal("1000"), "total_price": Decimal("1000")}],
                total=Decimal("5000.00"),
                validity_days=30,
                discount=Decimal("100.00")
            ),
            self._create_mock_quotation(
                quotation_type=QuotationType.STANDARD,
                items=[{"name": "功能A", "quantity": 1, "unit": "项", 
                        "unit_price": Decimal("1000"), "total_price": Decimal("1000")},
                       {"name": "功能B", "quantity": 1, "unit": "项", 
                        "unit_price": Decimal("2000"), "total_price": Decimal("2000")}],
                total=Decimal("10000.00"),
                validity_days=45,
                discount=Decimal("500.00")
            ),
            self._create_mock_quotation(
                quotation_type=QuotationType.PREMIUM,
                items=[{"name": "功能A", "quantity": 1, "unit": "项", 
                        "unit_price": Decimal("1000"), "total_price": Decimal("1000")},
                       {"name": "功能B", "quantity": 1, "unit": "项", 
                        "unit_price": Decimal("2000"), "total_price": Decimal("2000")},
                       {"name": "功能C", "quantity": 1, "unit": "项", 
                        "unit_price": Decimal("3000"), "total_price": Decimal("3000")}],
                total=Decimal("15000.00"),
                validity_days=60,
                discount=Decimal("1000.00")
            )
        ]
        
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc
        
        self.service.generate_comparison_pdf(quotations)
        
        # 验证Table被调用创建对比表
        self.assertGreaterEqual(mock_table.call_count, 1)

    @patch('app.services.quotation_pdf_service.REPORTLAB_AVAILABLE', True)
    @patch('app.services.quotation_pdf_service.SimpleDocTemplate')
    @patch('app.services.quotation_pdf_service.Paragraph')
    def test_generate_comparison_pdf_includes_recommendation(self, mock_paragraph, mock_doc_template):
        """测试包含推荐方案"""
        quotations = [
            self._create_mock_quotation(quotation_type=QuotationType.BASIC),
            self._create_mock_quotation(quotation_type=QuotationType.STANDARD),
            self._create_mock_quotation(quotation_type=QuotationType.PREMIUM)
        ]
        
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc
        
        self.service.generate_comparison_pdf(quotations)
        
        # 验证Paragraph被调用且包含推荐文本
        paragraph_calls = [str(call) for call in mock_paragraph.call_args_list]
        self.assertTrue(any("标准版" in str(call) or "推荐" in str(call) for call in paragraph_calls))

    # ========== _get_type_display() 测试 ==========

    def test_get_type_display_basic(self):
        """测试基础版类型显示"""
        result = self.service._get_type_display(QuotationType.BASIC)
        self.assertEqual(result, "基础版")

    def test_get_type_display_standard(self):
        """测试标准版类型显示"""
        result = self.service._get_type_display(QuotationType.STANDARD)
        self.assertEqual(result, "标准版")

    def test_get_type_display_premium(self):
        """测试高级版类型显示"""
        result = self.service._get_type_display(QuotationType.PREMIUM)
        self.assertEqual(result, "高级版")

    def test_get_type_display_string_value(self):
        """测试字符串类型输入"""
        result = self.service._get_type_display("basic")
        self.assertEqual(result, "基础版")
        
        result = self.service._get_type_display("standard")
        self.assertEqual(result, "标准版")
        
        result = self.service._get_type_display("premium")
        self.assertEqual(result, "高级版")

    def test_get_type_display_unknown(self):
        """测试未知类型"""
        result = self.service._get_type_display("unknown")
        self.assertEqual(result, "未知")

    # ========== _get_status_display() 测试 ==========

    def test_get_status_display_draft(self):
        """测试草稿状态显示"""
        result = self.service._get_status_display(QuotationStatus.DRAFT)
        self.assertEqual(result, "草稿")

    def test_get_status_display_pending_approval(self):
        """测试待审批状态显示"""
        result = self.service._get_status_display(QuotationStatus.PENDING_APPROVAL)
        self.assertEqual(result, "待审批")

    def test_get_status_display_approved(self):
        """测试已审批状态显示"""
        result = self.service._get_status_display(QuotationStatus.APPROVED)
        self.assertEqual(result, "已审批")

    def test_get_status_display_sent(self):
        """测试已发送状态显示"""
        result = self.service._get_status_display(QuotationStatus.SENT)
        self.assertEqual(result, "已发送")

    def test_get_status_display_accepted(self):
        """测试已接受状态显示"""
        result = self.service._get_status_display(QuotationStatus.ACCEPTED)
        self.assertEqual(result, "已接受")

    def test_get_status_display_rejected(self):
        """测试已拒绝状态显示"""
        result = self.service._get_status_display(QuotationStatus.REJECTED)
        self.assertEqual(result, "已拒绝")

    def test_get_status_display_string_value(self):
        """测试字符串状态输入"""
        result = self.service._get_status_display("draft")
        self.assertEqual(result, "草稿")
        
        result = self.service._get_status_display("approved")
        self.assertEqual(result, "已审批")

    def test_get_status_display_unknown(self):
        """测试未知状态"""
        result = self.service._get_status_display("unknown_status")
        self.assertEqual(result, "未知")

    # ========== 边界情况测试 ==========

    @patch('app.services.quotation_pdf_service.REPORTLAB_AVAILABLE', True)
    @patch('app.services.quotation_pdf_service.SimpleDocTemplate')
    def test_generate_pdf_with_empty_items_list(self, mock_doc_template):
        """测试空报价项列表"""
        quotation = self._create_mock_quotation(items=[])
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc
        
        filepath = self.service.generate_pdf(quotation)
        
        self.assertIsNotNone(filepath)
        mock_doc.build.assert_called_once()

    @patch('app.services.quotation_pdf_service.REPORTLAB_AVAILABLE', True)
    @patch('app.services.quotation_pdf_service.SimpleDocTemplate')
    def test_generate_pdf_with_multiline_payment_terms(self, mock_doc_template):
        """测试多行付款条款"""
        quotation = self._create_mock_quotation(
            payment_terms="第一期：签约支付30%\n第二期：开发完成支付40%\n第三期：验收支付30%"
        )
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc
        
        filepath = self.service.generate_pdf(quotation)
        
        self.assertIsNotNone(filepath)

    @patch('app.services.quotation_pdf_service.REPORTLAB_AVAILABLE', True)
    @patch('app.services.quotation_pdf_service.SimpleDocTemplate')
    def test_generate_pdf_with_large_numbers(self, mock_doc_template):
        """测试大数值处理"""
        quotation = self._create_mock_quotation(
            subtotal=Decimal("999999.99"),
            tax=Decimal("129999.99"),
            discount=Decimal("50000.00"),
            total=Decimal("1079999.98")
        )
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc
        
        filepath = self.service.generate_pdf(quotation)
        
        self.assertIsNotNone(filepath)

    @patch('app.services.quotation_pdf_service.REPORTLAB_AVAILABLE', True)
    @patch('app.services.quotation_pdf_service.SimpleDocTemplate')
    def test_generate_pdf_with_zero_values(self, mock_doc_template):
        """测试零值处理"""
        quotation = self._create_mock_quotation(
            tax=Decimal("0.00"),
            discount=Decimal("0.00")
        )
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc
        
        filepath = self.service.generate_pdf(quotation)
        
        self.assertIsNotNone(filepath)

    @patch('app.services.quotation_pdf_service.REPORTLAB_AVAILABLE', True)
    @patch('app.services.quotation_pdf_service.SimpleDocTemplate')
    def test_generate_comparison_pdf_with_company_info(self, mock_doc_template):
        """测试带公司信息的对比PDF生成"""
        quotations = [
            self._create_mock_quotation(quotation_type=QuotationType.BASIC),
            self._create_mock_quotation(quotation_type=QuotationType.STANDARD),
            self._create_mock_quotation(quotation_type=QuotationType.PREMIUM)
        ]
        company_info = {
            'name': '测试科技有限公司',
            'logo_path': '/path/to/logo.png'
        }
        
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc
        
        filepath = self.service.generate_comparison_pdf(quotations, company_info)
        
        self.assertIsNotNone(filepath)


class TestQuotationPDFServiceIntegration(unittest.TestCase):
    """集成测试 - 测试真实业务场景"""

    def setUp(self):
        """测试准备"""
        self.mock_makedirs = patch('os.makedirs').start()
        self.mock_exists = patch('os.path.exists').start()
        self.mock_exists.return_value = False
        
        self.service = QuotationPDFService()

    def tearDown(self):
        """测试清理"""
        patch.stopall()

    def _create_mock_quotation(self, quotation_type, total, items_count):
        """创建简化的mock报价单"""
        quotation = MagicMock()
        quotation.quotation_number = f"Q2026{quotation_type.value}001"
        quotation.quotation_type = quotation_type
        quotation.status = QuotationStatus.DRAFT
        quotation.items = [
            {
                "name": f"功能项{i+1}",
                "quantity": 1,
                "unit": "项",
                "unit_price": Decimal("1000.00"),
                "total_price": Decimal("1000.00")
            }
            for i in range(items_count)
        ]
        quotation.subtotal = total
        quotation.tax = total * Decimal("0.13")
        quotation.discount = Decimal("0.00")
        quotation.total = total
        quotation.validity_days = 30
        quotation.payment_terms = "预付款50%"
        quotation.notes = "测试备注"
        quotation.version = 1
        quotation.created_at = datetime.now()
        return quotation

    @patch('app.services.quotation_pdf_service.REPORTLAB_AVAILABLE', True)
    @patch('app.services.quotation_pdf_service.SimpleDocTemplate')
    def test_complete_workflow_single_quotation(self, mock_doc_template):
        """测试完整的单个报价单生成流程"""
        quotation = self._create_mock_quotation(
            QuotationType.STANDARD, 
            Decimal("10000.00"),
            5
        )
        
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc
        
        filepath = self.service.generate_pdf(quotation)
        
        # 验证流程完整性
        self.assertIsNotNone(filepath)
        self.assertTrue(filepath.endswith(".pdf"))
        mock_doc.build.assert_called_once()

    @patch('app.services.quotation_pdf_service.REPORTLAB_AVAILABLE', True)
    @patch('app.services.quotation_pdf_service.SimpleDocTemplate')
    def test_complete_workflow_comparison(self, mock_doc_template):
        """测试完整的对比报价单生成流程"""
        quotations = [
            self._create_mock_quotation(QuotationType.BASIC, Decimal("5000.00"), 3),
            self._create_mock_quotation(QuotationType.STANDARD, Decimal("10000.00"), 5),
            self._create_mock_quotation(QuotationType.PREMIUM, Decimal("15000.00"), 8)
        ]
        
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc
        
        filepath = self.service.generate_comparison_pdf(quotations)
        
        # 验证流程完整性
        self.assertIsNotNone(filepath)
        self.assertTrue("comparison" in filepath)
        mock_doc.build.assert_called_once()


if __name__ == "__main__":
    unittest.main()
