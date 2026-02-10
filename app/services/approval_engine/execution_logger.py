# -*- coding: utf-8 -*-
"""
审批流程执行日志工具

提供结构化的审批流程执行日志记录，便于追踪和调试
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.approval import (
    ApprovalActionLog,
    ApprovalInstance,
    ApprovalTask,
    ApprovalNodeDefinition,
)
from app.models.user import User
from app.core.logging_config import (
    get_logger,
    log_info_with_context,
    log_error_with_context,
    log_warning_with_context,
)

logger = get_logger(__name__)


class ApprovalExecutionLogger:
    """审批流程执行日志记录器

    在审批流程的关键节点记录日志，同时写入 ApprovalActionLog 数据库表
    """

    def __init__(self, db: Session):
        self.db = db

        # 日志级别配置
        self.log_actions = True  # 记录所有审批动作
        self.log_routing = True  # 记录路由决策
        self.log_performance = True  # 记录性能指标
        self.log_errors = True  # 记录错误和异常

    # ============================================================
    # 审批实例生命周期日志
    # ============================================================

    def log_instance_created(
        self,
        instance: ApprovalInstance,
        initiator: User,
        context: Optional[Dict[str, Any]] = None,
    ):
        """记录审批实例创建"""
        log_context = {
            "instance_id": instance.id,
            "instance_no": instance.instance_no,
            "entity_type": instance.entity_type,
            "entity_id": instance.entity_id,
            "template_id": instance.template_id,
            "flow_id": instance.flow_id,
            "initiator_id": initiator.id,
            "initiator_name": initiator.username,
            **(context or {}),
        }

        # 结构化日志
        log_info_with_context(
            logger,
            f"审批实例创建: {instance.instance_no} ({instance.entity_type})",
            context=log_context,
        )

        # 数据库日志
        if self.log_actions:
            self._create_action_log(
                instance_id=instance.id,
                operator_id=initiator.id,
                operator_name=initiator.real_name or initiator.username,
                action="SUBMIT",
                comment="提交审批申请",
                before_status=None,
                after_status=instance.status,
                action_detail=context or {},
            )

    def log_instance_status_change(
        self,
        instance: ApprovalInstance,
        old_status: str,
        new_status: str,
        reason: Optional[str] = None,
        operator: Optional[User] = None,
    ):
        """记录审批实例状态变更"""
        log_context = {
            "instance_id": instance.id,
            "instance_no": instance.instance_no,
            "old_status": old_status,
            "new_status": new_status,
            "reason": reason,
            "operator_id": operator.id if operator else None,
        }

        log_info_with_context(
            logger,
            f"审批状态变更: {instance.instance_no} [{old_status} -> {new_status}]",
            context=log_context,
        )

    def log_instance_completed(
        self,
        instance: ApprovalInstance,
        operator: User,
        completion_reason: Optional[str] = None,
    ):
        """记录审批实例完成"""
        log_context = {
            "instance_id": instance.id,
            "instance_no": instance.instance_no,
            "final_status": instance.status,
            "completed_nodes": instance.completed_nodes,
            "total_nodes": instance.total_nodes,
            "completed_at": instance.completed_at,
            "completion_reason": completion_reason,
        }

        log_info_with_context(
            logger,
            f"审批实例完成: {instance.instance_no} - 状态: {instance.status}",
            context=log_context,
        )

        if self.log_actions:
            self._create_action_log(
                instance_id=instance.id,
                operator_id=operator.id,
                operator_name=operator.real_name or operator.username,
                action="COMPLETE" if instance.status == "APPROVED" else "TERMINATE",
                comment=completion_reason,
                before_status=instance.current_status,
                after_status=instance.status,
            )

    # ============================================================
    # 审批任务生命周期日志
    # ============================================================

    def log_task_created(
        self,
        task: ApprovalTask,
        node: ApprovalNodeDefinition,
        context: Optional[Dict[str, Any]] = None,
    ):
        """记录审批任务创建"""
        log_context = {
            "task_id": task.id,
            "instance_id": task.instance_id,
            "node_id": node.id,
            "node_code": node.node_code,
            "node_name": node.node_name,
            "assignee_id": task.assignee_id,
            "task_type": task.task_type,
            "due_at": task.due_at.isoformat() if task.due_at else None,
            **(context or {}),
        }

        log_info_with_context(
            logger,
            f"审批任务创建: {node.node_name} -> 用户ID: {task.assignee_id}",
            context=log_context,
        )

        # 数据库日志
        if self.log_actions:
            self._create_action_log(
                instance_id=task.instance_id,
                task_id=task.id,
                node_id=node.id,
                operator_id=task.assignee_id,
                operator_name=f"User_{task.assignee_id}",
                action="READ_CC" if task.task_type == "CC" else "ASSIGN_TASK",
                comment=f"分配到节点: {node.node_name}",
                action_detail=context or {},
            )

    def log_task_completed(
        self,
        task: ApprovalTask,
        operator: User,
        decision: str,
        comment: Optional[str] = None,
    ):
        """记录审批任务完成"""
        log_context = {
            "task_id": task.id,
            "instance_id": task.instance_id,
            "node_id": task.node_id,
            "node_code": task.node_code if hasattr(task, "node") else None,
            "assignee_id": task.assignee_id,
            "decision": decision,
            "comment": comment,
            "completed_at": datetime.now().isoformat(),
        }

        log_info_with_context(
            logger,
            f"审批任务完成: 节点ID: {task.node_id}, 决策: {decision}",
            context=log_context,
        )

        # 数据库日志
        if self.log_actions:
            action_map = {
                "APPROVED": "APPROVE",
                "REJECTED": "REJECT",
                "RETURNED": "RETURN",
            }
            self._create_action_log(
                instance_id=task.instance_id,
                task_id=task.id,
                node_id=task.node_id,
                operator_id=operator.id,
                operator_name=operator.real_name or operator.username,
                action=action_map.get(decision, "UNKNOWN"),
                comment=comment,
                before_status="PENDING",
                after_status=decision,
            )

    def log_task_timeout(
        self,
        task: ApprovalTask,
        timeout_action: str,
    ):
        """记录审批任务超时"""
        log_context = {
            "task_id": task.id,
            "instance_id": task.instance_id,
            "node_id": task.node_id,
            "assignee_id": task.assignee_id,
            "due_at": task.due_at.isoformat() if task.due_at else None,
            "timeout_action": timeout_action,
        }

        log_warning_with_context(
            logger,
            f"审批任务超时: 任务ID: {task.id}, 超时操作: {timeout_action}",
            context=log_context,
        )

        # 数据库日志
        if self.log_actions:
            self._create_action_log(
                instance_id=task.instance_id,
                task_id=task.id,
                node_id=task.node_id,
                operator_id=task.assignee_id,
                operator_name="System_Timeout",
                action="TIMEOUT",
                comment=f"任务超时,自动执行: {timeout_action}",
                action_detail={"timeout_action": timeout_action},
            )

    # ============================================================
    # 路由决策日志
    # ============================================================

    def log_flow_selection(
        self,
        instance: ApprovalInstance,
        flow_id: int,
        flow_name: str,
        routing_rule: Optional[str] = None,
        condition: Optional[str] = None,
    ):
        """记录流程选择决策"""
        log_context = {
            "instance_id": instance.id,
            "instance_no": instance.instance_no,
            "selected_flow_id": flow_id,
            "flow_name": flow_name,
            "routing_rule": routing_rule,
            "condition_evaluated": condition,
            "decision_time": datetime.now().isoformat(),
        }

        if self.log_routing:
            log_info_with_context(
                logger,
                f"路由决策: 实例 {instance.instance_no} 选择流程: {flow_name}",
                context=log_context,
            )

    def log_node_transition(
        self,
        instance=None,
        from_node=None,
        to_node=None,
        reason: Optional[str] = None,
        *,
        instance_id: Optional[int] = None,
        from_node_id: Optional[int] = None,
        to_node_id: Optional[int] = None,
        trigger: Optional[str] = None,
    ):
        """记录节点流转

        支持两种调用方式:
        1. ORM 对象方式: log_node_transition(instance, from_node, to_node, reason)
        2. ID 方式: log_node_transition(instance_id=1, from_node_id=1, to_node_id=2, trigger="AUTO")
        """
        # 简化接口：使用 ID 调用
        if instance_id is not None or (instance is not None and isinstance(instance, int)):
            actual_instance_id = instance_id if instance_id is not None else instance
            actual_from_node_id = from_node_id if from_node_id is not None else from_node
            actual_to_node_id = to_node_id if to_node_id is not None else to_node
            actual_trigger = trigger if trigger is not None else reason

            self._create_action_log(
                instance_id=actual_instance_id,
                operator_id=0,
                operator_name="System_Router",
                action="ADVANCE",
                comment=f"节点流转, trigger={actual_trigger}",
                before_node_id=actual_from_node_id,
                after_node_id=actual_to_node_id,
            )
            return

        # ORM 对象方式（原有逻辑）
        log_context = {
            "instance_id": instance.id,
            "instance_no": instance.instance_no,
            "from_node_id": from_node.id if from_node else None,
            "from_node_name": from_node.node_name if from_node else "开始",
            "to_node_id": to_node.id,
            "to_node_name": to_node.node_name,
            "reason": reason,
        }

        if self.log_routing:
            log_info_with_context(
                logger,
                f"节点流转: {instance.instance_no} [{from_node.node_name if from_node else '开始'} -> {to_node.node_name}]",
                context=log_context,
            )

        # 数据库日志
        if self.log_actions:
            self._create_action_log(
                instance_id=instance.id,
                node_id=to_node.id,
                operator_id=instance.initiator_id,
                operator_name="System_Router",
                action="ADVANCE",
                comment=f"流转到节点: {to_node.node_name}",
                before_node_id=from_node.id if from_node else None,
                after_node_id=to_node.id,
            )

    def log_condition_evaluation(
        self,
        node: ApprovalNodeDefinition,
        instance: ApprovalInstance,
        expression: str,
        result: bool,
        matched: bool = False,
    ):
        """记录条件表达式评估"""
        log_context = {
            "instance_id": instance.id,
            "instance_no": instance.instance_no,
            "node_id": node.id,
            "node_code": node.node_code,
            "expression": expression,
            "evaluation_result": result,
            "matched": matched,
        }

        if self.log_routing:
            if matched:
                log_info_with_context(
                    logger,
                    f"条件评估通过: {node.node_code}",
                    context=log_context,
                )
            else:
                log_info_with_context(
                    logger,
                    f"条件评估失败: {node.node_code}",
                    context=log_context,
                )

    # ============================================================
    # 性能和调试日志
    # ============================================================

    def log_performance_metric(
        self,
        instance: ApprovalInstance,
        metric_name: str,
        value: float,
        unit: str = "ms",
    ):
        """记录性能指标"""
        if self.log_performance:
            log_context = {
                "instance_id": instance.id,
                "instance_no": instance.instance_no,
                "metric_name": metric_name,
                "value": value,
                "unit": unit,
            }

            log_info_with_context(
                logger,
                f"性能指标: {metric_name}={value}{unit}",
                context=log_context,
            )

    def log_debug_info(
        self,
        instance_id: int,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        """记录调试信息（仅在 DEBUG 级别）"""
        log_context = {
            "instance_id": instance_id,
            **(context or {}),
        }

        logger.debug(
            f"[DEBUG] {message}",
            extra=log_context,
        )

    # ============================================================
    # 错误和异常日志
    # ============================================================

    def log_error(
        self,
        instance: Optional[ApprovalInstance],
        error: Exception,
        operation: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        """记录审批流程错误"""
        log_context = {
            "instance_id": instance.id if instance else None,
            "instance_no": instance.instance_no if instance else None,
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            **(context or {}),
        }

        log_error_with_context(
            logger,
            f"审批流程错误: {operation}",
            error=error,
            context=log_context,
        )

    def log_validation_error(
        self,
        instance: ApprovalInstance,
        validation_type: str,
        validation_error: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        """记录验证错误"""
        log_context = {
            "instance_id": instance.id,
            "instance_no": instance.instance_no,
            "validation_type": validation_type,
            "validation_error": validation_error,
            **(context or {}),
        }

        log_error_with_context(
            logger,
            f"验证失败: {validation_type} - {validation_error}",
            context=log_context,
        )

    # ============================================================
    # 辅助方法
    # ============================================================

    def _create_action_log(
        self,
        instance_id: int,
        operator_id: int,
        operator_name: str,
        action: str,
        comment: Optional[str] = None,
        task_id: Optional[int] = None,
        node_id: Optional[int] = None,
        before_status: Optional[str] = None,
        after_status: Optional[str] = None,
        before_node_id: Optional[int] = None,
        after_node_id: Optional[int] = None,
        action_detail: Optional[Dict] = None,
    ):
        """创建审批操作日志记录到数据库"""
        try:
            log = ApprovalActionLog(
                instance_id=instance_id,
                task_id=task_id,
                node_id=node_id,
                operator_id=operator_id,
                operator_name=operator_name,
                action=action,
                comment=comment,
                action_detail=action_detail,
                before_status=before_status,
                after_status=after_status,
                before_node_id=before_node_id,
                after_node_id=after_node_id,
                action_at=datetime.now(),
            )

            self.db.add(log)
            self.db.commit()

        except Exception as e:
            logger.error(f"创建审批操作日志失败: {e}", exc_info=True)
            # 不要因为日志失败影响主流程

    # ============================================================
    # 简化接口（兼容综合测试，接受 ID 而非 ORM 对象）
    # ============================================================

    def log_execution(
        self,
        instance_id: int,
        action: str,
        actor_id: int,
        details: Optional[Dict[str, Any]] = None,
    ):
        """记录通用执行日志（简化接口，使用 ID 而非 ORM 对象）

        Args:
            instance_id: 审批实例ID
            action: 操作类型（SUBMIT, APPROVE, REJECT 等）
            actor_id: 操作人ID
            details: 操作详情
        """
        self._create_action_log(
            instance_id=instance_id,
            operator_id=actor_id,
            operator_name=f"User_{actor_id}",
            action=action,
            action_detail=details,
        )

    def log_approval_action(
        self,
        instance_id: int,
        node_id: int,
        approver_id: int,
        action: str,
        comment: Optional[str] = None,
        delegate_to: Optional[int] = None,
    ):
        """记录审批动作（简化接口，使用 ID 而非 ORM 对象）

        Args:
            instance_id: 审批实例ID
            node_id: 审批节点ID
            approver_id: 审批人ID
            action: 审批动作（APPROVE, REJECT, DELEGATE 等）
            comment: 审批意见
            delegate_to: 委托目标用户ID（仅 DELEGATE 时使用）
        """
        action_detail = {}
        if delegate_to is not None:
            action_detail["delegate_to"] = delegate_to

        self._create_action_log(
            instance_id=instance_id,
            node_id=node_id,
            operator_id=approver_id,
            operator_name=f"User_{approver_id}",
            action=action,
            comment=comment,
            action_detail=action_detail if action_detail else None,
        )

    def get_execution_history(
        self,
        instance_id: int,
    ) -> List:
        """获取执行历史记录

        Args:
            instance_id: 审批实例ID

        Returns:
            按创建时间排序的日志记录列表
        """
        query = self.db.query(ApprovalActionLog)
        query = query.filter(ApprovalActionLog.instance_id == instance_id)
        query = query.order_by(ApprovalActionLog.created_at)
        return query.all()

    def get_approval_logs(
        self,
        instance_id: int,
        node_id: Optional[int] = None,
        approver_id: Optional[int] = None,
    ) -> List:
        """获取审批日志

        Args:
            instance_id: 审批实例ID
            node_id: 可选，按节点ID过滤
            approver_id: 可选，按审批人ID过滤

        Returns:
            按创建时间排序的审批日志列表
        """
        query = self.db.query(ApprovalActionLog)
        query = query.filter(ApprovalActionLog.instance_id == instance_id)
        if node_id is not None:
            query = query.filter(ApprovalActionLog.node_id == node_id)
        if approver_id is not None:
            query = query.filter(ApprovalActionLog.operator_id == approver_id)
        query = query.order_by(ApprovalActionLog.created_at)
        return query.all()

    # ============================================================
    # 批量操作日志
    # ============================================================

    def log_batch_task_creation(
        self,
        tasks: List[ApprovalTask],
        node: ApprovalNodeDefinition,
    ):
        """批量记录任务创建"""
        if self.log_performance:
            log_info_with_context(
                logger,
                f"批量任务创建: 节点 {node.node_name}, 任务数: {len(tasks)}",
                context={
                    "node_id": node.id,
                    "node_name": node.node_name,
                    "task_count": len(tasks),
                },
            )

        for task in tasks:
            self.log_task_created(task, node)

    def log_workflow_summary(
        self,
        instance: ApprovalInstance,
    ):
        """记录工作流摘要（用于审批完成后）"""
        # 获取所有任务统计
        from sqlalchemy import func

        stats = (
            self.db.query(
                func.count(ApprovalTask.id).label("total_tasks"),
                func.sum(
                    func.case((ApprovalTask.status == "PENDING", 1), else_=0)
                ).label("pending_tasks"),
                func.sum(
                    func.case((ApprovalTask.status == "APPROVED", 1), else_=0)
                ).label("approved_tasks"),
                func.sum(
                    func.case((ApprovalTask.status == "REJECTED", 1), else_=0)
                ).label("rejected_tasks"),
            )
            .filter(ApprovalTask.instance_id == instance.id)
            .first()
        )

        log_context = {
            "instance_id": instance.id,
            "instance_no": instance.instance_no,
            "status": instance.status,
            "total_tasks": stats.total_tasks or 0,
            "pending_tasks": stats.pending_tasks or 0,
            "approved_tasks": stats.approved_tasks or 0,
            "rejected_tasks": stats.rejected_tasks or 0,
            "duration_hours": (
                (datetime.now() - instance.submitted_at).total_seconds() / 3600
                if instance.submitted_at
                else 0
            ),
        }

        if self.log_performance:
            log_info_with_context(
                logger,
                f"工作流摘要: {instance.instance_no} 完成",
                context=log_context,
            )


# 兼容别名：重构前类名为 ExecutionLogger
ExecutionLogger = ApprovalExecutionLogger
