# -*- coding: utf-8 -*-
"""
审批节点执行器

负责处理各类审批节点的具体执行逻辑
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.approval import (
    ApprovalCarbonCopy,
    ApprovalCountersignResult,
    ApprovalInstance,
    ApprovalNodeDefinition,
    ApprovalTask,
)


class ApprovalNodeExecutor:
    """审批节点执行器"""

    def __init__(self, db: Session):
        self.db = db

    def create_tasks_for_node(
        self,
        instance: ApprovalInstance,
        node: ApprovalNodeDefinition,
        approver_ids: List[int],
    ) -> List[ApprovalTask]:
        """
        为节点创建审批任务

        根据节点的审批模式（单人/或签/会签/依次）创建相应的任务
        """
        if not approver_ids:
            return []

        tasks = []
        approval_mode = node.approval_mode or "SINGLE"

        # 计算截止时间
        due_at = None
        if node.timeout_hours:
            due_at = datetime.now() + timedelta(hours=node.timeout_hours)

        if approval_mode == "SINGLE":
            # 单人审批：只创建一个任务
            task = ApprovalTask(
                instance_id=instance.id,
                node_id=node.id,
                task_type="APPROVAL",
                task_order=1,
                assignee_id=approver_ids[0],
                status="PENDING",
                due_at=due_at,
                is_countersign=False,
            )
            self.db.add(task)
            tasks.append(task)

        elif approval_mode == "OR_SIGN":
            # 或签：为每个审批人创建任务，任一通过即可
            for idx, approver_id in enumerate(approver_ids):
                task = ApprovalTask(
                    instance_id=instance.id,
                    node_id=node.id,
                    task_type="APPROVAL",
                    task_order=idx + 1,
                    assignee_id=approver_id,
                    status="PENDING",
                    due_at=due_at,
                    is_countersign=False,
                )
                self.db.add(task)
                tasks.append(task)

        elif approval_mode == "AND_SIGN":
            # 会签：为每个审批人创建任务，需要全部通过
            for idx, approver_id in enumerate(approver_ids):
                task = ApprovalTask(
                    instance_id=instance.id,
                    node_id=node.id,
                    task_type="APPROVAL",
                    task_order=idx + 1,
                    assignee_id=approver_id,
                    status="PENDING",
                    due_at=due_at,
                    is_countersign=True,
                )
                self.db.add(task)
                tasks.append(task)

            # 创建会签结果统计记录
            countersign_result = ApprovalCountersignResult(
                instance_id=instance.id,
                node_id=node.id,
                total_count=len(approver_ids),
                approved_count=0,
                rejected_count=0,
                pending_count=len(approver_ids),
                final_result="PENDING",
            )
            self.db.add(countersign_result)

        elif approval_mode == "SEQUENTIAL":
            # 依次审批：按顺序创建任务，只有第一个是PENDING
            for idx, approver_id in enumerate(approver_ids):
                task = ApprovalTask(
                    instance_id=instance.id,
                    node_id=node.id,
                    task_type="APPROVAL",
                    task_order=idx + 1,
                    assignee_id=approver_id,
                    status="PENDING" if idx == 0 else "SKIPPED",  # 后续任务先标记为SKIPPED
                    due_at=due_at if idx == 0 else None,
                    is_countersign=False,
                )
                self.db.add(task)
                tasks.append(task)

        self.db.flush()
        return tasks

    def process_approval(
        self,
        task: ApprovalTask,
        action: str,
        comment: Optional[str] = None,
        attachments: Optional[List[Dict]] = None,
        eval_data: Optional[Dict] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        处理审批操作

        Args:
            task: 审批任务
            action: 操作类型（APPROVE/REJECT）
            comment: 审批意见
            attachments: 附件
            eval_data: 评估数据（ECN场景）

        Returns:
            (是否可以流转到下一节点, 错误信息)
        """
        if task.status != "PENDING":
            return False, f"任务状态不正确: {task.status}"

        # 更新任务
        task.action = action
        task.comment = comment
        task.attachments = attachments
        task.eval_data = eval_data
        task.status = "COMPLETED"
        task.completed_at = datetime.now()

        node = task.node
        approval_mode = node.approval_mode or "SINGLE"

        if approval_mode == "SINGLE":
            # 单人审批：直接流转
            return True, None

        elif approval_mode == "OR_SIGN":
            # 或签：任一通过即可流转
            if action == "APPROVE":
                # 取消其他待处理任务
                self._cancel_pending_tasks(task.instance_id, task.node_id, exclude_task_id=task.id)
                return True, None
            else:
                # 检查是否所有人都已驳回
                pending_count = self._count_pending_tasks(task.instance_id, task.node_id)
                if pending_count == 0:
                    # 全部驳回
                    return True, None
                return False, None

        elif approval_mode == "AND_SIGN":
            # 会签：更新统计，检查是否全部完成
            return self._process_countersign(task, action)

        elif approval_mode == "SEQUENTIAL":
            # 依次审批
            if action == "REJECT":
                # 驳回时直接流转（结束）
                return True, None

            # 通过时，激活下一个任务
            next_task = self._activate_next_sequential_task(task)
            if next_task:
                return False, None  # 还有后续任务
            return True, None  # 所有人都已通过

        return True, None

    def _process_countersign(
        self,
        task: ApprovalTask,
        action: str,
    ) -> Tuple[bool, Optional[str]]:
        """处理会签结果"""
        result = (
            self.db.query(ApprovalCountersignResult)
            .filter(
                ApprovalCountersignResult.instance_id == task.instance_id,
                ApprovalCountersignResult.node_id == task.node_id,
            )
            .first()
        )

        if not result:
            return False, "会签结果记录不存在"

        # 更新统计
        result.pending_count -= 1
        if action == "APPROVE":
            result.approved_count += 1
        else:
            result.rejected_count += 1

        # 检查是否全部完成
        if result.pending_count == 0:
            # 确定最终结果
            node = task.node
            pass_rule = (node.approver_config or {}).get("pass_rule", "ALL")

            if pass_rule == "ALL":
                # 全部通过才算通过
                result.final_result = "PASSED" if result.rejected_count == 0 else "FAILED"
            elif pass_rule == "MAJORITY":
                # 多数通过
                result.final_result = "PASSED" if result.approved_count > result.rejected_count else "FAILED"
            elif pass_rule == "ANY":
                # 任一通过
                result.final_result = "PASSED" if result.approved_count > 0 else "FAILED"
            else:
                # 默认全部通过
                result.final_result = "PASSED" if result.rejected_count == 0 else "FAILED"

            # 汇总评估数据（ECN场景）
            self._summarize_eval_data(result)

            return True, None

        return False, None

    def _summarize_eval_data(self, result: ApprovalCountersignResult):
        """汇总会签的评估数据"""
        tasks = (
            self.db.query(ApprovalTask)
            .filter(
                ApprovalTask.instance_id == result.instance_id,
                ApprovalTask.node_id == result.node_id,
                ApprovalTask.status == "COMPLETED",
            )
            .all()
        )

        evaluations = []
        total_cost = 0
        total_schedule_days = 0
        max_risk = "低"
        risk_order = {"低": 1, "中": 2, "高": 3}

        for task in tasks:
            if task.eval_data:
                eval_item = {
                    "assignee_id": task.assignee_id,
                    "assignee_name": task.assignee_name,
                    "action": task.action,
                    "comment": task.comment,
                    **task.eval_data,
                }
                evaluations.append(eval_item)

                # 汇总数据
                cost = task.eval_data.get("cost_estimate", 0) or 0
                total_cost += cost

                schedule = task.eval_data.get("schedule_estimate", 0) or 0
                total_schedule_days += schedule

                risk = task.eval_data.get("risk_assessment", "低")
                if risk_order.get(risk, 0) > risk_order.get(max_risk, 0):
                    max_risk = risk

        result.summary_data = {
            "total_cost": total_cost,
            "total_schedule_days": total_schedule_days,
            "max_risk": max_risk,
            "evaluations": evaluations,
        }

    def _cancel_pending_tasks(
        self,
        instance_id: int,
        node_id: int,
        exclude_task_id: Optional[int] = None,
    ):
        """取消节点上其他待处理的任务（或签场景）"""
        query = self.db.query(ApprovalTask).filter(
            ApprovalTask.instance_id == instance_id,
            ApprovalTask.node_id == node_id,
            ApprovalTask.status == "PENDING",
        )

        if exclude_task_id:
            query = query.filter(ApprovalTask.id != exclude_task_id)

        query.update({"status": "CANCELLED"}, synchronize_session=False)

    def _count_pending_tasks(self, instance_id: int, node_id: int) -> int:
        """统计节点上待处理的任务数"""
        return (
            self.db.query(ApprovalTask)
            .filter(
                ApprovalTask.instance_id == instance_id,
                ApprovalTask.node_id == node_id,
                ApprovalTask.status == "PENDING",
            )
            .count()
        )

    def _activate_next_sequential_task(
        self,
        current_task: ApprovalTask,
    ) -> Optional[ApprovalTask]:
        """激活依次审批的下一个任务"""
        next_task = (
            self.db.query(ApprovalTask)
            .filter(
                ApprovalTask.instance_id == current_task.instance_id,
                ApprovalTask.node_id == current_task.node_id,
                ApprovalTask.task_order > current_task.task_order,
                ApprovalTask.status == "SKIPPED",
            )
            .order_by(ApprovalTask.task_order)
            .first()
        )

        if next_task:
            next_task.status = "PENDING"
            # 设置截止时间
            node = current_task.node
            if node.timeout_hours:
                next_task.due_at = datetime.now() + timedelta(hours=node.timeout_hours)
            return next_task

        return None

    def create_cc_records(
        self,
        instance: ApprovalInstance,
        node_id: Optional[int],
        cc_user_ids: List[int],
        cc_source: str = "FLOW",
        added_by: Optional[int] = None,
    ) -> List[ApprovalCarbonCopy]:
        """创建抄送记录"""
        records = []
        for user_id in cc_user_ids:
            # 避免重复抄送
            existing = (
                self.db.query(ApprovalCarbonCopy)
                .filter(
                    ApprovalCarbonCopy.instance_id == instance.id,
                    ApprovalCarbonCopy.cc_user_id == user_id,
                )
                .first()
            )

            if not existing:
                cc = ApprovalCarbonCopy(
                    instance_id=instance.id,
                    node_id=node_id,
                    cc_user_id=user_id,
                    cc_source=cc_source,
                    added_by=added_by,
                    is_read=False,
                )
                self.db.add(cc)
                records.append(cc)

        self.db.flush()
        return records

    def handle_timeout(self, task: ApprovalTask) -> Tuple[str, Optional[str]]:
        """
        处理任务超时

        Returns:
            (执行的操作, 错误信息)
        """
        if task.status != "PENDING":
            return "NONE", "任务已不是待处理状态"

        node = task.node
        timeout_action = node.timeout_action or "REMIND"

        if timeout_action == "REMIND":
            # 催办提醒
            task.remind_count = (task.remind_count or 0) + 1
            task.reminded_at = datetime.now()
            return "REMIND", None

        elif timeout_action == "AUTO_PASS":
            # 自动通过
            task.action = "APPROVE"
            task.comment = "系统自动通过（超时）"
            task.status = "COMPLETED"
            task.completed_at = datetime.now()
            return "AUTO_PASS", None

        elif timeout_action == "AUTO_REJECT":
            # 自动驳回
            task.action = "REJECT"
            task.comment = "系统自动驳回（超时）"
            task.status = "COMPLETED"
            task.completed_at = datetime.now()
            return "AUTO_REJECT", None

        elif timeout_action == "ESCALATE":
            # 升级处理（转给上级）
            # 这里需要结合具体业务逻辑
            task.status = "EXPIRED"
            return "ESCALATE", None

        else:
            task.status = "EXPIRED"
            return "EXPIRED", None
