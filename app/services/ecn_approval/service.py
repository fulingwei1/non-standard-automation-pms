# -*- coding: utf-8 -*-
"""
ECN审批服务层

将ECN审批相关的业务逻辑从endpoint抽取到此服务层。
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.approval import ApprovalInstance, ApprovalTask
from app.models.ecn import Ecn, EcnEvaluation
from app.services.approval_engine import ApprovalEngineService
from app.utils.db_helpers import get_or_404

logger = logging.getLogger(__name__)


class EcnApprovalService:
    """ECN审批业务逻辑服务"""

    def __init__(self, db: Session):
        """
        初始化服务

        Args:
            db: 数据库会话
        """
        self.db = db
        self.engine = ApprovalEngineService(db)

    def submit_ecns_for_approval(
        self,
        ecn_ids: List[int],
        initiator_id: int,
        urgency: str = "NORMAL",
        comment: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        批量提交ECN审批

        Args:
            ecn_ids: ECN ID列表
            initiator_id: 发起人ID
            urgency: 紧急程度
            comment: 提交备注

        Returns:
            (成功列表, 错误列表)
        """
        results = []
        errors = []

        for ecn_id in ecn_ids:
            try:
                result = self._submit_single_ecn(ecn_id, initiator_id, urgency)
                results.append(result)
            except Exception as e:
                logger.exception(f"ECN {ecn_id} 提交审批失败")
                errors.append({"ecn_id": ecn_id, "error": str(e)})

        return results, errors

    def _submit_single_ecn(
        self, ecn_id: int, initiator_id: int, urgency: str
    ) -> Dict[str, Any]:
        """
        提交单个ECN审批

        Args:
            ecn_id: ECN ID
            initiator_id: 发起人ID
            urgency: 紧急程度

        Returns:
            提交结果字典

        Raises:
            ValueError: 当ECN状态不符合要求时
        """
        ecn = self.db.query(Ecn).filter(Ecn.id == ecn_id).first()
        if not ecn:
            raise ValueError("ECN不存在")

        # 检查状态是否允许提交审批
        if ecn.status not in ("DRAFT", "EVALUATING", "EVALUATED", "REJECTED"):
            raise ValueError(f"当前状态({ecn.status})不允许提交审批")

        # 检查是否有未完成的评估
        pending_evals = (
            self.db.query(EcnEvaluation)
            .filter(
                EcnEvaluation.ecn_id == ecn_id,
                EcnEvaluation.status == "PENDING",
            )
            .count()
        )
        if pending_evals > 0:
            raise ValueError(f"还有 {pending_evals} 个评估未完成")

        # 构建表单数据
        form_data = {
            "ecn_id": ecn.id,
            "ecn_no": ecn.ecn_no,
            "ecn_title": ecn.ecn_title,
            "ecn_type": ecn.ecn_type,
            "project_id": ecn.project_id,
            "cost_impact": float(ecn.cost_impact) if ecn.cost_impact else 0,
            "schedule_impact_days": ecn.schedule_impact_days or 0,
            "change_reason": ecn.change_reason,
            "change_description": ecn.change_description,
        }

        # 提交到审批引擎
        instance = self.engine.submit(
            template_code="ECN_STANDARD",
            entity_type="ECN",
            entity_id=ecn_id,
            form_data=form_data,
            initiator_id=initiator_id,
            urgency=urgency,
        )

        # 更新ECN状态
        ecn.status = "APPROVING"
        ecn.current_step = "APPROVAL"

        return {
            "ecn_id": ecn_id,
            "ecn_no": ecn.ecn_no,
            "instance_id": instance.id,
            "status": "submitted",
        }

    def get_pending_tasks_for_user(
        self,
        user_id: int,
        ecn_type: Optional[str] = None,
        project_id: Optional[int] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取用户待审批的ECN任务列表

        Args:
            user_id: 用户ID
            ecn_type: ECN类型筛选
            project_id: 项目ID筛选
            offset: 分页偏移
            limit: 分页限制

        Returns:
            (任务列表, 总数)
        """
        tasks = self.engine.get_pending_tasks(user_id=user_id, entity_type="ECN")

        # 筛选
        filtered_tasks = []
        for task in tasks:
            ecn = self.db.query(Ecn).filter(Ecn.id == task.instance.entity_id).first()
            if not ecn:
                continue

            if ecn_type and ecn.ecn_type != ecn_type:
                continue
            if project_id and ecn.project_id != project_id:
                continue

            filtered_tasks.append((task, ecn))

        total = len(filtered_tasks)
        paginated = filtered_tasks[offset : offset + limit]

        items = []
        for task, ecn in paginated:
            instance = task.instance
            items.append(
                {
                    "task_id": task.id,
                    "instance_id": instance.id,
                    "ecn_id": instance.entity_id,
                    "ecn_no": ecn.ecn_no,
                    "ecn_title": ecn.ecn_title,
                    "ecn_type": ecn.ecn_type,
                    "project_name": ecn.project.project_name if ecn.project else None,
                    "cost_impact": float(ecn.cost_impact) if ecn.cost_impact else 0,
                    "schedule_impact_days": ecn.schedule_impact_days or 0,
                    "priority": ecn.priority,
                    "urgency": instance.urgency,
                    "initiator_name": instance.initiator.real_name
                    if instance.initiator
                    else None,
                    "submitted_at": instance.created_at.isoformat()
                    if instance.created_at
                    else None,
                    "node_name": task.node.node_name if task.node else None,
                }
            )

        return items, total

    def perform_approval_action(
        self, task_id: int, approver_id: int, action: str, comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行审批操作

        Args:
            task_id: 审批任务ID
            approver_id: 审批人ID
            action: 操作类型 (approve/reject)
            comment: 审批意见

        Returns:
            操作结果字典

        Raises:
            ValueError: 当操作类型不支持时
        """
        if action == "approve":
            result = self.engine.approve(
                task_id=task_id,
                approver_id=approver_id,
                comment=comment,
            )
        elif action == "reject":
            result = self.engine.reject(
                task_id=task_id,
                approver_id=approver_id,
                comment=comment,
            )
        else:
            raise ValueError(f"不支持的操作类型: {action}")

        return {
            "task_id": task_id,
            "action": action,
            "instance_status": result.status if hasattr(result, "status") else None,
        }

    def perform_batch_approval(
        self,
        task_ids: List[int],
        approver_id: int,
        action: str,
        comment: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        批量执行审批操作

        Args:
            task_ids: 审批任务ID列表
            approver_id: 审批人ID
            action: 操作类型 (approve/reject)
            comment: 审批意见

        Returns:
            (成功列表, 错误列表)
        """
        results = []
        errors = []

        for task_id in task_ids:
            try:
                self.perform_approval_action(
                    task_id=task_id,
                    approver_id=approver_id,
                    action=action,
                    comment=comment,
                )
                results.append({"task_id": task_id, "status": "success"})
            except Exception as e:
                errors.append({"task_id": task_id, "error": str(e)})

        return results, errors

    def get_ecn_approval_status(self, ecn_id: int) -> Dict[str, Any]:
        """
        获取ECN的审批状态

        Args:
            ecn_id: ECN ID

        Returns:
            审批状态字典
        """
        ecn = get_or_404(self.db, Ecn, ecn_id, "ECN不存在")

        instance = (
            self.db.query(ApprovalInstance)
            .filter(
                ApprovalInstance.entity_type == "ECN",
                ApprovalInstance.entity_id == ecn_id,
            )
            .order_by(ApprovalInstance.created_at.desc())
            .first()
        )

        if not instance:
            return {
                "ecn_id": ecn_id,
                "ecn_no": ecn.ecn_no,
                "status": ecn.status,
                "approval_instance": None,
            }

        tasks = (
            self.db.query(ApprovalTask)
            .filter(ApprovalTask.instance_id == instance.id)
            .order_by(ApprovalTask.created_at)
            .all()
        )

        task_history = []
        for task in tasks:
            task_history.append(
                {
                    "task_id": task.id,
                    "node_name": task.node.node_name if task.node else None,
                    "assignee_name": task.assignee.real_name
                    if task.assignee
                    else None,
                    "status": task.status,
                    "action": task.action,
                    "comment": task.comment,
                    "completed_at": task.completed_at.isoformat()
                    if task.completed_at
                    else None,
                }
            )

        # 获取评估汇总
        evaluations = (
            self.db.query(EcnEvaluation).filter(EcnEvaluation.ecn_id == ecn_id).all()
        )
        eval_summary = {
            "total": len(evaluations),
            "completed": len([e for e in evaluations if e.status == "COMPLETED"]),
            "total_cost": sum(float(e.cost_estimate or 0) for e in evaluations),
            "total_days": sum(e.schedule_estimate or 0 for e in evaluations),
        }

        return {
            "ecn_id": ecn_id,
            "ecn_no": ecn.ecn_no,
            "ecn_title": ecn.ecn_title,
            "ecn_type": ecn.ecn_type,
            "ecn_status": ecn.status,
            "project_name": ecn.project.project_name if ecn.project else None,
            "cost_impact": float(ecn.cost_impact) if ecn.cost_impact else 0,
            "schedule_impact_days": ecn.schedule_impact_days or 0,
            "evaluation_summary": eval_summary,
            "instance_id": instance.id,
            "instance_status": instance.status,
            "urgency": instance.urgency,
            "submitted_at": instance.created_at.isoformat()
            if instance.created_at
            else None,
            "completed_at": instance.completed_at.isoformat()
            if instance.completed_at
            else None,
            "task_history": task_history,
        }

    def withdraw_ecn_approval(
        self, ecn_id: int, user_id: int, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        撤回ECN审批

        Args:
            ecn_id: ECN ID
            user_id: 用户ID
            reason: 撤回原因

        Returns:
            撤回结果字典

        Raises:
            ValueError: 当ECN不存在、无审批流程或权限不足时
        """
        ecn = self.db.query(Ecn).filter(Ecn.id == ecn_id).first()
        if not ecn:
            raise ValueError("ECN不存在")

        instance = (
            self.db.query(ApprovalInstance)
            .filter(
                ApprovalInstance.entity_type == "ECN",
                ApprovalInstance.entity_id == ecn_id,
                ApprovalInstance.status == "PENDING",
            )
            .first()
        )

        if not instance:
            raise ValueError("没有进行中的审批流程可撤回")

        if instance.initiator_id != user_id:
            raise ValueError("只能撤回自己提交的审批")

        self.engine.withdraw(instance_id=instance.id, user_id=user_id)

        # 更新ECN状态
        ecn.status = "DRAFT"
        ecn.current_step = None

        return {
            "ecn_id": ecn_id,
            "ecn_no": ecn.ecn_no,
            "status": "withdrawn",
        }

    def get_approval_history_for_user(
        self,
        user_id: int,
        status_filter: Optional[str] = None,
        ecn_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取用户的审批历史

        Args:
            user_id: 用户ID
            status_filter: 状态筛选
            ecn_type: ECN类型筛选
            offset: 分页偏移
            limit: 分页限制

        Returns:
            (历史记录列表, 总数)
        """
        query = (
            self.db.query(ApprovalTask)
            .join(ApprovalInstance)
            .filter(
                ApprovalTask.assignee_id == user_id,
                ApprovalInstance.entity_type == "ECN",
                ApprovalTask.status.in_(["APPROVED", "REJECTED"]),
            )
        )

        if status_filter:
            query = query.filter(ApprovalTask.status == status_filter)

        total = query.count()
        tasks = (
            query.order_by(ApprovalTask.completed_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        items = []
        for task in tasks:
            instance = task.instance
            ecn = self.db.query(Ecn).filter(Ecn.id == instance.entity_id).first()

            # 类型筛选
            if ecn_type and ecn and ecn.ecn_type != ecn_type:
                continue

            items.append(
                {
                    "task_id": task.id,
                    "ecn_id": instance.entity_id,
                    "ecn_no": ecn.ecn_no if ecn else None,
                    "ecn_title": ecn.ecn_title if ecn else None,
                    "ecn_type": ecn.ecn_type if ecn else None,
                    "project_name": ecn.project.project_name
                    if ecn and ecn.project
                    else None,
                    "action": task.action,
                    "status": task.status,
                    "comment": task.comment,
                    "completed_at": task.completed_at.isoformat()
                    if task.completed_at
                    else None,
                }
            )

        return items, total
