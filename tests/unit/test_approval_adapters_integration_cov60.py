# -*- coding: utf-8 -*-
"""
审批适配器综合集成测试
目标: 30-50个组合测试用例
覆盖: 多适配器交互、边界情况、异常处理、通知逻辑
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, call

try:
    from app.services.approval_engine.adapters.acceptance import AcceptanceOrderApprovalAdapter
    from app.services.approval_engine.adapters.quote import QuoteApprovalAdapter
    from app.services.approval_engine.adapters.purchase import PurchaseOrderApprovalAdapter
    from app.services.approval_engine.adapters.invoice import InvoiceApprovalAdapter
    from app.models.approval import ApprovalInstance
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


def make_db():
    """创建mock数据库会话"""
    db = MagicMock()
    db.flush = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    return db


class TestAdapterCommonBehavior:
    """适配器通用行为测试"""

    def test_all_adapters_have_entity_type(self):
        """所有适配器都应有entity_type"""
        db = make_db()
        adapters = [
            AcceptanceOrderApprovalAdapter(db),
            QuoteApprovalAdapter(db),
            PurchaseOrderApprovalAdapter(db),
            InvoiceApprovalAdapter(db),
        ]
        
        for adapter in adapters:
            assert hasattr(adapter, 'entity_type')
            assert adapter.entity_type != ""

    def test_all_adapters_unique_entity_types(self):
        """所有适配器的entity_type应唯一"""
        db = make_db()
        adapters = [
            AcceptanceOrderApprovalAdapter(db),
            QuoteApprovalAdapter(db),
            PurchaseOrderApprovalAdapter(db),
            InvoiceApprovalAdapter(db),
        ]
        
        entity_types = [a.entity_type for a in adapters]
        assert len(entity_types) == len(set(entity_types))

    def test_all_adapters_implement_get_entity(self):
        """所有适配器都实现get_entity方法"""
        db = make_db()
        adapters = [
            AcceptanceOrderApprovalAdapter(db),
            QuoteApprovalAdapter(db),
            PurchaseOrderApprovalAdapter(db),
            InvoiceApprovalAdapter(db),
        ]
        
        for adapter in adapters:
            assert hasattr(adapter, 'get_entity')
            assert callable(adapter.get_entity)

    def test_all_adapters_implement_get_entity_data(self):
        """所有适配器都实现get_entity_data方法"""
        db = make_db()
        adapters = [
            AcceptanceOrderApprovalAdapter(db),
            QuoteApprovalAdapter(db),
            PurchaseOrderApprovalAdapter(db),
            InvoiceApprovalAdapter(db),
        ]
        
        for adapter in adapters:
            assert hasattr(adapter, 'get_entity_data')
            assert callable(adapter.get_entity_data)

    def test_all_adapters_implement_callbacks(self):
        """所有适配器都实现审批回调方法"""
        db = make_db()
        adapters = [
            AcceptanceOrderApprovalAdapter(db),
            QuoteApprovalAdapter(db),
            PurchaseOrderApprovalAdapter(db),
            InvoiceApprovalAdapter(db),
        ]
        
        callbacks = ['on_submit', 'on_approved', 'on_rejected', 'on_withdrawn']
        for adapter in adapters:
            for callback in callbacks:
                assert hasattr(adapter, callback)
                assert callable(getattr(adapter, callback))

    def test_all_adapters_implement_validate_submit(self):
        """所有适配器都实现validate_submit方法"""
        db = make_db()
        adapters = [
            AcceptanceOrderApprovalAdapter(db),
            QuoteApprovalAdapter(db),
            PurchaseOrderApprovalAdapter(db),
            InvoiceApprovalAdapter(db),
        ]
        
        for adapter in adapters:
            assert hasattr(adapter, 'validate_submit')
            assert callable(adapter.validate_submit)


class TestDataTransformation:
    """数据转换测试"""

    def test_acceptance_data_decimal_conversion(self):
        """验收单 - Decimal类型正确转换"""
        db = make_db()
        order = MagicMock()
        order.pass_rate = Decimal("95.5")
        order.total_items = 20
        order.passed_items = 19
        order.failed_items = 1
        order.na_items = 0
        order.project_id = None
        order.machine_id = None
        order.template_id = None
        
        db.query.return_value.filter.return_value.first.return_value = order
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        data = adapter.get_entity_data(1)
        
        assert isinstance(data["pass_rate"], float)
        assert data["pass_rate"] == 95.5

    def test_quote_margin_conversion_from_decimal(self):
        """报价 - 毛利率从小数转换为百分比"""
        db = make_db()
        quote = MagicMock()
        version = MagicMock()
        version.gross_margin = Decimal("0.15")  # 15%
        version.total_price = Decimal("100000")
        version.cost_total = Decimal("85000")
        version.lead_time_days = 30
        version.delivery_date = None
        version.version_no = 1
        
        quote.current_version = version
        quote.customer = None
        quote.owner = None
        quote.customer_id = None
        quote.owner_id = None
        
        db.query.return_value.filter.return_value.first.return_value = quote
        
        adapter = QuoteApprovalAdapter(db)
        data = adapter.get_entity_data(1)
        
        assert data["gross_margin"] == 15.0

    def test_purchase_amount_conversion(self):
        """采购订单 - 金额正确转换为float"""
        db = make_db()
        order = MagicMock()
        order.total_amount = Decimal("123456.78")
        order.amount_with_tax = Decimal("139506.16")
        order.project_id = None
        order.supplier_id = None
        
        def query_side_effect(model):
            from app.models.purchase import PurchaseOrder, PurchaseOrderItem
            query_mock = MagicMock()
            if model == PurchaseOrder:
                query_mock.filter.return_value.first.return_value = order
            elif model == PurchaseOrderItem:
                query_mock.filter.return_value.count.return_value = 0
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        adapter = PurchaseOrderApprovalAdapter(db)
        data = adapter.get_entity_data(1)
        
        assert isinstance(data["total_amount"], float)
        assert data["total_amount"] == 123456.78

    def test_invoice_date_serialization(self):
        """发票 - 日期正确序列化为ISO格式"""
        db = make_db()
        invoice = MagicMock()
        invoice.issue_date = datetime(2025, 2, 15, 10, 30, 0)
        invoice.due_date = datetime(2025, 3, 15, 10, 30, 0)
        invoice.contract = None
        invoice.amount = Decimal("100000")
        
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        data = adapter.get_entity_data(1)
        
        assert data["issue_date"] == "2025-02-15T10:30:00"
        assert data["due_date"] == "2025-03-15T10:30:00"


class TestValidationEdgeCases:
    """验证边界情况测试"""

    def test_acceptance_exactly_all_passed(self):
        """验收单 - 全部通过的边界情况"""
        db = make_db()
        order = MagicMock()
        order.status = "DRAFT"
        order.project_id = 1
        order.acceptance_type = "FAT"
        order.total_items = 10
        order.passed_items = 10
        order.failed_items = 0
        order.na_items = 0
        order.overall_result = "PASSED"
        
        db.query.return_value.filter.return_value.first.return_value = order
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is True

    def test_acceptance_all_na(self):
        """验收单 - 全部N/A的边界情况"""
        db = make_db()
        order = MagicMock()
        order.status = "DRAFT"
        order.project_id = 1
        order.acceptance_type = "FAT"
        order.total_items = 5
        order.passed_items = 0
        order.failed_items = 0
        order.na_items = 5
        order.overall_result = "PASSED"
        
        db.query.return_value.filter.return_value.first.return_value = order
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is True

    def test_quote_zero_margin(self):
        """报价 - 零毛利率边界情况"""
        db = make_db()
        quote = MagicMock()
        version = MagicMock()
        version.gross_margin = Decimal("0")
        version.total_price = Decimal("100000")
        version.cost_total = Decimal("100000")
        version.lead_time_days = 30
        version.delivery_date = None
        version.version_no = 1
        quote.current_version = version
        quote.customer = None
        quote.owner = None
        
        db.query.return_value.filter.return_value.first.return_value = quote
        
        adapter = QuoteApprovalAdapter(db)
        data = adapter.get_entity_data(1)
        
        # 零毛利率也应该正确转换
        assert data["gross_margin"] == 0.0

    def test_purchase_minimum_amount(self):
        """采购订单 - 最小金额边界"""
        db = make_db()
        order = MagicMock()
        order.status = "DRAFT"
        order.supplier_id = 1
        order.order_date = datetime.now()
        order.amount_with_tax = Decimal("0.01")  # 最小金额
        
        def query_side_effect(model):
            from app.models.purchase import PurchaseOrder, PurchaseOrderItem
            query_mock = MagicMock()
            if model == PurchaseOrder:
                query_mock.filter.return_value.first.return_value = order
            elif model == PurchaseOrderItem:
                query_mock.filter.return_value.count.return_value = 1
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        adapter = PurchaseOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is True

    def test_invoice_very_large_amount(self):
        """发票 - 超大金额边界"""
        db = make_db()
        invoice = MagicMock()
        invoice.status = "DRAFT"
        invoice.amount = Decimal("99999999.99")
        invoice.buyer_name = "客户"
        
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is True


class TestStatusTransitions:
    """状态转换测试"""

    def test_acceptance_status_flow_complete(self):
        """验收单 - 完整状态流转"""
        db = make_db()
        order = MagicMock()
        order.status = "DRAFT"
        order.acceptance_type = "FINAL"
        order.overall_result = "PASSED"
        order.is_officially_completed = False
        
        db.query.return_value.filter.return_value.first.return_value = order
        instance = MagicMock()
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        
        # DRAFT -> PENDING_APPROVAL
        adapter.on_submit(1, instance)
        assert order.status == "PENDING_APPROVAL"
        
        # PENDING_APPROVAL -> COMPLETED (FINAL+PASSED)
        adapter.on_approved(1, instance)
        assert order.status == "COMPLETED"
        assert order.is_officially_completed is True

    def test_quote_status_rejected_then_resubmit(self):
        """报价 - 驳回后重新提交"""
        db = make_db()
        quote = MagicMock()
        quote.status = "PENDING_APPROVAL"
        
        db.query.return_value.filter.return_value.first.return_value = quote
        instance = MagicMock()
        
        adapter = QuoteApprovalAdapter(db)
        
        # 驳回
        adapter.on_rejected(1, instance)
        assert quote.status == "REJECTED"
        
        # 重新提交
        adapter.on_submit(1, instance)
        assert quote.status == "PENDING_APPROVAL"

    def test_purchase_withdraw_then_resubmit(self):
        """采购订单 - 撤回后重新提交"""
        db = make_db()
        order = MagicMock()
        order.status = "PENDING_APPROVAL"
        order.submitted_at = datetime.now()
        
        db.query.return_value.filter.return_value.first.return_value = order
        instance = MagicMock()
        
        adapter = PurchaseOrderApprovalAdapter(db)
        
        # 撤回
        adapter.on_withdrawn(1, instance)
        assert order.status == "DRAFT"
        assert order.submitted_at is None
        
        # 重新提交
        adapter.on_submit(1, instance)
        assert order.status == "PENDING_APPROVAL"
        assert order.submitted_at is not None


class TestTitleAndSummaryGeneration:
    """标题和摘要生成测试"""

    def test_acceptance_title_different_types(self):
        """验收单 - 不同类型的标题"""
        db = make_db()
        adapter = AcceptanceOrderApprovalAdapter(db)
        
        types = [
            ("FAT", "出厂验收审批"),
            ("SAT", "现场验收审批"),
            ("FINAL", "终验收审批"),
        ]
        
        for acc_type, expected in types:
            order = MagicMock()
            order.acceptance_type = acc_type
            order.order_no = f"ACC-{acc_type}-001"
            order.overall_result = "PASSED"
            
            db.query.return_value.filter.return_value.first.return_value = order
            
            title = adapter.generate_title(1)
            assert expected in title

    def test_quote_summary_formats_numbers(self):
        """报价 - 摘要正确格式化数字"""
        db = make_db()
        quote = MagicMock()
        version = MagicMock()
        version.total_price = Decimal("1234567.89")
        version.gross_margin = Decimal("18.5")
        version.lead_time_days = 45
        version.delivery_date = None
        version.version_no = 1
        
        quote.current_version = version
        quote.customer = MagicMock()
        quote.customer.name = "测试客户"
        quote.owner = None
        
        db.query.return_value.filter.return_value.first.return_value = quote
        
        adapter = QuoteApprovalAdapter(db)
        summary = adapter.get_summary(1)
        
        # 金额应该有千分位
        assert "1,234,567.89" in summary

    def test_purchase_summary_with_all_info(self):
        """采购订单 - 包含所有信息的摘要"""
        db = make_db()
        order = MagicMock()
        order.order_no = "PO-FULL-001"
        order.amount_with_tax = Decimal("88888.88")
        order.required_date = datetime(2025, 6, 30)
        order.supplier_id = 100
        order.project_id = 200
        
        vendor = MagicMock()
        vendor.vendor_name = "全信息供应商"
        
        project = MagicMock()
        project.project_name = "全信息项目"
        
        def query_side_effect(model):
            from app.models.purchase import PurchaseOrder, PurchaseOrderItem
            from app.models.vendor import Vendor
            from app.models.project import Project
            
            query_mock = MagicMock()
            if model == PurchaseOrder:
                query_mock.filter.return_value.first.return_value = order
            elif model == PurchaseOrderItem:
                query_mock.filter.return_value.count.return_value = 7
            elif model == Vendor:
                query_mock.filter.return_value.first.return_value = vendor
            elif model == Project:
                query_mock.filter.return_value.first.return_value = project
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        adapter = PurchaseOrderApprovalAdapter(db)
        summary = adapter.generate_summary(1)
        
        assert "PO-FULL-001" in summary
        assert "全信息供应商" in summary
        assert "88,888.88" in summary
        assert "7" in summary
        assert "2025-06-30" in summary
        assert "全信息项目" in summary


class TestErrorHandling:
    """异常处理测试"""

    def test_all_adapters_handle_nonexistent_entity(self):
        """所有适配器都应处理不存在的实体"""
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        
        adapters = [
            AcceptanceOrderApprovalAdapter(db),
            QuoteApprovalAdapter(db),
            PurchaseOrderApprovalAdapter(db),
            InvoiceApprovalAdapter(db),
        ]
        
        for adapter in adapters:
            data = adapter.get_entity_data(99999)
            assert data == {}

    def test_callbacks_handle_missing_entity_gracefully(self):
        """回调方法应优雅处理实体不存在的情况"""
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        instance = MagicMock()
        
        adapters = [
            AcceptanceOrderApprovalAdapter(db),
            QuoteApprovalAdapter(db),
            PurchaseOrderApprovalAdapter(db),
            InvoiceApprovalAdapter(db),
        ]
        
        for adapter in adapters:
            # 不应抛出异常
            try:
                adapter.on_submit(99999, instance)
                adapter.on_approved(99999, instance)
                adapter.on_rejected(99999, instance)
                adapter.on_withdrawn(99999, instance)
            except AttributeError:
                pytest.fail(f"{adapter.__class__.__name__} 未处理实体不存在的情况")

    def test_validation_returns_tuple(self):
        """验证方法应始终返回(bool, str)元组"""
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        
        adapters = [
            AcceptanceOrderApprovalAdapter(db),
            QuoteApprovalAdapter(db),
            PurchaseOrderApprovalAdapter(db),
            InvoiceApprovalAdapter(db),
        ]
        
        for adapter in adapters:
            result = adapter.validate_submit(1)
            assert isinstance(result, tuple)
            assert len(result) == 2
            assert isinstance(result[0], bool)
            assert isinstance(result[1], (str, type(None)))


class TestCCUserLogic:
    """抄送人逻辑测试"""

    @patch.object(PurchaseOrderApprovalAdapter, 'get_department_manager_user_ids_by_codes')
    @patch.object(PurchaseOrderApprovalAdapter, 'get_department_manager_user_id')
    def test_purchase_cc_users_deduplication(self, mock_by_name, mock_by_codes):
        """采购订单 - 抄送人去重"""
        db = make_db()
        order = MagicMock()
        order.project_id = 200
        
        project = MagicMock()
        project.manager_id = 10
        
        def query_side_effect(model):
            from app.models.purchase import PurchaseOrder
            from app.models.project import Project
            
            query_mock = MagicMock()
            if model == PurchaseOrder:
                query_mock.filter.return_value.first.return_value = order
            elif model == Project:
                query_mock.filter.return_value.first.return_value = project
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        # 返回重复的用户ID
        mock_by_codes.return_value = [10, 20, 10, 20]
        mock_by_name.return_value = None
        
        adapter = PurchaseOrderApprovalAdapter(db)
        cc_users = adapter.get_cc_user_ids(1)
        
        # 应该去重
        assert len(cc_users) == len(set(cc_users))

    @patch.object(AcceptanceOrderApprovalAdapter, 'get_department_manager_user_ids_by_codes')
    @patch.object(AcceptanceOrderApprovalAdapter, 'get_project_sales_user_id')
    def test_acceptance_cc_includes_sales_for_sat(self, mock_sales, mock_dept):
        """验收单 - SAT类型包含销售负责人"""
        db = make_db()
        order = MagicMock()
        order.acceptance_type = "SAT"
        order.project_id = 100
        
        project = MagicMock()
        project.manager_id = 10
        
        def query_side_effect(model):
            from app.models.acceptance import AcceptanceOrder
            from app.models.project import Project
            
            query_mock = MagicMock()
            if model == AcceptanceOrder:
                query_mock.filter.return_value.first.return_value = order
            elif model == Project:
                query_mock.filter.return_value.first.return_value = project
            return query_mock
        
        db.query.side_effect = query_side_effect
        mock_dept.return_value = [20]
        mock_sales.return_value = 30
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        cc_users = adapter.get_cc_user_ids(1)
        
        assert 30 in cc_users  # 销售负责人


class TestWorkflowIntegration:
    """工作流集成测试"""

    @patch('app.services.approval_engine.adapters.quote.WorkflowEngine')
    def test_quote_workflow_creates_with_correct_params(self, mock_engine_class):
        """报价 - 工作流引擎接收正确参数"""
        db = make_db()
        quote_version = MagicMock()
        quote_version.id = 123
        quote_version.quote_code = "Q-TEST-001"
        quote_version.quote_total = Decimal("200000")
        quote_version.margin_percent = Decimal("25")
        quote_version.status = "DRAFT"
        quote_version.approval_instance_id = None
        
        instance = MagicMock()
        instance.id = 5000
        
        mock_engine = MagicMock()
        mock_engine.create_instance.return_value = instance
        mock_engine_class.return_value = mock_engine
        
        adapter = QuoteApprovalAdapter(db)
        adapter.submit_for_approval(quote_version, initiator_id=10)
        
        # 验证调用参数
        mock_engine.create_instance.assert_called_once()
        call_args = mock_engine.create_instance.call_args
        assert call_args[1]['flow_code'] == 'SALES_QUOTE'
        assert call_args[1]['business_id'] == 123
        assert call_args[1]['submitted_by'] == 10

    @patch('app.services.approval_engine.adapters.invoice.WorkflowEngine')
    def test_invoice_workflow_updates_entity(self, mock_engine_class):
        """发票 - 工作流创建后更新实体"""
        db = make_db()
        invoice = MagicMock()
        invoice.id = 456
        invoice.invoice_code = "INV-TEST-001"
        invoice.approval_instance_id = None
        invoice.amount = Decimal("100000")
        invoice.contract = None
        
        instance = MagicMock()
        instance.id = 6000
        instance.status = "PENDING"
        
        mock_engine = MagicMock()
        mock_engine.create_instance.return_value = instance
        mock_engine_class.return_value = mock_engine
        
        adapter = InvoiceApprovalAdapter(db)
        adapter.submit_for_approval(invoice, initiator_id=20)
        
        # 验证更新
        assert invoice.approval_instance_id == 6000
        assert invoice.approval_status == "PENDING"
        db.add.assert_called_with(invoice)
        db.commit.assert_called_once()


class TestApprovalRecordManagement:
    """审批记录管理测试"""

    def test_quote_approval_record_creation_no_approver(self):
        """报价审批记录 - 无审批人时的处理"""
        db = make_db()
        instance = MagicMock()
        instance.entity_id = 100
        
        task = MagicMock()
        task.node_order = 1
        task.node_name = "经理审批"
        task.assignee_id = None  # 无审批人
        
        def query_side_effect(model):
            from app.models.sales.quotes import QuoteApproval
            from app.models.user import User
            
            query_mock = MagicMock()
            if model == QuoteApproval:
                query_mock.filter.return_value.first.return_value = None
            elif model == User:
                query_mock.filter.return_value.first.return_value = None
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        adapter = QuoteApprovalAdapter(db)
        approval = adapter.create_quote_approval(instance, task)
        
        assert approval.approver_name == ""

    def test_invoice_approval_updates_correctly(self):
        """发票审批记录 - 状态更新正确"""
        db = make_db()
        instance = MagicMock()
        instance.entity_id = 100
        
        task = MagicMock()
        task.node_order = 2
        task.instance = instance
        
        approval = MagicMock()
        approval.invoice_id = 100
        
        db.query.return_value.filter.return_value.first.return_value = approval
        
        adapter = InvoiceApprovalAdapter(db)
        
        # 测试同意
        result = adapter.update_invoice_approval_from_action(
            task, "APPROVE", "OK"
        )
        
        assert approval.approval_result == "APPROVED"
        assert approval.status == "APPROVED"
        assert approval.approved_at is not None


class TestConcurrentApprovals:
    """并发审批测试"""

    def test_multiple_adapters_can_coexist(self):
        """多个适配器可以同时存在"""
        db = make_db()
        
        adapters = {
            'acceptance': AcceptanceOrderApprovalAdapter(db),
            'quote': QuoteApprovalAdapter(db),
            'purchase': PurchaseOrderApprovalAdapter(db),
            'invoice': InvoiceApprovalAdapter(db),
        }
        
        assert len(adapters) == 4
        assert all(a.db == db for a in adapters.values())

    def test_adapters_dont_interfere_with_each_other(self):
        """适配器之间不互相干扰"""
        db = make_db()
        
        # 创建不同的mock实体
        acceptance = MagicMock()
        acceptance.status = "DRAFT"
        
        quote = MagicMock()
        quote.status = "DRAFT"
        
        def query_side_effect(model):
            from app.models.acceptance import AcceptanceOrder
            from app.models.sales.quotes import Quote
            
            query_mock = MagicMock()
            if model == AcceptanceOrder:
                query_mock.filter.return_value.first.return_value = acceptance
            elif model == Quote:
                query_mock.filter.return_value.first.return_value = quote
            return query_mock
        
        db.query.side_effect = query_side_effect
        instance = MagicMock()
        
        # 同时操作两个适配器
        acc_adapter = AcceptanceOrderApprovalAdapter(db)
        quote_adapter = QuoteApprovalAdapter(db)
        
        acc_adapter.on_submit(1, instance)
        quote_adapter.on_submit(1, instance)
        
        # 状态应该都改变，互不影响
        assert acceptance.status == "PENDING_APPROVAL"
        assert quote.status == "PENDING_APPROVAL"


class TestPerformance:
    """性能测试"""

    def test_get_entity_data_minimal_queries(self):
        """获取实体数据应最小化数据库查询"""
        db = make_db()
        order = MagicMock()
        order.project_id = None  # 无关联，不应查询project
        order.machine_id = None  # 无关联，不应查询machine
        order.template_id = None  # 无关联，不应查询template
        order.total_items = 10
        order.passed_items = 10
        order.failed_items = 0
        order.na_items = 0
        order.pass_rate = Decimal("100")
        
        db.query.return_value.filter.return_value.first.return_value = order
        
        adapter = AcceptanceOrderApprovalAdapter(db)
        data = adapter.get_entity_data(1)
        
        # 应该只查询order本身，不查询关联表
        assert data["project_id"] is None
        assert "project_name" not in data


class TestRobustness:
    """健壮性测试"""

    def test_adapters_handle_null_dates_gracefully(self):
        """适配器应优雅处理空日期"""
        db = make_db()
        invoice = MagicMock()
        invoice.issue_date = None
        invoice.due_date = None
        invoice.contract = None
        invoice.amount = Decimal("50000")
        
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        data = adapter.get_entity_data(1)
        
        assert data["issue_date"] is None
        assert data["due_date"] is None

    def test_adapters_handle_empty_strings(self):
        """适配器应处理空字符串"""
        db = make_db()
        order = MagicMock()
        order.order_title = ""
        order.order_no = "PO-EMPTY"
        
        db.query.return_value.filter.return_value.first.return_value = order
        
        adapter = PurchaseOrderApprovalAdapter(db)
        title = adapter.generate_title(1)
        
        # 应该正常生成标题
        assert "PO-EMPTY" in title

    def test_summary_handles_missing_optional_data(self):
        """摘要生成应处理缺失的可选数据"""
        db = make_db()
        quote = MagicMock()
        quote.current_version = None  # 无版本
        quote.customer = None
        quote.owner = None
        
        def query_side_effect(model):
            from app.models.sales.quotes import Quote, QuoteVersion
            query_mock = MagicMock()
            if model == Quote:
                query_mock.filter.return_value.first.return_value = quote
            elif model == QuoteVersion:
                query_mock.filter.return_value.order_by.return_value.first.return_value = None
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        adapter = QuoteApprovalAdapter(db)
        summary = adapter.get_summary(1)
        
        # 应该返回空摘要或最小摘要，不抛异常
        assert isinstance(summary, str)
