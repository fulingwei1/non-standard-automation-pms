# -*- coding: utf-8 -*-
"""
统一日志配置模块

根据DEBUG模式配置不同的日志级别，避免生产环境泄露敏感信息。

同时提供带上下文的日志辅助函数：
- log_error_with_context: 记录错误 + 上下文信息
- log_warning_with_context: 记录警告 + 上下文信息
- log_info_with_context: 记录信息 + 上下文信息
"""

import logging
import os
import sys
from typing import Any, Dict, Optional

from .config import settings

# 保留日志格式常量，供外部引用
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DETAILED_LOG_FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s"
    " - %(pathname)s:%(lineno)d - %(message)s"
)

# 日志级别映射
LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class SensitiveDataFilter(logging.Filter):
    """
    敏感数据过滤器

    自动过滤日志中的敏感信息，如密码、token等
    """

    SENSITIVE_PATTERNS = [
        ("password", "*****"),
        ("pwd", "*****"),
        ("secret", "*****"),
        ("token", "******"),
        ("api_key", "******"),
        ("access_key", "******"),
        ("authorization", "******"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """
        过滤日志记录中的敏感信息

        Args:
            record: 日志记录对象

        Returns:
            bool: 是否记录该日志
        """
        if hasattr(record, "msg") and isinstance(record.msg, str):
            msg = record.msg
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                if pattern.lower() in msg.lower():
                    record.msg = msg.replace(pattern, replacement)
                    break

        return True


class ProductionSensitiveFilter(logging.Filter):
    """
    生产环境敏感数据过滤器

    在生产环境（DEBUG=False）中：
    - 不记录DEBUG级别的日志
    - 过滤详细的异常堆栈信息
    - 过滤SQL查询
    - 过滤ORM查询参数
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        过滤生产环境日志

        Args:
            record: 日志记录对象

        Returns:
            bool: 是否记录该日志
        """
        # 生产环境不记录DEBUG级别日志
        if not settings.DEBUG and record.levelno == logging.DEBUG:
            return False

        # 过滤SQL查询（避免泄露数据结构）
        if hasattr(record, "msg") and isinstance(record.msg, str):
            msg = record.msg.lower()
            sensitive_keywords = [
                "select",
                "insert",
                "update",
                "delete",
                "password_hash",
                "session.query",
                "execute(",
            ]
            for keyword in sensitive_keywords:
                if keyword in msg:
                    # 生产环境只记录高层级警告，不记录详细查询
                    if not settings.DEBUG and record.levelno < logging.WARNING:
                        return False
                    break

        return True


def setup_logging() -> None:
    """
    配置应用日志

    根据DEBUG模式设置不同的日志级别和格式化
    """
    root_logger = logging.getLogger()

    if settings.DEBUG:
        # 开发环境：详细日志
        log_level = logging.DEBUG
        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )
    else:
        # 生产环境：WARNING及以上级别
        log_level = logging.WARNING
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    root_logger.setLevel(log_level)

    # 清除现有处理器
    root_logger.handlers.clear()

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format))

    # 添加过滤器
    sensitive_filter = SensitiveDataFilter()
    production_filter = ProductionSensitiveFilter()

    console_handler.addFilter(sensitive_filter)
    console_handler.addFilter(production_filter)

    root_logger.addHandler(console_handler)

    # 第三方库日志级别控制（减少噪音）
    logging.getLogger("uvicorn").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.WARNING)
    logging.getLogger("jose").setLevel(logging.WARNING)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取已配置的logger

    Args:
        name: logger名称，通常使用 __name__。
            如果为 None，则使用 "app" 作为默认名称。

    Returns:
        Logger: 配置好的logger实例

    Example:
        ```python
        from app.core.logging_config import get_logger

        logger = get_logger(__name__)

        logger.info("操作成功")
        logger.error("操作失败", exc_info=True, extra={"user_id": 123})
        ```
    """
    if name is None:
        name = "app"
    return logging.getLogger(name)


def _get_log_level() -> int:
    """从环境变量获取日志级别（保留用于向后兼容）"""
    level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    return LOG_LEVEL_MAP.get(level_str, logging.INFO)


def log_error_with_context(
    logger: logging.Logger,
    message: str,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    exc_info: bool = True
) -> None:
    """
    记录错误并包含上下文信息

    Args:
        logger: 日志记录器
        message: 错误消息
        error: 异常对象
        context: 额外的上下文信息（如 user_id, project_id 等）
        exc_info: 是否包含堆栈信息

    Example:
        ```python
        try:
            process_data(data)
        except Exception as e:
            log_error_with_context(
                logger,
                "数据处理失败",
                e,
                context={"data_id": data.id, "user_id": user.id}
            )
        ```
    """
    extra = context or {}
    extra["error_type"] = type(error).__name__
    extra["error_message"] = str(error)

    logger.error(
        message,
        exc_info=exc_info,
        extra=extra
    )


def log_warning_with_context(
    logger: logging.Logger,
    message: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    记录警告并包含上下文信息

    Args:
        logger: 日志记录器
        message: 警告消息
        context: 额外的上下文信息

    Example:
        ```python
        if not item:
            log_warning_with_context(
                logger,
                "资源不存在",
                context={"item_id": item_id, "user_id": user.id}
            )
        ```
    """
    extra = context or {}
    logger.warning(message, extra=extra)


def log_info_with_context(
    logger: logging.Logger,
    message: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    记录信息并包含上下文信息

    Args:
        logger: 日志记录器
        message: 信息消息
        context: 额外的上下文信息
    """
    extra = context or {}
    logger.info(message, extra=extra)


__all__ = [
    "setup_logging",
    "get_logger",
    "log_error_with_context",
    "log_warning_with_context",
    "log_info_with_context",
    "LOG_FORMAT",
    "DETAILED_LOG_FORMAT",
    "LOG_LEVEL_MAP",
]
