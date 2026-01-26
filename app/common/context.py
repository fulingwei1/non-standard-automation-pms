# -*- coding: utf-8 -*-
"""
请求上下文模块
使用 ContextVar 存储当前请求的用户、IP 和用户代理
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


def set_audit_context(
    operator_id: Optional[int] = None,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    detail: Optional[Dict[str, Any]] = None,
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


def get_audit_context() -> Dict[str, Any]:
    """获取审计上下文"""
    return {
        "operator_id": operator_id_ctx.get(),
        "client_ip": client_ip_ctx.get(),
        "user_agent": user_agent_ctx.get(),
        "detail": audit_detail_ctx.get(),
    }


def clear_audit_context():
    """清除审计上下文"""
    operator_id_ctx.set(None)
    client_ip_ctx.set(None)
    user_agent_ctx.set(None)
    audit_detail_ctx.set({})
