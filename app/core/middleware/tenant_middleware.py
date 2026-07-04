# -*- coding: utf-8 -*-
"""
租户上下文中间件

提供多租户数据隔离的核心支持：
1. 从认证用户提取 tenant_id 并存入 request.state
2. 提供租户上下文工具函数
3. 支持跨请求的租户上下文传递
"""

import logging
import os
from contextvars import ContextVar
from typing import Optional, Tuple

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


def get_enforce_mode() -> str:
    """租户隔离执行模式（TEN-06）。

    - log（默认）：无租户的非超管放行但记告警——灰度观测期；
    - strict：拒绝（fail-closed）——存量用户归户迁移验证后切换。
    """
    mode = os.getenv("TENANT_ENFORCE_MODE", "log").lower()
    return mode if mode in ("log", "strict") else "log"


def evaluate_tenant_access(user, mode: str) -> Tuple[bool, str]:
    """租户访问决策（TEN-06 fail-closed 核心）。

    超管跨租户（tenant_id 允许为 NULL）；未认证请求由前置认证中间件的
    白名单管辖，这里放行；无租户的非超管按模式处理。
    """
    if user is None:
        return True, "unauthenticated"
    if getattr(user, "is_superuser", False):
        return True, "superuser"
    if getattr(user, "tenant_id", None) is not None:
        return True, "tenant"
    if mode == "strict":
        return False, "no-tenant"
    return True, "no-tenant(log)"

# 线程安全的租户上下文变量
_current_tenant_id: ContextVar[Optional[int]] = ContextVar("current_tenant_id", default=None)

# 当前请求是否为超级管理员（TEN-02 查询层过滤用）。
# None = 无请求上下文（后台任务/脚本等系统级调用，不受 ORM 层过滤约束）；
# True/False = 有已认证用户，是否超管。
_current_user_is_superuser: ContextVar[Optional[bool]] = ContextVar(
    "current_user_is_superuser", default=None
)


def get_current_tenant_id() -> Optional[int]:
    """获取当前请求的租户ID

    Returns:
        租户ID，如果未设置返回 None
    """
    return _current_tenant_id.get()


def set_current_tenant_id(tenant_id: Optional[int]) -> None:
    """设置当前请求的租户ID

    Args:
        tenant_id: 租户ID
    """
    _current_tenant_id.set(tenant_id)


def get_current_user_is_superuser() -> Optional[bool]:
    """获取当前请求用户是否为超级管理员。

    Returns:
        None：无请求上下文（后台任务/脚本）；True/False：已认证用户的超管标志。
    """
    return _current_user_is_superuser.get()


def set_current_user_is_superuser(value: Optional[bool]) -> None:
    """设置当前请求用户是否为超级管理员。"""
    _current_user_is_superuser.set(value)


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    租户上下文中间件

    工作原理：
    1. 在 GlobalAuthMiddleware 之后运行
    2. 从 request.state.user 提取 tenant_id
    3. 设置到 request.state.tenant_id 和上下文变量
    4. 请求结束后清理上下文
    """

    async def dispatch(self, request: Request, call_next):
        """处理每个请求"""
        tenant_id = None

        try:
            # 尝试从已认证的用户获取 tenant_id
            user = getattr(request.state, "user", None)

            # TEN-06：租户访问决策（fail-closed 可控）
            mode = get_enforce_mode()
            allowed, reason = evaluate_tenant_access(user, mode)
            if not allowed:
                logger.warning(
                    "Tenant fail-closed: user_id=%s 无租户归属被拒绝 path=%s",
                    getattr(user, "id", None), request.url.path,
                )
                return JSONResponse(
                    status_code=403,
                    content={
                        "code": "TENANT_REQUIRED",
                        "message": "账号未归属任何租户，请联系超级管理员分配租户",
                    },
                )
            if reason == "no-tenant(log)":
                logger.warning(
                    "Tenant fail-open(灰度): user_id=%s 无租户归属放行 path=%s "
                    "（TENANT_ENFORCE_MODE=strict 后将拒绝）",
                    getattr(user, "id", None), request.url.path,
                )

            if user:
                tenant_id = getattr(user, "tenant_id", None)
                # 设置到 request.state 方便后续访问
                request.state.tenant_id = tenant_id

                # 设置到上下文变量（支持嵌套调用）
                set_current_tenant_id(tenant_id)
                set_current_user_is_superuser(getattr(user, "is_superuser", False))

                logger.debug(
                    f"Tenant context set: tenant_id={tenant_id}, "
                    f"user_id={user.id}, path={request.url.path}"
                )
            else:
                # 未认证请求（白名单路径，由前置认证中间件放行）：
                # is_superuser 保持默认 None（不同于"已认证非超管无租户"的 False），
                # 查询层按无上下文的系统调用处理，不做租户过滤。
                request.state.tenant_id = None
                set_current_tenant_id(None)

            # 继续处理请求
            response = await call_next(request)
            return response

        finally:
            # 清理上下文（防止上下文泄露）
            set_current_tenant_id(None)
            set_current_user_is_superuser(None)


class TenantAwareQuery:
    """
    租户感知的查询构建器

    自动为查询添加 tenant_id 过滤条件。

    使用示例：
        from app.core.middleware.tenant_middleware import TenantAwareQuery

        # 在服务层使用
        query = TenantAwareQuery(db).query(Project)
        projects = query.filter(Project.status == "active").all()
    """

    def __init__(self, db, tenant_id: Optional[int] = None):
        """
        初始化租户感知查询

        Args:
            db: SQLAlchemy Session
            tenant_id: 租户ID（不传则从上下文获取）
        """
        self.db = db
        self.tenant_id = tenant_id if tenant_id is not None else get_current_tenant_id()

    def query(self, model, auto_filter: bool = True):
        """
        创建带租户过滤的查询

        Args:
            model: SQLAlchemy 模型类
            auto_filter: 是否自动添加租户过滤（默认 True）

        Returns:
            SQLAlchemy Query 对象
        """
        query = self.db.query(model)

        # 自动添加租户过滤
        if auto_filter and self.tenant_id and hasattr(model, "tenant_id"):
            query = query.filter(model.tenant_id == self.tenant_id)

        return query

    def filter_by_tenant(self, query, model):
        """
        为已有查询添加租户过滤

        Args:
            query: SQLAlchemy Query 对象
            model: SQLAlchemy 模型类

        Returns:
            添加过滤后的 Query 对象
        """
        if self.tenant_id and hasattr(model, "tenant_id"):
            return query.filter(model.tenant_id == self.tenant_id)
        return query


def require_same_tenant(user_tenant_id: Optional[int], resource_tenant_id: Optional[int]) -> bool:
    """
    检查资源是否属于用户的租户

    DEPRECATED: 建议使用 is_superuser(user) 函数判断超级管理员权限，
    而不是单纯依赖 tenant_id is None。

    Args:
        user_tenant_id: 用户的租户ID
        resource_tenant_id: 资源的租户ID

    Returns:
        是否属于同一租户

    Raises:
        None - 返回 False 而不是抛出异常，让调用方决定处理方式

    Note:
        此函数仅检查 tenant_id，不验证 is_superuser 标志位。
        对于超级管理员判断，应该使用：
        >>> from app.core.auth import is_superuser
        >>> if is_superuser(user):
        >>>     # 超级管理员可以访问所有资源
        >>>     pass
    """
    # 注意：这里的 tenant_id=None 判断不够严谨
    # 真正的超级管理员应该同时满足 is_superuser=True AND tenant_id IS NULL
    # 建议调用方先使用 is_superuser(user) 函数判断
    if user_tenant_id is None:
        return True

    # 系统级资源（tenant_id=None）所有租户可访问
    if resource_tenant_id is None:
        return True

    # 同一租户
    return user_tenant_id == resource_tenant_id
