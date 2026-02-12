# -*- coding: utf-8 -*-
"""
ECN自动分配服务
功能：根据部门、角色自动分配评估、审批、执行任务
"""

from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.ecn import Ecn, EcnApproval, EcnEvaluation, EcnTask
from app.models.user import Role, User, UserRole


def find_users_by_department(
    db: Session,
    department_name: str
) -> List[User]:
    """
    根据部门名称查找用户
    """
    users = db.query(User).filter(
        and_(
            User.department == department_name,
            User.is_active
        )
    ).all()
    return users


def find_users_by_role(
    db: Session,
    role_name: str
) -> List[User]:
    """
    根据角色名称查找用户
    """
    # 先查找角色
    role = db.query(Role).filter(
        and_(
            Role.role_name == role_name,
            Role.is_active
        )
    ).first()

    if not role:
        return []

    # 查找拥有该角色的用户
    user_roles = db.query(UserRole).filter(UserRole.role_id == role.id).all()
    user_ids = [ur.user_id for ur in user_roles]

    if not user_ids:
        return []

    users = db.query(User).filter(
        and_(
            User.id.in_(user_ids),
            User.is_active
        )
    ).all()

    return users


def auto_assign_evaluation(
    db: Session,
    ecn: Ecn,
    evaluation: EcnEvaluation
) -> Optional[int]:
    """
    自动分配评估任务
    优先分配给项目相关的部门负责人，如果没有负责人，分配给部门经理
    """
    dept_name = evaluation.eval_dept
    if not dept_name:
        return None

    # 如果ECN关联了项目，优先从项目成员中选择
    if ecn.project_id:
        from app.models.project import ProjectMember

        # 查找项目成员中属于该部门的用户
        project_members = db.query(ProjectMember).filter(
            ProjectMember.project_id == ecn.project_id
        ).all()

        project_user_ids = [pm.user_id for pm in project_members]

        if project_user_ids:
            # 查找项目成员中属于该部门的用户
            project_dept_users = db.query(User).filter(
                User.id.in_(project_user_ids),
                User.department == dept_name,
                User.is_active
            ).all()

            if project_dept_users:
                # 优先选择项目成员中的部门负责人
                for user in project_dept_users:
                    if user.position and "负责人" in user.position:
                        return user.id

                # 如果没有负责人，选择项目成员中的部门经理
                for user in project_dept_users:
                    if user.position and ("经理" in user.position or "主管" in user.position):
                        return user.id

    # 如果项目成员中没有找到，从部门所有用户中选择
    users = find_users_by_department(db, dept_name)

    if not users:
        return None

    # 优先选择部门负责人
    for user in users:
        if user.position and "负责人" in user.position:
            return user.id

    # 如果没有负责人，选择部门经理
    for user in users:
        if user.position and ("经理" in user.position or "主管" in user.position):
            return user.id

    # 如果都没有，返回None（不分配给普通活跃用户）
    return None


def auto_assign_approval(
    db: Session,
    ecn: Ecn,
    approval: EcnApproval
) -> Optional[int]:
    """
    自动分配审批任务
    优先分配给项目相关的角色负责人，如果没有负责人，分配给角色经理
    """
    role_name = approval.approval_role
    if not role_name:
        return None

    # 查找拥有该角色的用户
    users = find_users_by_role(db, role_name)

    if not users:
        return None

    # 如果ECN关联了项目，优先从项目成员中选择
    if ecn.project_id:
        from app.models.project import ProjectMember

        # 查找角色
        role = db.query(Role).filter(Role.role_name == role_name).first()
        if not role:
            return None

        # 查找项目成员
        project_members = db.query(ProjectMember).filter(
            ProjectMember.project_id == ecn.project_id,
            ProjectMember.is_active
        ).all()

        project_user_ids = [pm.user_id for pm in project_members]

        if project_user_ids:
            # 查找项目成员中拥有该角色的用户
            project_role_users = []
            for user_id in project_user_ids:
                user = db.query(User).filter(
                    User.id == user_id,
                    User.is_active
                ).first()
                if user:
                    # 检查用户是否拥有该角色
                    user_roles = db.query(UserRole).filter(UserRole.user_id == user_id).all()
                    if any(ur.role_id == role.id for ur in user_roles):
                        project_role_users.append(user)

            if project_role_users:
                # 优先选择项目成员中的负责人
                for user in project_role_users:
                    if user.position and "负责人" in user.position:
                        return user.id

                # 如果没有负责人，选择项目成员中的经理
                for user in project_role_users:
                    if user.position and ("经理" in user.position or "主管" in user.position):
                        return user.id

    # 如果项目成员中没有找到，从所有拥有该角色的用户中选择
    # 优先选择负责人
    for user in users:
        if user.position and "负责人" in user.position:
            return user.id

    # 如果没有负责人，选择经理
    for user in users:
        if user.position and ("经理" in user.position or "主管" in user.position):
            return user.id

    # 如果都没有，返回None（不分配给普通活跃用户）
    return None


def auto_assign_task(
    db: Session,
    ecn: Ecn,
    task: EcnTask
) -> Optional[int]:
    """
    自动分配执行任务
    优先分配给项目相关的部门负责人，如果没有负责人，分配给部门经理
    """
    dept_name = task.task_dept
    if not dept_name:
        return None

    # 如果ECN关联了项目，优先从项目成员中选择
    if ecn.project_id:
        from app.models.project import ProjectMember

        # 查找项目成员中属于该部门的用户
        project_members = db.query(ProjectMember).filter(
            ProjectMember.project_id == ecn.project_id
        ).all()

        project_user_ids = [pm.user_id for pm in project_members]

        if project_user_ids:
            # 查找项目成员中属于该部门的用户
            project_dept_users = db.query(User).filter(
                User.id.in_(project_user_ids),
                User.department == dept_name,
                User.is_active
            ).all()

            if project_dept_users:
                # 优先选择项目成员中的部门负责人
                for user in project_dept_users:
                    if user.position and "负责人" in user.position:
                        return user.id

                # 如果没有负责人，选择项目成员中的部门经理
                for user in project_dept_users:
                    if user.position and ("经理" in user.position or "主管" in user.position):
                        return user.id

    # 如果项目成员中没有找到，从部门所有用户中选择
    users = find_users_by_department(db, dept_name)

    if not users:
        return None

    # 优先选择部门负责人
    for user in users:
        if user.position and "负责人" in user.position:
            return user.id

    # 如果没有负责人，选择部门经理
    for user in users:
        if user.position and ("经理" in user.position or "主管" in user.position):
            return user.id

    # 如果都没有，返回None（不分配给普通活跃用户）
    return None


def auto_assign_pending_evaluations(
    db: Session,
    ecn_id: int
) -> int:
    """
    自动分配所有待分配的评估任务
    返回分配成功的数量
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        return 0

    pending_evals = db.query(EcnEvaluation).filter(
        and_(
            EcnEvaluation.ecn_id == ecn_id,
            EcnEvaluation.status == "PENDING",
            EcnEvaluation.evaluator_id.is_(None)
        )
    ).all()

    assigned_count = 0
    for eval in pending_evals:
        evaluator_id = auto_assign_evaluation(db, ecn, eval)
        if evaluator_id:
            eval.evaluator_id = evaluator_id
            eval.status = "ASSIGNED"  # 如果状态支持，可以设置为已分配
            db.add(eval)
            assigned_count += 1

    if assigned_count > 0:
        db.commit()

    return assigned_count


def auto_assign_pending_approvals(
    db: Session,
    ecn_id: int
) -> int:
    """
    自动分配所有待分配的审批任务
    返回分配成功的数量
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        return 0

    pending_approvals = db.query(EcnApproval).filter(
        and_(
            EcnApproval.ecn_id == ecn_id,
            EcnApproval.status == "PENDING",
            EcnApproval.approver_id.is_(None)
        )
    ).all()

    assigned_count = 0
    for approval in pending_approvals:
        approver_id = auto_assign_approval(db, ecn, approval)
        if approver_id:
            approval.approver_id = approver_id
            db.add(approval)
            assigned_count += 1

    if assigned_count > 0:
        db.commit()

    return assigned_count


def auto_assign_pending_tasks(
    db: Session,
    ecn_id: int
) -> int:
    """
    自动分配所有待分配的执行任务
    返回分配成功的数量
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        return 0

    pending_tasks = db.query(EcnTask).filter(
        and_(
            EcnTask.ecn_id == ecn_id,
            EcnTask.status == "PENDING",
            EcnTask.assignee_id.is_(None)
        )
    ).all()

    assigned_count = 0
    for task in pending_tasks:
        assignee_id = auto_assign_task(db, ecn, task)
        if assignee_id:
            task.assignee_id = assignee_id
            db.add(task)
            assigned_count += 1

    if assigned_count > 0:
        db.commit()

    return assigned_count

