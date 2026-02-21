# -*- coding: utf-8 -*-
"""
业务支持订单工具服务单元测试

目标：
1. 只mock外部依赖（db.query, db.add, db.commit等数据库操作）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import json
import unittest
from datetime import datetime, date
from unittest.mock import MagicMock, patch, call

from app.services.business_support_utils.service import BusinessSupportUtilsService
from app.models.business_support import (
    CustomerSupplierRegistration,
    DeliveryOrder,
    InvoiceRequest,
    Reconciliation,
    SalesOrder,
)
from app.models.sales import Invoice


class TestBusinessSupportUtilsServiceInit(unittest.TestCase):
    """测试初始化"""

    def test_init(self):
        """测试服务初始化"""
        mock_db = MagicMock()
        service = BusinessSupportUtilsService(mock_db)
        self.assertEqual(service.db, mock_db)


class TestNotificationMethods(unittest.TestCase):
    """测试通知发送方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = BusinessSupportUtilsService(self.mock_db)

    @patch('app.services.business_support_utils.service.NotificationDispatcher')
    def test_send_department_notification_success(self, mock_dispatcher_class):
        """测试成功发送部门通知"""
        mock_dispatcher = MagicMock()
        mock_dispatcher_class.return_value = mock_dispatcher

        self.service.send_department_notification(
            user_id=1,
            notification_type="APPROVAL",
            title="测试通知",
            content="这是测试内容",
            source_type="SalesOrder",
            source_id=100,
            priority="HIGH",
            extra_data={"key": "value"}
        )

        mock_dispatcher_class.assert_called_once_with(self.mock_db)
        mock_dispatcher.create_system_notification.assert_called_once_with(
            recipient_id=1,
            notification_type="APPROVAL",
            title="测试通知",
            content="这是测试内容",
            source_type="SalesOrder",
            source_id=100,
            link_url="/salesorder?id=100",
            priority="HIGH",
            extra_data={"key": "value"},
        )
        self.mock_db.commit.assert_called_once()

    @patch('app.services.business_support_utils.service.NotificationDispatcher')
    def test_send_department_notification_default_priority(self, mock_dispatcher_class):
        """测试使用默认优先级发送通知"""
        mock_dispatcher = MagicMock()
        mock_dispatcher_class.return_value = mock_dispatcher

        self.service.send_department_notification(
            user_id=1,
            notification_type="INFO",
            title="测试",
            content="内容",
            source_type="Invoice",
            source_id=50
        )

        call_args = mock_dispatcher.create_system_notification.call_args
        self.assertEqual(call_args.kwargs['priority'], "NORMAL")
        self.assertEqual(call_args.kwargs['extra_data'], {})

    @patch('app.services.business_support_utils.service.NotificationDispatcher')
    @patch('app.services.business_support_utils.service.logger')
    def test_send_department_notification_failure(self, mock_logger, mock_dispatcher_class):
        """测试发送通知失败（记录警告但不抛出异常）"""
        mock_dispatcher = MagicMock()
        mock_dispatcher_class.return_value = mock_dispatcher
        mock_dispatcher.create_system_notification.side_effect = Exception("发送失败")

        # 不应该抛出异常
        self.service.send_department_notification(
            user_id=1,
            notification_type="INFO",
            title="测试",
            content="内容",
            source_type="Order",
            source_id=1
        )

        mock_logger.warning.assert_called_once()
        self.assertIn("发送通知失败", mock_logger.warning.call_args[0][0])


class TestCodeGenerationMethods(unittest.TestCase):
    """测试编码生成方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = BusinessSupportUtilsService(self.mock_db)

    @patch('app.services.business_support_utils.service.apply_like_filter')
    @patch('app.services.business_support_utils.service.datetime')
    def test_generate_order_no_first_order(self, mock_datetime, mock_apply_like):
        """测试生成第一个销售订单编号"""
        mock_datetime.now.return_value = datetime(2025, 1, 15, 10, 30)
        
        mock_query = MagicMock()
        mock_query.order_by.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        # apply_like_filter 返回传入的第一个参数（query）
        mock_apply_like.side_effect = lambda q, *args, **kwargs: q

        result = self.service.generate_order_no()
        
        self.assertEqual(result, "SO250115-001")

    @patch('app.services.business_support_utils.service.apply_like_filter')
    @patch('app.services.business_support_utils.service.datetime')
    def test_generate_order_no_increment(self, mock_datetime, mock_apply_like):
        """测试生成递增的订单编号"""
        mock_datetime.now.return_value = datetime(2025, 1, 15, 10, 30)
        
        mock_order = MagicMock()
        mock_order.order_no = "SO250115-005"
        
        mock_query = MagicMock()
        mock_query.order_by.return_value.first.return_value = mock_order
        self.mock_db.query.return_value = mock_query
        # apply_like_filter 返回传入的第一个参数（query）
        mock_apply_like.side_effect = lambda q, *args, **kwargs: q

        result = self.service.generate_order_no()
        
        self.assertEqual(result, "SO250115-006")

    @patch('app.services.business_support_utils.service.apply_like_filter')
    @patch('app.services.business_support_utils.service.datetime')
    def test_generate_order_no_invalid_format(self, mock_datetime, mock_apply_like):
        """测试处理无效格式的订单编号"""
        mock_datetime.now.return_value = datetime(2025, 1, 15, 10, 30)
        
        mock_order = MagicMock()
        mock_order.order_no = "INVALID-FORMAT"
        
        mock_query = MagicMock()
        mock_query.order_by.return_value.first.return_value = mock_order
        self.mock_db.query.return_value = mock_query
        # apply_like_filter 返回传入的第一个参数（query）
        mock_apply_like.side_effect = lambda q, *args, **kwargs: q

        result = self.service.generate_order_no()
        
        self.assertEqual(result, "SO250115-001")

    @patch('app.services.business_support_utils.service.apply_like_filter')
    @patch('app.services.business_support_utils.service.datetime')
    def test_generate_delivery_no_first(self, mock_datetime, mock_apply_like):
        """测试生成第一个送货单号"""
        mock_datetime.now.return_value = datetime(2025, 2, 20, 14, 0)
        
        mock_query = MagicMock()
        mock_query.order_by.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        # apply_like_filter 返回传入的第一个参数（query）
        mock_apply_like.side_effect = lambda q, *args, **kwargs: q

        result = self.service.generate_delivery_no()
        
        self.assertEqual(result, "DO250220-001")

    @patch('app.services.business_support_utils.service.apply_like_filter')
    @patch('app.services.business_support_utils.service.datetime')
    def test_generate_delivery_no_increment(self, mock_datetime, mock_apply_like):
        """测试递增送货单号"""
        mock_datetime.now.return_value = datetime(2025, 2, 20, 14, 0)
        
        mock_delivery = MagicMock()
        mock_delivery.delivery_no = "DO250220-010"
        
        mock_query = MagicMock()
        mock_query.order_by.return_value.first.return_value = mock_delivery
        self.mock_db.query.return_value = mock_query
        # apply_like_filter 返回传入的第一个参数（query）
        mock_apply_like.side_effect = lambda q, *args, **kwargs: q

        result = self.service.generate_delivery_no()
        
        self.assertEqual(result, "DO250220-011")

    @patch('app.services.business_support_utils.service.apply_like_filter')
    @patch('app.services.business_support_utils.service.datetime')
    def test_generate_invoice_request_no_first(self, mock_datetime, mock_apply_like):
        """测试生成第一个开票申请编号"""
        mock_datetime.now.return_value = datetime(2025, 3, 5)
        
        mock_query = MagicMock()
        mock_query.order_by.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        # apply_like_filter 返回传入的第一个参数（query）
        mock_apply_like.side_effect = lambda q, *args, **kwargs: q

        result = self.service.generate_invoice_request_no()
        
        self.assertEqual(result, "IR250305-001")

    @patch('app.services.business_support_utils.service.apply_like_filter')
    @patch('app.services.business_support_utils.service.datetime')
    def test_generate_invoice_request_no_increment(self, mock_datetime, mock_apply_like):
        """测试递增开票申请编号"""
        mock_datetime.now.return_value = datetime(2025, 3, 5)
        
        mock_request = MagicMock()
        mock_request.request_no = "IR250305-099"
        
        mock_query = MagicMock()
        mock_query.order_by.return_value.first.return_value = mock_request
        self.mock_db.query.return_value = mock_query
        # apply_like_filter 返回传入的第一个参数（query）
        mock_apply_like.side_effect = lambda q, *args, **kwargs: q

        result = self.service.generate_invoice_request_no()
        
        self.assertEqual(result, "IR250305-100")

    @patch('app.services.business_support_utils.service.apply_like_filter')
    @patch('app.services.business_support_utils.service.datetime')
    def test_generate_invoice_request_no_parse_error(self, mock_datetime, mock_apply_like):
        """测试解析错误时重置编号"""
        mock_datetime.now.return_value = datetime(2025, 3, 5)
        
        mock_request = MagicMock()
        mock_request.request_no = "INVALID"
        
        mock_query = MagicMock()
        mock_query.order_by.return_value.first.return_value = mock_request
        self.mock_db.query.return_value = mock_query
        # apply_like_filter 返回传入的第一个参数（query）
        mock_apply_like.side_effect = lambda q, *args, **kwargs: q

        result = self.service.generate_invoice_request_no()
        
        self.assertEqual(result, "IR250305-001")

    @patch('app.services.business_support_utils.service.apply_like_filter')
    @patch('app.services.business_support_utils.service.datetime')
    def test_generate_registration_no_first(self, mock_datetime, mock_apply_like):
        """测试生成第一个入驻编号"""
        mock_datetime.now.return_value = datetime(2025, 4, 10)
        
        mock_query = MagicMock()
        mock_query.order_by.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        # apply_like_filter 返回传入的第一个参数（query）
        mock_apply_like.side_effect = lambda q, *args, **kwargs: q

        result = self.service.generate_registration_no()
        
        self.assertEqual(result, "CR250410-001")

    @patch('app.services.business_support_utils.service.apply_like_filter')
    @patch('app.services.business_support_utils.service.datetime')
    def test_generate_registration_no_increment(self, mock_datetime, mock_apply_like):
        """测试递增入驻编号"""
        mock_datetime.now.return_value = datetime(2025, 4, 10)
        
        mock_reg = MagicMock()
        mock_reg.registration_no = "CR250410-042"
        
        mock_query = MagicMock()
        mock_query.order_by.return_value.first.return_value = mock_reg
        self.mock_db.query.return_value = mock_query
        # apply_like_filter 返回传入的第一个参数（query）
        mock_apply_like.side_effect = lambda q, *args, **kwargs: q

        result = self.service.generate_registration_no()
        
        self.assertEqual(result, "CR250410-043")

    @patch('app.services.business_support_utils.service.apply_like_filter')
    @patch('app.services.business_support_utils.service.datetime')
    def test_generate_invoice_code_first(self, mock_datetime, mock_apply_like):
        """测试生成第一个发票编码"""
        mock_datetime.now.return_value = datetime(2025, 5, 20, 9, 0)
        
        mock_query = MagicMock()
        mock_query.order_by.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        # apply_like_filter 返回传入的第一个参数（query）
        mock_apply_like.side_effect = lambda q, *args, **kwargs: q

        result = self.service.generate_invoice_code()
        
        self.assertEqual(result, "INV-250520-001")

    @patch('app.services.business_support_utils.service.apply_like_filter')
    @patch('app.services.business_support_utils.service.datetime')
    def test_generate_invoice_code_increment(self, mock_datetime, mock_apply_like):
        """测试递增发票编码"""
        mock_datetime.now.return_value = datetime(2025, 5, 20, 9, 0)
        
        mock_invoice = MagicMock()
        mock_invoice.invoice_code = "INV-250520-077"
        
        mock_query = MagicMock()
        mock_query.order_by.return_value.first.return_value = mock_invoice
        self.mock_db.query.return_value = mock_query
        # apply_like_filter 返回传入的第一个参数（query）
        mock_apply_like.side_effect = lambda q, *args, **kwargs: q

        result = self.service.generate_invoice_code()
        
        self.assertEqual(result, "INV-250520-078")

    @patch('app.services.business_support_utils.service.apply_like_filter')
    @patch('app.services.business_support_utils.service.datetime')
    def test_generate_reconciliation_no_first(self, mock_datetime, mock_apply_like):
        """测试生成第一个对账单号"""
        mock_datetime.now.return_value = datetime(2025, 6, 15, 10, 0)
        
        mock_query = MagicMock()
        mock_query.order_by.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        # apply_like_filter 返回传入的第一个参数（query）
        mock_apply_like.side_effect = lambda q, *args, **kwargs: q

        result = self.service.generate_reconciliation_no()
        
        self.assertEqual(result, "RC250615-001")

    @patch('app.services.business_support_utils.service.apply_like_filter')
    @patch('app.services.business_support_utils.service.datetime')
    def test_generate_reconciliation_no_increment(self, mock_datetime, mock_apply_like):
        """测试递增对账单号"""
        mock_datetime.now.return_value = datetime(2025, 6, 15, 10, 0)
        
        mock_reconciliation = MagicMock()
        mock_reconciliation.reconciliation_no = "RC250615-123"
        
        mock_query = MagicMock()
        mock_query.order_by.return_value.first.return_value = mock_reconciliation
        self.mock_db.query.return_value = mock_query
        # apply_like_filter 返回传入的第一个参数（query）
        mock_apply_like.side_effect = lambda q, *args, **kwargs: q

        result = self.service.generate_reconciliation_no()
        
        self.assertEqual(result, "RC250615-124")


class TestSerializationMethods(unittest.TestCase):
    """测试序列化方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = BusinessSupportUtilsService(self.mock_db)

    def test_serialize_attachments_valid_list(self):
        """测试序列化有效的附件列表"""
        attachments = ["file1.pdf", "file2.doc", "file3.jpg"]
        result = self.service.serialize_attachments(attachments)
        
        self.assertIsInstance(result, str)
        self.assertEqual(json.loads(result), attachments)

    def test_serialize_attachments_empty_list(self):
        """测试序列化空列表"""
        result = self.service.serialize_attachments([])
        self.assertIsNone(result)

    def test_serialize_attachments_none(self):
        """测试序列化None"""
        result = self.service.serialize_attachments(None)
        self.assertIsNone(result)

    def test_serialize_attachments_with_objects(self):
        """测试序列化包含对象的列表（降级处理）"""
        class CustomObj:
            def __str__(self):
                return "custom_object"
        
        items = [CustomObj(), "normal.txt"]
        result = self.service.serialize_attachments(items)
        
        self.assertIsInstance(result, str)
        data = json.loads(result)
        self.assertEqual(data[0], "custom_object")
        self.assertEqual(data[1], "normal.txt")

    def test_deserialize_attachments_valid_json(self):
        """测试反序列化有效的JSON"""
        payload = '["file1.pdf", "file2.doc"]'
        result = self.service.deserialize_attachments(payload)
        
        self.assertEqual(result, ["file1.pdf", "file2.doc"])

    def test_deserialize_attachments_empty_string(self):
        """测试反序列化空字符串"""
        result = self.service.deserialize_attachments("")
        self.assertIsNone(result)

    def test_deserialize_attachments_none(self):
        """测试反序列化None"""
        result = self.service.deserialize_attachments(None)
        self.assertIsNone(result)

    def test_deserialize_attachments_invalid_json(self):
        """测试反序列化无效JSON（降级为单元素列表）"""
        payload = "not-a-json"
        result = self.service.deserialize_attachments(payload)
        
        self.assertEqual(result, ["not-a-json"])

    def test_deserialize_attachments_non_list_json(self):
        """测试反序列化非列表JSON"""
        payload = '{"key": "value"}'
        result = self.service.deserialize_attachments(payload)
        
        self.assertIsNone(result)


class TestResponseConversionMethods(unittest.TestCase):
    """测试响应转换方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = BusinessSupportUtilsService(self.mock_db)

    def test_to_invoice_request_response_full_data(self):
        """测试转换完整的开票申请数据"""
        mock_contract = MagicMock()
        mock_contract.contract_code = "CT-2025-001"
        
        mock_project = MagicMock()
        mock_project.project_name = "测试项目"
        
        mock_customer = MagicMock()
        mock_customer.customer_name = "测试客户"
        
        mock_approver = MagicMock()
        mock_approver.real_name = "张三"
        mock_approver.username = "zhangsan"
        
        mock_invoice = MagicMock()
        mock_invoice.invoice_code = "INV-250101-001"
        
        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.request_no = "IR250101-001"
        mock_request.contract_id = 10
        mock_request.contract = mock_contract
        mock_request.project_id = 20
        mock_request.project = mock_project
        mock_request.project_name = None
        mock_request.customer_id = 30
        mock_request.customer = mock_customer
        mock_request.customer_name = None
        mock_request.payment_plan_id = 40
        mock_request.invoice_type = "VAT"
        mock_request.invoice_title = "测试发票"
        mock_request.tax_rate = 0.13
        mock_request.amount = 10000.0
        mock_request.tax_amount = 1300.0
        mock_request.total_amount = 11300.0
        mock_request.currency = "CNY"
        mock_request.expected_issue_date = date(2025, 1, 15)
        mock_request.expected_payment_date = date(2025, 2, 15)
        mock_request.reason = "正常开票"
        mock_request.attachments = '["file1.pdf", "file2.doc"]'
        mock_request.remark = "备注信息"
        mock_request.status = "APPROVED"
        mock_request.approval_comment = "同意"
        mock_request.requested_by = 100
        mock_request.requested_by_name = "李四"
        mock_request.approved_by = 200
        mock_request.approver = mock_approver
        mock_request.approved_at = datetime(2025, 1, 10, 10, 0)
        mock_request.invoice_id = 300
        mock_request.invoice = mock_invoice
        mock_request.receipt_status = "RECEIVED"
        mock_request.receipt_updated_at = datetime(2025, 1, 20, 10, 0)
        mock_request.created_at = datetime(2025, 1, 5, 10, 0)
        mock_request.updated_at = datetime(2025, 1, 10, 10, 0)

        result = self.service.to_invoice_request_response(mock_request)

        self.assertEqual(result.id, 1)
        self.assertEqual(result.request_no, "IR250101-001")
        self.assertEqual(result.contract_code, "CT-2025-001")
        self.assertEqual(result.project_name, "测试项目")
        self.assertEqual(result.customer_name, "测试客户")
        self.assertEqual(result.approved_by_name, "张三")
        self.assertEqual(result.invoice_code, "INV-250101-001")
        self.assertEqual(result.attachments, ["file1.pdf", "file2.doc"])

    def test_to_invoice_request_response_minimal_data(self):
        """测试转换最小化的开票申请数据"""
        mock_request = MagicMock()
        mock_request.id = 2
        mock_request.request_no = "IR250102-001"
        mock_request.contract = None
        mock_request.project = None
        mock_request.project_name = "直接指定项目名"
        mock_request.customer = None
        mock_request.customer_name = "直接指定客户名"
        mock_request.approver = None
        mock_request.invoice = None
        mock_request.attachments = None
        
        # 必填字段
        mock_request.contract_id = 1  # 改为有效整数
        mock_request.project_id = None
        mock_request.customer_id = 1  # 改为有效整数
        mock_request.payment_plan_id = None
        mock_request.invoice_type = "NORMAL"
        mock_request.invoice_title = "发票标题"
        mock_request.tax_rate = 0.06
        mock_request.amount = 5000.0
        mock_request.tax_amount = 300.0
        mock_request.total_amount = 5300.0
        mock_request.currency = "CNY"
        mock_request.expected_issue_date = None
        mock_request.expected_payment_date = None
        mock_request.reason = None
        mock_request.remark = None
        mock_request.status = "PENDING"
        mock_request.approval_comment = None
        mock_request.requested_by = 100
        mock_request.requested_by_name = "王五"
        mock_request.approved_by = None
        mock_request.approved_at = None
        mock_request.invoice_id = None
        mock_request.receipt_status = None
        mock_request.receipt_updated_at = None
        mock_request.created_at = datetime(2025, 1, 5, 10, 0)
        mock_request.updated_at = datetime(2025, 1, 5, 10, 0)

        result = self.service.to_invoice_request_response(mock_request)

        self.assertEqual(result.id, 2)
        self.assertEqual(result.project_name, "直接指定项目名")
        self.assertEqual(result.customer_name, "直接指定客户名")
        self.assertIsNone(result.contract_code)
        self.assertIsNone(result.approved_by_name)
        self.assertIsNone(result.invoice_code)
        self.assertIsNone(result.attachments)

    def test_to_invoice_request_response_approver_no_real_name(self):
        """测试审批人无真实姓名时使用用户名"""
        mock_approver = MagicMock()
        mock_approver.real_name = None
        mock_approver.username = "admin"
        
        mock_request = MagicMock()
        mock_request.approver = mock_approver
        mock_request.contract = None
        mock_request.project = None
        mock_request.customer = None
        mock_request.invoice = None
        mock_request.attachments = None
        
        # 必填字段
        mock_request.id = 3
        mock_request.request_no = "IR250103-001"
        mock_request.contract_id = 1  # 改为有效整数
        mock_request.project_id = None
        mock_request.project_name = "项目"
        mock_request.customer_id = 1  # 改为有效整数
        mock_request.customer_name = "客户"
        mock_request.payment_plan_id = None
        mock_request.invoice_type = "VAT"
        mock_request.invoice_title = "标题"
        mock_request.tax_rate = 0.13
        mock_request.amount = 1000.0
        mock_request.tax_amount = 130.0
        mock_request.total_amount = 1130.0
        mock_request.currency = "CNY"
        mock_request.expected_issue_date = None
        mock_request.expected_payment_date = None
        mock_request.reason = None
        mock_request.remark = None
        mock_request.status = "APPROVED"
        mock_request.approval_comment = None
        mock_request.requested_by = 100
        mock_request.requested_by_name = "测试"
        mock_request.approved_by = 200
        mock_request.approved_at = None
        mock_request.invoice_id = None
        mock_request.receipt_status = None
        mock_request.receipt_updated_at = None
        mock_request.created_at = datetime(2025, 1, 5, 10, 0)
        mock_request.updated_at = datetime(2025, 1, 5, 10, 0)

        result = self.service.to_invoice_request_response(mock_request)

        self.assertEqual(result.approved_by_name, "admin")

    def test_to_registration_response_full_data(self):
        """测试转换完整的入驻记录"""
        mock_reviewer = MagicMock()
        mock_reviewer.real_name = "审核员"
        mock_reviewer.username = "reviewer"
        
        mock_record = MagicMock()
        mock_record.id = 1
        mock_record.registration_no = "CR250101-001"
        mock_record.customer_id = 10
        mock_record.customer_name = "客户A"
        mock_record.platform_name = "某电商平台"
        mock_record.platform_url = "https://example.com"
        mock_record.registration_status = "APPROVED"
        mock_record.application_date = date(2025, 1, 1)
        mock_record.approved_date = date(2025, 1, 5)
        mock_record.expire_date = date(2026, 1, 5)
        mock_record.contact_person = "联系人"
        mock_record.contact_phone = "13800138000"
        mock_record.contact_email = "contact@example.com"
        mock_record.required_docs = '["doc1.pdf", "doc2.pdf"]'
        mock_record.reviewer_id = 20
        mock_record.reviewer = mock_reviewer
        mock_record.review_comment = "通过审核"
        mock_record.external_sync_status = "SYNCED"
        mock_record.last_sync_at = datetime(2025, 1, 6, 10, 0)
        mock_record.remark = "备注"
        mock_record.created_at = datetime(2025, 1, 1, 10, 0)
        mock_record.updated_at = datetime(2025, 1, 5, 10, 0)

        result = self.service.to_registration_response(mock_record)

        self.assertEqual(result.id, 1)
        self.assertEqual(result.registration_no, "CR250101-001")
        self.assertEqual(result.customer_name, "客户A")
        self.assertEqual(result.platform_name, "某电商平台")
        self.assertEqual(result.reviewer_name, "审核员")
        self.assertEqual(result.required_docs, ["doc1.pdf", "doc2.pdf"])

    def test_to_registration_response_no_reviewer(self):
        """测试无审核人的入驻记录"""
        mock_record = MagicMock()
        mock_record.id = 2
        mock_record.registration_no = "CR250102-001"
        mock_record.customer_id = 20
        mock_record.customer_name = "客户B"
        mock_record.platform_name = "平台B"
        mock_record.platform_url = None
        mock_record.registration_status = "PENDING"
        mock_record.application_date = date(2025, 1, 10)
        mock_record.approved_date = None
        mock_record.expire_date = None
        mock_record.contact_person = "联系人B"
        mock_record.contact_phone = "13900139000"
        mock_record.contact_email = None
        mock_record.required_docs = None
        mock_record.reviewer_id = None
        mock_record.reviewer = None
        mock_record.review_comment = None
        mock_record.external_sync_status = "PENDING"
        mock_record.last_sync_at = None
        mock_record.remark = None
        mock_record.created_at = datetime(2025, 1, 10, 10, 0)
        mock_record.updated_at = datetime(2025, 1, 10, 10, 0)

        result = self.service.to_registration_response(mock_record)

        self.assertEqual(result.id, 2)
        self.assertIsNone(result.reviewer_name)
        self.assertIsNone(result.required_docs)

    def test_to_registration_response_reviewer_no_real_name(self):
        """测试审核人无真实姓名"""
        mock_reviewer = MagicMock()
        mock_reviewer.real_name = ""
        mock_reviewer.username = "reviewer123"
        
        mock_record = MagicMock()
        mock_record.id = 3
        mock_record.registration_no = "CR250103-001"
        mock_record.customer_id = 30
        mock_record.customer_name = "客户C"
        mock_record.platform_name = "平台C"
        mock_record.platform_url = "https://c.com"
        mock_record.registration_status = "APPROVED"
        mock_record.application_date = date(2025, 1, 15)
        mock_record.approved_date = date(2025, 1, 20)
        mock_record.expire_date = date(2026, 1, 20)
        mock_record.contact_person = "C联系人"
        mock_record.contact_phone = "13700137000"
        mock_record.contact_email = "c@example.com"
        mock_record.required_docs = None
        mock_record.reviewer_id = 30
        mock_record.reviewer = mock_reviewer
        mock_record.review_comment = "OK"
        mock_record.external_sync_status = "SYNCED"
        mock_record.last_sync_at = datetime(2025, 1, 21, 10, 0)
        mock_record.remark = None
        mock_record.created_at = datetime(2025, 1, 15, 10, 0)
        mock_record.updated_at = datetime(2025, 1, 20, 10, 0)

        result = self.service.to_registration_response(mock_record)

        self.assertEqual(result.reviewer_name, "reviewer123")


if __name__ == "__main__":
    unittest.main()
