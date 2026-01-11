# -*- coding: utf-8 -*-
"""
审批工作流服务
支持多级审批、审批路由、审批委托
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.sales import (
    ApprovalWorkflow, ApprovalWorkflowStep, ApprovalRecord, ApprovalHistory
)
from app.models.user import User
from app.models.enums import (
    WorkflowTypeEnum, ApprovalRecordStatusEnum, ApprovalActionEnum
)


class ApprovalWorkflowService:
    """审批工作流服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def start_approval(
        self,
        entity_type: str,
        entity_id: int,
        initiator_id: int,
        workflow_id: Optional[int] = None,
        routing_params: Optional[Dict[str, Any]] = None,
        comment: Optional[str] = None
    ) -> ApprovalRecord:
        """
        启动审批流程
        
        Args:
            entity_type: 实体类型（QUOTE/CONTRACT/INVOICE）
            entity_id: 实体ID
            initiator_id: 发起人ID
            workflow_id: 指定工作流ID（可选，不指定则根据路由规则自动选择）
            routing_params: 路由参数（如金额、类型等，用于自动选择工作流）
            comment: 提交说明
        
        Returns:
            ApprovalRecord: 审批记录
        """
        # 如果指定了工作流ID，直接使用
        if workflow_id:
            workflow = self.db.query(ApprovalWorkflow).filter(
                and_(
                    ApprovalWorkflow.id == workflow_id,
                    ApprovalWorkflow.workflow_type == entity_type,
                    ApprovalWorkflow.is_active == True
                )
            ).first()
            if not workflow:
                raise ValueError(f"工作流 {workflow_id} 不存在或已禁用")
        else:
            # 根据路由规则自动选择工作流
            workflow = self._select_workflow_by_routing(entity_type, routing_params)
            if not workflow:
                raise ValueError(f"未找到适合的 {entity_type} 审批工作流")
        
        # 检查是否已有审批记录
        existing = self.db.query(ApprovalRecord).filter(
            and_(
                ApprovalRecord.entity_type == entity_type,
                ApprovalRecord.entity_id == entity_id,
                ApprovalRecord.status == ApprovalRecordStatusEnum.PENDING
            )
        ).first()
        if existing:
            raise ValueError("该实体已有待审批的记录")
        
        # 创建审批记录
        record = ApprovalRecord(
            entity_type=entity_type,
            entity_id=entity_id,
            workflow_id=workflow.id,
            current_step=1,
            status=ApprovalRecordStatusEnum.PENDING,
            initiator_id=initiator_id
        )
        self.db.add(record)
        self.db.flush()
        
        # 创建第一条历史记录（提交记录）
        if comment:
            history = ApprovalHistory(
                approval_record_id=record.id,
                step_order=0,
                approver_id=initiator_id,
                action=ApprovalActionEnum.APPROVE,  # 提交视为通过第一步
                comment=comment,
                action_at=datetime.now()
            )
            self.db.add(history)
        
        self.db.commit()
        self.db.refresh(record)
        
        return record
    
    def _select_workflow_by_routing(
        self,
        entity_type: str,
        routing_params: Optional[Dict[str, Any]] = None
    ) -> Optional[ApprovalWorkflow]:
        """
        根据路由规则选择工作流
        
        Args:
            entity_type: 实体类型
            routing_params: 路由参数（如金额、类型等）
        
        Returns:
            Optional[ApprovalWorkflow]: 选中的工作流，如果没有则返回None
        """
        # 查询该类型的所有启用工作流
        workflows = self.db.query(ApprovalWorkflow).filter(
            and_(
                ApprovalWorkflow.workflow_type == entity_type,
                ApprovalWorkflow.is_active == True
            )
        ).all()
        
        if not workflows:
            return None
        
        # 如果只有一个，直接返回
        if len(workflows) == 1:
            return workflows[0]
        
        # 如果有多个，根据路由规则选择
        # 按优先级排序：有具体路由规则的工作流优先于默认工作流
        workflows_with_rules = [w for w in workflows if w.routing_rules]
        default_workflows = [w for w in workflows if not w.routing_rules]

        selected_workflow = None

        if routing_params and workflows_with_rules:
            # 根据路由参数匹配最合适的工作流
            amount = routing_params.get('amount', 0)
            urgency = routing_params.get('urgency', 'normal')  # normal/urgent/critical
            customer_type = routing_params.get('customer_type', '')
            project_type = routing_params.get('project_type', '')

            # 评分系统：根据匹配度评分
            best_score = -1
            best_workflow = None

            for workflow in workflows_with_rules:
                rules = workflow.routing_rules or {}
                score = 0

                # 金额匹配：检查金额是否在规则范围内
                if 'min_amount' in rules:
                    min_amount = rules.get('min_amount', 0)
                    max_amount = rules.get('max_amount', float('inf'))
                    if min_amount <= amount <= max_amount:
                        score += 10  # 金额匹配优先级最高
                    elif amount > max_amount:
                        score += 5  # 金额超过范围也可以作为备选

                # 紧急程度匹配
                if 'urgency' in rules:
                    if rules['urgency'] == urgency:
                        score += 5

                # 客户类型匹配
                if 'customer_types' in rules and customer_type:
                    if customer_type in rules.get('customer_types', []):
                        score += 3

                # 项目类型匹配
                if 'project_types' in rules and project_type:
                    if project_type in rules.get('project_types', []):
                        score += 3

                # 默认标记
                if rules.get('default', False):
                    score += 1

                if score > best_score:
                    best_score = score
                    best_workflow = workflow

            selected_workflow = best_workflow

        # 如果没有匹配到，使用默认工作流
        if not selected_workflow:
            # 查找标记为默认的工作流
            for workflow in default_workflows:
                rules = workflow.routing_rules or {}
                if rules.get('default', False) or not rules:
                    selected_workflow = workflow
                    break

            # 如果还没有，选择第一个有规则的或第一个默认的
            if not selected_workflow:
                selected_workflow = workflows_with_rules[0] if workflows_with_rules else workflows[0]

        return selected_workflow
    
    def get_current_step(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        获取当前审批步骤信息
        
        Args:
            record_id: 审批记录ID
        
        Returns:
            Optional[Dict[str, Any]]: 当前步骤信息
        """
        record = self.db.query(ApprovalRecord).filter(
            ApprovalRecord.id == record_id
        ).first()
        
        if not record:
            return None
        
        # 获取工作流步骤
        step = self.db.query(ApprovalWorkflowStep).filter(
            and_(
                ApprovalWorkflowStep.workflow_id == record.workflow_id,
                ApprovalWorkflowStep.step_order == record.current_step
            )
        ).first()
        
        if not step:
            return None
        
        return {
            "step_order": step.step_order,
            "step_name": step.step_name,
            "approver_role": step.approver_role,
            "approver_id": step.approver_id,
            "is_required": step.is_required,
            "can_delegate": step.can_delegate,
            "can_withdraw": step.can_withdraw,
            "due_hours": step.due_hours
        }
    
    def approve_step(
        self,
        record_id: int,
        approver_id: int,
        comment: Optional[str] = None
    ) -> ApprovalRecord:
        """
        审批通过
        
        Args:
            record_id: 审批记录ID
            approver_id: 审批人ID
            comment: 审批意见
        
        Returns:
            ApprovalRecord: 更新后的审批记录
        """
        record = self.db.query(ApprovalRecord).filter(
            ApprovalRecord.id == record_id
        ).first()
        
        if not record:
            raise ValueError("审批记录不存在")
        
        if record.status != ApprovalRecordStatusEnum.PENDING:
            raise ValueError(f"审批记录状态为 {record.status}，无法审批")
        
        # 获取当前步骤
        step = self.db.query(ApprovalWorkflowStep).filter(
            and_(
                ApprovalWorkflowStep.workflow_id == record.workflow_id,
                ApprovalWorkflowStep.step_order == record.current_step
            )
        ).first()
        
        if not step:
            raise ValueError("当前审批步骤不存在")

        # 验证审批人权限
        if not self._validate_approver(step, approver_id):
            approver = self.db.query(User).filter(User.id == approver_id).first()
            approver_name = approver.real_name if approver else str(approver_id)
            required = step.approver_role or f"指定审批人({step.approver_id})"
            raise ValueError(f"用户 {approver_name} 无权限审批此步骤，需要: {required}")

        # 创建审批历史
        history = ApprovalHistory(
            approval_record_id=record.id,
            step_order=record.current_step,
            approver_id=approver_id,
            action=ApprovalActionEnum.APPROVE,
            comment=comment,
            action_at=datetime.now()
        )
        self.db.add(history)
        
        # 检查是否还有下一步
        next_step = self.db.query(ApprovalWorkflowStep).filter(
            and_(
                ApprovalWorkflowStep.workflow_id == record.workflow_id,
                ApprovalWorkflowStep.step_order == record.current_step + 1
            )
        ).first()
        
        if next_step:
            # 还有下一步，更新当前步骤
            record.current_step += 1
        else:
            # 没有下一步，审批完成
            record.status = ApprovalRecordStatusEnum.APPROVED
        
        self.db.commit()
        self.db.refresh(record)
        
        return record
    
    def reject_step(
        self,
        record_id: int,
        approver_id: int,
        comment: str
    ) -> ApprovalRecord:
        """
        审批驳回
        
        Args:
            record_id: 审批记录ID
            approver_id: 审批人ID
            comment: 驳回原因（必填）
        
        Returns:
            ApprovalRecord: 更新后的审批记录
        """
        if not comment:
            raise ValueError("驳回原因不能为空")
        
        record = self.db.query(ApprovalRecord).filter(
            ApprovalRecord.id == record_id
        ).first()
        
        if not record:
            raise ValueError("审批记录不存在")
        
        if record.status != ApprovalRecordStatusEnum.PENDING:
            raise ValueError(f"审批记录状态为 {record.status}，无法驳回")
        
        # 创建审批历史
        history = ApprovalHistory(
            approval_record_id=record.id,
            step_order=record.current_step,
            approver_id=approver_id,
            action=ApprovalActionEnum.REJECT,
            comment=comment,
            action_at=datetime.now()
        )
        self.db.add(history)
        
        # 更新状态为驳回
        record.status = ApprovalRecordStatusEnum.REJECTED
        
        self.db.commit()
        self.db.refresh(record)
        
        return record
    
    def delegate_step(
        self,
        record_id: int,
        approver_id: int,
        delegate_to_id: int,
        comment: Optional[str] = None
    ) -> ApprovalRecord:
        """
        审批委托
        
        Args:
            record_id: 审批记录ID
            approver_id: 原审批人ID
            delegate_to_id: 委托给的用户ID
            comment: 委托说明
        
        Returns:
            ApprovalRecord: 更新后的审批记录
        """
        record = self.db.query(ApprovalRecord).filter(
            ApprovalRecord.id == record_id
        ).first()
        
        if not record:
            raise ValueError("审批记录不存在")
        
        # 获取当前步骤
        step = self.db.query(ApprovalWorkflowStep).filter(
            and_(
                ApprovalWorkflowStep.workflow_id == record.workflow_id,
                ApprovalWorkflowStep.step_order == record.current_step
            )
        ).first()
        
        if not step or not step.can_delegate:
            raise ValueError("当前步骤不允许委托")
        
        # 创建审批历史
        history = ApprovalHistory(
            approval_record_id=record.id,
            step_order=record.current_step,
            approver_id=approver_id,
            action=ApprovalActionEnum.DELEGATE,
            comment=comment,
            delegate_to_id=delegate_to_id,
            action_at=datetime.now()
        )
        self.db.add(history)
        
        # 更新当前步骤的审批人（临时）
        step.approver_id = delegate_to_id
        
        self.db.commit()
        self.db.refresh(record)
        
        return record
    
    def withdraw_approval(
        self,
        record_id: int,
        initiator_id: int,
        comment: Optional[str] = None
    ) -> ApprovalRecord:
        """
        撤回审批（在下一级审批前）
        
        Args:
            record_id: 审批记录ID
            initiator_id: 发起人ID
            comment: 撤回说明
        
        Returns:
            ApprovalRecord: 更新后的审批记录
        """
        record = self.db.query(ApprovalRecord).filter(
            ApprovalRecord.id == record_id
        ).first()
        
        if not record:
            raise ValueError("审批记录不存在")
        
        if record.initiator_id != initiator_id:
            raise ValueError("只有发起人才能撤回审批")
        
        if record.status != ApprovalRecordStatusEnum.PENDING:
            raise ValueError(f"审批记录状态为 {record.status}，无法撤回")
        
        # 检查是否已有审批历史（除了提交记录）
        has_approval = self.db.query(ApprovalHistory).filter(
            and_(
                ApprovalHistory.approval_record_id == record.id,
                ApprovalHistory.step_order > 0,
                ApprovalHistory.action == ApprovalActionEnum.APPROVE
            )
        ).first()
        
        if has_approval:
            raise ValueError("已有审批人通过，无法撤回")
        
        # 创建撤回历史
        history = ApprovalHistory(
            approval_record_id=record.id,
            step_order=record.current_step,
            approver_id=initiator_id,
            action=ApprovalActionEnum.WITHDRAW,
            comment=comment,
            action_at=datetime.now()
        )
        self.db.add(history)
        
        # 更新状态为已取消
        record.status = ApprovalRecordStatusEnum.CANCELLED
        
        self.db.commit()
        self.db.refresh(record)
        
        return record
    
    def get_approval_history(self, record_id: int) -> List[ApprovalHistory]:
        """
        获取审批历史
        
        Args:
            record_id: 审批记录ID
        
        Returns:
            List[ApprovalHistory]: 审批历史列表
        """
        return self.db.query(ApprovalHistory).filter(
            ApprovalHistory.approval_record_id == record_id
        ).order_by(ApprovalHistory.step_order, ApprovalHistory.action_at).all()
    
    def get_approval_record(
        self,
        entity_type: str,
        entity_id: int
    ) -> Optional[ApprovalRecord]:
        """
        获取实体的审批记录
        
        Args:
            entity_type: 实体类型
            entity_id: 实体ID
        
        Returns:
            Optional[ApprovalRecord]: 审批记录，如果没有则返回None
        """
        return self.db.query(ApprovalRecord).filter(
            and_(
                ApprovalRecord.entity_type == entity_type,
                ApprovalRecord.entity_id == entity_id
            )
        ).order_by(ApprovalRecord.created_at.desc()).first()

    def _validate_approver(
        self,
        step: ApprovalWorkflowStep,
        approver_id: int
    ) -> bool:
        """
        验证审批人是否有权限审批当前步骤

        Args:
            step: 审批步骤配置
            approver_id: 审批人ID

        Returns:
            bool: 是否有权限
        """
        approver = self.db.query(User).filter(User.id == approver_id).first()
        if not approver or not approver.is_active:
            return False

        # 超级管理员可以审批所有步骤
        if approver.is_superuser:
            return True

        # 1. 检查是否是指定审批人
        if step.approver_id and step.approver_id == approver_id:
            return True

        # 2. 检查角色匹配
        if step.approver_role:
            # 查询用户的角色
            from app.models.user import UserRole, Role

            user_roles = self.db.query(UserRole).filter(
                UserRole.user_id == approver_id
            ).all()

            role_codes = [ur.role.role_code for ur in user_roles if ur.role]

            # 检查是否有所需角色
            if step.approver_role in role_codes:
                return True

        # 3. 检查是否有委托权限（检查审批历史中是否有委托给当前用户的记录）
        # 如果原审批人将步骤委托给了当前用户
        if step.approver_id and step.approver_id != approver_id:
            delegation_history = self.db.query(ApprovalHistory).filter(
                and_(
                    ApprovalHistory.step_order == step.step_order,
                    ApprovalHistory.action == ApprovalActionEnum.DELEGATE,
                    ApprovalHistory.approver_id == step.approver_id,
                    ApprovalHistory.delegate_to_id == approver_id
                )
            ).first()

            if delegation_history:
                return True

        return False
