# -*- coding: utf-8 -*-
"""
工程师绩效数据范围控制核心模块 (Engineer Performance Data Scope)

Sprint 3 / Scope Core — 提供 scope 解析、单条记录校验、查询过滤三大能力。

设计要点:
- 复用现有 Role.data_scope / RoleDataScope / DataScopeServiceEnhanced 基础设施
- resource_type = "engineer_performance"
- PerformanceResult 使用 department_id（非 org_unit_id），需适配
- fail-closed: 任何异常或未知情况均拒绝访问
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Set

from sqlalchemy.orm import Query, Session

from app.models.performance import PerformanceResult
from app.models.permission import ScopeType
from app.models.user import User
from app.services.data_scope.user_scope import UserScopeService
from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced
from app.services.permission_service import PermissionService

logger = logging.getLogger(__name__)

# 本模块在 RoleDataScope 中使用的 resource_type 标识
ENGPERF_RESOURCE_TYPE = "engineer_performance"


# ---------------------------------------------------------------------------
# Scope 上下文
# ---------------------------------------------------------------------------

@dataclass
class EngPerfScopeContext:
    """工程师绩效数据范围上下文

    Attributes:
        scope_type: 范围类型 (ALL / DEPARTMENT / TEAM / OWN 等)
        user_id: 当前用户 ID
        accessible_dept_ids: 可访问的部门 ID 列表。
            None  = 不限（ALL scope）
            []    = 空（OWN scope，由 user_id 过滤）
        accessible_user_ids: 可访问的用户 ID 列表（TEAM scope 时使用，包含自己）
    """
    scope_type: str = ScopeType.OWN.value
    user_id: int = 0
    accessible_dept_ids: Optional[List[int]] = None
    accessible_user_ids: Optional[List[int]] = None

    @property
    def is_all(self) -> bool:
        return self.scope_type == ScopeType.ALL.value

    @property
    def is_own(self) -> bool:
        return self.scope_type == ScopeType.OWN.value


# ---------------------------------------------------------------------------
# 1. resolve_engperf_scope  —  解析当前用户的绩效数据范围
# ---------------------------------------------------------------------------

def resolve_engperf_scope(db: Session, user: User) -> EngPerfScopeContext:
    """解析用户在 engineer_performance 模块的数据范围

    解析顺序:
    1. 超级管理员 → ALL
    2. RoleDataScope(resource_type="engineer_performance") → 精细配置
    3. Role.data_scope → 降级读取角色默认 scope
    4. 以上均无 → OWN（fail-closed）

    TEAM scope 特殊处理: 查询 User.reporting_to 获取直属下级 ID 列表，
    与 accessible_dept_ids 并行使用。
    """
    # 超级管理员
    if user.is_superuser:
        logger.debug("用户 %s 是超级管理员，scope=ALL", user.id)
        return EngPerfScopeContext(scope_type=ScopeType.ALL.value, user_id=user.id)

    try:
        # ---- 步骤 1: 从 RoleDataScope 读取 resource_type 级别的 scope ----
        scopes = PermissionService.get_user_data_scopes(db, user.id)
        scope_type = scopes.get(ENGPERF_RESOURCE_TYPE)

        # ---- 步骤 2: 降级到 Role.data_scope ----
        if not scope_type:
            for user_role in user.roles:
                if user_role.role and user_role.role.is_active:
                    scope_type = user_role.role.data_scope
                    break

        scope_type = scope_type or ScopeType.OWN.value

        logger.debug(
            "用户 %s 的 engperf scope_type=%s", user.id, scope_type,
        )

        # ---- 步骤 3: 根据 scope_type 计算可访问范围 ----
        accessible_dept_ids: Optional[List[int]] = None
        accessible_user_ids: Optional[List[int]] = None

        if scope_type == ScopeType.ALL.value:
            # None 表示不限
            accessible_dept_ids = None

        elif scope_type in (
            ScopeType.DEPARTMENT.value,
            ScopeType.BUSINESS_UNIT.value,
        ):
            accessible_dept_ids = DataScopeServiceEnhanced.get_accessible_org_units(
                db, user.id, scope_type,
            )
            if not accessible_dept_ids:
                logger.warning(
                    "用户 %s scope=%s 但无关联组织单元，降级为 OWN",
                    user.id, scope_type,
                )
                scope_type = ScopeType.OWN.value
                accessible_dept_ids = []

        elif scope_type == ScopeType.TEAM.value:
            # TEAM: 自己 + 直属下级
            subordinate_ids: Set[int] = UserScopeService.get_subordinate_ids(
                db, user.id,
            )
            if not subordinate_ids:
                logger.warning(
                    "用户 %s scope=TEAM 但无下属，降级为 OWN",
                    user.id,
                )
                scope_type = ScopeType.OWN.value
                accessible_dept_ids = []
            else:
                accessible_user_ids = list(subordinate_ids | {user.id})
                # 同时获取这些人所在部门，用于 department_id 过滤
                accessible_dept_ids = _get_dept_ids_for_users(db, accessible_user_ids)

        else:
            # OWN / CUSTOM / PROJECT 等 → 均视为 OWN
            scope_type = ScopeType.OWN.value
            accessible_dept_ids = []

        return EngPerfScopeContext(
            scope_type=scope_type,
            user_id=user.id,
            accessible_dept_ids=accessible_dept_ids,
            accessible_user_ids=accessible_user_ids,
        )

    except Exception as e:
        logger.error(
            "解析 engperf scope 失败 (user_id=%s): %s", user.id, e, exc_info=True,
        )
        # fail-closed
        return EngPerfScopeContext(
            scope_type=ScopeType.OWN.value,
            user_id=user.id,
            accessible_dept_ids=[],
        )


# ---------------------------------------------------------------------------
# 2. can_access_engineer_data  —  单条记录访问校验
# ---------------------------------------------------------------------------

def can_access_engineer_data(
    scope: EngPerfScopeContext,
    target_user_id: int,
    target_dept_id: Optional[int] = None,
) -> bool:
    """判断当前 scope 是否允许访问目标工程师的数据

    Args:
        scope: 已解析的 scope 上下文
        target_user_id: 目标工程师的 user_id
        target_dept_id: 目标工程师的 department_id（可为 None）

    Returns:
        True = 允许访问, False = 拒绝
    """
    # ALL → 全部可见
    if scope.is_all:
        return True

    # OWN → 仅自己
    if scope.is_own:
        return target_user_id == scope.user_id

    # TEAM → 自己 + 直属下级（by user_id）
    if scope.accessible_user_ids is not None:
        if target_user_id in scope.accessible_user_ids:
            return True

    # DEPARTMENT / BUSINESS_UNIT → 按部门
    if scope.accessible_dept_ids is not None and target_dept_id is not None:
        if target_dept_id in scope.accessible_dept_ids:
            return True

    # fail-closed
    logger.debug(
        "拒绝访问: scope_type=%s, user_id=%s → target_user=%s, target_dept=%s",
        scope.scope_type, scope.user_id, target_user_id, target_dept_id,
    )
    return False


# ---------------------------------------------------------------------------
# 3. apply_engperf_scope_to_query  —  查询级 scope 过滤
# ---------------------------------------------------------------------------

def apply_engperf_scope_to_query(
    query: Query,
    scope: EngPerfScopeContext,
    *,
    user_id_column=None,
    dept_id_column=None,
) -> Query:
    """向 SQLAlchemy 查询注入数据范围过滤条件

    默认作用于 PerformanceResult 表的 user_id / department_id 字段。
    也可通过参数指定其他模型的列（如 CollaborationRating.ratee_id）。

    Args:
        query: SQLAlchemy Query 对象
        scope: 已解析的 scope 上下文
        user_id_column: 自定义 user_id 列（默认 PerformanceResult.user_id）
        dept_id_column: 自定义 department_id 列（默认 PerformanceResult.department_id）

    Returns:
        过滤后的 Query
    """
    if user_id_column is None:
        user_id_column = PerformanceResult.user_id
    if dept_id_column is None:
        dept_id_column = PerformanceResult.department_id

    # ALL → 不限
    if scope.is_all:
        return query

    # OWN → 仅自己
    if scope.is_own:
        return query.filter(user_id_column == scope.user_id)

    # TEAM → 按 user_id 列表过滤
    if scope.scope_type == ScopeType.TEAM.value and scope.accessible_user_ids:
        return query.filter(user_id_column.in_(scope.accessible_user_ids))

    # DEPARTMENT / BUSINESS_UNIT → 按 department_id 列表过滤
    if scope.accessible_dept_ids is not None:
        if scope.accessible_dept_ids:
            return query.filter(dept_id_column.in_(scope.accessible_dept_ids))
        else:
            # 空列表 → 无数据（fail-closed）
            return query.filter(user_id_column == scope.user_id)

    # 未知情况 → fail-closed
    logger.warning(
        "apply_engperf_scope_to_query: 未匹配到 scope 策略 "
        "(scope_type=%s), 返回空结果",
        scope.scope_type,
    )
    return query.filter(False)


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _get_dept_ids_for_users(db: Session, user_ids: List[int]) -> List[int]:
    """查询一组用户所属的 department_id 列表（去重）"""
    if not user_ids:
        return []

    rows = (
        db.query(User.department_id)
        .filter(User.id.in_(user_ids), User.department_id.isnot(None))
        .distinct()
        .all()
    )
    return [r[0] for r in rows]
