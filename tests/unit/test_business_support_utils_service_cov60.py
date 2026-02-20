# -*- coding: utf-8 -*-
"""
BusinessSupportUtilsService 单元测试
目标覆盖率: 60%+
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.services.business_support_utils import BusinessSupportUtilsService
from app.models.business_support import (
    CustomerSupplierRegistration,
    InvoiceRequest,
    SalesOrder,
    DeliveryOrder,
    Reconciliation,
)
from app.models.sales import Invoice


class TestBusinessSupportUtilsService(unittest.TestCase):
    """测试 BusinessSupportUtilsService"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        self.service = BusinessSupportUtilsService(self.mock_db)

    def tearDown(self):
        """测试后清理"""
        self.mock_db.reset_mock()

    # ==================== 编码生成测试 ====================

    def test_generate_order_no_first_order(self):
        """测试生成销售订单编号 - 第一个订单"""
        # 模拟没有现有订单
        mock_query = MagicMock()
        mock_query.order_by.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query

        with patch('app.services.business_support_utils.service.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 1, 1, 10, 0, 0)
            mock_datetime.strftime = datetime.strftime
            result = self.service.generate_order_no()

        # 验证格式：SO250101-001
        self.assertTrue(result.startswith("SO250101-"))
        self.assertEqual(result, "SO250101-001")

    def test_generate_order_no_with_existing_orders(self):
        """测试生成销售订单编号 - 有现有订单"""
        # 模拟已有订单 SO250101-005
        mock_order = MagicMock(spec=SalesOrder)
        mock_order.order_no = "SO250101-005"

        mock_query = MagicMock()
        mock_query.order_by.return_value.first.return_value = mock_order
        self.mock_db.query.return_value = mock_query

        with patch('app.services.business_support_utils.service.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 1, 1, 10, 0, 0)
            mock_datetime.strftime = datetime.strftime
            result = self.service.generate_order_no()

        # 应该是 006
        self.assertEqual(result, "SO250101-006")

    def test_generate_delivery_no_first_delivery(self):
        """测试生成送货单号 - 第一个送货单"""
        mock_query = MagicMock()
        mock_query.order_by.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query

        with patch('app.services.business_support_utils.service.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 2, 15, 10, 0, 0)
            mock_datetime.strftime = datetime.strftime
            result = self.service.generate_delivery_no()

        self.assertEqual(result, "DO250215-001")

    def test_generate_invoice_request_no(self):
        """测试生成开票申请编号"""
        mock_query = MagicMock()
        mock_query.order_by.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query

        with patch('app.services.business_support_utils.service.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 3, 20, 10, 0, 0)
            mock_datetime.strftime = datetime.strftime
            result = self.service.generate_invoice_request_no()

        self.assertEqual(result, "IR250320-001")

    def test_generate_registration_no(self):
        """测试生成客户供应商入驻编号"""
        mock_query = MagicMock()
        mock_query.order_by.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query

        with patch('app.services.business_support_utils.service.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 4, 10, 10, 0, 0)
            mock_datetime.strftime = datetime.strftime
            result = self.service.generate_registration_no()

        self.assertEqual(result, "CR250410-001")

    def test_generate_invoice_code(self):
        """测试生成发票编码"""
        mock_query = MagicMock()
        mock_query.order_by.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query

        with patch('app.services.business_support_utils.service.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 5, 25, 10, 0, 0)
            mock_datetime.strftime = datetime.strftime
            result = self.service.generate_invoice_code()

        self.assertEqual(result, "INV-250525-001")

    def test_generate_reconciliation_no(self):
        """测试生成对账单号"""
        mock_query = MagicMock()
        mock_query.order_by.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query

        with patch('app.services.business_support_utils.service.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 6, 30, 10, 0, 0)
            mock_datetime.strftime = datetime.strftime
            result = self.service.generate_reconciliation_no()

        self.assertEqual(result, "RC250630-001")

    # ==================== 序列化测试 ====================

    def test_serialize_attachments_valid_list(self):
        """测试序列化附件 - 有效列表"""
        items = ["file1.pdf", "file2.doc", "file3.jpg"]
        result = BusinessSupportUtilsService.serialize_attachments(items)

        self.assertIsNotNone(result)
        self.assertIn("file1.pdf", result)
        self.assertIn("file2.doc", result)

    def test_serialize_attachments_empty(self):
        """测试序列化附件 - 空列表"""
        result = BusinessSupportUtilsService.serialize_attachments([])
        self.assertIsNone(result)

    def test_serialize_attachments_none(self):
        """测试序列化附件 - None"""
        result = BusinessSupportUtilsService.serialize_attachments(None)
        self.assertIsNone(result)

    def test_deserialize_attachments_valid_json(self):
        """测试反序列化附件 - 有效JSON"""
        payload = '["file1.pdf", "file2.doc"]'
        result = BusinessSupportUtilsService.deserialize_attachments(payload)

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertIn("file1.pdf", result)

    def test_deserialize_attachments_invalid_json(self):
        """测试反序列化附件 - 无效JSON"""
        payload = "not_a_json"
        result = BusinessSupportUtilsService.deserialize_attachments(payload)

        # 应该返回包含原字符串的列表
        self.assertIsNotNone(result)
        self.assertEqual(result, ["not_a_json"])

    def test_deserialize_attachments_none(self):
        """测试反序列化附件 - None"""
        result = BusinessSupportUtilsService.deserialize_attachments(None)
        self.assertIsNone(result)

    # ==================== 通知发送测试 ====================

    @patch('app.services.business_support_utils.service.NotificationDispatcher')
    def test_send_department_notification_success(self, mock_dispatcher_class):
        """测试发送部门通知 - 成功"""
        mock_dispatcher = MagicMock()
        mock_dispatcher_class.return_value = mock_dispatcher

        self.service.send_department_notification(
            user_id=1,
            notification_type="APPROVAL",
            title="测试通知",
            content="这是测试内容",
            source_type="ORDER",
            source_id=100,
            priority="HIGH"
        )

        # 验证调用
        mock_dispatcher_class.assert_called_once_with(self.mock_db)
        mock_dispatcher.create_system_notification.assert_called_once()
        self.mock_db.commit.assert_called_once()

    @patch('app.services.business_support_utils.service.NotificationDispatcher')
    def test_send_department_notification_failure(self, mock_dispatcher_class):
        """测试发送部门通知 - 失败处理"""
        mock_dispatcher = MagicMock()
        mock_dispatcher.create_system_notification.side_effect = Exception("测试异常")
        mock_dispatcher_class.return_value = mock_dispatcher

        # 不应该抛出异常
        self.service.send_department_notification(
            user_id=1,
            notification_type="APPROVAL",
            title="测试通知",
            content="这是测试内容",
            source_type="ORDER",
            source_id=100
        )

        # 验证没有 commit
        self.mock_db.commit.assert_not_called()

    # ==================== 响应转换测试 ====================

    def test_to_invoice_request_response(self):
        """测试转换开票申请响应"""
        # 创建 mock 对象
        mock_invoice_request = MagicMock(spec=InvoiceRequest)
        mock_invoice_request.id = 1
        mock_invoice_request.request_no = "IR250101-001"
        mock_invoice_request.contract = None
        mock_invoice_request.project = None
        mock_invoice_request.project_name = "测试项目"
        mock_invoice_request.customer = None
        mock_invoice_request.customer_name = "测试客户"
        mock_invoice_request.approver = None
        mock_invoice_request.invoice = None
        mock_invoice_request.invoice_type = "VAT"
        mock_invoice_request.attachments = '["file1.pdf"]'
        mock_invoice_request.status = "PENDING"

        result = self.service.to_invoice_request_response(mock_invoice_request)

        self.assertEqual(result.id, 1)
        self.assertEqual(result.request_no, "IR250101-001")
        self.assertEqual(result.project_name, "测试项目")
        self.assertEqual(result.customer_name, "测试客户")
        self.assertIsNotNone(result.attachments)

    def test_to_registration_response(self):
        """测试转换客户供应商入驻响应"""
        mock_registration = MagicMock(spec=CustomerSupplierRegistration)
        mock_registration.id = 1
        mock_registration.registration_no = "CR250101-001"
        mock_registration.customer_name = "测试客户"
        mock_registration.platform_name = "测试平台"
        mock_registration.reviewer = None
        mock_registration.required_docs = '["doc1.pdf", "doc2.pdf"]'
        mock_registration.registration_status = "APPROVED"

        result = self.service.to_registration_response(mock_registration)

        self.assertEqual(result.id, 1)
        self.assertEqual(result.registration_no, "CR250101-001")
        self.assertEqual(result.customer_name, "测试客户")
        self.assertEqual(result.platform_name, "测试平台")
        self.assertIsNotNone(result.required_docs)


if __name__ == "__main__":
    unittest.main()
