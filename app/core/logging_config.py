# -*- coding: utf-8 -*-
"""
日志配置模块

根据DEBUG模式配置不同的日志级别，避免生产环境泄露敏感信息。
"""

import logging
import sys

from .config import settings


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
                    record.msg = msg.replace(pattern, replacement, flags=0)
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


def get_logger(name: str) -> logging.Logger:
    """
    获取已配置的logger

    Args:
        name: logger名称

    Returns:
        Logger: 配置好的logger实例
    """
    return logging.getLogger(name)


__all__ = ["setup_logging", "get_logger"]
