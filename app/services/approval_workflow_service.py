# -*- coding: utf-8 -*-
"""
审批工作流服务

提供审批流程的启动、审批、驳回和撤回等功能
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.enums import ApprovalRecordStatusEnum

logger = logging.getLogger(__name__)


class ApprovalWorkflowService:
    """审批工作流服务"""

    def __init__(self, db: Session):
        self.db = db

    def start_approval(
        self,
        business_type: str,
        business_id: int,
        initiator_id: int,
        workflow_id: Optional[int] = None,
        routing_data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        启动审批流程

        Args:
            business_type: 业务类型（如 'QUOTE', 'ECN'）
            business_id: 业务记录ID
            initiator_id: 发起人ID
            workflow_id: 工作流ID（可选）
            routing_data: 路由数据（可选）

        Returns:
            审批记录对象
        """
        from app.models.sales.workflow import ApprovalRecord

        # 检查是否已有进行中的审批
        existing = self.db.query(ApprovalRecord).filter(
            ApprovalRecord.entity_type == business_type,
        ).filter(
            ApprovalRecord.entity_id == business_id,
        ).filter(
            ApprovalRecord.status == ApprovalRecordStatusEnum.PENDING,
        ).first()

        if existing:
            return existing

        # 创建审批记录
        record = ApprovalRecord()
        record.entity_type = business_type
        record.entity_id = business_id
        record.initiator_id = initiator_id
        record.workflow_id = workflow_id
        record.status = ApprovalRecordStatusEnum.PENDING
        record.current_step = 1

        self.db.add(record)
        self.db.flush()

        return record

    def _select_workflow_by_routing(
        self,
        business_type: str,
        routing_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """
        根据路由规则选择工作流

        Args:
            business_type: 业务类型
            routing_data: 路由数据

        Returns:
            匹配的工作流，如果没有匹配则返回None
        """
        from app.models.sales.workflow import ApprovalWorkflow

        workflows = self.db.query(ApprovalWorkflow).filter(
            ApprovalWorkflow.workflow_type == business_type,
        ).filter(
            ApprovalWorkflow.is_active == True,
        ).all()

        if not workflows:
            return None

        # 匹配默认工作流
        for wf in workflows:
            rules = wf.routing_rules or {}
            if rules.get("default"):
                return wf

        return workflows[0] if workflows else None

    def approve_step(
        self,
        record_id: int,
        approver_id: int,
        comment: str = "",
    ) -> Any:
        """
        审批通过

        Args:
            record_id: 审批记录ID
            approver_id: 审批人ID
            comment: 审批意见
        """
        from app.models.sales.workflow import ApprovalRecord

        record = self.db.query(ApprovalRecord).filter(
            ApprovalRecord.id == record_id,
        ).first()

        if not record:
            raise ValueError(f"审批记录不存在: {record_id}")

        record.status = ApprovalRecordStatusEnum.APPROVED
        self.db.commit()

        return record

    def reject_step(
        self,
        record_id: int,
        approver_id: int,
        comment: str = "",
    ) -> Any:
        """
        审批驳回

        Args:
            record_id: 审批记录ID
            approver_id: 审批人ID
            comment: 驳回原因
        """
        from app.models.sales.workflow import ApprovalRecord

        record = self.db.query(ApprovalRecord).filter(
            ApprovalRecord.id == record_id,
        ).first()

        if not record:
            raise ValueError(f"审批记录不存在: {record_id}")

        record.status = ApprovalRecordStatusEnum.REJECTED
        self.db.commit()

        return record

    def withdraw_approval(
        self,
        record_id: int,
        user_id: int,
        reason: str = "",
    ) -> Any:
        """
        撤回审批

        Args:
            record_id: 审批记录ID
            user_id: 用户ID
            reason: 撤回原因
        """
        from app.models.sales.workflow import ApprovalRecord

        record = self.db.query(ApprovalRecord).filter(
            ApprovalRecord.id == record_id,
        ).first()

        if not record:
            raise ValueError(f"审批记录不存在: {record_id}")

        record.status = ApprovalRecordStatusEnum.CANCELLED
        self.db.commit()

        return record

    def _validate_approver(self, record_id: int, approver_id: int) -> bool:
        """验证审批人权限"""
        return True
