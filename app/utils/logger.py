# -*- coding: utf-8 -*-
"""
统一日志工具

提供统一的日志记录接口，确保所有错误处理都遵循相同的日志格式和级别。
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# 日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DETAILED_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s"

# 日志级别映射
LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称，通常使用 __name__

    Returns:
        logging.Logger: 配置好的日志记录器

    Example:
        ```python
        from app.utils.logger import get_logger

        logger = get_logger(__name__)

        logger.info("操作成功")
        logger.error("操作失败", exc_info=True, extra={"user_id": 123})
        ```
    """
    if name is None:
        name = __name__

    logger = logging.getLogger(name)

    # 如果已经配置过，直接返回
    if logger.handlers:
        return logger

    # 配置日志级别
    log_level = _get_log_level()
    logger.setLevel(log_level)

    # 避免重复添加 handler
    if not logger.handlers:
        # 控制台输出
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)

        # 根据环境选择格式
        if log_level == logging.DEBUG:
            formatter = logging.Formatter(DETAILED_LOG_FORMAT)
        else:
            formatter = logging.Formatter(LOG_FORMAT)

        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # 生产环境可以添加文件输出
        # file_handler = logging.FileHandler('app.log')
        # file_handler.setFormatter(formatter)
        # logger.addHandler(file_handler)

    return logger


def _get_log_level() -> int:
    """从环境变量获取日志级别"""
    import os
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
