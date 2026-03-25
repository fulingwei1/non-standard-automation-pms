# -*- coding: utf-8 -*-
"""
工程师绩效数据范围控制

提供 scope 解析、查询过滤、单条记录访问判断。
所有排名/列表/详情接口通过本模块注入数据范围限制。
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Set

from sqlalchemy.orm import Query, Session

from app.models.performance import PerformanceResult
from app.models.permission import ScopeType
from app.models.user import User
from app.services.data_scope.user_scope import UserScopeService
from app.services.permission_service import PermissionService

logger = logging.getLogger(__name__)

RESOURCE_TYPE = "engineer_performance"


@dataclass
class EngPerfScopeContext:
    """工程师绩效数据范围上下文"""

    scope_type: str  # ScopeType value: ALL / DEPARTMENT / TEAM / OWN ...
    user_id: int
    # 可访问的部门ID列表；None 表示不限（ALL），空列表表示仅自己（OWN）
    accessible_dept_ids: Optional[List[int]] = None
    # TEAM scope 下可访问的用户ID集合（自己 + 直属下级）
    accessible_user_ids: Set[int] = field(default_factory=set)


def resolve_engperf_scope(db: Session, user: User) -> EngPerfScopeContext:
    """
    解析当前用户的工程师绩效数据范围。

    优先从 RoleDataScope 读取 resource_type="engineer_performance"，
    未配置则降级读取 Role.data_scope 字段。
    """
    if user.is_superuser:
        return EngPerfScopeContext(
            scope_type=ScopeType.ALL.value,
            user_id=user.id,
            accessible_dept_ids=None,
        )

    # 1. 从 RoleDataScope 读取
    scopes = PermissionService.get_user_data_scopes(db, user.id)
    scope_type = scopes.get(RESOURCE_TYPE)

    # 2. 降级到 Role.data_scope
    if not scope_type:
        for user_role in getattr(user, "roles", []):
            role = getattr(user_role, "role", None)
            if role and getattr(role, "is_active", False):
                scope_type = getattr(role, "data_scope", None)
                if scope_type:
                    break

    scope_type = scope_type or ScopeType.OWN.value

    # 3. 解析可访问范围
    accessible_dept_ids: Optional[List[int]] = None
    accessible_user_ids: Set[int] = set()

    if scope_type == ScopeType.ALL.value:
        accessible_dept_ids = None  # 不限

    elif scope_type in (
        ScopeType.DEPARTMENT.value,
        ScopeType.BUSINESS_UNIT.value,
    ):
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        accessible_dept_ids = DataScopeServiceEnhanced.get_accessible_org_units(
            db, user.id, scope_type
        )
        if not accessible_dept_ids:
            logger.warning(
                "用户 %d scope=%s 但无关联组织单元，降级为 OWN", user.id, scope_type
            )
            scope_type = ScopeType.OWN.value
            accessible_dept_ids = []

    elif scope_type == ScopeType.TEAM.value:
        subordinate_ids = UserScopeService.get_subordinate_ids(db, user.id)
        accessible_user_ids = subordinate_ids | {user.id}
        accessible_dept_ids = []  # TEAM 用 user_ids 过滤，不用 dept

    else:
        # OWN / PROJECT / CUSTOM / 其他 → 仅自己
        scope_type = ScopeType.OWN.value
        accessible_dept_ids = []

    ctx = EngPerfScopeContext(
        scope_type=scope_type,
        user_id=user.id,
        accessible_dept_ids=accessible_dept_ids,
        accessible_user_ids=accessible_user_ids,
    )
    logger.debug("engperf scope: user=%d → %s", user.id, scope_type)
    return ctx


# ---------------------------------------------------------------------------
# 查询过滤器
# ---------------------------------------------------------------------------


def apply_ranking_scope(query: Query, scope: EngPerfScopeContext) -> Query:
    """
    为 PerformanceResult 排名查询注入数据范围过滤。
    """
    if scope.scope_type == ScopeType.ALL.value:
        return query

    if scope.scope_type == ScopeType.OWN.value:
        return query.filter(PerformanceResult.user_id == scope.user_id)

    if scope.scope_type == ScopeType.TEAM.value:
        if scope.accessible_user_ids:
            return query.filter(
                PerformanceResult.user_id.in_(list(scope.accessible_user_ids))
            )
        return query.filter(PerformanceResult.user_id == scope.user_id)

    # DEPARTMENT / BUSINESS_UNIT
    if scope.accessible_dept_ids is not None:
        if scope.accessible_dept_ids:
            return query.filter(
                PerformanceResult.department_id.in_(scope.accessible_dept_ids)
            )
        # 空列表 → fail-closed
        return query.filter(PerformanceResult.user_id == scope.user_id)

    # fail-closed
    return query.filter(False)


def apply_user_id_scope(
    query: Query,
    scope: EngPerfScopeContext,
    user_id_column,
) -> Query:
    """
    为以 user_id 为主键的查询（如 CollaborationRating、KnowledgeContribution）
    注入数据范围过滤。

    Args:
        query: SQLAlchemy 查询
        scope: 数据范围上下文
        user_id_column: 模型的 user_id 列（如 CollaborationRating.ratee_id）
    """
    if scope.scope_type == ScopeType.ALL.value:
        return query

    if scope.scope_type == ScopeType.OWN.value:
        return query.filter(user_id_column == scope.user_id)

    if scope.scope_type == ScopeType.TEAM.value:
        if scope.accessible_user_ids:
            return query.filter(user_id_column.in_(list(scope.accessible_user_ids)))
        return query.filter(user_id_column == scope.user_id)

    # DEPARTMENT / BUSINESS_UNIT → 需要 JOIN User 获取 department
    if scope.accessible_dept_ids:
        from sqlalchemy import and_

        return query.join(
            User, user_id_column == User.id
        ).filter(User.department_id.in_(scope.accessible_dept_ids))

    return query.filter(user_id_column == scope.user_id)


# ---------------------------------------------------------------------------
# 单条记录访问判断
# ---------------------------------------------------------------------------


def can_view_engineer(
    scope: EngPerfScopeContext,
    target_user_id: int,
    target_dept_id: Optional[int] = None,
) -> bool:
    """
    判断当前用户是否可以查看目标工程师的绩效数据。
    """
    if scope.scope_type == ScopeType.ALL.value:
        return True

    if scope.scope_type == ScopeType.OWN.value:
        return target_user_id == scope.user_id

    if scope.scope_type == ScopeType.TEAM.value:
        return target_user_id in scope.accessible_user_ids

    # DEPARTMENT / BUSINESS_UNIT
    if scope.accessible_dept_ids and target_dept_id is not None:
        return target_dept_id in scope.accessible_dept_ids

    # dept_id 为 None 时，允许自己查自己
    if target_user_id == scope.user_id:
        return True

    return False


def check_department_accessible(
    scope: EngPerfScopeContext,
    department_id: int,
) -> bool:
    """
    判断当前 scope 是否可以访问指定部门的数据。
    """
    if scope.scope_type == ScopeType.ALL.value:
        return True

    if scope.accessible_dept_ids is not None:
        return department_id in scope.accessible_dept_ids

    return False
