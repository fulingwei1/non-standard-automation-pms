# -*- coding: utf-8 -*-
"""
全局认证中间件 - 默认拒绝策略

实现"先关门后开窗"的安全策略：
1. 默认所有API都需要认证
2. 白名单中的路径可以公开访问
3. 验证通过后将用户信息存入 request.state
"""

import logging
from typing import List

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.auth import get_current_user
from app.core.config import settings
from app.models.base import get_db

logger = logging.getLogger(__name__)


class GlobalAuthMiddleware(BaseHTTPMiddleware):
    """
    全局认证中间件 - 默认拒绝策略

    工作原理：
    1. 检查请求路径是否在白名单
    2. 白名单内 -> 直接放行
    3. 白名单外 -> 验证Authorization header
    4. 验证成功 -> 将用户存入request.state，继续处理
    5. 验证失败 -> 返回401
    """

    # 白名单：这些路径不需要认证
    WHITE_LIST: List[str] = [
        # 认证相关
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",

        # 系统接口
        "/health",
        "/",

        # API文档（生产环境建议移除或需要认证）
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/openapi.json",  # 实际配置的OpenAPI路径
    ]

    # 白名单前缀：以这些开头的路径都允许
    WHITE_LIST_PREFIXES: List[str] = [
        "/static/",
        "/assets/",
    ]

    async def dispatch(self, request: Request, call_next):
        """处理每个请求"""
        path = request.url.path

        # 开发环境可以通过配置临时禁用全局认证
        if hasattr(settings, 'ENABLE_GLOBAL_AUTH') and not settings.ENABLE_GLOBAL_AUTH:
            logger.warning("全局认证已禁用（仅开发环境）")
            return await call_next(request)

        # 检查白名单
        if self._is_whitelisted(path):
            logger.debug(f"白名单路径: {path}")
            return await call_next(request)

        # 验证Token
        try:
            # 从Authorization header获取token
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                logger.warning(f"未提供认证凭据: {request.method} {path}")
                return self._unauthorized_response("未提供认证凭据", "MISSING_TOKEN")

            token = auth_header.split(" ")[1]

            # 验证token并获取用户
            db = next(get_db())
            try:
                user = await get_current_user(token=token, db=db)

                # 将用户信息存入request.state供后续使用
                request.state.user = user
                request.state.user_id = user.id

                # 记录访问日志（可选）
                logger.debug(
                    f"API访问: {request.method} {path} | "
                    f"用户: {user.username} (ID: {user.id})"
                )

                # 继续处理请求
                response = await call_next(request)
                return response

            finally:
                db.close()

        except HTTPException as e:
            logger.warning(f"认证失败: {path} - {e.detail}")
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "code": e.status_code,
                    "message": str(e.detail),
                    "error_code": "AUTH_FAILED"
                },
                headers=e.headers or {},
            )
        except Exception as e:
            logger.error(f"认证服务异常: {path} - {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "code": 500,
                    "message": "认证服务异常，请稍后重试",
                    "error_code": "AUTH_ERROR"
                },
            )

    def _is_whitelisted(self, path: str) -> bool:
        """
        检查路径是否在白名单中

        Args:
            path: 请求路径

        Returns:
            bool: True表示在白名单中，可以放行
        """
        # 精确匹配
        if path in self.WHITE_LIST:
            return True

        # 前缀匹配
        for prefix in self.WHITE_LIST_PREFIXES:
            if path.startswith(prefix):
                return True

        return False

    @staticmethod
    def _unauthorized_response(message: str, error_code: str) -> JSONResponse:
        """
        返回401未授权响应

        Args:
            message: 错误消息
            error_code: 错误代码

        Returns:
            JSONResponse: 401响应
        """
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "code": 401,
                "message": message,
                "error_code": error_code
            },
            headers={"WWW-Authenticate": "Bearer"},
        )


# 辅助函数：供其他模块添加白名单路径
def add_whitelist_path(path: str) -> None:
    """
    动态添加白名单路径

    Args:
        path: 要添加的路径
    """
    if path not in GlobalAuthMiddleware.WHITE_LIST:
        GlobalAuthMiddleware.WHITE_LIST.append(path)
        logger.info(f"添加白名单路径: {path}")


def add_whitelist_prefix(prefix: str) -> None:
    """
    动态添加白名单前缀

    Args:
        prefix: 要添加的前缀
    """
    if prefix not in GlobalAuthMiddleware.WHITE_LIST_PREFIXES:
        GlobalAuthMiddleware.WHITE_LIST_PREFIXES.append(prefix)
        logger.info(f"添加白名单前缀: {prefix}")
