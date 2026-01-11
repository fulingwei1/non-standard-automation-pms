# -*- coding: utf-8 -*-
"""
ECN通知服务
功能：ECN相关通知的创建和发送
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.notification import Notification
from app.models.ecn import Ecn, EcnEvaluation, EcnApproval, EcnTask
from app.models.user import User
from app.models.organization import Department


def find_users_by_department(db: Session, dept_name: str) -> List[User]:
    """
    根据部门名称查找用户
    支持模糊匹配部门名称
    """
    if not dept_name:
        return []

    users = db.query(User).filter(
        User.is_active == True,
        or_(
            User.department == dept_name,
            User.department.like(f"%{dept_name}%")
        )
    ).all()
    return users


def find_users_by_role(db: Session, role_name: str) -> List[User]:
    """
    根据角色名称查找用户
    支持模糊匹配角色名称
    """
    if not role_name:
        return []

    from app.models.user import UserRole, Role

    # 查找匹配的角色
    roles = db.query(Role).filter(
        Role.is_active == True,
        or_(
            Role.role_name == role_name,
            Role.role_name.like(f"%{role_name}%"),
            Role.role_code.like(f"%{role_name}%")
        )
    ).all()

    if not roles:
        return []

    role_ids = [r.id for r in roles]

    # 查找拥有这些角色的用户
    user_roles = db.query(UserRole).filter(
        UserRole.role_id.in_(role_ids)
    ).all()

    user_ids = list(set([ur.user_id for ur in user_roles]))

    if not user_ids:
        return []

    users = db.query(User).filter(
        User.id.in_(user_ids),
        User.is_active == True
    ).all()

    return users


def create_ecn_notification(
    db: Session,
    user_id: int,
    notification_type: str,
    title: str,
    content: str,
    ecn_id: int,
    priority: str = "NORMAL",
    extra_data: Optional[Dict[str, Any]] = None
) -> Notification:
    """
    创建ECN相关通知
    """
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        content=content,
        source_type="ECN",
        source_id=ecn_id,
        link_url=f"/ecns?ecnId={ecn_id}",
        priority=priority,
        extra_data=extra_data or {}
    )
    db.add(notification)
    return notification


def notify_evaluation_assigned(
    db: Session,
    ecn: Ecn,
    evaluation: EcnEvaluation,
    evaluator_id: Optional[int] = None
) -> None:
    """
    通知评估任务分配
    """
    evaluator_ids = []

    if evaluator_id:
        evaluator_ids = [evaluator_id]
    else:
        # 根据评估部门自动查找用户
        if evaluation.eval_dept:
            dept_users = find_users_by_department(db, evaluation.eval_dept)
            evaluator_ids = [u.id for u in dept_users]

    if not evaluator_ids:
        return

    title = f"ECN评估任务分配：{ecn.ecn_no}"
    content = f"您有一个新的ECN评估任务：\n\nECN编号：{ecn.ecn_no}\nECN标题：{ecn.ecn_title}\n评估部门：{evaluation.eval_dept}\n\n请及时完成评估。"

    for user_id in evaluator_ids:
        create_ecn_notification(
            db=db,
            user_id=user_id,
            notification_type="ECN_EVALUATION_ASSIGNED",
            title=title,
            content=content,
            ecn_id=ecn.id,
            priority="HIGH",
            extra_data={
                "ecn_no": ecn.ecn_no,
                "ecn_title": ecn.ecn_title,
                "eval_dept": evaluation.eval_dept,
                "eval_id": evaluation.id
            }
        )
    db.commit()


def notify_evaluation_completed(
    db: Session,
    ecn: Ecn,
    evaluation: EcnEvaluation
) -> None:
    """
    通知评估完成
    通知ECN申请人、项目相关人员和其他相关人员
    """
    # 通知申请人
    if ecn.applicant_id:
        title = f"ECN评估完成：{ecn.ecn_no}"
        content = f"ECN {ecn.ecn_no} 的{evaluation.eval_dept}评估已完成。\n\n评估结论：{evaluation.eval_result}\n成本估算：¥{evaluation.cost_estimate or 0}\n工期估算：{evaluation.schedule_estimate or 0}天"
        
        create_ecn_notification(
            db=db,
            user_id=ecn.applicant_id,
            notification_type="ECN_EVALUATION_COMPLETED",
            title=title,
            content=content,
            ecn_id=ecn.id,
            priority="NORMAL",
            extra_data={
                "ecn_no": ecn.ecn_no,
                "eval_dept": evaluation.eval_dept,
                "eval_result": evaluation.eval_result
            }
        )
    
    # 抄送项目相关人员（如果ECN关联了项目）
    if ecn.project_id:
        from app.models.project import ProjectMember
        
        # 查找项目成员（排除申请人，避免重复通知）
        project_members = db.query(ProjectMember).filter(
            ProjectMember.project_id == ecn.project_id,
            ProjectMember.is_active == True,
            ProjectMember.user_id != ecn.applicant_id
        ).all()
        
        project_user_ids = [pm.user_id for pm in project_members]
        
        if project_user_ids:
            title = f"ECN评估完成（抄送）：{ecn.ecn_no}"
            content = f"ECN {ecn.ecn_no} 的{evaluation.eval_dept}评估已完成。\n\n评估结论：{evaluation.eval_result}\n成本估算：¥{evaluation.cost_estimate or 0}\n工期估算：{evaluation.schedule_estimate or 0}天\n\n请关注项目变更影响。"
            
            for user_id in project_user_ids:
                create_ecn_notification(
                    db=db,
                    user_id=user_id,
                    notification_type="ECN_EVALUATION_COMPLETED",
                    title=title,
                    content=content,
                    ecn_id=ecn.id,
                    priority="NORMAL",
                    extra_data={
                        "ecn_no": ecn.ecn_no,
                        "eval_dept": evaluation.eval_dept,
                        "eval_result": evaluation.eval_result,
                        "is_cc": True  # 标记为抄送
                    }
                )
    
    # 检查是否所有评估都完成，如果是则通知审批人员
    all_evaluations = db.query(EcnEvaluation).filter(
        EcnEvaluation.ecn_id == ecn.id
    ).all()

    if all_evaluations:
        completed_count = sum(1 for e in all_evaluations if e.eval_status == "COMPLETED")
        if completed_count == len(all_evaluations):
            # 所有评估都完成，查找并通知审批人员
            # 查找第一级审批人员
            first_approval = db.query(EcnApproval).filter(
                EcnApproval.ecn_id == ecn.id,
                EcnApproval.approval_level == 1,
                EcnApproval.approval_status == "PENDING"
            ).first()

            if first_approval:
                # 根据审批角色查找用户
                approvers = find_users_by_role(db, first_approval.approval_role)
                if approvers:
                    title = f"ECN评估完成，待审批：{ecn.ecn_no}"
                    content = f"ECN {ecn.ecn_no} 的所有部门评估已完成，现进入审批阶段。\n\n请及时进行审批。"

                    for approver in approvers:
                        create_ecn_notification(
                            db=db,
                            user_id=approver.id,
                            notification_type="ECN_READY_FOR_APPROVAL",
                            title=title,
                            content=content,
                            ecn_id=ecn.id,
                            priority="HIGH",
                            extra_data={
                                "ecn_no": ecn.ecn_no,
                                "ecn_title": ecn.ecn_title,
                                "approval_level": 1
                            }
                        )

    db.commit()


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
    approver_ids = []

    if approver_id:
        approver_ids = [approver_id]
    else:
        # 如果没有指定审批人，根据审批角色自动查找用户
        if approval.approval_role:
            role_users = find_users_by_role(db, approval.approval_role)
            approver_ids = [u.id for u in role_users]

    if not approver_ids:
        return

    # 通知审批人员
    title = f"ECN审批任务分配：{ecn.ecn_no}"
    content = f"您有一个新的ECN审批任务：\n\nECN编号：{ecn.ecn_no}\nECN标题：{ecn.ecn_title}\n审批层级：第{approval.approval_level}级\n审批角色：{approval.approval_role}\n截止日期：{approval.due_date.strftime('%Y-%m-%d') if approval.due_date else '未设置'}\n\n请及时完成审批。"

    priority = "URGENT" if approval.due_date and approval.due_date < datetime.now() else "HIGH"

    for approver_id in approver_ids:
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
    
    # 抄送项目相关人员（如果ECN关联了项目）
    if ecn.project_id:
        from app.models.project import ProjectMember

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
        from app.models.project import ProjectMember
        
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
        # 查找该ECN的所有待执行任务
        pending_tasks = db.query(EcnTask).filter(
            EcnTask.ecn_id == ecn.id,
            EcnTask.task_status.in_(["PENDING", "IN_PROGRESS"])
        ).all()

        for task in pending_tasks:
            # 确定通知的用户
            task_user_ids = []
            if task.assignee_id:
                task_user_ids = [task.assignee_id]
            elif task.task_dept:
                # 根据任务部门查找用户
                dept_users = find_users_by_department(db, task.task_dept)
                task_user_ids = [u.id for u in dept_users]

            if task_user_ids:
                task_title = f"ECN审批通过，请执行任务：{ecn.ecn_no}"
                task_content = f"ECN {ecn.ecn_no} 已审批通过，请开始执行以下任务：\n\n任务名称：{task.task_name}\n任务类型：{task.task_type}\n责任部门：{task.task_dept}\n计划完成：{task.planned_end.strftime('%Y-%m-%d') if task.planned_end else '未设置'}"

                for task_user_id in task_user_ids:
                    create_ecn_notification(
                        db=db,
                        user_id=task_user_id,
                        notification_type="ECN_TASK_READY",
                        title=task_title,
                        content=task_content,
                        ecn_id=ecn.id,
                        priority="HIGH",
                        extra_data={
                            "ecn_no": ecn.ecn_no,
                            "task_id": task.id,
                            "task_name": task.task_name,
                            "task_dept": task.task_dept
                        }
                    )

    db.commit()


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
    assignee_ids = []

    if assignee_id:
        assignee_ids = [assignee_id]
    else:
        # 如果没有指定执行人，根据任务部门自动查找用户
        if task.task_dept:
            dept_users = find_users_by_department(db, task.task_dept)
            assignee_ids = [u.id for u in dept_users]

    if not assignee_ids:
        return

    # 通知执行人员
    title = f"ECN执行任务分配：{ecn.ecn_no}"
    content = f"您有一个新的ECN执行任务：\n\nECN编号：{ecn.ecn_no}\nECN标题：{ecn.ecn_title}\n任务名称：{task.task_name}\n任务类型：{task.task_type}\n责任部门：{task.task_dept}\n计划完成：{task.planned_end.strftime('%Y-%m-%d') if task.planned_end else '未设置'}\n\n请及时开始执行。"

    priority = "HIGH"
    if task.planned_end and task.planned_end < datetime.now().date():
        priority = "URGENT"

    for assignee_id in assignee_ids:
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

    # 抄送项目相关人员（如果ECN关联了项目）
    if ecn.project_id:
        from app.models.project import ProjectMember

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
        from app.models.project import ProjectMember
        
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


def notify_ecn_submitted(
    db: Session,
    ecn: Ecn
) -> None:
    """
    通知ECN提交
    通知申请人、项目相关人员和其他相关人员
    """
    # 通知申请人确认提交
    if ecn.applicant_id:
        title = f"ECN已提交：{ecn.ecn_no}"
        content = f"您的ECN {ecn.ecn_no} 已成功提交，已进入评估流程。"
        
        create_ecn_notification(
            db=db,
            user_id=ecn.applicant_id,
            notification_type="ECN_SUBMITTED",
            title=title,
            content=content,
            ecn_id=ecn.id,
            priority="NORMAL",
            extra_data={
                "ecn_no": ecn.ecn_no,
                "ecn_title": ecn.ecn_title
            }
        )
    
    # 抄送项目相关人员（如果ECN关联了项目）
    if ecn.project_id:
        from app.models.project import ProjectMember
        
        # 查找项目成员（排除申请人，避免重复通知）
        project_members = db.query(ProjectMember).filter(
            ProjectMember.project_id == ecn.project_id,
            ProjectMember.is_active == True,
            ProjectMember.user_id != ecn.applicant_id
        ).all()
        
        project_user_ids = [pm.user_id for pm in project_members]
        
        if project_user_ids:
            title = f"ECN已提交（抄送）：{ecn.ecn_no}"
            content = f"项目相关的ECN {ecn.ecn_no} 已提交，已进入评估流程。\n\nECN标题：{ecn.ecn_title}\n变更类型：{ecn.ecn_type}\n变更原因：{ecn.change_reason}\n\n请关注项目变更情况。"
            
            for user_id in project_user_ids:
                create_ecn_notification(
                    db=db,
                    user_id=user_id,
                    notification_type="ECN_SUBMITTED",
                    title=title,
                    content=content,
                    ecn_id=ecn.id,
                    priority="NORMAL",
                    extra_data={
                        "ecn_no": ecn.ecn_no,
                        "ecn_title": ecn.ecn_title,
                        "is_cc": True  # 标记为抄送
                    }
                )
    
    db.commit()


def notify_overdue_alert(
    db: Session,
    alert: Dict[str, Any],
    user_ids: List[int]
) -> None:
    """
    通知超时提醒
    """
    for user_id in user_ids:
        title = f"ECN超时提醒：{alert.get('ecn_no', '')}"
        content = alert.get('message', '')
        
        priority = "URGENT" if alert.get('overdue_days', 0) > 7 else "HIGH"
        
        create_ecn_notification(
            db=db,
            user_id=user_id,
            notification_type="ECN_OVERDUE_ALERT",
            title=title,
            content=content,
            ecn_id=alert.get('ecn_id'),
            priority=priority,
            extra_data={
                "alert_type": alert.get('type'),
                "overdue_days": alert.get('overdue_days', 0),
                "ecn_no": alert.get('ecn_no')
            }
        )
    
    db.commit()

