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


# TEN-05：TenantAwareQuery（简易查询构建器）与 require_same_tenant（DEPRECATED
# 单点检查函数）已删除——全仓零真实调用点，租户隔离统一由 TEN-02 的框架级
# 查询过滤（app/core/database/tenant_scope.py，do_orm_execute+
# with_loader_criteria）承担，不需要调用方手动构造或检查。
