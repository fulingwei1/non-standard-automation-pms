# -*- coding: utf-8 -*-
"""
项目变更请求服务完整测试
覆盖变更请求管理、审批流程、影响分析、变更记录
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.services.project_change_requests.service import ProjectChangeRequestsService
from app.models.change_request import ChangeRequest, ChangeApprovalRecord, ChangeNotification
from app.models.project import Project
from app.models.user import User
from app.models.enums import (
    ChangeStatusEnum,
    ChangeTypeEnum,
    ChangeSourceEnum,
    ApprovalDecisionEnum,
)
from app.schemas.change_request import (
    ChangeRequestCreate,
    ChangeRequestUpdate,
    ChangeApprovalRequest,
    ChangeStatusUpdateRequest,
    ChangeImplementationRequest,
    ChangeVerificationRequest,
    ChangeCloseRequest,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock数据库会话"""
    return MagicMock(spec=Session)


@pytest.fixture
def service(mock_db):
    """创建服务实例"""
    return ProjectChangeRequestsService(mock_db)


@pytest.fixture
def mock_user():
    """Mock用户"""
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.real_name = "测试用户"
    return user


@pytest.fixture
def mock_project():
    """Mock项目"""
    project = MagicMock(spec=Project)
    project.id = 1
    project.project_code = "PRJ001"
    project.project_name = "测试项目"
    return project


@pytest.fixture
def mock_change_request():
    """Mock变更请求"""
    change = MagicMock(spec=ChangeRequest)
    change.id = 1
    change.change_code = "CHG-PRJ001-001"
    change.project_id = 1
    change.title = "测试变更"
    change.description = "测试变更描述"
    change.change_type = ChangeTypeEnum.SCOPE
    change.change_source = ChangeSourceEnum.CUSTOMER
    change.status = ChangeStatusEnum.SUBMITTED
    change.approval_decision = ApprovalDecisionEnum.PENDING
    change.submitter_id = 1
    change.submitter_name = "测试用户"
    change.cost_impact = Decimal("10000")
    change.time_impact = 5
    change.notify_team = True
    change.submit_date = datetime.utcnow()
    return change


# ============================================================================
# 测试 generate_change_code
# ============================================================================

def test_generate_change_code_first_change(service, mock_db, mock_project):
    """测试生成第一个变更编号"""
    # Mock get_or_404
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get:
        mock_get.return_value = mock_project
        
        # Mock count query
        mock_query = MagicMock()
        mock_query.filter.return_value.scalar.return_value = 0
        mock_db.query.return_value = mock_query
        
        code = service.generate_change_code(1)
        
        assert code == "CHG-PRJ001-001"
        mock_get.assert_called_once()


def test_generate_change_code_second_change(service, mock_db, mock_project):
    """测试生成第二个变更编号"""
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get:
        mock_get.return_value = mock_project
        
        # Mock count = 1
        mock_query = MagicMock()
        mock_query.filter.return_value.scalar.return_value = 1
        mock_db.query.return_value = mock_query
        
        code = service.generate_change_code(1)
        
        assert code == "CHG-PRJ001-002"


def test_generate_change_code_project_not_found(service):
    """测试项目不存在时抛出异常"""
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get:
        mock_get.side_effect = HTTPException(status_code=404, detail="项目不存在")
        
        with pytest.raises(HTTPException) as exc:
            service.generate_change_code(999)
        
        assert exc.value.status_code == 404


# ============================================================================
# 测试 validate_status_transition
# ============================================================================

def test_validate_status_transition_submitted_to_assessing(service):
    """测试从已提交到评估中"""
    assert service.validate_status_transition(
        ChangeStatusEnum.SUBMITTED,
        ChangeStatusEnum.ASSESSING
    ) is True


def test_validate_status_transition_assessing_to_pending_approval(service):
    """测试从评估中到待审批"""
    assert service.validate_status_transition(
        ChangeStatusEnum.ASSESSING,
        ChangeStatusEnum.PENDING_APPROVAL
    ) is True


def test_validate_status_transition_pending_to_approved(service):
    """测试从待审批到已批准"""
    assert service.validate_status_transition(
        ChangeStatusEnum.PENDING_APPROVAL,
        ChangeStatusEnum.APPROVED
    ) is True


def test_validate_status_transition_approved_to_implementing(service):
    """测试从已批准到实施中"""
    assert service.validate_status_transition(
        ChangeStatusEnum.APPROVED,
        ChangeStatusEnum.IMPLEMENTING
    ) is True


def test_validate_status_transition_implementing_to_verifying(service):
    """测试从实施中到验证中"""
    assert service.validate_status_transition(
        ChangeStatusEnum.IMPLEMENTING,
        ChangeStatusEnum.VERIFYING
    ) is True


def test_validate_status_transition_verifying_to_closed(service):
    """测试从验证中到已关闭"""
    assert service.validate_status_transition(
        ChangeStatusEnum.VERIFYING,
        ChangeStatusEnum.CLOSED
    ) is True


def test_validate_status_transition_invalid_rejected_to_approved(service):
    """测试非法转换：已拒绝到已批准"""
    assert service.validate_status_transition(
        ChangeStatusEnum.REJECTED,
        ChangeStatusEnum.APPROVED
    ) is False


def test_validate_status_transition_invalid_closed_to_implementing(service):
    """测试非法转换：已关闭到实施中"""
    assert service.validate_status_transition(
        ChangeStatusEnum.CLOSED,
        ChangeStatusEnum.IMPLEMENTING
    ) is False


def test_validate_status_transition_cancelled_to_any(service):
    """测试取消状态不能转换"""
    assert service.validate_status_transition(
        ChangeStatusEnum.CANCELLED,
        ChangeStatusEnum.SUBMITTED
    ) is False


# ============================================================================
# 测试 create_change_request
# ============================================================================

def test_create_change_request_success(service, mock_db, mock_project, mock_user):
    """测试成功创建变更请求"""
    change_in = ChangeRequestCreate(
        project_id=1,
        title="需求变更",
        description="客户要求增加新功能",
        change_type=ChangeTypeEnum.SCOPE,
        change_source=ChangeSourceEnum.CUSTOMER,
        cost_impact=Decimal("50000"),
        time_impact=10,
        notify_team=True,
    )
    
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get, \
         patch('app.services.project_change_requests.service.save_obj') as mock_save:
        
        mock_get.return_value = mock_project
        
        # Mock count for change code generation
        mock_query = MagicMock()
        mock_query.filter.return_value.scalar.return_value = 0
        mock_db.query.return_value = mock_query
        
        result = service.create_change_request(change_in, mock_user)
        
        assert result.title == "需求变更"
        assert result.status == ChangeStatusEnum.SUBMITTED
        assert result.approval_decision == ApprovalDecisionEnum.PENDING
        assert result.submitter_id == 1
        assert result.submitter_name == "测试用户"
        mock_save.assert_called_once()


def test_create_change_request_project_not_found(service, mock_user):
    """测试项目不存在"""
    change_in = ChangeRequestCreate(
        project_id=999,
        title="变更",
        description="描述",
        change_type=ChangeTypeEnum.SCOPE,
        change_source=ChangeSourceEnum.CUSTOMER,
    )
    
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get:
        mock_get.side_effect = HTTPException(status_code=404, detail="项目不存在")
        
        with pytest.raises(HTTPException) as exc:
            service.create_change_request(change_in, mock_user)
        
        assert exc.value.status_code == 404


# ============================================================================
# 测试 list_change_requests
# ============================================================================

def test_list_change_requests_all(service, mock_db, mock_change_request):
    """测试获取所有变更请求"""
    with patch('app.services.project_change_requests.service.apply_pagination') as mock_pagination:
        mock_pagination.return_value.all.return_value = [mock_change_request]
        
        # Mock query chain
        mock_query = MagicMock()
        mock_query.order_by.return_value = mock_query
        mock_db.query.return_value = mock_query
        
        results = service.list_change_requests(offset=0, limit=10)
        
        assert len(results) == 1
        assert results[0].id == 1


def test_list_change_requests_filter_by_project(service, mock_db):
    """测试按项目过滤"""
    with patch('app.services.project_change_requests.service.apply_pagination') as mock_pagination:
        mock_pagination.return_value.all.return_value = []
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_db.query.return_value = mock_query
        
        service.list_change_requests(offset=0, limit=10, project_id=1)
        
        # Verify filter was called
        assert mock_query.filter.called


def test_list_change_requests_filter_by_status(service, mock_db):
    """测试按状态过滤"""
    with patch('app.services.project_change_requests.service.apply_pagination') as mock_pagination:
        mock_pagination.return_value.all.return_value = []
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_db.query.return_value = mock_query
        
        service.list_change_requests(
            offset=0, 
            limit=10, 
            status=ChangeStatusEnum.PENDING_APPROVAL
        )
        
        assert mock_query.filter.called


def test_list_change_requests_search(service, mock_db):
    """测试搜索功能"""
    with patch('app.services.project_change_requests.service.apply_pagination') as mock_pagination:
        mock_pagination.return_value.all.return_value = []
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_db.query.return_value = mock_query
        
        service.list_change_requests(offset=0, limit=10, search="关键词")
        
        assert mock_query.filter.called


# ============================================================================
# 测试 get_change_request
# ============================================================================

def test_get_change_request_success(service, mock_change_request):
    """测试获取变更请求详情"""
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get:
        mock_get.return_value = mock_change_request
        
        result = service.get_change_request(1)
        
        assert result.id == 1
        assert result.change_code == "CHG-PRJ001-001"


def test_get_change_request_not_found(service):
    """测试变更请求不存在"""
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get:
        mock_get.side_effect = HTTPException(status_code=404, detail="变更请求不存在")
        
        with pytest.raises(HTTPException) as exc:
            service.get_change_request(999)
        
        assert exc.value.status_code == 404


# ============================================================================
# 测试 update_change_request
# ============================================================================

def test_update_change_request_success(service, mock_change_request):
    """测试成功更新变更请求"""
    update_in = ChangeRequestUpdate(
        title="更新后的标题",
        description="更新后的描述",
    )
    
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get, \
         patch('app.services.project_change_requests.service.save_obj') as mock_save:
        
        mock_get.return_value = mock_change_request
        
        result = service.update_change_request(1, update_in)
        
        assert result.title == "更新后的标题"
        assert result.description == "更新后的描述"
        mock_save.assert_called_once()


def test_update_change_request_approved_status_fails(service, mock_change_request):
    """测试已批准的变更不能修改"""
    mock_change_request.status = ChangeStatusEnum.APPROVED
    
    update_in = ChangeRequestUpdate(title="新标题")
    
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get:
        mock_get.return_value = mock_change_request
        
        with pytest.raises(HTTPException) as exc:
            service.update_change_request(1, update_in)
        
        assert exc.value.status_code == 400
        assert "不能修改" in exc.value.detail


def test_update_change_request_rejected_status_fails(service, mock_change_request):
    """测试已拒绝的变更不能修改"""
    mock_change_request.status = ChangeStatusEnum.REJECTED
    
    update_in = ChangeRequestUpdate(title="新标题")
    
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get:
        mock_get.return_value = mock_change_request
        
        with pytest.raises(HTTPException) as exc:
            service.update_change_request(1, update_in)
        
        assert exc.value.status_code == 400


def test_update_change_request_closed_status_fails(service, mock_change_request):
    """测试已关闭的变更不能修改"""
    mock_change_request.status = ChangeStatusEnum.CLOSED
    
    update_in = ChangeRequestUpdate(title="新标题")
    
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get:
        mock_get.return_value = mock_change_request
        
        with pytest.raises(HTTPException) as exc:
            service.update_change_request(1, update_in)
        
        assert exc.value.status_code == 400


# ============================================================================
# 测试 approve_change_request
# ============================================================================

def test_approve_change_request_approved(service, mock_db, mock_change_request, mock_user):
    """测试批准变更请求"""
    mock_change_request.status = ChangeStatusEnum.PENDING_APPROVAL
    
    approval_in = ChangeApprovalRequest(
        decision=ApprovalDecisionEnum.APPROVED,
        comments="同意该变更",
    )
    
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get:
        mock_get.return_value = mock_change_request
        
        result = service.approve_change_request(1, approval_in, mock_user)
        
        assert result.status == ChangeStatusEnum.APPROVED
        assert result.approval_decision == ApprovalDecisionEnum.APPROVED
        assert result.approver_id == 1
        assert result.approver_name == "测试用户"
        mock_db.add.assert_called()
        mock_db.commit.assert_called_once()


def test_approve_change_request_rejected(service, mock_db, mock_change_request, mock_user):
    """测试拒绝变更请求"""
    mock_change_request.status = ChangeStatusEnum.PENDING_APPROVAL
    
    approval_in = ChangeApprovalRequest(
        decision=ApprovalDecisionEnum.REJECTED,
        comments="不同意该变更",
    )
    
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get:
        mock_get.return_value = mock_change_request
        
        result = service.approve_change_request(1, approval_in, mock_user)
        
        assert result.status == ChangeStatusEnum.REJECTED
        assert result.approval_decision == ApprovalDecisionEnum.REJECTED


def test_approve_change_request_returned(service, mock_db, mock_change_request, mock_user):
    """测试退回变更请求"""
    mock_change_request.status = ChangeStatusEnum.PENDING_APPROVAL
    
    approval_in = ChangeApprovalRequest(
        decision=ApprovalDecisionEnum.RETURNED,
        comments="需要补充信息",
    )
    
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get:
        mock_get.return_value = mock_change_request
        
        result = service.approve_change_request(1, approval_in, mock_user)
        
        assert result.status == ChangeStatusEnum.ASSESSING


def test_approve_change_request_wrong_status(service, mock_change_request, mock_user):
    """测试非待审批状态不能审批"""
    mock_change_request.status = ChangeStatusEnum.SUBMITTED
    
    approval_in = ChangeApprovalRequest(
        decision=ApprovalDecisionEnum.APPROVED,
        comments="同意",
    )
    
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get:
        mock_get.return_value = mock_change_request
        
        with pytest.raises(HTTPException) as exc:
            service.approve_change_request(1, approval_in, mock_user)
        
        assert exc.value.status_code == 400
        assert "待审批" in exc.value.detail


# ============================================================================
# 测试 get_approval_records
# ============================================================================

def test_get_approval_records_success(service, mock_db, mock_change_request):
    """测试获取审批记录"""
    mock_record = MagicMock(spec=ChangeApprovalRecord)
    mock_record.id = 1
    mock_record.decision = ApprovalDecisionEnum.APPROVED
    
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get:
        mock_get.return_value = mock_change_request
        
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [mock_record]
        mock_db.query.return_value = mock_query
        
        results = service.get_approval_records(1)
        
        assert len(results) == 1
        assert results[0].decision == ApprovalDecisionEnum.APPROVED


# ============================================================================
# 测试 update_change_status
# ============================================================================

def test_update_change_status_success(service, mock_change_request):
    """测试成功更新状态"""
    mock_change_request.status = ChangeStatusEnum.SUBMITTED
    
    status_in = ChangeStatusUpdateRequest(
        new_status=ChangeStatusEnum.ASSESSING,
        notes="开始评估",
    )
    
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get, \
         patch('app.services.project_change_requests.service.save_obj') as mock_save:
        
        mock_get.return_value = mock_change_request
        
        result, old_status = service.update_change_status(1, status_in)
        
        assert result.status == ChangeStatusEnum.ASSESSING
        assert old_status == "SUBMITTED"
        mock_save.assert_called_once()


def test_update_change_status_invalid_transition(service, mock_change_request):
    """测试非法状态转换"""
    mock_change_request.status = ChangeStatusEnum.CLOSED
    
    status_in = ChangeStatusUpdateRequest(
        new_status=ChangeStatusEnum.IMPLEMENTING,
    )
    
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get:
        mock_get.return_value = mock_change_request
        
        with pytest.raises(HTTPException) as exc:
            service.update_change_status(1, status_in)
        
        assert exc.value.status_code == 400
        assert "不允许" in exc.value.detail


def test_update_change_status_to_implementing(service, mock_change_request):
    """测试转换到实施中状态"""
    mock_change_request.status = ChangeStatusEnum.APPROVED
    mock_change_request.implementation_start_date = None
    
    status_in = ChangeStatusUpdateRequest(
        new_status=ChangeStatusEnum.IMPLEMENTING,
    )
    
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get, \
         patch('app.services.project_change_requests.service.save_obj') as mock_save:
        
        mock_get.return_value = mock_change_request
        
        result, _ = service.update_change_status(1, status_in)
        
        assert result.implementation_start_date is not None


def test_update_change_status_to_verifying(service, mock_change_request):
    """测试转换到验证中状态"""
    mock_change_request.status = ChangeStatusEnum.IMPLEMENTING
    mock_change_request.implementation_end_date = None
    
    status_in = ChangeStatusUpdateRequest(
        new_status=ChangeStatusEnum.VERIFYING,
    )
    
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get, \
         patch('app.services.project_change_requests.service.save_obj') as mock_save:
        
        mock_get.return_value = mock_change_request
        
        result, _ = service.update_change_status(1, status_in)
        
        assert result.implementation_end_date is not None


def test_update_change_status_to_closed(service, mock_change_request):
    """测试转换到关闭状态"""
    mock_change_request.status = ChangeStatusEnum.VERIFYING
    
    status_in = ChangeStatusUpdateRequest(
        new_status=ChangeStatusEnum.CLOSED,
        notes="验证通过，关闭变更",
    )
    
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get, \
         patch('app.services.project_change_requests.service.save_obj') as mock_save:
        
        mock_get.return_value = mock_change_request
        
        result, _ = service.update_change_status(1, status_in)
        
        assert result.close_date is not None
        assert result.close_notes == "验证通过，关闭变更"


# ============================================================================
# 测试 update_implementation_info
# ============================================================================

def test_update_implementation_info_success(service, mock_change_request):
    """测试更新实施信息"""
    mock_change_request.status = ChangeStatusEnum.APPROVED
    
    impl_in = ChangeImplementationRequest(
        implementation_start_date=datetime(2024, 6, 1),
        implementation_end_date=datetime(2024, 6, 15),
        implementation_notes="实施完成",
    )
    
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get, \
         patch('app.services.project_change_requests.service.save_obj') as mock_save:
        
        mock_get.return_value = mock_change_request
        
        result = service.update_implementation_info(1, impl_in)
        
        assert result.status == ChangeStatusEnum.IMPLEMENTING
        assert result.implementation_start_date == datetime(2024, 6, 1)
        mock_save.assert_called_once()


def test_update_implementation_info_wrong_status(service, mock_change_request):
    """测试错误状态不能更新实施信息"""
    mock_change_request.status = ChangeStatusEnum.SUBMITTED
    
    impl_in = ChangeImplementationRequest(
        implementation_notes="实施完成",
    )
    
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get:
        mock_get.return_value = mock_change_request
        
        with pytest.raises(HTTPException) as exc:
            service.update_implementation_info(1, impl_in)
        
        assert exc.value.status_code == 400


# ============================================================================
# 测试 verify_change_request
# ============================================================================

def test_verify_change_request_success(service, mock_change_request, mock_user):
    """测试验证变更"""
    mock_change_request.status = ChangeStatusEnum.VERIFYING
    
    verify_in = ChangeVerificationRequest(
        verification_notes="验证通过",
    )
    
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get, \
         patch('app.services.project_change_requests.service.save_obj') as mock_save:
        
        mock_get.return_value = mock_change_request
        
        result = service.verify_change_request(1, verify_in, mock_user)
        
        assert result.status == ChangeStatusEnum.CLOSED
        assert result.verification_notes == "验证通过"
        assert result.verified_by_id == 1
        assert result.close_date is not None


def test_verify_change_request_wrong_status(service, mock_change_request, mock_user):
    """测试非验证中状态不能验证"""
    mock_change_request.status = ChangeStatusEnum.IMPLEMENTING
    
    verify_in = ChangeVerificationRequest(
        verification_notes="验证",
    )
    
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get:
        mock_get.return_value = mock_change_request
        
        with pytest.raises(HTTPException) as exc:
            service.verify_change_request(1, verify_in, mock_user)
        
        assert exc.value.status_code == 400
        assert "验证中" in exc.value.detail


# ============================================================================
# 测试 close_change_request
# ============================================================================

def test_close_change_request_success(service, mock_change_request):
    """测试关闭变更"""
    mock_change_request.status = ChangeStatusEnum.IMPLEMENTING
    
    close_in = ChangeCloseRequest(
        close_notes="手动关闭",
    )
    
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get, \
         patch('app.services.project_change_requests.service.save_obj') as mock_save:
        
        mock_get.return_value = mock_change_request
        
        result = service.close_change_request(1, close_in)
        
        assert result.status == ChangeStatusEnum.CLOSED
        assert result.close_notes == "手动关闭"
        assert result.close_date is not None


def test_close_change_request_already_closed(service, mock_change_request):
    """测试已关闭的变更不能重复关闭"""
    mock_change_request.status = ChangeStatusEnum.CLOSED
    
    close_in = ChangeCloseRequest(
        close_notes="关闭",
    )
    
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get:
        mock_get.return_value = mock_change_request
        
        with pytest.raises(HTTPException) as exc:
            service.close_change_request(1, close_in)
        
        assert exc.value.status_code == 400
        assert "关闭或取消" in exc.value.detail


def test_close_change_request_already_cancelled(service, mock_change_request):
    """测试已取消的变更不能关闭"""
    mock_change_request.status = ChangeStatusEnum.CANCELLED
    
    close_in = ChangeCloseRequest(
        close_notes="关闭",
    )
    
    with patch('app.services.project_change_requests.service.get_or_404') as mock_get:
        mock_get.return_value = mock_change_request
        
        with pytest.raises(HTTPException) as exc:
            service.close_change_request(1, close_in)
        
        assert exc.value.status_code == 400


# ============================================================================
# 测试 get_statistics
# ============================================================================

def test_get_statistics_all_changes(service, mock_db):
    """测试获取所有变更统计"""
    # Create mock changes with proper value attributes
    mock_change_1 = MagicMock()
    mock_change_1.status = MagicMock()
    mock_change_1.status.value = "SUBMITTED"
    mock_change_1.change_type = MagicMock()
    mock_change_1.change_type.value = "SCOPE"
    mock_change_1.change_source = MagicMock()
    mock_change_1.change_source.value = "CUSTOMER"
    mock_change_1.cost_impact = Decimal("10000")
    mock_change_1.time_impact = 5
    
    mock_change_2 = MagicMock()
    mock_change_2.status = MagicMock()
    mock_change_2.status.value = "APPROVED"
    mock_change_2.change_type = MagicMock()
    mock_change_2.change_type.value = "SCHEDULE"
    mock_change_2.change_source = MagicMock()
    mock_change_2.change_source.value = "INTERNAL"
    mock_change_2.cost_impact = Decimal("20000")
    mock_change_2.time_impact = 10
    
    mock_change_3 = MagicMock()
    mock_change_3.status = MagicMock()
    mock_change_3.status.value = "PENDING_APPROVAL"
    mock_change_3.change_type = MagicMock()
    mock_change_3.change_type.value = "COST"
    mock_change_3.change_source = MagicMock()
    mock_change_3.change_source.value = "TECHNICAL"
    mock_change_3.cost_impact = None
    mock_change_3.time_impact = None
    
    mock_changes = [mock_change_1, mock_change_2, mock_change_3]
    
    mock_query = MagicMock()
    mock_query.all.return_value = mock_changes
    mock_db.query.return_value = mock_query
    
    result = service.get_statistics()
    
    assert result.total == 3
    assert result.by_status["SUBMITTED"] == 1
    assert result.by_status["APPROVED"] == 1
    assert result.by_status["PENDING_APPROVAL"] == 1
    assert result.by_type["SCOPE"] == 1
    assert result.by_source["CUSTOMER"] == 1
    assert result.pending_approval == 1
    assert result.approved == 1
    assert result.total_cost_impact == Decimal("30000")
    assert result.total_time_impact == 15


def test_get_statistics_filter_by_project(service, mock_db):
    """测试按项目统计"""
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = []
    mock_db.query.return_value = mock_query
    
    result = service.get_statistics(project_id=1)
    
    mock_query.filter.assert_called()


def test_get_statistics_filter_by_date_range(service, mock_db):
    """测试按日期范围统计"""
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = []
    mock_db.query.return_value = mock_query
    
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    
    result = service.get_statistics(start_date=start_date, end_date=end_date)
    
    assert mock_query.filter.call_count >= 2


def test_get_statistics_empty_result(service, mock_db):
    """测试无数据时的统计"""
    mock_query = MagicMock()
    mock_query.all.return_value = []
    mock_db.query.return_value = mock_query
    
    result = service.get_statistics()
    
    assert result.total == 0
    assert result.by_status == {}
    assert result.pending_approval == 0
    assert result.total_cost_impact == Decimal(0)
    assert result.total_time_impact == 0
