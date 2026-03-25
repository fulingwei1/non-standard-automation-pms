# -*- coding: utf-8 -*-
"""
审批可见性 / 参与人范围控制（participant_scope）

与 engineer_performance / sales 的 data_scope 不同，审批可见性基于参与关系而非组织架构：
- 发起人、审批人（含代理/转审）、抄送人可看到自己参与的实例
- 审批管理员（approval:admin）可看到所有实例
- 抄送人仅可看摘要，不可看表单详情

本模块仅提供核心判断逻辑，不改动 endpoint。
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Set

from sqlalchemy import or_, union_all
from sqlalchemy.orm import Query, Session

from app.models.approval.instance import ApprovalInstance
from app.models.approval.task import ApprovalCarbonCopy, ApprovalTask

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 参与人角色枚举
# ---------------------------------------------------------------------------


class ParticipantRole(str, Enum):
    """用户在某审批实例中的参与角色"""

    INITIATOR = "INITIATOR"  # 发起人
    APPROVER = "APPROVER"  # 当前/历史审批人（含正常分配）
    DELEGATED_APPROVER = "DELEGATED_APPROVER"  # 代理审批人
    TRANSFERRED_APPROVER = "TRANSFERRED_APPROVER"  # 转审审批人
    CC = "CC"  # 抄送人
    ADMIN = "ADMIN"  # 审批管理员（全局角色，非实例级）


# 拥有完整详情查看权的角色（含 form_data / action_logs）
FULL_DETAIL_ROLES: Set[ParticipantRole] = {
    ParticipantRole.INITIATOR,
    ParticipantRole.APPROVER,
    ParticipantRole.DELEGATED_APPROVER,
    ParticipantRole.TRANSFERRED_APPROVER,
    ParticipantRole.ADMIN,
}

# 仅摘要可见的角色（不含 form_data）
SUMMARY_ONLY_ROLES: Set[ParticipantRole] = {
    ParticipantRole.CC,
}

# 可评论的角色
COMMENTABLE_ROLES: Set[ParticipantRole] = {
    ParticipantRole.INITIATOR,
    ParticipantRole.APPROVER,
    ParticipantRole.DELEGATED_APPROVER,
    ParticipantRole.TRANSFERRED_APPROVER,
    ParticipantRole.ADMIN,
}

# 可催办的角色（发起人 + 管理员）
REMINDABLE_ROLES: Set[ParticipantRole] = {
    ParticipantRole.INITIATOR,
    ParticipantRole.ADMIN,
}


# ---------------------------------------------------------------------------
# 上下文
# ---------------------------------------------------------------------------


@dataclass
class ApprovalScopeContext:
    """审批可见性上下文"""

    user_id: int
    is_admin: bool = False  # 是否拥有 approval:admin 权限
    roles_in_instance: Set[ParticipantRole] = field(default_factory=set)

    @property
    def can_view(self) -> bool:
        """是否可以看到该实例（至少是摘要）"""
        return self.is_admin or bool(self.roles_in_instance)

    @property
    def can_view_detail(self) -> bool:
        """是否可以看到完整详情（form_data / logs）"""
        if self.is_admin:
            return True
        return bool(self.roles_in_instance & FULL_DETAIL_ROLES)

    @property
    def can_comment(self) -> bool:
        """是否可以评论"""
        if self.is_admin:
            return True
        return bool(self.roles_in_instance & COMMENTABLE_ROLES)

    @property
    def can_remind(self) -> bool:
        """是否可以催办"""
        if self.is_admin:
            return True
        return bool(self.roles_in_instance & REMINDABLE_ROLES)


# ---------------------------------------------------------------------------
# 核心：解析用户在某实例中的参与角色
# ---------------------------------------------------------------------------


def resolve_participant_roles(
    db: Session,
    instance_id: int,
    user_id: int,
) -> Set[ParticipantRole]:
    """
    查询用户在指定审批实例中的所有参与角色。

    返回空集合表示用户不是该实例的任何参与人。
    """
    roles: Set[ParticipantRole] = set()

    # 1. 发起人
    is_initiator = (
        db.query(ApprovalInstance.id)
        .filter(
            ApprovalInstance.id == instance_id,
            ApprovalInstance.initiator_id == user_id,
        )
        .first()
    )
    if is_initiator:
        roles.add(ParticipantRole.INITIATOR)

    # 2. 审批任务（当前/历史，含代理/转审）
    tasks = (
        db.query(ApprovalTask.assignee_type)
        .filter(
            ApprovalTask.instance_id == instance_id,
            ApprovalTask.assignee_id == user_id,
        )
        .all()
    )
    for (assignee_type,) in tasks:
        if assignee_type == "DELEGATED":
            roles.add(ParticipantRole.DELEGATED_APPROVER)
        elif assignee_type == "TRANSFERRED":
            roles.add(ParticipantRole.TRANSFERRED_APPROVER)
        else:
            # NORMAL / ADDED_BEFORE / ADDED_AFTER 均视为普通审批人
            roles.add(ParticipantRole.APPROVER)

    # 3. 抄送人
    is_cc = (
        db.query(ApprovalCarbonCopy.id)
        .filter(
            ApprovalCarbonCopy.instance_id == instance_id,
            ApprovalCarbonCopy.cc_user_id == user_id,
        )
        .first()
    )
    if is_cc:
        roles.add(ParticipantRole.CC)

    return roles


# ---------------------------------------------------------------------------
# 组合：构建完整的 ApprovalScopeContext
# ---------------------------------------------------------------------------


def build_approval_scope(
    db: Session,
    instance_id: int,
    user_id: int,
    is_admin: bool = False,
) -> ApprovalScopeContext:
    """
    构建用户对某审批实例的完整可见性上下文。

    Args:
        db: 数据库会话
        instance_id: 审批实例 ID
        user_id: 当前用户 ID
        is_admin: 是否拥有 approval:admin 权限（由调用方从权限系统获取）
    """
    roles = resolve_participant_roles(db, instance_id, user_id)
    return ApprovalScopeContext(
        user_id=user_id,
        is_admin=is_admin,
        roles_in_instance=roles,
    )


# ---------------------------------------------------------------------------
# 公开 API：单条实例判断
# ---------------------------------------------------------------------------


def can_view_approval_instance(
    db: Session,
    instance_id: int,
    user_id: int,
    is_admin: bool = False,
) -> bool:
    """判断用户是否可以查看指定审批实例（至少摘要级）"""
    if is_admin:
        return True
    ctx = build_approval_scope(db, instance_id, user_id, is_admin=False)
    return ctx.can_view


def can_comment_on_approval(
    db: Session,
    instance_id: int,
    user_id: int,
    is_admin: bool = False,
) -> bool:
    """判断用户是否可以在指定审批实例上评论"""
    if is_admin:
        return True
    ctx = build_approval_scope(db, instance_id, user_id, is_admin=False)
    return ctx.can_comment


def can_remind_approval(
    db: Session,
    instance_id: int,
    user_id: int,
    is_admin: bool = False,
) -> bool:
    """判断用户是否可以催办指定审批实例"""
    if is_admin:
        return True
    ctx = build_approval_scope(db, instance_id, user_id, is_admin=False)
    return ctx.can_remind


# ---------------------------------------------------------------------------
# 公开 API：批量 — 获取用户可见的审批实例 ID
# ---------------------------------------------------------------------------


def get_visible_approval_instance_ids(
    db: Session,
    user_id: int,
    is_admin: bool = False,
    status: Optional[str] = None,
    limit: int = 5000,
) -> List[int]:
    """
    获取用户可见的所有审批实例 ID 列表。

    管理员直接返回全部（受 limit 限制）；
    普通用户通过 UNION 三张表取参与的实例 ID。

    Args:
        db: 数据库会话
        user_id: 用户 ID
        is_admin: 是否审批管理员
        status: 可选状态过滤
        limit: 最大返回数量（防止全表扫描）
    """
    if is_admin:
        query = db.query(ApprovalInstance.id)
        if status:
            query = query.filter(ApprovalInstance.status == status)
        rows = query.order_by(ApprovalInstance.id.desc()).limit(limit).all()
        return [r[0] for r in rows]

    # 发起人
    q_initiator = db.query(ApprovalInstance.id).filter(
        ApprovalInstance.initiator_id == user_id,
    )

    # 审批人（含代理/转审/加签）
    q_approver = db.query(ApprovalTask.instance_id).filter(
        ApprovalTask.assignee_id == user_id,
    )

    # 抄送人
    q_cc = db.query(ApprovalCarbonCopy.instance_id).filter(
        ApprovalCarbonCopy.cc_user_id == user_id,
    )

    # UNION 去重
    all_ids_subq = union_all(q_initiator, q_approver, q_cc).subquery()
    query = (
        db.query(ApprovalInstance.id)
        .filter(ApprovalInstance.id.in_(db.query(all_ids_subq.c[0])))
    )

    if status:
        query = query.filter(ApprovalInstance.status == status)

    rows = query.order_by(ApprovalInstance.id.desc()).limit(limit).all()
    return [r[0] for r in rows]


# ---------------------------------------------------------------------------
# 公开 API：查询过滤器 — 注入到 list endpoint
# ---------------------------------------------------------------------------


def apply_approval_visibility(
    query: Query,
    user_id: int,
    is_admin: bool = False,
) -> Query:
    """
    为 ApprovalInstance 列表查询注入可见性过滤。

    管理员不过滤；普通用户只能看到自己参与的实例。
    使用 EXISTS 子查询而非 JOIN，避免结果重复。
    """
    if is_admin:
        return query

    from sqlalchemy import exists

    # EXISTS: 发起人
    cond_initiator = ApprovalInstance.initiator_id == user_id

    # EXISTS: 审批人
    cond_approver = exists().where(
        (ApprovalTask.instance_id == ApprovalInstance.id)
        & (ApprovalTask.assignee_id == user_id)
    )

    # EXISTS: 抄送人
    cond_cc = exists().where(
        (ApprovalCarbonCopy.instance_id == ApprovalInstance.id)
        & (ApprovalCarbonCopy.cc_user_id == user_id)
    )

    return query.filter(or_(cond_initiator, cond_approver, cond_cc))
