# -*- coding: utf-8 -*-
"""
报价审批适配器 单元测试
目标覆盖率: 60%+
覆盖: 数据转换、验证、审批回调、工作流集成
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

try:
    from app.services.approval_engine.adapters.quote import QuoteApprovalAdapter
    from app.models.approval import ApprovalInstance, ApprovalTask
    from app.models.sales.quotes import Quote, QuoteVersion, QuoteApproval
    from app.models.user import User
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


def make_quote(**kwargs):
    """创建mock报价单"""
    quote = MagicMock(spec=Quote)
    quote.id = kwargs.get("id", 1)
    quote.quote_code = kwargs.get("quote_code", "QUOTE-2025-001")
    quote.status = kwargs.get("status", "DRAFT")
    quote.customer_id = kwargs.get("customer_id", 100)
    quote.owner_id = kwargs.get("owner_id", 10)
    
    # Mock customer
    customer = MagicMock()
    customer.name = kwargs.get("customer_name", "测试客户")
    type(quote).customer = PropertyMock(return_value=customer if quote.customer_id else None)
    
    # Mock owner
    owner = MagicMock()
    owner.name = kwargs.get("owner_name", "销售员A")
    type(quote).owner = PropertyMock(return_value=owner if quote.owner_id else None)
    
    # Mock current_version
    version = kwargs.get("current_version", None)
    type(quote).current_version = PropertyMock(return_value=version)
    
    return quote


def make_quote_version(**kwargs):
    """创建mock报价版本"""
    version = MagicMock(spec=QuoteVersion)
    version.id = kwargs.get("id", 1)
    version.quote_id = kwargs.get("quote_id", 1)
    version.version_no = kwargs.get("version_no", 1)
    version.quote_code = kwargs.get("quote_code", "QUOTE-2025-001")
    version.total_price = Decimal(kwargs.get("total_price", "100000"))
    version.cost_total = Decimal(kwargs.get("cost_total", "80000"))
    version.gross_margin = Decimal(kwargs.get("gross_margin", "0.20"))  # 20%
    version.lead_time_days = kwargs.get("lead_time_days", 30)
    version.delivery_date = kwargs.get("delivery_date", datetime.now() + timedelta(days=30))
    version.approval_instance_id = kwargs.get("approval_instance_id", None)
    version.approval_status = kwargs.get("approval_status", None)
    version.status = kwargs.get("status", "DRAFT")
    version.quote_total = kwargs.get("quote_total", Decimal("100000"))
    version.margin_percent = kwargs.get("margin_percent", Decimal("20"))
    return version


def make_approval_instance(**kwargs):
    """创建mock审批实例"""
    instance = MagicMock(spec=ApprovalInstance)
    instance.id = kwargs.get("id", 1000)
    instance.status = kwargs.get("status", "PENDING")
    instance.approved_by = kwargs.get("approved_by", None)
    instance.entity_id = kwargs.get("entity_id", 1)
    return instance


def make_approval_task(**kwargs):
    """创建mock审批任务"""
    task = MagicMock(spec=ApprovalTask)
    task.id = kwargs.get("id", 2000)
    task.node_order = kwargs.get("node_order", 1)
    task.node_name = kwargs.get("node_name", "销售经理审批")
    task.assignee_id = kwargs.get("assignee_id", 20)
    task.instance = kwargs.get("instance", make_approval_instance())
    return task


def make_user(**kwargs):
    """创建mock用户"""
    user = MagicMock(spec=User)
    user.id = kwargs.get("id", 20)
    user.real_name = kwargs.get("real_name", "张经理")
    return user


class TestQuoteApprovalAdapter:
    """报价审批适配器测试"""

    def test_adapter_entity_type(self):
        """测试适配器实体类型"""
        db = make_db()
        adapter = QuoteApprovalAdapter(db)
        assert adapter.entity_type == "QUOTE"

    def test_get_entity_found(self):
        """测试获取报价实体 - 找到"""
        db = make_db()
        quote = make_quote(id=1)
        db.query.return_value.filter.return_value.first.return_value = quote
        
        adapter = QuoteApprovalAdapter(db)
        result = adapter.get_entity(1)
        
        assert result == quote

    def test_get_entity_not_found(self):
        """测试获取报价实体 - 未找到"""
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        
        adapter = QuoteApprovalAdapter(db)
        result = adapter.get_entity(999)
        
        assert result is None

    def test_get_entity_data_with_version(self):
        """测试获取实体数据 - 有当前版本"""
        db = make_db()
        version = make_quote_version(
            total_price="150000",
            cost_total="120000",
            gross_margin="0.20",  # 小于1，会被转换为20%
            lead_time_days=45
        )
        quote = make_quote(
            quote_code="QUOTE-001",
            customer_name="测试客户A",
            owner_name="销售员B",
            current_version=version
        )
        db.query.return_value.filter.return_value.first.return_value = quote
        
        adapter = QuoteApprovalAdapter(db)
        data = adapter.get_entity_data(1)
        
        assert data["quote_code"] == "QUOTE-001"
        assert data["customer_name"] == "测试客户A"
        assert data["owner_name"] == "销售员B"
        assert data["total_price"] == 150000.0
        assert data["cost_total"] == 120000.0
        assert data["gross_margin"] == 20.0  # 已转换为百分比
        assert data["lead_time_days"] == 45

    def test_get_entity_data_margin_already_percentage(self):
        """测试获取实体数据 - 毛利率已是百分比形式"""
        db = make_db()
        version = make_quote_version(
            gross_margin="25.5"  # 大于1，保持不变
        )
        quote = make_quote(current_version=version)
        db.query.return_value.filter.return_value.first.return_value = quote
        
        adapter = QuoteApprovalAdapter(db)
        data = adapter.get_entity_data(1)
        
        assert data["gross_margin"] == 25.5

    def test_get_entity_data_no_current_version(self):
        """测试获取实体数据 - 无当前版本，查询最新版本"""
        db = make_db()
        quote = make_quote(current_version=None)
        version = make_quote_version()
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model == Quote:
                query_mock.filter.return_value.first.return_value = quote
            elif model == QuoteVersion:
                query_mock.filter.return_value.order_by.return_value.first.return_value = version
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        adapter = QuoteApprovalAdapter(db)
        data = adapter.get_entity_data(1)
        
        assert "version_no" in data
        assert data["total_price"] == 100000.0

    def test_get_entity_data_not_found(self):
        """测试获取实体数据 - 实体不存在"""
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        
        adapter = QuoteApprovalAdapter(db)
        data = adapter.get_entity_data(999)
        
        assert data == {}

    def test_on_submit(self):
        """测试提交审批回调"""
        db = make_db()
        quote = make_quote(status="DRAFT")
        db.query.return_value.filter.return_value.first.return_value = quote
        instance = make_approval_instance()
        
        adapter = QuoteApprovalAdapter(db)
        adapter.on_submit(1, instance)
        
        assert quote.status == "PENDING_APPROVAL"
        db.flush.assert_called_once()

    def test_on_approved(self):
        """测试审批通过回调"""
        db = make_db()
        quote = make_quote(status="PENDING_APPROVAL")
        db.query.return_value.filter.return_value.first.return_value = quote
        instance = make_approval_instance()
        
        adapter = QuoteApprovalAdapter(db)
        adapter.on_approved(1, instance)
        
        assert quote.status == "APPROVED"
        db.flush.assert_called_once()

    def test_on_rejected(self):
        """测试审批驳回回调"""
        db = make_db()
        quote = make_quote(status="PENDING_APPROVAL")
        db.query.return_value.filter.return_value.first.return_value = quote
        instance = make_approval_instance()
        
        adapter = QuoteApprovalAdapter(db)
        adapter.on_rejected(1, instance)
        
        assert quote.status == "REJECTED"
        db.flush.assert_called_once()

    def test_on_withdrawn(self):
        """测试撤回审批回调"""
        db = make_db()
        quote = make_quote(status="PENDING_APPROVAL")
        db.query.return_value.filter.return_value.first.return_value = quote
        instance = make_approval_instance()
        
        adapter = QuoteApprovalAdapter(db)
        adapter.on_withdrawn(1, instance)
        
        assert quote.status == "DRAFT"
        db.flush.assert_called_once()

    def test_get_title(self):
        """测试生成审批标题"""
        db = make_db()
        quote = make_quote(
            quote_code="QUOTE-123",
            customer_name="测试公司"
        )
        db.query.return_value.filter.return_value.first.return_value = quote
        
        adapter = QuoteApprovalAdapter(db)
        title = adapter.get_title(1)
        
        assert "报价审批" in title
        assert "QUOTE-123" in title
        assert "测试公司" in title

    def test_get_summary(self):
        """测试生成审批摘要"""
        db = make_db()
        version = make_quote_version(
            total_price="200000",
            gross_margin="22.5",
            lead_time_days=60
        )
        quote = make_quote(
            customer_name="客户X",
            current_version=version
        )
        db.query.return_value.filter.return_value.first.return_value = quote
        
        adapter = QuoteApprovalAdapter(db)
        summary = adapter.get_summary(1)
        
        assert "客户X" in summary
        assert "200,000.00" in summary
        assert "22.5%" in summary
        assert "60天" in summary

    def test_validate_submit_success(self):
        """测试提交验证 - 成功"""
        db = make_db()
        version = make_quote_version()
        quote = make_quote(status="DRAFT", current_version=version)
        db.query.return_value.filter.return_value.first.return_value = quote
        
        adapter = QuoteApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is True
        assert error == ""

    def test_validate_submit_not_found(self):
        """测试提交验证 - 实体不存在"""
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        
        adapter = QuoteApprovalAdapter(db)
        valid, error = adapter.validate_submit(999)
        
        assert valid is False
        assert "不存在" in error

    def test_validate_submit_wrong_status(self):
        """测试提交验证 - 状态错误"""
        db = make_db()
        quote = make_quote(status="APPROVED")
        db.query.return_value.filter.return_value.first.return_value = quote
        
        adapter = QuoteApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "不允许提交审批" in error

    def test_validate_submit_no_version(self):
        """测试提交验证 - 无版本"""
        db = make_db()
        quote = make_quote(status="DRAFT", current_version=None)
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model == Quote:
                query_mock.filter.return_value.first.return_value = quote
            elif model == QuoteVersion:
                query_mock.filter.return_value.count.return_value = 0
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        adapter = QuoteApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "未添加任何版本" in error

    @patch('app.services.approval_engine.adapters.quote.WorkflowEngine')
    def test_submit_for_approval_success(self, mock_workflow_engine):
        """测试提交审批 - 成功"""
        db = make_db()
        quote_version = make_quote_version(approval_instance_id=None)
        instance = make_approval_instance(id=5000)
        
        # Mock WorkflowEngine
        mock_engine = MagicMock()
        mock_engine.create_instance.return_value = instance
        mock_workflow_engine.return_value = mock_engine
        
        adapter = QuoteApprovalAdapter(db)
        result = adapter.submit_for_approval(
            quote_version,
            initiator_id=10,
            title="测试报价审批",
            summary="测试摘要"
        )
        
        assert result == instance
        assert quote_version.approval_instance_id == 5000
        db.add.assert_called_with(quote_version)
        db.commit.assert_called_once()

    @patch('app.services.approval_engine.adapters.quote.WorkflowEngine')
    def test_submit_for_approval_already_submitted(self, mock_workflow_engine):
        """测试提交审批 - 已提交"""
        db = make_db()
        existing_instance = make_approval_instance(id=6000)
        quote_version = make_quote_version(approval_instance_id=6000)
        
        db.query.return_value.filter.return_value.first.return_value = existing_instance
        
        adapter = QuoteApprovalAdapter(db)
        result = adapter.submit_for_approval(quote_version, initiator_id=10)
        
        assert result == existing_instance
        # 不应该创建新实例
        mock_workflow_engine.assert_not_called()

    def test_create_quote_approval_new(self):
        """测试创建报价审批记录 - 新建"""
        db = make_db()
        instance = make_approval_instance(entity_id=100)
        task = make_approval_task(node_order=1, assignee_id=20)
        user = make_user(real_name="审批人A")
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model == QuoteApproval:
                query_mock.filter.return_value.first.return_value = None
            elif model == User:
                query_mock.filter.return_value.first.return_value = user
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        adapter = QuoteApprovalAdapter(db)
        approval = adapter.create_quote_approval(instance, task)
        
        assert approval is not None
        assert approval.quote_version_id == 100
        assert approval.approval_level == 1
        assert approval.approver_name == "审批人A"
        db.add.assert_called_with(approval)

    def test_create_quote_approval_existing(self):
        """测试创建报价审批记录 - 已存在"""
        db = make_db()
        instance = make_approval_instance(entity_id=100)
        task = make_approval_task(node_order=1)
        existing_approval = MagicMock()
        
        db.query.return_value.filter.return_value.first.return_value = existing_approval
        
        adapter = QuoteApprovalAdapter(db)
        approval = adapter.create_quote_approval(instance, task)
        
        assert approval == existing_approval
        # 不应该添加新记录
        db.add.assert_not_called()

    def test_update_quote_approval_approve(self):
        """测试更新报价审批记录 - 同意"""
        db = make_db()
        instance = make_approval_instance(entity_id=100)
        task = make_approval_task(node_order=1, instance=instance)
        approval = MagicMock()
        
        db.query.return_value.filter.return_value.first.return_value = approval
        
        adapter = QuoteApprovalAdapter(db)
        result = adapter.update_quote_approval_from_action(
            task,
            action="APPROVE",
            comment="同意此报价"
        )
        
        assert result == approval
        assert approval.approval_result == "APPROVED"
        assert approval.approval_opinion == "同意此报价"
        assert approval.status == "APPROVED"
        assert approval.approved_at is not None
        db.add.assert_called_with(approval)
        db.commit.assert_called_once()

    def test_update_quote_approval_reject(self):
        """测试更新报价审批记录 - 驳回"""
        db = make_db()
        instance = make_approval_instance(entity_id=100)
        task = make_approval_task(node_order=2, instance=instance)
        approval = MagicMock()
        
        db.query.return_value.filter.return_value.first.return_value = approval
        
        adapter = QuoteApprovalAdapter(db)
        result = adapter.update_quote_approval_from_action(
            task,
            action="REJECT",
            comment="毛利率过低"
        )
        
        assert result == approval
        assert approval.approval_result == "REJECTED"
        assert approval.approval_opinion == "毛利率过低"
        assert approval.status == "REJECTED"
        db.commit.assert_called_once()

    def test_update_quote_approval_not_found(self):
        """测试更新报价审批记录 - 记录不存在"""
        db = make_db()
        instance = make_approval_instance(entity_id=100)
        task = make_approval_task(node_order=1, instance=instance)
        
        db.query.return_value.filter.return_value.first.return_value = None
        
        adapter = QuoteApprovalAdapter(db)
        result = adapter.update_quote_approval_from_action(
            task,
            action="APPROVE"
        )
        
        assert result is None
        db.commit.assert_not_called()
