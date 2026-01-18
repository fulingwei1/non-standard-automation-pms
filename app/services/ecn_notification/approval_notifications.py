# -*- coding: utf-8 -*-
"""
ECN通知服务 - 审批相关通知
包含：审批任务分配、审批结果通知
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.ecn import Ecn, EcnApproval, EcnTask
from app.models.project import ProjectMember
from app.models.user import User

from .base import create_ecn_notification
from .utils import find_users_by_role


def notify_approval_assigned(
    db: Session,
    ecn: Ecn,
    approval: EcnApproval,
    approver_id: Optional[int] = None
) -> None:
    """
    通知审批任务分配
    通知审批人员，并抄送项目相关人员
    """
    if not approver_id:
        # 如果没有指定审批人，根据角色查找用户
        role_users = find_users_by_role(db, approval.approval_role)
        if role_users:
            approver_id = role_users[0].id

    if not approver_id:
        return

    approver = db.query(User).filter(User.id == approver_id).first()
    if not approver:
        return

    approver_ids = [approver_id]

    # 通知审批人员
    title = f"ECN审批任务分配：{ecn.ecn_no}"
    content = f"您有一个新的ECN审批任务：\n\nECN编号：{ecn.ecn_no}\nECN标题：{ecn.ecn_title}\n审批层级：第{approval.approval_level}级\n审批角色：{approval.approval_role}\n截止日期：{approval.due_date.strftime('%Y-%m-%d') if approval.due_date else '未设置'}\n\n请及时完成审批。"

    priority = "URGENT" if approval.due_date and approval.due_date < datetime.now().date() else "HIGH"

    create_ecn_notification(
        db=db,
        user_id=approver_id,
        notification_type="ECN_APPROVAL_ASSIGNED",
        title=title,
        content=content,
        ecn_id=ecn.id,
        priority=priority,
        extra_data={
            "ecn_no": ecn.ecn_no,
            "ecn_title": ecn.ecn_title,
            "approval_level": approval.approval_level,
            "approval_role": approval.approval_role,
            "approval_id": approval.id,
            "due_date": approval.due_date.isoformat() if approval.due_date else None
        }
    )

    # 抄送项目相关人员（如果ECN关联了项目，且审批人员不是项目成员）
    if ecn.project_id:
        # 查找项目成员（排除审批人员，避免重复通知）
        project_members = db.query(ProjectMember).filter(
            ProjectMember.project_id == ecn.project_id,
            ProjectMember.is_active == True,
            ~ProjectMember.user_id.in_(approver_ids)
        ).all()

        project_user_ids = [pm.user_id for pm in project_members]

        if project_user_ids:
            # 获取审批人员名称列表
            approvers = db.query(User).filter(User.id.in_(approver_ids)).all()
            approver_names = ", ".join([a.real_name or a.username for a in approvers])

            title_cc = f"ECN审批任务分配（抄送）：{ecn.ecn_no}"
            content_cc = f"ECN {ecn.ecn_no} 的第{approval.approval_level}级审批（{approval.approval_role}）任务已分配给{approver_names}。\n\nECN标题：{ecn.ecn_title}\n审批层级：第{approval.approval_level}级\n审批角色：{approval.approval_role}\n截止日期：{approval.due_date.strftime('%Y-%m-%d') if approval.due_date else '未设置'}\n\n请关注项目变更审批情况。"

            for user_id in project_user_ids:
                create_ecn_notification(
                    db=db,
                    user_id=user_id,
                    notification_type="ECN_APPROVAL_ASSIGNED",
                    title=title_cc,
                    content=content_cc,
                    ecn_id=ecn.id,
                    priority="NORMAL",
                    extra_data={
                        "ecn_no": ecn.ecn_no,
                        "ecn_title": ecn.ecn_title,
                        "approval_level": approval.approval_level,
                        "approval_role": approval.approval_role,
                        "approval_id": approval.id,
                        "approver_ids": approver_ids,
                        "due_date": approval.due_date.isoformat() if approval.due_date else None,
                        "is_cc": True  # 标记为抄送
                    }
                )

    db.commit()


def notify_approval_result(
    db: Session,
    ecn: Ecn,
    approval: EcnApproval,
    result: str
) -> None:
    """
    通知审批结果
    通知ECN申请人、项目相关人员和其他相关人员
    """
    result_text = "通过" if result == "APPROVED" else "驳回"
    priority = "HIGH" if result == "APPROVED" else "NORMAL"

    # 通知申请人
    if ecn.applicant_id:
        title = f"ECN审批结果：{ecn.ecn_no}"
        content = f"ECN {ecn.ecn_no} 的第{approval.approval_level}级审批（{approval.approval_role}）{result_text}。\n\n审批意见：{approval.approval_opinion or '无'}"

        create_ecn_notification(
            db=db,
            user_id=ecn.applicant_id,
            notification_type="ECN_APPROVAL_RESULT",
            title=title,
            content=content,
            ecn_id=ecn.id,
            priority=priority,
            extra_data={
                "ecn_no": ecn.ecn_no,
                "approval_level": approval.approval_level,
                "approval_role": approval.approval_role,
                "approval_result": result
            }
        )

    # 抄送项目相关人员（如果ECN关联了项目）
    if ecn.project_id:
        # 查找项目成员（排除申请人，避免重复通知）
        project_members = db.query(ProjectMember).filter(
            ProjectMember.project_id == ecn.project_id,
            ProjectMember.is_active == True,
            ProjectMember.user_id != ecn.applicant_id
        ).all()

        project_user_ids = [pm.user_id for pm in project_members]

        if project_user_ids:
            title = f"ECN审批结果（抄送）：{ecn.ecn_no}"
            content = f"ECN {ecn.ecn_no} 的第{approval.approval_level}级审批（{approval.approval_role}）{result_text}。\n\n审批意见：{approval.approval_opinion or '无'}\n\n请关注项目变更影响。"

            for user_id in project_user_ids:
                create_ecn_notification(
                    db=db,
                    user_id=user_id,
                    notification_type="ECN_APPROVAL_RESULT",
                    title=title,
                    content=content,
                    ecn_id=ecn.id,
                    priority=priority,
                    extra_data={
                        "ecn_no": ecn.ecn_no,
                        "approval_level": approval.approval_level,
                        "approval_role": approval.approval_role,
                        "approval_result": result,
                        "is_cc": True  # 标记为抄送
                    }
                )

    # 如果审批通过，通知执行人员
    if result == "APPROVED":
        # 查找所有待执行的ECN任务
        pending_tasks = db.query(EcnTask).filter(
            EcnTask.ecn_id == ecn.id,
            EcnTask.task_status.in_(['PENDING', 'IN_PROGRESS'])
        ).all()

        for task in pending_tasks:
            if task.assignee_id:
                title = f"ECN已批准，请开始执行：{ecn.ecn_no}"
                content = f"ECN {ecn.ecn_no} 已通过审批，请开始执行您的任务。\n\n任务名称：{task.task_name}\n任务类型：{task.task_type}\n计划完成：{task.planned_end.strftime('%Y-%m-%d') if task.planned_end else '未设置'}"

                create_ecn_notification(
                    db=db,
                    user_id=task.assignee_id,
                    notification_type="ECN_APPROVED_EXECUTION",
                    title=title,
                    content=content,
                    ecn_id=ecn.id,
                    priority="HIGH",
                    extra_data={
                        "ecn_no": ecn.ecn_no,
                        "task_id": task.id,
                        "task_name": task.task_name
                    }
                )

    db.commit()
