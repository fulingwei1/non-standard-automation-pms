# -*- coding: utf-8 -*-
"""
ECN通知服务 - 任务相关通知
包含：执行任务分配、执行任务完成通知
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.ecn import Ecn, EcnTask
from app.models.project import ProjectMember
from app.models.user import User

from .base import create_ecn_notification
from .utils import find_users_by_department


def notify_task_assigned(
    db: Session,
    ecn: Ecn,
    task: EcnTask,
    assignee_id: Optional[int] = None
) -> None:
    """
    通知执行任务分配
    通知执行人员，并抄送项目相关人员
    """
    if not assignee_id:
        # 如果没有指定执行人，根据部门查找用户
        dept_users = find_users_by_department(db, task.task_dept)
        if dept_users:
            # 选择第一个用户作为执行人
            assignee_id = dept_users[0].id

    if not assignee_id:
        return

    assignee = db.query(User).filter(User.id == assignee_id).first()
    if not assignee:
        return

    assignee_ids = [assignee_id]

    # 通知执行人员
    title = f"ECN执行任务分配：{ecn.ecn_no}"
    content = f"您有一个新的ECN执行任务：\n\nECN编号：{ecn.ecn_no}\nECN标题：{ecn.ecn_title}\n任务名称：{task.task_name}\n任务类型：{task.task_type}\n责任部门：{task.task_dept}\n计划完成：{task.planned_end.strftime('%Y-%m-%d') if task.planned_end else '未设置'}\n\n请及时开始执行。"

    priority = "HIGH"
    if task.planned_end and task.planned_end < datetime.now().date():
        priority = "URGENT"

    create_ecn_notification(
        db=db,
        user_id=assignee_id,
        notification_type="ECN_TASK_ASSIGNED",
        title=title,
        content=content,
        ecn_id=ecn.id,
        priority=priority,
        extra_data={
            "ecn_no": ecn.ecn_no,
            "ecn_title": ecn.ecn_title,
            "task_id": task.id,
            "task_name": task.task_name,
            "task_type": task.task_type,
            "task_dept": task.task_dept,
            "planned_end": task.planned_end.isoformat() if task.planned_end else None
        }
    )

    # 抄送项目相关人员（如果ECN关联了项目，且执行人员不是项目成员）
    if ecn.project_id:
        # 查找项目成员（排除执行人员，避免重复通知）
        project_members = db.query(ProjectMember).filter(
            ProjectMember.project_id == ecn.project_id,
            ProjectMember.is_active == True,
            ~ProjectMember.user_id.in_(assignee_ids)
        ).all()

        project_user_ids = [pm.user_id for pm in project_members]

        if project_user_ids:
            # 获取执行人员名称列表
            assignees = db.query(User).filter(User.id.in_(assignee_ids)).all()
            assignee_names = ", ".join([a.real_name or a.username for a in assignees])

            title_cc = f"ECN执行任务分配（抄送）：{ecn.ecn_no}"
            content_cc = f"ECN {ecn.ecn_no} 的执行任务「{task.task_name}」已分配给{assignee_names}。\n\nECN标题：{ecn.ecn_title}\n任务名称：{task.task_name}\n任务类型：{task.task_type}\n责任部门：{task.task_dept}\n计划完成：{task.planned_end.strftime('%Y-%m-%d') if task.planned_end else '未设置'}\n\n请关注项目变更执行情况。"

            for user_id in project_user_ids:
                create_ecn_notification(
                    db=db,
                    user_id=user_id,
                    notification_type="ECN_TASK_ASSIGNED",
                    title=title_cc,
                    content=content_cc,
                    ecn_id=ecn.id,
                    priority="NORMAL",
                    extra_data={
                        "ecn_no": ecn.ecn_no,
                        "ecn_title": ecn.ecn_title,
                        "task_id": task.id,
                        "task_name": task.task_name,
                        "task_type": task.task_type,
                        "task_dept": task.task_dept,
                        "assignee_ids": assignee_ids,
                        "planned_end": task.planned_end.isoformat() if task.planned_end else None,
                        "is_cc": True  # 标记为抄送
                    }
                )

    db.commit()


def notify_task_completed(
    db: Session,
    ecn: Ecn,
    task: EcnTask
) -> None:
    """
    通知执行任务完成
    通知ECN申请人、项目相关人员和其他相关人员
    """
    # 通知申请人
    if ecn.applicant_id:
        title = f"ECN执行任务完成：{ecn.ecn_no}"
        content = f"ECN {ecn.ecn_no} 的执行任务「{task.task_name}」已完成。\n\n完成说明：{task.completion_note or '无'}"

        create_ecn_notification(
            db=db,
            user_id=ecn.applicant_id,
            notification_type="ECN_TASK_COMPLETED",
            title=title,
            content=content,
            ecn_id=ecn.id,
            priority="NORMAL",
            extra_data={
                "ecn_no": ecn.ecn_no,
                "task_id": task.id,
                "task_name": task.task_name
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
            title = f"ECN执行任务完成（抄送）：{ecn.ecn_no}"
            content = f"ECN {ecn.ecn_no} 的执行任务「{task.task_name}」已完成。\n\n完成说明：{task.completion_note or '无'}\n\n请关注项目变更执行情况。"

            for user_id in project_user_ids:
                create_ecn_notification(
                    db=db,
                    user_id=user_id,
                    notification_type="ECN_TASK_COMPLETED",
                    title=title,
                    content=content,
                    ecn_id=ecn.id,
                    priority="NORMAL",
                    extra_data={
                        "ecn_no": ecn.ecn_no,
                        "task_id": task.id,
                        "task_name": task.task_name,
                        "is_cc": True  # 标记为抄送
                    }
                )

    db.commit()
