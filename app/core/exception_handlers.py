# -*- coding: utf-8 -*-
"""
统一异常处理器

根据DEBUG模式返回不同的错误信息，避免生产环境泄露系统内部信息。
"""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.exceptions import StarletteHTTPException
from typing import Any, Dict, Optional

from .config import settings
from .logging_config import get_logger

logger = get_logger(__name__)


class SecurityException(HTTPException):
    """
    安全相关的自定义异常
    """

    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str,
        user_friendly_message: Optional[str] = None,
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        self.user_friendly_message = user_friendly_message


class ResourceNotFoundException(SecurityException):
    """资源不存在异常"""

    def __init__(self, resource_name: str = "资源"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_name}不存在",
            error_code="RESOURCE_NOT_FOUND",
            user_friendly_message=f"未找到该{resource_name}",
        )


class PermissionDeniedException(SecurityException):
    """权限不足异常"""

    def __init__(self, detail: str = "权限不足"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="PERMISSION_DENIED",
            user_friendly_message="您没有执行此操作的权限",
        )


class RateLimitExceededException(SecurityException):
    """请求频率超限异常"""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求过于频繁，请稍后重试",
            error_code="RATE_LIMIT_EXCEEDED",
            user_friendly_message="请求过于频繁，请稍后重试",
        )


def _sanitize_error_detail(detail: Any) -> Any:
    """
    清理错误详情，避免泄露敏感信息

    Args:
        detail: 错误详情

    Returns:
        Any: 清理后的错误详情，保留原始结构
    """
    if isinstance(detail, dict):
        sanitized = {}
        for key, value in detail.items():
            # 过滤敏感信息
            if any(
                sensitive in key.lower()
                for sensitive in [
                    "password",
                    "token",
                    "secret",
                    "key",
                    "credential",
                ]
            ):
                sanitized[key] = "***"
            else:
                sanitized[key] = _sanitize_error_detail(value)
        return sanitized
    elif isinstance(detail, list):
        return [_sanitize_error_detail(item) for item in detail]
    elif isinstance(detail, tuple):
        return tuple(_sanitize_error_detail(item) for item in detail)
    elif isinstance(detail, (int, float, bool)) or detail is None:
        return detail
    elif isinstance(detail, str):
        # 简单的字符串清理
        return detail[:500] if len(detail) > 500 else detail
    return str(detail)


def _extract_user_message(detail: Any) -> str:
    """根据 detail 提取用户友好的提示信息"""
    if isinstance(detail, dict):
        for key in ("message", "detail", "error"):
            value = detail.get(key)
            if isinstance(value, str) and value:
                return value
        return str(detail)
    elif isinstance(detail, list) and detail:
        first = detail[0]
        if isinstance(first, dict):
            return first.get("message") or str(first)
        return str(first)
    return str(detail)


def _build_error_response(
    status_code: int,
    error_code: str,
    detail: str,
    user_friendly_message: str,
    request: Optional[Request] = None,
    exc: Optional[Exception] = None,
) -> Dict[str, Any]:
    """
    构建统一的错误响应

    Args:
        status_code: HTTP状态码
        error_code: 错误代码
        detail: 错误详情
        user_friendly_message: 用户友好的错误消息
        request: 请求对象（可选）
        exc: 异常对象（可选）

    Returns:
        Dict: 错误响应字典
    """
    response = {
        "code": error_code,
        "message": user_friendly_message,
    }

    # 生产环境不返回详细错误信息
    if not settings.DEBUG:
        logger.warning(
            f"Error: {error_code} - {user_friendly_message} "
            f"Request: {request.url.path if request else 'N/A'} "
            f"Exception: {exc.__class__.__name__ if exc else 'N/A'}"
        )
    else:
        # 开发环境返回详细错误信息
        response["detail"] = _sanitize_error_detail(detail)

        if exc and not isinstance(exc, SecurityException):
            logger.debug(f"Exception details: {exc}", exc_info=True)

    return response


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    HTTP异常处理器
    """
    status_code = exc.status_code

    if isinstance(exc, SecurityException):
        # 自定义安全异常
        content = _build_error_response(
            status_code=exc.status_code,
            error_code=exc.error_code,
            detail=exc.detail,
            user_friendly_message=exc.user_friendly_message or exc.detail,
            request=request,
            exc=exc,
        )
    else:
        # FastAPI/Starlette默认HTTP异常
        detail = exc.detail
        content = _build_error_response(
            status_code=status_code,
            error_code="HTTP_ERROR",
            detail=detail,
            user_friendly_message=_extract_user_message(detail),
            request=request,
            exc=exc,
        )

    return JSONResponse(status_code=status_code, content=content)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    请求验证异常处理器
    """
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

    errors = exc.errors()
    user_friendly_message = "请求参数验证失败"

    # 格式化验证错误
    error_details = []
    for error in errors:
        error_details.append(
            {
                "field": error["loc"][0] if error["loc"] else "unknown",
                "message": error["msg"],
            }
        )

    if error_details:
        user_friendly_message += (
            f"：{error_details[0]['field']} {error_details[0]['message']}"
        )

    content = _build_error_response(
        status_code=status_code,
        error_code="VALIDATION_ERROR",
        detail=error_details,
        user_friendly_message=user_friendly_message,
        request=request,
        exc=exc,
    )

    return JSONResponse(status_code=status_code, content=content)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    通用异常处理器（捕获所有未处理的异常）
    """
    logger.error(
        f"Unhandled exception: {exc.__class__.__name__}",
        exc_info=True,
    )

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    if settings.DEBUG:
        user_friendly_message = f"内部服务器错误: {str(exc)}"
        detail = {
            "type": exc.__class__.__name__,
            "message": str(exc),
        }
    else:
        user_friendly_message = "服务器内部错误，请联系管理员"
        detail = "Internal server error"

    content = _build_error_response(
        status_code=status_code,
        error_code="INTERNAL_ERROR",
        detail=detail,
        user_friendly_message=user_friendly_message,
        request=request,
        exc=exc,
    )

    return JSONResponse(status_code=status_code, content=content)


def setup_exception_handlers(app) -> None:
    """
    配置全局异常处理器

    Args:
        app: FastAPI应用实例
    """
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)


__all__ = [
    "SecurityException",
    "ResourceNotFoundException",
    "PermissionDeniedException",
    "RateLimitExceededException",
    "http_exception_handler",
    "validation_exception_handler",
    "general_exception_handler",
    "setup_exception_handlers",
]
