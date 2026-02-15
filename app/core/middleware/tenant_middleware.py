# -*- coding: utf-8 -*-
"""
租户上下文中间件

提供多租户数据隔离的核心支持：
1. 从认证用户提取 tenant_id 并存入 request.state
2. 提供租户上下文工具函数
3. 支持跨请求的租户上下文传递
"""

import logging
from contextvars import ContextVar
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# 线程安全的租户上下文变量
_current_tenant_id: ContextVar[Optional[int]] = ContextVar("current_tenant_id", default=None)


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
            if user:
                tenant_id = getattr(user, "tenant_id", None)
                # 设置到 request.state 方便后续访问
                request.state.tenant_id = tenant_id

                # 设置到上下文变量（支持嵌套调用）
                set_current_tenant_id(tenant_id)

                logger.debug(
                    f"Tenant context set: tenant_id={tenant_id}, "
                    f"user_id={user.id}, path={request.url.path}"
                )
            else:
                # 未认证请求（白名单路径）
                request.state.tenant_id = None
                set_current_tenant_id(None)

            # 继续处理请求
            response = await call_next(request)
            return response

        finally:
            # 清理上下文（防止上下文泄露）
            set_current_tenant_id(None)


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
