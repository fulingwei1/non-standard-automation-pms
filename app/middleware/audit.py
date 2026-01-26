# -*- coding: utf-8 -*-
"""
审计日志中间件
捕获请求的 IP 和 User-Agent 并存入上下文中
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.common.context import set_audit_context


class AuditMiddleware(BaseHTTPMiddleware):
    """审计日志中间件"""

    async def dispatch(self, request: Request, call_next):
        # 提取客户端信息
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # 设置到上下文中
        set_audit_context(client_ip=client_ip, user_agent=user_agent)

        try:
            response = await call_next(request)
            return response
        finally:
            # 清理上下文，避免跨请求污染（ContextVar 本身是协程隔离的，但清理是好习惯）
            pass
            # clear_audit_context() # 如果在 auth 之后清理，可能会丢掉 operator_id
            # 实际上 ContextVar 在协程结束时会自动处理，不需要手动清理，除非是在线程池中复用线程。
