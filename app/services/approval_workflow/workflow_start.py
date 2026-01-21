# -*- coding: utf-8 -*-
"""
审批启动模块
提供审批流程启动和工作流路由选择功能
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import and_

from app.models.enums import ApprovalActionEnum, ApprovalRecordStatusEnum
from app.models.sales import (
    ApprovalHistory,
    ApprovalRecord,
    ApprovalWorkflow,
)


class WorkflowStartMixin:
    """审批启动功能混入类"""

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
