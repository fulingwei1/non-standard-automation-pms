# -*- coding: utf-8 -*-
"""
销售模块数据范围控制

复用 engperf_scope 的模式：
  1. 从 RoleDataScope 读取 resource_type 对应的 scope_type
  2. 降级到 Role.data_scope
  3. 解析为 SalesScopeContext（含 accessible_dept_ids / accessible_user_ids）
  4. 提供通用 query filter 和单条记录访问判断

支持的销售资源类型：
  - customer     客户
  - opportunity   商机
  - quote         报价
  - contract      合同
  - sales（通配） 未单独配置时的默认资源

所有过滤 fail-closed：异常 / 空列表 → OWN。
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Set

from sqlalchemy.orm import Query, Session

from app.models.permission import ScopeType
from app.models.user import User
from app.services.data_scope.user_scope import UserScopeService
from app.services.permission_service import PermissionService

logger = logging.getLogger(__name__)

# 销售资源类型常量 —— 与 RoleDataScope.resource_type 对应
RT_CUSTOMER = "customer"
RT_OPPORTUNITY = "opportunity"
RT_QUOTE = "quote"
RT_CONTRACT = "contract"
RT_SALES = "sales"  # 通配 / 默认

# 资源类型查找顺序：先精确匹配，再降级到 "sales"
_SALES_RESOURCE_TYPES = (RT_CUSTOMER, RT_OPPORTUNITY, RT_QUOTE, RT_CONTRACT)

# 财务角色代码（用于 Invoice 等无 owner_id 的特殊处理）
_FINANCE_ROLE_CODES = frozenset({
    "FINANCE", "FI", "CFO",
    "财务", "财务人员", "财务专员", "财务经理", "财务总监",
})


# ---------------------------------------------------------------------------
# 上下文
# ---------------------------------------------------------------------------


@dataclass
class SalesScopeContext:
    """销售数据范围上下文

    Attributes:
        scope_type:          ScopeType value (ALL / DEPARTMENT / TEAM / OWN …)
        user_id:             当前用户 ID
        resource_type:       实际命中的资源类型（如 "quote" 或降级后的 "sales"）
        accessible_dept_ids: None=不限（ALL）; []=仅自己; [1,2,3]=指定部门
        accessible_user_ids: TEAM scope 时包含 自己 + 直属下级
        is_finance_role:     是否为财务角色（Invoice 等特殊权限）
    """

    scope_type: str
    user_id: int
    resource_type: str = RT_SALES
    accessible_dept_ids: Optional[List[int]] = None
    accessible_user_ids: Set[int] = field(default_factory=set)
    is_finance_role: bool = False


# ---------------------------------------------------------------------------
# Scope 解析
# ---------------------------------------------------------------------------


def resolve_sales_scope(
    db: Session,
    user: User,
    resource_type: str = RT_SALES,
) -> SalesScopeContext:
    """
    解析当前用户对指定销售资源的数据范围。

    解析优先级：
      1. superuser → ALL
      2. RoleDataScope[resource_type] （精确资源）
      3. RoleDataScope["sales"]       （通配降级）
      4. Role.data_scope              （全局降级）
      5. 默认 → OWN

    Args:
        db:            数据库会话
        user:          当前用户
        resource_type: 资源类型，默认 "sales"（通配）

    Returns:
        SalesScopeContext
    """
    # 检查财务角色
    is_finance = _check_finance_role(user)

    if user.is_superuser:
        return SalesScopeContext(
            scope_type=ScopeType.ALL.value,
            user_id=user.id,
            resource_type=resource_type,
            accessible_dept_ids=None,
            is_finance_role=is_finance,
        )

    # 1. 从 RoleDataScope 读取（精确 → 通配）
    scopes = PermissionService.get_user_data_scopes(db, user.id)
    scope_type = scopes.get(resource_type)
    hit_resource = resource_type

    if not scope_type and resource_type != RT_SALES:
        # 精确资源未配置，降级到 "sales" 通配
        scope_type = scopes.get(RT_SALES)
        hit_resource = RT_SALES

    # 2. 降级到 Role.data_scope
    if not scope_type:
        for user_role in getattr(user, "roles", []):
            role = getattr(user_role, "role", None)
            if role and getattr(role, "is_active", False):
                scope_type = getattr(role, "data_scope", None)
                if scope_type:
                    hit_resource = RT_SALES
                    break

    scope_type = scope_type or ScopeType.OWN.value

    # 3. 解析可访问范围
    accessible_dept_ids: Optional[List[int]] = None
    accessible_user_ids: Set[int] = set()

    if scope_type == ScopeType.ALL.value:
        accessible_dept_ids = None  # 不限

    elif scope_type in (ScopeType.DEPARTMENT.value, ScopeType.BUSINESS_UNIT.value):
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
        accessible_dept_ids = []  # TEAM 用 user_ids 过滤

    else:
        # OWN / PROJECT / CUSTOM / 其他 → 仅自己
        scope_type = ScopeType.OWN.value
        accessible_dept_ids = []

    ctx = SalesScopeContext(
        scope_type=scope_type,
        user_id=user.id,
        resource_type=hit_resource,
        accessible_dept_ids=accessible_dept_ids,
        accessible_user_ids=accessible_user_ids,
        is_finance_role=is_finance,
    )
    logger.debug(
        "sales scope: user=%d resource=%s → %s", user.id, resource_type, scope_type
    )
    return ctx


# ---------------------------------------------------------------------------
# 查询过滤器
# ---------------------------------------------------------------------------


def apply_owner_scope(
    query: Query,
    scope: SalesScopeContext,
    owner_column,
) -> Query:
    """
    为含 owner_id 的销售实体注入数据范围过滤。

    适用于：Quote.owner_id, Opportunity.owner_id, Lead.owner_id,
            Customer.sales_owner_id, Contract.sales_owner_id 等。

    Args:
        query:        SQLAlchemy 查询
        scope:        SalesScopeContext
        owner_column: 模型的 owner 列（如 Quote.owner_id）

    Returns:
        过滤后的 Query
    """
    if scope.scope_type == ScopeType.ALL.value:
        return query

    if scope.scope_type == ScopeType.OWN.value:
        return query.filter(owner_column == scope.user_id)

    if scope.scope_type == ScopeType.TEAM.value:
        if scope.accessible_user_ids:
            return query.filter(owner_column.in_(list(scope.accessible_user_ids)))
        return query.filter(owner_column == scope.user_id)

    # DEPARTMENT / BUSINESS_UNIT → 需要 JOIN User 获取 department_id
    if scope.accessible_dept_ids:
        return query.join(
            User, owner_column == User.id
        ).filter(User.department_id.in_(scope.accessible_dept_ids))

    # 空 dept_ids → fail-closed
    return query.filter(owner_column == scope.user_id)


def apply_finance_scope(
    query: Query,
    scope: SalesScopeContext,
    owner_column=None,
) -> Query:
    """
    发票 / 收款等无直接 owner_id 的财务数据过滤。

    规则：
      - ALL / 财务角色 → 不过滤
      - 有 owner_column → 走 apply_owner_scope
      - 无 owner_column → fail-closed（仅 ALL / 财务可见）

    Args:
        query:        SQLAlchemy 查询
        scope:        SalesScopeContext
        owner_column: 可选的 owner 列；Invoice 通常为 None

    Returns:
        过滤后的 Query
    """
    if scope.scope_type == ScopeType.ALL.value or scope.is_finance_role:
        return query

    if owner_column is not None:
        return apply_owner_scope(query, scope, owner_column)

    # 无 owner_column、非 ALL、非财务 → 不可见
    return query.filter(False)


# ---------------------------------------------------------------------------
# 单条记录访问判断
# ---------------------------------------------------------------------------


def can_access_sales_entity(
    scope: SalesScopeContext,
    owner_id: Optional[int],
    owner_dept_id: Optional[int] = None,
) -> bool:
    """
    判断当前用户是否可以访问某个销售实体。

    Args:
        scope:        SalesScopeContext
        owner_id:     实体负责人 ID
        owner_dept_id: 负责人所在部门 ID（DEPARTMENT scope 需要）

    Returns:
        bool
    """
    if scope.scope_type == ScopeType.ALL.value:
        return True

    if owner_id is None:
        # 无 owner → 仅 ALL 可见（已排除），或自己查自己
        return False

    if scope.scope_type == ScopeType.OWN.value:
        return owner_id == scope.user_id

    if scope.scope_type == ScopeType.TEAM.value:
        return owner_id in scope.accessible_user_ids

    # DEPARTMENT / BUSINESS_UNIT
    if scope.accessible_dept_ids and owner_dept_id is not None:
        return owner_dept_id in scope.accessible_dept_ids

    # dept_id 未知时，允许自己查自己
    if owner_id == scope.user_id:
        return True

    return False


def can_access_finance_entity(
    scope: SalesScopeContext,
    owner_id: Optional[int] = None,
    owner_dept_id: Optional[int] = None,
) -> bool:
    """
    判断当前用户是否可以访问财务实体（Invoice 等）。

    财务角色或 ALL → True；否则走 can_access_sales_entity。
    """
    if scope.is_finance_role or scope.scope_type == ScopeType.ALL.value:
        return True

    if owner_id is not None:
        return can_access_sales_entity(scope, owner_id, owner_dept_id)

    return False


# ---------------------------------------------------------------------------
# 辅助
# ---------------------------------------------------------------------------


def _check_finance_role(user: User) -> bool:
    """检查用户是否拥有财务角色"""
    for user_role in getattr(user, "roles", []):
        role = getattr(user_role, "role", None)
        if role and getattr(role, "is_active", False):
            code = (getattr(role, "role_code", "") or "").upper()
            if code in _FINANCE_ROLE_CODES:
                return True
    return False
