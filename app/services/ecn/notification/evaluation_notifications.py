# -*- coding: utf-8 -*-
"""
ECN通知服务 - 评估相关通知（使用统一NotificationService）
包含：评估任务分配、评估完成通知
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.approval import ApprovalInstance, ApprovalTask
from app.models.ecn import Ecn, EcnEvaluation
from app.models.user import User
from app.services.notification.channels.base import (
    NotificationPriority,
    NotificationRequest,
)
from app.services.notification.notification_dispatcher import NotificationDispatcher

from .utils import (
    check_all_evaluations_completed,
    find_department_manager,
    find_users_by_department,
)


def notify_evaluation_assigned(
    db: Session, ecn: Ecn, evaluation: EcnEvaluation, evaluator_id: Optional[int] = None
) -> None:
    """
    通知评估任务分配
    """
    if not evaluator_id:
        # 如果没有指定评估人，根据部门查找用户
        dept_users = find_users_by_department(db, evaluation.eval_dept)
        if dept_users:
            # 选择部门经理作为评估人
            dept_manager = find_department_manager(db)
            if dept_manager:
                evaluator_id = dept_manager.id
            elif dept_users:
                evaluator_id = dept_users[0].id

    if not evaluator_id:
        return

    evaluator = db.query(User).filter(User.id == evaluator_id).first()
    if not evaluator:
        return

    title = f"ECN评估任务分配：{ecn.ecn_no}"
    content = f"您有一个新的ECN评估任务：\n\nECN编号：{ecn.ecn_no}\nECN标题：{ecn.ecn_title}\n评估部门：{evaluation.eval_dept}\n\n请及时完成评估。"

    dispatcher = NotificationDispatcher(db)
    request = NotificationRequest(
        recipient_id=evaluator_id,
        notification_type="ECN_EVALUATION_ASSIGNED",
        category="ecn",
        title=title,
        content=content,
        priority=NotificationPriority.HIGH,
        source_type="ecn",
        source_id=ecn.id,
        link_url=f"/ecns?ecnId={ecn.id}",
        extra_data={
            "ecn_no": ecn.ecn_no,
            "ecn_title": ecn.ecn_title,
            "eval_dept": evaluation.eval_dept,
            "eval_id": evaluation.id,
        },
    )
    dispatcher.send_notification_request(request)


def notify_evaluation_completed(db: Session, ecn: Ecn, evaluation: EcnEvaluation) -> None:
    """
    通知评估完成
    通知ECN申请人、项目相关人员和其他相关人员
    """
    dispatcher = NotificationDispatcher(db)
    # 通知申请人
    if ecn.applicant_id:
        title = f"ECN评估完成：{ecn.ecn_no}"
        content = f"ECN {ecn.ecn_no} 的{evaluation.eval_dept}评估已完成。\n\n评估结论：{evaluation.eval_result}\n成本估算：¥{evaluation.cost_estimate or 0}\n工期估算：{evaluation.schedule_estimate or 0}天"

        request = NotificationRequest(
            recipient_id=ecn.applicant_id,
            notification_type="ECN_EVALUATION_COMPLETED",
            category="ecn",
            title=title,
            content=content,
            priority=NotificationPriority.NORMAL,
            source_type="ecn",
            source_id=ecn.id,
            link_url=f"/ecns?ecnId={ecn.id}",
            extra_data={
                "ecn_no": ecn.ecn_no,
                "eval_dept": evaluation.eval_dept,
                "eval_result": evaluation.eval_result,
            },
        )
    dispatcher.send_notification_request(request)

    # 抄送项目相关人员（如果ECN关联了项目）
    if ecn.project_id:
        from app.models.project import ProjectMember

        # 查找项目成员（排除申请人，避免重复通知）
        project_members = (
            db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == ecn.project_id,
                ProjectMember.is_active,
                ProjectMember.user_id != ecn.applicant_id,
            )
            .all()
        )

        project_user_ids = [pm.user_id for pm in project_members]

        if project_user_ids:
            title = f"ECN评估完成（抄送）：{ecn.ecn_no}"
            content = f"ECN {ecn.ecn_no} 的{evaluation.eval_dept}评估已完成。\n\n评估结论：{evaluation.eval_result}\n成本估算：¥{evaluation.cost_estimate or 0}\n工期估算：{evaluation.schedule_estimate or 0}天\n\n请关注项目变更影响。"

            for user_id in project_user_ids:
                request = NotificationRequest(
                    recipient_id=user_id,
                    notification_type="ECN_EVALUATION_COMPLETED",
                    category="ecn",
                    title=title,
                    content=content,
                    priority=NotificationPriority.NORMAL,
                    source_type="ecn",
                    source_id=ecn.id,
                    link_url=f"/ecns?ecnId={ecn.id}",
                    extra_data={
                        "ecn_no": ecn.ecn_no,
                        "eval_dept": evaluation.eval_dept,
                        "eval_result": evaluation.eval_result,
                        "is_cc": True,  # 标记为抄送
                    },
                )
                dispatcher.send_notification_request(request)

    # 通知审批人员（如果所有评估都完成，进入审批阶段）
    if check_all_evaluations_completed(db, ecn.id):
        pending_tasks = (
            db.query(ApprovalTask)
            .join(ApprovalInstance, ApprovalTask.instance_id == ApprovalInstance.id)
            .filter(
                ApprovalInstance.entity_type == "ECN",
                ApprovalInstance.entity_id == ecn.id,
                ApprovalTask.status == "PENDING",
            )
            .order_by(ApprovalTask.task_order)
            .all()
        )

        for task in pending_tasks:
            approval_level = task.node.node_order if task.node else task.task_order
            title = f"ECN审批任务分配：{ecn.ecn_no}"
            content = f"所有评估已完成，您有一个新的ECN审批任务：\n\nECN编号：{ecn.ecn_no}\nECN标题：{ecn.ecn_title}\n审批层级：第{approval_level}级\n\n请及时完成审批。"

            request = NotificationRequest(
                recipient_id=task.assignee_id,
                notification_type="ECN_APPROVAL_ASSIGNED",
                category="ecn",
                title=title,
                content=content,
                priority=NotificationPriority.HIGH,
                source_type="ecn",
                source_id=ecn.id,
                link_url=f"/ecns?ecnId={ecn.id}",
                extra_data={
                    "ecn_no": ecn.ecn_no,
                    "ecn_title": ecn.ecn_title,
                    "approval_level": approval_level,
                    "approval_task_id": task.id,
                },
            )
            dispatcher.send_notification_request(request)
