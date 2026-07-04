# -*- coding: utf-8 -*-
"""审批超时处理。"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, Optional

from app.models.approval import (
    ApprovalInstance,
    ApprovalNodeDefinition,
    ApprovalTask,
)
from app.models.user import User

from .core import ApprovalEngineCore


class ApprovalTimeoutMixin:
    """通用审批任务超时扫描与处理。"""

    def process_approval_timeouts(
        self: ApprovalEngineCore,
        now: Optional[datetime] = None,
        limit: int = 500,
    ) -> Dict[str, object]:
        """扫描已超时审批任务并执行节点配置的 timeout_action。"""
        now = now or datetime.now()
        tasks = (
            self.db.query(ApprovalTask)
            .join(ApprovalInstance, ApprovalTask.instance_id == ApprovalInstance.id)
            .filter(
                ApprovalTask.status == "PENDING",
                ApprovalTask.due_at.isnot(None),
                ApprovalTask.due_at <= now,
                ApprovalInstance.status == "PENDING",
            )
            .order_by(ApprovalTask.due_at.asc(), ApprovalTask.id.asc())
            .limit(limit)
            .all()
        )

        action_counts: Counter[str] = Counter()
        failed_count = 0

        for task in tasks:
            instance = task.instance
            before_status = instance.status
            action, error = self.executor.handle_timeout(task)
            if error:
                failed_count += 1
                self._log_timeout_action(task, action, before_status, error=error)
                continue

            if action == "REMIND":
                self.notify.notify_remind(task, reminder_id=task.assignee_id, reminder_name="系统")
            elif action == "AUTO_PASS":
                self._complete_auto_pass_timeout(task)
            elif action == "AUTO_REJECT":
                self._complete_auto_reject_timeout(task)
            elif action == "ESCALATE":
                escalated = self._create_escalated_timeout_task(task, now)
                if not escalated:
                    failed_count += 1
                    task.status = "PENDING"
                    error = "审批人未配置直属上级，无法升级"

            self._log_timeout_action(task, action, before_status, error=error)
            if error:
                continue
            action_counts[action] += 1

        self.db.commit()
        return {
            "status": "success",
            "task": "process_approval_timeouts",
            "checked_count": len(tasks),
            "processed_count": sum(action_counts.values()),
            "failed_count": failed_count,
            "action_counts": dict(action_counts),
            "timestamp": datetime.now().isoformat(),
        }

    def process_approval_timeout_warnings(
        self: ApprovalEngineCore,
        now: Optional[datetime] = None,
        limit: int = 500,
    ) -> Dict[str, object]:
        """扫描即将超时的审批任务，按节点 timeout_remind_hours 发送预警。"""
        now = now or datetime.now()
        tasks = (
            self.db.query(ApprovalTask)
            .join(ApprovalInstance, ApprovalTask.instance_id == ApprovalInstance.id)
            .join(ApprovalNodeDefinition, ApprovalTask.node_id == ApprovalNodeDefinition.id)
            .filter(
                ApprovalTask.status == "PENDING",
                ApprovalTask.due_at.isnot(None),
                ApprovalTask.due_at > now,
                ApprovalInstance.status == "PENDING",
                ApprovalNodeDefinition.timeout_remind_hours.isnot(None),
            )
            .order_by(ApprovalTask.due_at.asc(), ApprovalTask.id.asc())
            .limit(limit)
            .all()
        )

        warning_count = 0
        for task in tasks:
            hours_remaining = max(0, int((task.due_at - now).total_seconds() // 3600))
            if hours_remaining > task.node.timeout_remind_hours:
                continue
            if task.reminded_at and task.reminded_at >= now - timedelta(hours=1):
                continue

            task.remind_count = (task.remind_count or 0) + 1
            task.reminded_at = now
            self.notify.notify_timeout_warning(task, hours_remaining)
            self._log_timeout_action(
                task,
                "TIMEOUT_WARNING",
                task.instance.status,
                detail={"hours_remaining": hours_remaining},
            )
            warning_count += 1

        self.db.commit()
        return {
            "status": "success",
            "task": "process_approval_timeout_warnings",
            "checked_count": len(tasks),
            "warning_count": warning_count,
            "timestamp": datetime.now().isoformat(),
        }

    def _complete_auto_pass_timeout(self: ApprovalEngineCore, task: ApprovalTask) -> None:
        if not getattr(task, "_timeout_can_proceed", False):
            return

        instance = task.instance
        if self._get_countersign_final_result(task) == "FAILED":
            self._complete_instance_as_rejected(instance, exclude_task_id=task.id)
            self._call_adapter_callback(instance, "on_rejected")
            self.notify.notify_rejected(
                instance,
                rejector_name="系统",
                reject_comment="会签超时自动处理未通过",
            )
            return

        self._advance_to_next_node(instance, task)

    def _complete_auto_reject_timeout(self: ApprovalEngineCore, task: ApprovalTask) -> None:
        if not getattr(task, "_timeout_can_proceed", False):
            return

        instance = task.instance
        if self._get_countersign_final_result(task) == "PASSED":
            self._advance_to_next_node(instance, task)
            return

        self._complete_instance_as_rejected(instance, exclude_task_id=task.id)
        self._call_adapter_callback(instance, "on_rejected")
        self.notify.notify_rejected(
            instance,
            rejector_name="系统",
            reject_comment="系统自动驳回（超时）",
        )

    def _create_escalated_timeout_task(
        self: ApprovalEngineCore,
        task: ApprovalTask,
        now: datetime,
    ) -> Optional[ApprovalTask]:
        assignee = task.assignee or self.db.query(User).filter(User.id == task.assignee_id).first()
        manager_id = getattr(assignee, "reporting_to", None)
        if not manager_id:
            return None

        manager = self.db.query(User).filter(User.id == manager_id, User.is_active.is_(True)).first()
        if not manager:
            return None

        timeout_hours = task.node.timeout_hours or 24
        escalated_task = ApprovalTask(
            instance_id=task.instance_id,
            node_id=task.node_id,
            task_type=task.task_type,
            task_order=task.task_order,
            assignee_id=manager.id,
            assignee_name=manager.real_name or manager.username,
            assignee_dept_id=manager.department_id,
            assignee_type="TRANSFERRED",
            original_assignee_id=task.assignee_id,
            status="PENDING",
            due_at=now + timedelta(hours=timeout_hours),
            is_countersign=task.is_countersign,
            countersign_weight=task.countersign_weight,
        )
        self.db.add(escalated_task)
        self.db.flush()
        self.notify.notify_pending(escalated_task)
        return escalated_task

    def _log_timeout_action(
        self: ApprovalEngineCore,
        task: ApprovalTask,
        timeout_action: str,
        before_status: Optional[str],
        error: Optional[str] = None,
        detail: Optional[Dict[str, object]] = None,
    ) -> None:
        action_detail = {"timeout_action": timeout_action}
        if detail:
            action_detail.update(detail)
        if error:
            action_detail["error"] = error

        self._log_action(
            instance_id=task.instance_id,
            task_id=task.id,
            node_id=task.node_id,
            operator_id=task.assignee_id,
            operator_name="系统自动处理",
            action="TIMEOUT",
            comment=error or f"审批任务超时自动处理: {timeout_action}",
            action_detail=action_detail,
            before_status=before_status,
            after_status=task.instance.status,
        )
