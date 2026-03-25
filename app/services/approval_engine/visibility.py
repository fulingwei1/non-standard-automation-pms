# -*- coding: utf-8 -*-
"""
审批参与者可见性控制

基于参与关系（而非 data_scope 组织层级）判断用户对审批实例的可见性。
设计原则：fail-closed —— 任何异常均拒绝访问。

参与角色：
- 发起人 (initiator)
- 审批人 (assignee，含委托/转审/加签)
- 抄送人 (cc)
- 审批管理员 (approval:admin 权限)
"""

import logging
from enum import Enum
from typing import Optional

from sqlalchemy import exists
from sqlalchemy.orm import Query, Session

from app.core.auth import check_permission, is_superuser
from app.models.approval.instance import ApprovalInstance
from app.models.approval.task import ApprovalCarbonCopy, ApprovalTask
from app.models.user import User

logger = logging.getLogger(__name__)


class ParticipantRole(str, Enum):
    """用户在某个审批实例中的参与角色"""

    INITIATOR = "INITIATOR"
    APPROVER = "APPROVER"
    CC = "CC"
    ADMIN = "ADMIN"
    NONE = "NONE"


def _is_approval_admin(user: User, db: Session) -> bool:
    """检查用户是否为审批管理员（superuser 或持有 approval:admin）"""
    if is_superuser(user):
        return True
    return check_permission(user, "approval:admin", db)


def resolve_participant_role(
    db: Session,
    instance_id: int,
    user: User,
) -> ParticipantRole:
    """
    解析用户在指定审批实例中的参与角色。

    优先级：ADMIN > INITIATOR > APPROVER > CC > NONE
    fail-closed：异常时返回 NONE。
    """
    try:
        # 管理员
        if _is_approval_admin(user, db):
            return ParticipantRole.ADMIN

        # 发起人
        is_initiator = (
            db.query(ApprovalInstance.id)
            .filter(
                ApprovalInstance.id == instance_id,
                ApprovalInstance.initiator_id == user.id,
            )
            .first()
            is not None
        )
        if is_initiator:
            return ParticipantRole.INITIATOR

        # 审批人（含委托、转审、加签）
        has_task = (
            db.query(ApprovalTask.id)
            .filter(
                ApprovalTask.instance_id == instance_id,
                ApprovalTask.assignee_id == user.id,
            )
            .first()
            is not None
        )
        if has_task:
            return ParticipantRole.APPROVER

        # 抄送人
        has_cc = (
            db.query(ApprovalCarbonCopy.id)
            .filter(
                ApprovalCarbonCopy.instance_id == instance_id,
                ApprovalCarbonCopy.cc_user_id == user.id,
            )
            .first()
            is not None
        )
        if has_cc:
            return ParticipantRole.CC

        return ParticipantRole.NONE
    except Exception:
        logger.exception(
            "resolve_participant_role failed: instance_id=%s, user_id=%s",
            instance_id,
            user.id,
        )
        return ParticipantRole.NONE


def check_instance_visible(
    db: Session,
    instance_id: int,
    user: User,
) -> bool:
    """
    检查用户是否可查看指定审批实例。

    任何参与角色（发起人/审批人/抄送人/管理员）均可见。
    fail-closed：异常时返回 False。
    """
    return resolve_participant_role(db, instance_id, user) != ParticipantRole.NONE


def check_task_visible(
    db: Session,
    task: ApprovalTask,
    user: User,
) -> bool:
    """
    检查用户是否可查看指定审批任务。

    可见条件：用户是该任务所属实例的任意参与者。
    """
    return check_instance_visible(db, task.instance_id, user)


def filter_visible_instances(
    query: Query,
    db: Session,
    user: User,
) -> Query:
    """
    对审批实例列表查询施加参与者可见性过滤。

    管理员/超管看全部，普通用户只看自己参与的实例。
    fail-closed：异常时返回空结果。
    """
    try:
        if _is_approval_admin(user, db):
            return query

        # 子查询：用户作为发起人
        is_initiator = ApprovalInstance.initiator_id == user.id

        # 子查询：用户作为审批人
        has_task = exists().where(
            ApprovalTask.instance_id == ApprovalInstance.id,
            ApprovalTask.assignee_id == user.id,
        )

        # 子查询：用户作为抄送人
        has_cc = exists().where(
            ApprovalCarbonCopy.instance_id == ApprovalInstance.id,
            ApprovalCarbonCopy.cc_user_id == user.id,
        )

        return query.filter(is_initiator | has_task | has_cc)
    except Exception:
        logger.exception(
            "filter_visible_instances failed: user_id=%s", user.id
        )
        return query.filter(False)


def check_can_operate_instance(
    db: Session,
    instance_id: int,
    user: User,
    allowed_roles: tuple[ParticipantRole, ...] = (
        ParticipantRole.INITIATOR,
        ParticipantRole.APPROVER,
        ParticipantRole.ADMIN,
    ),
) -> bool:
    """
    检查用户是否可对实例执行写操作。

    默认允许发起人、审批人和管理员操作，抄送人只能查看。
    """
    role = resolve_participant_role(db, instance_id, user)
    return role in allowed_roles


def check_can_remind(
    db: Session,
    task: ApprovalTask,
    user: User,
) -> bool:
    """
    检查用户是否可催办指定任务。

    允许：发起人、管理员（与 approval_scope.REMINDABLE_ROLES 对齐）。
    """
    return check_can_operate_instance(
        db,
        task.instance_id,
        user,
        allowed_roles=(
            ParticipantRole.INITIATOR,
            ParticipantRole.ADMIN,
        ),
    )


def check_can_comment(
    db: Session,
    instance_id: int,
    user: User,
) -> bool:
    """
    检查用户是否可在指定审批实例上评论。

    允许：发起人、审批人、管理员。抄送人仅可查看，不可评论。
    与 approval_scope.COMMENTABLE_ROLES 对齐。
    """
    return check_can_operate_instance(
        db,
        instance_id,
        user,
        allowed_roles=(
            ParticipantRole.INITIATOR,
            ParticipantRole.APPROVER,
            ParticipantRole.ADMIN,
        ),
    )
