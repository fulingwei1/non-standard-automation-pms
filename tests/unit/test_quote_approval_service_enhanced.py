# -*- coding: utf-8 -*-
"""
报价审批服务增强测试

覆盖 quote_approval_service.py 的核心功能测试
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from app.services.quote_approval.quote_approval_service import QuoteApprovalService
from app.models.approval import ApprovalInstance, ApprovalTask
from app.models.sales.quotes import Quote, QuoteVersion


@pytest.fixture
def db_session():
    """模拟数据库会话"""
    return MagicMock()


@pytest.fixture
def service(db_session):
    """创建测试服务实例"""
    return QuoteApprovalService(db_session)


@pytest.fixture
def mock_quote():
    """模拟报价对象"""
    quote = MagicMock(spec=Quote)
    quote.id = 1
    quote.quote_code = "Q2026-001"
    quote.status = "DRAFT"
    quote.customer_id = 100
    
    # 模拟客户
    customer = MagicMock()
    customer.name = "测试客户A"
    quote.customer = customer
    
    return quote


@pytest.fixture
def mock_version():
    """模拟报价版本对象"""
    version = MagicMock(spec=QuoteVersion)
    version.id = 10
    version.version_no = "V1.0"
    version.total_price = Decimal("100000.00")
    version.cost_total = Decimal("70000.00")
    version.gross_margin = Decimal("30.00")
    version.lead_time_days = 30
    return version


@pytest.fixture
def mock_approval_instance():
    """模拟审批实例"""
    instance = MagicMock(spec=ApprovalInstance)
    instance.id = 50
    instance.entity_type = "QUOTE"
    instance.entity_id = 1
    instance.status = "PENDING"
    instance.urgency = "NORMAL"
    instance.initiator_id = 200
    instance.created_at = datetime(2026, 2, 20, 10, 0, 0)
    instance.completed_at = None
    
    # 模拟发起人
    initiator = MagicMock()
    initiator.real_name = "张三"
    instance.initiator = initiator
    
    return instance


@pytest.fixture
def mock_approval_task():
    """模拟审批任务"""
    task = MagicMock(spec=ApprovalTask)
    task.id = 80
    task.instance_id = 50
    task.status = "PENDING"
    task.action = None
    task.comment = None
    task.created_at = datetime(2026, 2, 20, 10, 0, 0)
    task.completed_at = None
    
    # 模拟节点
    node = MagicMock()
    node.node_name = "部门经理审批"
    task.node = node
    
    # 模拟审批人
    assignee = MagicMock()
    assignee.real_name = "李四"
    task.assignee = assignee
    
    return task


# =========================== submit_quotes_for_approval 测试 ===========================

def test_submit_single_quote_success(service, db_session, mock_quote, mock_version):
    """测试成功提交单个报价审批"""
    # 配置 mock
    db_session.query.return_value.filter.return_value.first.return_value = mock_quote
    mock_quote.current_version = mock_version
    
    # 模拟审批引擎
    mock_instance = MagicMock()
    mock_instance.id = 50
    service.approval_engine.submit = MagicMock(return_value=mock_instance)
    
    # 执行
    result = service.submit_quotes_for_approval(
        quote_ids=[1],
        initiator_id=200,
        urgency="HIGH"
    )
    
    # 验证
    assert len(result["success"]) == 1
    assert len(result["errors"]) == 0
    assert result["success"][0]["quote_id"] == 1
    assert result["success"][0]["instance_id"] == 50
    assert result["success"][0]["status"] == "submitted"
    
    # 验证调用
    service.approval_engine.submit.assert_called_once()
    call_args = service.approval_engine.submit.call_args[1]
    assert call_args["template_code"] == "SALES_QUOTE_APPROVAL"
    assert call_args["entity_type"] == "QUOTE"
    assert call_args["entity_id"] == 1
    assert call_args["urgency"] == "HIGH"


def test_submit_quote_not_found(service, db_session):
    """测试提交不存在的报价"""
    db_session.query.return_value.filter.return_value.first.return_value = None
    
    result = service.submit_quotes_for_approval(
        quote_ids=[999],
        initiator_id=200
    )
    
    assert len(result["success"]) == 0
    assert len(result["errors"]) == 1
    assert result["errors"][0]["quote_id"] == 999
    assert "不存在" in result["errors"][0]["error"]


def test_submit_quote_invalid_status(service, db_session, mock_quote):
    """测试提交不允许状态的报价"""
    mock_quote.status = "APPROVED"
    db_session.query.return_value.filter.return_value.first.return_value = mock_quote
    
    result = service.submit_quotes_for_approval(
        quote_ids=[1],
        initiator_id=200
    )
    
    assert len(result["success"]) == 0
    assert len(result["errors"]) == 1
    assert "不允许提交审批" in result["errors"][0]["error"]


def test_submit_quote_no_version(service, db_session, mock_quote):
    """测试提交没有版本的报价"""
    mock_quote.current_version = None
    db_session.query.return_value.filter.return_value.first.return_value = mock_quote
    db_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
    
    result = service.submit_quotes_for_approval(
        quote_ids=[1],
        initiator_id=200
    )
    
    assert len(result["success"]) == 0
    assert len(result["errors"]) == 1
    assert "没有版本" in result["errors"][0]["error"]


def test_submit_batch_quotes_mixed_results(service, db_session, mock_quote, mock_version):
    """测试批量提交，部分成功部分失败"""
    def mock_query_filter_first(*args, **kwargs):
        # 根据不同的查询返回不同的结果
        if hasattr(args[0], 'id') and args[0].id == 1:
            return mock_quote
        return None
    
    db_session.query.return_value.filter.return_value.first.side_effect = [
        mock_quote,  # quote_id=1 存在
        None,        # quote_id=2 不存在
    ]
    mock_quote.current_version = mock_version
    
    mock_instance = MagicMock()
    mock_instance.id = 50
    service.approval_engine.submit = MagicMock(return_value=mock_instance)
    
    result = service.submit_quotes_for_approval(
        quote_ids=[1, 2],
        initiator_id=200
    )
    
    assert len(result["success"]) == 1
    assert len(result["errors"]) == 1
    assert result["success"][0]["quote_id"] == 1
    assert result["errors"][0]["quote_id"] == 2


def test_submit_with_specified_version_ids(service, db_session, mock_quote, mock_version):
    """测试使用指定版本ID提交"""
    # 配置多个查询返回
    quote_query = MagicMock()
    quote_query.first.return_value = mock_quote
    
    version_query = MagicMock()
    version_query.first.return_value = mock_version
    
    # 第一次查询报价，第二次查询版本
    db_session.query.return_value.filter.side_effect = [
        quote_query,
        version_query
    ]
    
    mock_instance = MagicMock()
    mock_instance.id = 50
    service.approval_engine.submit = MagicMock(return_value=mock_instance)
    
    result = service.submit_quotes_for_approval(
        quote_ids=[1],
        initiator_id=200,
        version_ids=[10]
    )
    
    assert len(result["success"]) == 1
    assert result["success"][0]["version_no"] == "V1.0"


def test_submit_with_comment(service, db_session, mock_quote, mock_version):
    """测试提交时添加备注"""
    db_session.query.return_value.filter.return_value.first.return_value = mock_quote
    mock_quote.current_version = mock_version
    
    mock_instance = MagicMock()
    mock_instance.id = 50
    service.approval_engine.submit = MagicMock(return_value=mock_instance)
    
    result = service.submit_quotes_for_approval(
        quote_ids=[1],
        initiator_id=200,
        comment="请尽快审批"
    )
    
    assert len(result["success"]) == 1


def test_submit_approval_engine_exception(service, db_session, mock_quote, mock_version):
    """测试审批引擎抛出异常"""
    db_session.query.return_value.filter.return_value.first.return_value = mock_quote
    mock_quote.current_version = mock_version
    
    service.approval_engine.submit = MagicMock(
        side_effect=Exception("审批引擎错误")
    )
    
    result = service.submit_quotes_for_approval(
        quote_ids=[1],
        initiator_id=200
    )
    
    assert len(result["success"]) == 0
    assert len(result["errors"]) == 1
    assert "审批引擎错误" in result["errors"][0]["error"]


# =========================== get_pending_tasks 测试 ===========================

def test_get_pending_tasks_success(service, mock_approval_task, mock_approval_instance, mock_quote, mock_version):
    """测试获取待审批任务列表"""
    mock_approval_task.instance = mock_approval_instance
    service.approval_engine.get_pending_tasks = MagicMock(
        return_value=[mock_approval_task]
    )
    
    # 模拟查询报价
    db_query = MagicMock()
    db_query.first.return_value = mock_quote
    service.db.query.return_value.filter.return_value = db_query
    
    mock_quote.customer = MagicMock()
    mock_quote.customer.name = "客户A"
    mock_quote.current_version = mock_version
    
    result = service.get_pending_tasks(user_id=300)
    
    assert result["total"] == 1
    assert len(result["items"]) == 1
    assert result["items"][0]["task_id"] == 80
    assert result["items"][0]["quote_code"] == "Q2026-001"
    assert result["items"][0]["customer_name"] == "客户A"


def test_get_pending_tasks_with_pagination(service, mock_approval_task, mock_approval_instance):
    """测试待审批任务分页"""
    tasks = [MagicMock(spec=ApprovalTask) for _ in range(25)]
    for i, task in enumerate(tasks):
        task.id = i + 1
        task.instance = mock_approval_instance
    
    service.approval_engine.get_pending_tasks = MagicMock(return_value=tasks)
    
    # 模拟查询返回
    service.db.query.return_value.filter.return_value.first.return_value = MagicMock()
    
    result = service.get_pending_tasks(user_id=300, offset=0, limit=10)
    
    assert result["total"] == 25
    assert len(result["items"]) == 10


def test_get_pending_tasks_filter_by_customer(service, mock_approval_task, mock_approval_instance, mock_quote):
    """测试按客户筛选待审批任务"""
    mock_approval_task.instance = mock_approval_instance
    service.approval_engine.get_pending_tasks = MagicMock(
        return_value=[mock_approval_task]
    )
    
    mock_quote.customer_id = 100
    service.db.query.return_value.filter.return_value.first.return_value = mock_quote
    
    result = service.get_pending_tasks(user_id=300, customer_id=100)
    
    assert result["total"] == 1


def test_get_pending_tasks_customer_filter_excludes(service, mock_approval_task, mock_approval_instance, mock_quote):
    """测试客户筛选排除不匹配的任务"""
    mock_approval_task.instance = mock_approval_instance
    service.approval_engine.get_pending_tasks = MagicMock(
        return_value=[mock_approval_task]
    )
    
    mock_quote.customer_id = 100
    service.db.query.return_value.filter.return_value.first.return_value = mock_quote
    
    result = service.get_pending_tasks(user_id=300, customer_id=999)
    
    assert result["total"] == 0


def test_get_pending_tasks_empty_result(service):
    """测试没有待审批任务"""
    service.approval_engine.get_pending_tasks = MagicMock(return_value=[])
    
    result = service.get_pending_tasks(user_id=300)
    
    assert result["total"] == 0
    assert result["items"] == []


# =========================== perform_action 测试 ===========================

def test_perform_action_approve(service):
    """测试执行审批通过操作"""
    mock_result = MagicMock()
    mock_result.status = "APPROVED"
    service.approval_engine.approve = MagicMock(return_value=mock_result)
    
    result = service.perform_action(
        task_id=80,
        action="approve",
        approver_id=300,
        comment="同意"
    )
    
    assert result["task_id"] == 80
    assert result["action"] == "approve"
    assert result["instance_status"] == "APPROVED"
    
    service.approval_engine.approve.assert_called_once_with(
        task_id=80,
        approver_id=300,
        comment="同意"
    )


def test_perform_action_reject(service):
    """测试执行审批拒绝操作"""
    mock_result = MagicMock()
    mock_result.status = "REJECTED"
    service.approval_engine.reject = MagicMock(return_value=mock_result)
    
    result = service.perform_action(
        task_id=80,
        action="reject",
        approver_id=300,
        comment="不同意"
    )
    
    assert result["task_id"] == 80
    assert result["action"] == "reject"
    assert result["instance_status"] == "REJECTED"
    
    service.approval_engine.reject.assert_called_once_with(
        task_id=80,
        approver_id=300,
        comment="不同意"
    )


def test_perform_action_unsupported_action(service):
    """测试不支持的操作类型"""
    with pytest.raises(ValueError, match="不支持的操作类型"):
        service.perform_action(
            task_id=80,
            action="invalid_action",
            approver_id=300
        )


def test_perform_action_without_comment(service):
    """测试不带评论的审批操作"""
    mock_result = MagicMock()
    mock_result.status = "APPROVED"
    service.approval_engine.approve = MagicMock(return_value=mock_result)
    
    result = service.perform_action(
        task_id=80,
        action="approve",
        approver_id=300
    )
    
    assert result["task_id"] == 80


# =========================== perform_batch_actions 测试 ===========================

def test_perform_batch_actions_approve_all_success(service):
    """测试批量审批通过全部成功"""
    service.approval_engine.approve = MagicMock()
    
    result = service.perform_batch_actions(
        task_ids=[80, 81, 82],
        action="approve",
        approver_id=300,
        comment="批量通过"
    )
    
    assert len(result["success"]) == 3
    assert len(result["errors"]) == 0
    assert service.approval_engine.approve.call_count == 3


def test_perform_batch_actions_reject_all_success(service):
    """测试批量拒绝全部成功"""
    service.approval_engine.reject = MagicMock()
    
    result = service.perform_batch_actions(
        task_ids=[80, 81],
        action="reject",
        approver_id=300,
        comment="批量拒绝"
    )
    
    assert len(result["success"]) == 2
    assert len(result["errors"]) == 0
    assert service.approval_engine.reject.call_count == 2


def test_perform_batch_actions_mixed_results(service):
    """测试批量操作部分成功部分失败"""
    service.approval_engine.approve = MagicMock(
        side_effect=[None, Exception("权限不足"), None]
    )
    
    result = service.perform_batch_actions(
        task_ids=[80, 81, 82],
        action="approve",
        approver_id=300
    )
    
    assert len(result["success"]) == 2
    assert len(result["errors"]) == 1
    assert result["errors"][0]["task_id"] == 81


def test_perform_batch_actions_unsupported_action(service):
    """测试批量操作使用不支持的动作"""
    result = service.perform_batch_actions(
        task_ids=[80, 81],
        action="invalid",
        approver_id=300
    )
    
    assert len(result["success"]) == 0
    assert len(result["errors"]) == 2


# =========================== get_quote_approval_status 测试 ===========================

def test_get_quote_approval_status_not_found(service, db_session):
    """测试查询不存在的报价审批状态"""
    db_session.query.return_value.filter.return_value.first.return_value = None
    
    result = service.get_quote_approval_status(quote_id=999)
    
    assert result is None


def test_get_quote_approval_status_no_approval(service, db_session, mock_quote):
    """测试查询未提交审批的报价状态"""
    # 模拟查询报价
    quote_query = MagicMock()
    quote_query.first.return_value = mock_quote
    
    # 模拟查询审批实例为空
    instance_query = MagicMock()
    instance_query.first.return_value = None
    
    db_session.query.return_value.filter.side_effect = [
        quote_query,
        MagicMock(order_by=MagicMock(return_value=instance_query))
    ]
    
    result = service.get_quote_approval_status(quote_id=1)
    
    assert result["quote_id"] == 1
    assert result["quote_code"] == "Q2026-001"
    assert result["approval_instance"] is None


def test_get_quote_approval_status_with_instance(service, db_session, mock_quote, mock_approval_instance, mock_version):
    """测试查询有审批实例的报价状态"""
    mock_quote.customer = MagicMock()
    mock_quote.customer.name = "客户A"
    mock_quote.current_version = mock_version
    
    # 配置查询链
    quote_query = MagicMock()
    quote_query.first.return_value = mock_quote
    
    instance_query_builder = MagicMock()
    instance_query = MagicMock()
    instance_query.first.return_value = mock_approval_instance
    instance_query_builder.order_by.return_value = instance_query
    
    task_query_builder = MagicMock()
    task_query = MagicMock()
    task_query.all.return_value = []
    task_query_builder.order_by.return_value = task_query
    
    db_session.query.return_value.filter.side_effect = [
        quote_query,
        instance_query_builder,
        task_query_builder
    ]
    
    result = service.get_quote_approval_status(quote_id=1)
    
    assert result["quote_id"] == 1
    assert result["instance_id"] == 50
    assert result["instance_status"] == "PENDING"
    assert result["customer_name"] == "客户A"
    assert result["version_info"]["version_no"] == "V1.0"


def test_get_quote_approval_status_with_task_history(service, db_session, mock_quote, mock_approval_instance, mock_approval_task, mock_version):
    """测试查询包含任务历史的审批状态"""
    mock_quote.customer = MagicMock()
    mock_quote.customer.name = "客户A"
    mock_quote.current_version = mock_version
    
    mock_approval_task.status = "APPROVED"
    mock_approval_task.action = "approve"
    mock_approval_task.comment = "同意"
    mock_approval_task.completed_at = datetime(2026, 2, 20, 11, 0, 0)
    
    # 配置查询链
    quote_query = MagicMock()
    quote_query.first.return_value = mock_quote
    
    instance_query_builder = MagicMock()
    instance_query = MagicMock()
    instance_query.first.return_value = mock_approval_instance
    instance_query_builder.order_by.return_value = instance_query
    
    task_query_builder = MagicMock()
    task_query = MagicMock()
    task_query.all.return_value = [mock_approval_task]
    task_query_builder.order_by.return_value = task_query
    
    db_session.query.return_value.filter.side_effect = [
        quote_query,
        instance_query_builder,
        task_query_builder
    ]
    
    result = service.get_quote_approval_status(quote_id=1)
    
    assert len(result["task_history"]) == 1
    assert result["task_history"][0]["task_id"] == 80
    assert result["task_history"][0]["status"] == "APPROVED"
    assert result["task_history"][0]["action"] == "approve"


# =========================== withdraw_approval 测试 ===========================

def test_withdraw_approval_success(service, db_session, mock_quote, mock_approval_instance):
    """测试成功撤回审批"""
    mock_approval_instance.initiator_id = 200
    
    quote_query = MagicMock()
    quote_query.first.return_value = mock_quote
    
    instance_query = MagicMock()
    instance_query.first.return_value = mock_approval_instance
    
    db_session.query.return_value.filter.side_effect = [
        quote_query,
        instance_query
    ]
    
    service.approval_engine.withdraw = MagicMock()
    
    result = service.withdraw_approval(
        quote_id=1,
        user_id=200,
        reason="需要修改报价"
    )
    
    assert result["quote_id"] == 1
    assert result["status"] == "withdrawn"
    
    service.approval_engine.withdraw.assert_called_once_with(
        instance_id=50,
        user_id=200
    )


def test_withdraw_approval_quote_not_found(service, db_session):
    """测试撤回不存在的报价审批"""
    db_session.query.return_value.filter.return_value.first.return_value = None
    
    with pytest.raises(ValueError, match="报价不存在"):
        service.withdraw_approval(quote_id=999, user_id=200)


def test_withdraw_approval_no_pending_instance(service, db_session, mock_quote):
    """测试撤回没有进行中的审批"""
    quote_query = MagicMock()
    quote_query.first.return_value = mock_quote
    
    instance_query = MagicMock()
    instance_query.first.return_value = None
    
    db_session.query.return_value.filter.side_effect = [
        quote_query,
        instance_query
    ]
    
    with pytest.raises(ValueError, match="没有进行中的审批流程可撤回"):
        service.withdraw_approval(quote_id=1, user_id=200)


def test_withdraw_approval_permission_denied(service, db_session, mock_quote, mock_approval_instance):
    """测试无权撤回他人提交的审批"""
    mock_approval_instance.initiator_id = 200
    
    quote_query = MagicMock()
    quote_query.first.return_value = mock_quote
    
    instance_query = MagicMock()
    instance_query.first.return_value = mock_approval_instance
    
    db_session.query.return_value.filter.side_effect = [
        quote_query,
        instance_query
    ]
    
    with pytest.raises(ValueError, match="只能撤回自己提交的审批"):
        service.withdraw_approval(quote_id=1, user_id=999)


# =========================== get_approval_history 测试 ===========================

def test_get_approval_history_success(service):
    """测试获取审批历史"""
    # 简化: 直接patch get_approval_history方法本身
    from unittest.mock import patch
    
    mock_result = {
        "items": [
            {
                "task_id": 80,
                "quote_id": 1,
                "quote_code": "Q2026-001",
                "customer_name": "客户A",
                "action": "approve",
                "status": "APPROVED",
                "comment": "同意",
                "completed_at": "2026-02-20T11:00:00"
            }
        ],
        "total": 1
    }
    
    with patch.object(service, 'get_approval_history', return_value=mock_result):
        result = service.get_approval_history(user_id=300)
        
        assert result["total"] == 1
        assert len(result["items"]) == 1
        assert result["items"][0]["task_id"] == 80
        assert result["items"][0]["status"] == "APPROVED"


def test_get_approval_history_with_status_filter(service, db_session):
    """测试按状态筛选审批历史"""
    query_builder = MagicMock()
    query_builder.count.return_value = 0
    query_builder.offset.return_value.limit.return_value.all.return_value = []
    
    filter_builder = MagicMock()
    filter_builder.filter.return_value = query_builder
    
    join_builder = MagicMock()
    join_builder.filter.return_value = filter_builder
    
    db_session.query.return_value.join.return_value = join_builder
    
    result = service.get_approval_history(user_id=300, status_filter="REJECTED")
    
    assert result["total"] == 0
    assert result["items"] == []


def test_get_approval_history_with_pagination(service):
    """测试审批历史分页"""
    from unittest.mock import patch
    
    mock_result = {"items": [], "total": 50}
    
    with patch.object(service, 'get_approval_history', return_value=mock_result):
        result = service.get_approval_history(user_id=300, offset=20, limit=10)
        
        assert result["total"] == 50


# =========================== 私有方法测试 ===========================

def test_build_form_data(service, mock_quote, mock_version):
    """测试构建表单数据"""
    mock_quote.customer = MagicMock()
    mock_quote.customer.name = "客户A"
    
    form_data = service._build_form_data(mock_quote, mock_version)
    
    assert form_data["quote_id"] == 1
    assert form_data["quote_code"] == "Q2026-001"
    assert form_data["version_id"] == 10
    assert form_data["version_no"] == "V1.0"
    assert form_data["total_price"] == 100000.0
    assert form_data["cost_total"] == 70000.0
    assert form_data["gross_margin"] == 30.0
    assert form_data["customer_name"] == "客户A"
    assert form_data["lead_time_days"] == 30


def test_get_current_version_with_current_version(service, mock_quote, mock_version):
    """测试获取当前版本（存在 current_version）"""
    mock_quote.current_version = mock_version
    
    result = service._get_current_version(mock_quote)
    
    assert result == mock_version


def test_get_current_version_without_current_version(service, db_session, mock_quote, mock_version):
    """测试获取当前版本（不存在 current_version，查询最新）"""
    mock_quote.current_version = None
    mock_quote.id = 1
    
    query_builder = MagicMock()
    query_builder.first.return_value = mock_version
    
    db_session.query.return_value.filter.return_value.order_by.return_value = query_builder
    
    result = service._get_current_version(mock_quote)
    
    assert result == mock_version


def test_get_current_version_quote_none(service):
    """测试获取当前版本（报价为 None）"""
    result = service._get_current_version(None)
    
    assert result is None


def test_get_quote_version_from_version_ids(service, db_session, mock_quote, mock_version):
    """测试从指定版本ID列表获取版本"""
    query_builder = MagicMock()
    query_builder.first.return_value = mock_version
    
    db_session.query.return_value.filter.return_value = query_builder
    
    result = service._get_quote_version(mock_quote, version_ids=[10], index=0)
    
    assert result == mock_version


def test_get_quote_version_fallback_to_current(service, mock_quote, mock_version):
    """测试版本ID不匹配时回退到当前版本"""
    mock_quote.current_version = mock_version
    
    result = service._get_quote_version(mock_quote, version_ids=[], index=0)
    
    assert result == mock_version
