# -*- coding: utf-8 -*-
"""
data_audit_service 单元测试

测试销售数据审核服务的核心功能。
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.models.sales.data_audit import (
    DataAuditPriorityEnum,
    DataAuditStatusEnum,
    DataChangeType,
    SalesDataAuditRequest,
)
from app.models.sales.operation_log import SalesEntityType
from app.services.sales.data_audit_service import (
    SalesDataAuditService,
    _get_entity_name,
)


# ========== 测试夹具 ==========

@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    db = MagicMock()
    db.add = MagicMock()
    db.flush = MagicMock()
    return db


@pytest.fixture
def service(mock_db):
    """创建服务实例"""
    return SalesDataAuditService(mock_db)


@pytest.fixture
def mock_requester():
    """模拟申请人"""
    user = MagicMock()
    user.id = 1
    user.username = "zhangsan"
    user.real_name = "张三"
    user.department = MagicMock()
    user.department.name = "销售部"
    return user


@pytest.fixture
def mock_reviewer():
    """模拟审核人"""
    user = MagicMock()
    user.id = 2
    user.username = "lisi"
    user.real_name = "李四"
    user.department = MagicMock()
    user.department.name = "财务部"
    return user


@pytest.fixture
def sample_pending_request(mock_requester):
    """示例待审核请求"""
    request = MagicMock(spec=SalesDataAuditRequest)
    request.id = 1
    request.entity_type = SalesEntityType.CONTRACT
    request.entity_id = 100
    request.entity_code = "HT-001"
    request.status = DataAuditStatusEnum.PENDING.value
    request.requester_id = mock_requester.id
    request.old_value = {"contract_amount": 100000}
    request.new_value = {"contract_amount": 120000}
    request.changed_fields = ["contract_amount"]
    return request


# ========== requires_audit 测试 ==========

class TestRequiresAudit:
    """requires_audit 测试"""

    def test_audit_required_for_contract_amount(self, service):
        """合同金额变更需要审核"""
        result = service.requires_audit("CONTRACT", ["contract_amount"])
        assert result is True

    def test_audit_required_for_opportunity_amount(self, service):
        """商机金额变更需要审核"""
        result = service.requires_audit("OPPORTUNITY", ["est_amount"])
        assert result is True

    def test_audit_not_required_for_regular_field(self, service):
        """普通字段变更不需要审核"""
        result = service.requires_audit("CONTRACT", ["description", "remark"])
        assert result is False

    def test_audit_required_for_mixed_fields(self, service):
        """混合字段（包含审核字段）需要审核"""
        result = service.requires_audit("CONTRACT", ["description", "contract_amount"])
        assert result is True

    def test_unknown_entity_type(self, service):
        """未知实体类型不需要审核"""
        result = service.requires_audit("UNKNOWN_TYPE", ["any_field"])
        assert result is False


# ========== submit_audit_request 测试 ==========

class TestSubmitAuditRequest:
    """submit_audit_request 测试"""

    def test_submit_request_success(self, service, mock_db, mock_requester):
        """成功提交审核请求"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # 无重复请求

        old_value = {"contract_amount": 100000}
        new_value = {"contract_amount": 120000}

        result = service.submit_audit_request(
            entity_type="CONTRACT",
            entity_id=100,
            old_value=old_value,
            new_value=new_value,
            requester=mock_requester,
            entity_code="HT-001",
            change_reason="客户要求增加服务内容",
        )

        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

        # 验证添加的请求对象
        request = mock_db.add.call_args[0][0]
        assert request.entity_type == "CONTRACT"
        assert request.entity_id == 100
        assert request.status == DataAuditStatusEnum.PENDING.value
        assert request.changed_fields == ["contract_amount"]

    def test_submit_request_duplicate_rejected(self, service, mock_db, mock_requester):
        """重复提交被拒绝"""
        existing_request = MagicMock(spec=SalesDataAuditRequest)
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = existing_request

        with pytest.raises(ValueError, match="已有待审核的变更请求"):
            service.submit_audit_request(
                entity_type="CONTRACT",
                entity_id=100,
                old_value={"amount": 100},
                new_value={"amount": 200},
                requester=mock_requester,
            )

    def test_submit_with_priority(self, service, mock_db, mock_requester):
        """提交高优先级请求"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        service.submit_audit_request(
            entity_type="CONTRACT",
            entity_id=100,
            old_value={"amount": 100},
            new_value={"amount": 200},
            requester=mock_requester,
            priority=DataAuditPriorityEnum.HIGH.value,
        )

        request = mock_db.add.call_args[0][0]
        assert request.priority == DataAuditPriorityEnum.HIGH.value


# ========== get_pending_requests 测试 ==========

class TestGetPendingRequests:
    """get_pending_requests 测试"""

    def test_get_all_pending(self, service, mock_db):
        """获取所有待审核"""
        mock_requests = [MagicMock(spec=SalesDataAuditRequest) for _ in range(3)]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_requests

        requests, total = service.get_pending_requests()

        assert len(requests) == 3
        assert total == 10

    def test_get_pending_by_entity_type(self, service, mock_db):
        """按实体类型筛选"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        requests, total = service.get_pending_requests(entity_type="CONTRACT")

        assert total == 5


# ========== approve_request 测试 ==========

class TestApproveRequest:
    """approve_request 测试"""

    def test_approve_success(self, service, mock_db, mock_reviewer, sample_pending_request):
        """审核通过成功"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_pending_request

        with patch.object(service, '_apply_change'):
            result = service.approve_request(
                request_id=1,
                reviewer=mock_reviewer,
                comment="同意",
                apply_immediately=True,
            )

        assert sample_pending_request.status == DataAuditStatusEnum.APPROVED.value
        assert sample_pending_request.reviewer_id == mock_reviewer.id
        mock_db.flush.assert_called()

    def test_approve_own_request_rejected(self, service, mock_db, mock_requester, sample_pending_request):
        """不能审核自己的请求"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_pending_request

        with pytest.raises(ValueError, match="不能审核自己提交的请求"):
            service.approve_request(
                request_id=1,
                reviewer=mock_requester,  # 同一个人
            )

    def test_approve_non_pending_rejected(self, service, mock_db, mock_reviewer):
        """不能审核非待处理请求"""
        approved_request = MagicMock(spec=SalesDataAuditRequest)
        approved_request.id = 1
        approved_request.status = DataAuditStatusEnum.APPROVED.value
        approved_request.requester_id = 999

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = approved_request

        with pytest.raises(ValueError, match="只能审核待处理的请求"):
            service.approve_request(request_id=1, reviewer=mock_reviewer)

    def test_approve_request_not_found(self, service, mock_db, mock_reviewer):
        """请求不存在"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        with pytest.raises(ValueError, match="审核请求不存在"):
            service.approve_request(request_id=999, reviewer=mock_reviewer)


# ========== reject_request 测试 ==========

class TestRejectRequest:
    """reject_request 测试"""

    def test_reject_success(self, service, mock_db, mock_reviewer, sample_pending_request):
        """驳回成功"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_pending_request

        result = service.reject_request(
            request_id=1,
            reviewer=mock_reviewer,
            comment="金额变更幅度过大，请重新评估",
        )

        assert sample_pending_request.status == DataAuditStatusEnum.REJECTED.value
        assert sample_pending_request.review_comment == "金额变更幅度过大，请重新评估"

    def test_reject_without_comment(self, service, mock_db, mock_reviewer, sample_pending_request):
        """驳回必须填写原因"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_pending_request

        with pytest.raises(ValueError, match="驳回时必须填写原因"):
            service.reject_request(
                request_id=1,
                reviewer=mock_reviewer,
                comment="",
            )


# ========== cancel_request 测试 ==========

class TestCancelRequest:
    """cancel_request 测试"""

    def test_cancel_own_request(self, service, mock_db, mock_requester, sample_pending_request):
        """撤销自己的请求"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_pending_request

        result = service.cancel_request(
            request_id=1,
            user=mock_requester,
            reason="不再需要",
        )

        assert sample_pending_request.status == DataAuditStatusEnum.CANCELLED.value
        assert "申请人撤销" in sample_pending_request.review_comment

    def test_cancel_others_request_rejected(self, service, mock_db, mock_reviewer, sample_pending_request):
        """不能撤销他人请求"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_pending_request

        with pytest.raises(ValueError, match="只能撤销自己提交的请求"):
            service.cancel_request(
                request_id=1,
                user=mock_reviewer,  # 不是申请人
            )


# ========== get_entity_audit_history 测试 ==========

class TestGetEntityAuditHistory:
    """get_entity_audit_history 测试"""

    def test_get_history(self, service, mock_db):
        """获取实体审核历史"""
        mock_requests = [MagicMock(spec=SalesDataAuditRequest) for _ in range(5)]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 15
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_requests

        requests, total = service.get_entity_audit_history(
            entity_type="CONTRACT",
            entity_id=100,
        )

        assert len(requests) == 5
        assert total == 15


# ========== _get_entity_name 测试 ==========

class TestGetEntityName:
    """_get_entity_name 辅助函数测试"""

    def test_get_known_names(self):
        """获取已知实体名称"""
        assert _get_entity_name(SalesEntityType.LEAD) == "线索"
        assert _get_entity_name(SalesEntityType.OPPORTUNITY) == "商机"
        assert _get_entity_name(SalesEntityType.QUOTE) == "报价"
        assert _get_entity_name(SalesEntityType.CONTRACT) == "合同"
        assert _get_entity_name(SalesEntityType.CUSTOMER) == "客户"

    def test_get_unknown_name(self):
        """未知类型返回原值"""
        assert _get_entity_name("UNKNOWN") == "UNKNOWN"
