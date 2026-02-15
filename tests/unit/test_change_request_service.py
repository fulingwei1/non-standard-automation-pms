# -*- coding: utf-8 -*-
"""
项目变更管理模块单元测试
包含数据模型、API端点、工作流状态机的测试
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.models.change_request import (
    ChangeRequest,
    ChangeApprovalRecord,
    ChangeNotification,
)
from app.models.enums import (
    ChangeTypeEnum,
    ChangeSourceEnum,
    ChangeStatusEnum,
    ImpactLevelEnum,
    ApprovalDecisionEnum,
)


@pytest.fixture
def db():
    """模拟数据库会话"""
    return MagicMock()


@pytest.fixture
def mock_user():
    """模拟用户"""
    user = MagicMock()
    user.id = 1
    user.username = "testuser"
    user.real_name = "测试用户"
    user.is_superuser = False
    return user


@pytest.fixture
def mock_project():
    """模拟项目"""
    project = MagicMock()
    project.id = 1
    project.project_code = "PRJ001"
    project.project_name = "测试项目"
    return project


@pytest.fixture
def sample_change_request():
    """示例变更请求"""
    return ChangeRequest(
        id=1,
        change_code="CHG-PRJ001-001",
        project_id=1,
        title="需求变更测试",
        description="测试描述",
        change_type=ChangeTypeEnum.REQUIREMENT,
        change_source=ChangeSourceEnum.CUSTOMER,
        submitter_id=1,
        submitter_name="测试用户",
        status=ChangeStatusEnum.SUBMITTED,
        approval_decision=ApprovalDecisionEnum.PENDING,
        cost_impact=Decimal("10000.00"),
        cost_impact_level=ImpactLevelEnum.MEDIUM,
        time_impact=10,
        time_impact_level=ImpactLevelEnum.MEDIUM,
    )


# ==================== 测试用例 1-5: 创建变更请求 ====================

class TestCreateChangeRequest:
    """测试创建变更请求"""
    
    def test_create_change_request_success(self, db, mock_user, mock_project):
        """测试1：成功创建变更请求"""
        from app.api.v1.endpoints.projects.change_requests import generate_change_code
        
        db.query.return_value.filter.return_value.first.return_value = mock_project
        db.query.return_value.filter.return_value.scalar.return_value = 0
        
        change_code = generate_change_code(db, 1)
        assert change_code == "CHG-PRJ001-001"
    
    def test_create_change_request_invalid_project(self, db, mock_user):
        """测试2：创建变更请求时项目不存在"""
        from app.api.v1.endpoints.projects.change_requests import generate_change_code
        from fastapi import HTTPException
        
        db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            generate_change_code(db, 999)
        assert exc_info.value.status_code == 404
    
    def test_change_code_sequential(self, db, mock_project):
        """测试3：变更编号连续生成"""
        from app.api.v1.endpoints.projects.change_requests import generate_change_code
        
        db.query.return_value.filter.return_value.first.return_value = mock_project
        db.query.return_value.filter.return_value.scalar.return_value = 5
        
        change_code = generate_change_code(db, 1)
        assert change_code == "CHG-PRJ001-006"
    
    def test_create_with_impact_assessment(self, sample_change_request):
        """测试4：创建带影响评估的变更"""
        assert sample_change_request.cost_impact == Decimal("10000.00")
        assert sample_change_request.cost_impact_level == ImpactLevelEnum.MEDIUM
        assert sample_change_request.time_impact == 10
    
    def test_create_with_attachments(self):
        """测试5：创建带附件的变更"""
        attachments = [
            {"name": "需求文档.pdf", "url": "/uploads/doc.pdf", "size": 1024}
        ]
        change = ChangeRequest(
            change_code="CHG-TEST-001",
            project_id=1,
            title="测试",
            change_type=ChangeTypeEnum.REQUIREMENT,
            change_source=ChangeSourceEnum.CUSTOMER,
            submitter_id=1,
            status=ChangeStatusEnum.SUBMITTED,
            approval_decision=ApprovalDecisionEnum.PENDING,
            attachments=attachments,
        )
        assert len(change.attachments) == 1
        assert change.attachments[0]["name"] == "需求文档.pdf"


# ==================== 测试用例 6-10: 状态转换验证 ====================

class TestStatusTransition:
    """测试状态转换"""
    
    def test_valid_transition_submitted_to_assessing(self):
        """测试6：有效转换 - 已提交到影响评估中"""
        from app.api.v1.endpoints.projects.change_requests import validate_status_transition
        
        assert validate_status_transition(
            ChangeStatusEnum.SUBMITTED,
            ChangeStatusEnum.ASSESSING
        ) is True
    
    def test_valid_transition_assessing_to_pending(self):
        """测试7：有效转换 - 影响评估中到待审批"""
        from app.api.v1.endpoints.projects.change_requests import validate_status_transition
        
        assert validate_status_transition(
            ChangeStatusEnum.ASSESSING,
            ChangeStatusEnum.PENDING_APPROVAL
        ) is True
    
    def test_invalid_transition_rejected_to_approved(self):
        """测试8：无效转换 - 已拒绝到已批准"""
        from app.api.v1.endpoints.projects.change_requests import validate_status_transition
        
        assert validate_status_transition(
            ChangeStatusEnum.REJECTED,
            ChangeStatusEnum.APPROVED
        ) is False
    
    def test_invalid_transition_closed_to_implementing(self):
        """测试9：无效转换 - 已关闭到实施中"""
        from app.api.v1.endpoints.projects.change_requests import validate_status_transition
        
        assert validate_status_transition(
            ChangeStatusEnum.CLOSED,
            ChangeStatusEnum.IMPLEMENTING
        ) is False
    
    def test_valid_transition_implementing_to_verifying(self):
        """测试10：有效转换 - 实施中到验证中"""
        from app.api.v1.endpoints.projects.change_requests import validate_status_transition
        
        assert validate_status_transition(
            ChangeStatusEnum.IMPLEMENTING,
            ChangeStatusEnum.VERIFYING
        ) is True


# ==================== 测试用例 11-15: 审批流程 ====================

class TestApprovalWorkflow:
    """测试审批流程"""
    
    def test_approve_change_request(self, sample_change_request, mock_user):
        """测试11：批准变更请求"""
        sample_change_request.status = ChangeStatusEnum.PENDING_APPROVAL
        sample_change_request.approver_id = mock_user.id
        sample_change_request.approver_name = mock_user.real_name
        sample_change_request.approval_decision = ApprovalDecisionEnum.APPROVED
        sample_change_request.status = ChangeStatusEnum.APPROVED
        
        assert sample_change_request.status == ChangeStatusEnum.APPROVED
        assert sample_change_request.approval_decision == ApprovalDecisionEnum.APPROVED
    
    def test_reject_change_request(self, sample_change_request, mock_user):
        """测试12：拒绝变更请求"""
        sample_change_request.status = ChangeStatusEnum.PENDING_APPROVAL
        sample_change_request.approval_decision = ApprovalDecisionEnum.REJECTED
        sample_change_request.status = ChangeStatusEnum.REJECTED
        
        assert sample_change_request.status == ChangeStatusEnum.REJECTED
        assert sample_change_request.approval_decision == ApprovalDecisionEnum.REJECTED
    
    def test_return_change_request(self, sample_change_request):
        """测试13：退回变更请求修改"""
        sample_change_request.status = ChangeStatusEnum.PENDING_APPROVAL
        sample_change_request.approval_decision = ApprovalDecisionEnum.RETURNED
        sample_change_request.status = ChangeStatusEnum.ASSESSING
        
        assert sample_change_request.status == ChangeStatusEnum.ASSESSING
        assert sample_change_request.approval_decision == ApprovalDecisionEnum.RETURNED
    
    def test_create_approval_record(self, mock_user):
        """测试14：创建审批记录"""
        approval_record = ChangeApprovalRecord(
            change_request_id=1,
            approver_id=mock_user.id,
            approver_name=mock_user.real_name,
            approver_role="PM",
            decision=ApprovalDecisionEnum.APPROVED,
            comments="同意该变更",
        )
        
        assert approval_record.change_request_id == 1
        assert approval_record.decision == ApprovalDecisionEnum.APPROVED
        assert approval_record.comments == "同意该变更"
    
    def test_approval_with_attachments(self):
        """测试15：带附件的审批"""
        attachments = [
            {"name": "审批意见.pdf", "url": "/uploads/approval.pdf"}
        ]
        approval_record = ChangeApprovalRecord(
            change_request_id=1,
            approver_id=1,
            approver_name="审批人",
            decision=ApprovalDecisionEnum.APPROVED,
            attachments=attachments,
        )
        
        assert len(approval_record.attachments) == 1


# ==================== 测试用例 16-20: 通知系统 ====================

class TestNotificationSystem:
    """测试通知系统"""
    
    def test_create_notification(self):
        """测试16：创建通知记录"""
        notification = ChangeNotification(
            change_request_id=1,
            notification_type="SUBMITTED",
            recipient_id=2,
            recipient_name="项目经理",
            notification_channel="EMAIL",
            notification_title="新的变更请求",
            notification_content="有新的变更请求需要审批",
        )
        
        assert notification.notification_type == "SUBMITTED"
        assert notification.notification_channel == "EMAIL"
    
    def test_notification_sent_status(self):
        """测试17：通知发送状态"""
        notification = ChangeNotification(
            change_request_id=1,
            notification_type="APPROVED",
            recipient_id=1,
            is_sent=True,
            sent_at=datetime.utcnow(),
        )
        
        assert notification.is_sent is True
        assert notification.sent_at is not None
    
    def test_notification_read_status(self):
        """测试18：通知阅读状态"""
        notification = ChangeNotification(
            change_request_id=1,
            notification_type="APPROVED",
            recipient_id=1,
            is_read=True,
            read_at=datetime.utcnow(),
        )
        
        assert notification.is_read is True
        assert notification.read_at is not None
    
    def test_notification_to_customer(self, sample_change_request):
        """测试19：客户通知"""
        sample_change_request.notify_customer = True
        assert sample_change_request.notify_customer is True
    
    def test_notification_to_team(self, sample_change_request):
        """测试20：团队通知"""
        sample_change_request.notify_team = True
        assert sample_change_request.notify_team is True


# ==================== 测试用例 21-25: 完整工作流 ====================

class TestCompleteWorkflow:
    """测试完整工作流"""
    
    def test_workflow_submitted_to_closed(self):
        """测试21：完整工作流 - 提交到关闭"""
        change = ChangeRequest(
            change_code="CHG-TEST-001",
            project_id=1,
            title="测试工作流",
            change_type=ChangeTypeEnum.REQUIREMENT,
            change_source=ChangeSourceEnum.CUSTOMER,
            submitter_id=1,
            status=ChangeStatusEnum.SUBMITTED,
            approval_decision=ApprovalDecisionEnum.PENDING,
        )
        
        # 提交 -> 影响评估
        change.status = ChangeStatusEnum.ASSESSING
        assert change.status == ChangeStatusEnum.ASSESSING
        
        # 影响评估 -> 待审批
        change.status = ChangeStatusEnum.PENDING_APPROVAL
        assert change.status == ChangeStatusEnum.PENDING_APPROVAL
        
        # 待审批 -> 已批准
        change.status = ChangeStatusEnum.APPROVED
        change.approval_decision = ApprovalDecisionEnum.APPROVED
        assert change.status == ChangeStatusEnum.APPROVED
        
        # 已批准 -> 实施中
        change.status = ChangeStatusEnum.IMPLEMENTING
        assert change.status == ChangeStatusEnum.IMPLEMENTING
        
        # 实施中 -> 验证中
        change.status = ChangeStatusEnum.VERIFYING
        assert change.status == ChangeStatusEnum.VERIFYING
        
        # 验证中 -> 已关闭
        change.status = ChangeStatusEnum.CLOSED
        assert change.status == ChangeStatusEnum.CLOSED
    
    def test_workflow_rejected(self):
        """测试22：工作流 - 拒绝场景"""
        change = ChangeRequest(
            change_code="CHG-TEST-002",
            project_id=1,
            title="测试拒绝",
            change_type=ChangeTypeEnum.SCOPE,
            change_source=ChangeSourceEnum.INTERNAL,
            submitter_id=1,
            status=ChangeStatusEnum.PENDING_APPROVAL,
            approval_decision=ApprovalDecisionEnum.PENDING,
        )
        
        # 待审批 -> 已拒绝
        change.status = ChangeStatusEnum.REJECTED
        change.approval_decision = ApprovalDecisionEnum.REJECTED
        assert change.status == ChangeStatusEnum.REJECTED
    
    def test_workflow_cancelled(self):
        """测试23：工作流 - 取消场景"""
        change = ChangeRequest(
            change_code="CHG-TEST-003",
            project_id=1,
            title="测试取消",
            change_type=ChangeTypeEnum.TECHNICAL,
            change_source=ChangeSourceEnum.INTERNAL,
            submitter_id=1,
            status=ChangeStatusEnum.SUBMITTED,
            approval_decision=ApprovalDecisionEnum.PENDING,
        )
        
        # 已提交 -> 已取消
        change.status = ChangeStatusEnum.CANCELLED
        assert change.status == ChangeStatusEnum.CANCELLED
    
    def test_implementation_info(self):
        """测试24：实施信息更新"""
        change = ChangeRequest(
            change_code="CHG-TEST-004",
            project_id=1,
            title="测试实施",
            change_type=ChangeTypeEnum.DESIGN,
            change_source=ChangeSourceEnum.CUSTOMER,
            submitter_id=1,
            status=ChangeStatusEnum.IMPLEMENTING,
            approval_decision=ApprovalDecisionEnum.PENDING,
            implementation_plan="实施计划说明",
            implementation_start_date=datetime(2026, 2, 15),
        )
        
        assert change.implementation_plan == "实施计划说明"
        assert change.implementation_start_date is not None
    
    def test_verification_info(self):
        """测试25：验证信息更新"""
        change = ChangeRequest(
            change_code="CHG-TEST-005",
            project_id=1,
            title="测试验证",
            change_type=ChangeTypeEnum.REQUIREMENT,
            change_source=ChangeSourceEnum.CUSTOMER,
            submitter_id=1,
            status=ChangeStatusEnum.VERIFYING,
            approval_decision=ApprovalDecisionEnum.PENDING,
            verification_notes="验证通过",
            verified_by_id=2,
            verified_by_name="验证人",
        )
        
        assert change.verification_notes == "验证通过"
        assert change.verified_by_id == 2


# ==================== 测试用例 26-28: 影响评估 ====================

class TestImpactAssessment:
    """测试影响评估"""
    
    def test_cost_impact_assessment(self):
        """测试26：成本影响评估"""
        change = ChangeRequest(
            change_code="CHG-TEST-006",
            project_id=1,
            title="测试成本影响",
            change_type=ChangeTypeEnum.SCOPE,
            change_source=ChangeSourceEnum.CUSTOMER,
            submitter_id=1,
            status=ChangeStatusEnum.SUBMITTED,
            approval_decision=ApprovalDecisionEnum.PENDING,
            cost_impact=Decimal("50000.00"),
            cost_impact_level=ImpactLevelEnum.HIGH,
        )
        
        assert change.cost_impact == Decimal("50000.00")
        assert change.cost_impact_level == ImpactLevelEnum.HIGH
    
    def test_time_impact_assessment(self):
        """测试27：时间影响评估"""
        change = ChangeRequest(
            change_code="CHG-TEST-007",
            project_id=1,
            title="测试时间影响",
            change_type=ChangeTypeEnum.TECHNICAL,
            change_source=ChangeSourceEnum.INTERNAL,
            submitter_id=1,
            status=ChangeStatusEnum.SUBMITTED,
            approval_decision=ApprovalDecisionEnum.PENDING,
            time_impact=30,
            time_impact_level=ImpactLevelEnum.CRITICAL,
        )
        
        assert change.time_impact == 30
        assert change.time_impact_level == ImpactLevelEnum.CRITICAL
    
    def test_impact_details_json(self):
        """测试28：影响详情JSON"""
        impact_details = {
            "cost": {"labor": 10000, "material": 5000, "total": 15000},
            "schedule": {"delay_days": 15, "affected_milestones": ["MS-001"]},
            "scope": {"added_features": ["F1", "F2"]},
        }
        
        change = ChangeRequest(
            change_code="CHG-TEST-008",
            project_id=1,
            title="测试影响详情",
            change_type=ChangeTypeEnum.REQUIREMENT,
            change_source=ChangeSourceEnum.CUSTOMER,
            submitter_id=1,
            status=ChangeStatusEnum.SUBMITTED,
            approval_decision=ApprovalDecisionEnum.PENDING,
            impact_details=impact_details,
        )
        
        assert change.impact_details["cost"]["total"] == 15000
        assert len(change.impact_details["scope"]["added_features"]) == 2


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
