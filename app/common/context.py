# -*- coding: utf-8 -*-
"""
请求上下文模块
使用 ContextVar 存储当前请求的用户、IP、用户代理和租户信息
"""

from contextvars import ContextVar
from typing import Any, Dict, Optional

# 操作人ID
operator_id_ctx: ContextVar[Optional[int]] = ContextVar("operator_id", default=None)

# 客户端IP
client_ip_ctx: ContextVar[Optional[str]] = ContextVar("client_ip", default=None)

# 用户代理
user_agent_ctx: ContextVar[Optional[str]] = ContextVar("user_agent", default=None)

# 附加详情
audit_detail_ctx: ContextVar[Dict[str, Any]] = ContextVar("audit_detail", default={})

# 租户ID（多租户隔离）
tenant_id_ctx: ContextVar[Optional[int]] = ContextVar("tenant_id", default=None)


def set_audit_context(
    operator_id: Optional[int] = None,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    detail: Optional[Dict[str, Any]] = None,
    tenant_id: Optional[int] = None,
):
    """设置审计上下文"""
    if operator_id is not None:
        operator_id_ctx.set(operator_id)
    if client_ip is not None:
        client_ip_ctx.set(client_ip)
    if user_agent is not None:
        user_agent_ctx.set(user_agent)
    if detail is not None:
        audit_detail_ctx.set(detail)
    if tenant_id is not None:
        tenant_id_ctx.set(tenant_id)


def get_audit_context() -> Dict[str, Any]:
    """获取审计上下文"""
    return {
        "operator_id": operator_id_ctx.get(),
        "client_ip": client_ip_ctx.get(),
        "user_agent": user_agent_ctx.get(),
        "detail": audit_detail_ctx.get(),
        "tenant_id": tenant_id_ctx.get(),
    }


def clear_audit_context():
    """清除审计上下文"""
    operator_id_ctx.set(None)
    client_ip_ctx.set(None)
    user_agent_ctx.set(None)
    audit_detail_ctx.set({})
    tenant_id_ctx.set(None)


def get_current_tenant_id() -> Optional[int]:
    """获取当前租户ID"""
    return tenant_id_ctx.get()


def set_current_tenant_id(tenant_id: Optional[int]):
    """设置当前租户ID"""
    tenant_id_ctx.set(tenant_id)
