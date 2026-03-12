# -*- coding: utf-8 -*-
"""
日志工具函数

提供统一的日志记录格式和便捷方法，确保日志信息的一致性和可追踪性。
"""

import logging
from typing import Any, Dict, Optional


def get_module_logger(module_name: str) -> logging.Logger:
    """
    获取模块 logger。

    提供统一的 logger 获取方式，便于后续统一配置。

    Args:
        module_name: 模块名称，通常使用 __name__

    Returns:
        配置好的 Logger 实例

    Examples:
        >>> logger = get_module_logger(__name__)
        >>> logger.info("操作完成")
    """
    return logging.getLogger(module_name)


def log_entity_operation(
    logger: logging.Logger,
    operation: str,
    entity_type: str,
    entity_id: Any,
    operator: Optional[str] = None,
    **details: Any
) -> None:
    """
    记录实体操作日志。

    提供统一的实体操作日志格式，便于日志聚合和分析。

    Args:
        logger: Logger 实例
        operation: 操作类型（如 create, update, delete）
        entity_type: 实体类型（如 contract, quote, opportunity）
        entity_id: 实体 ID
        operator: 操作人（可选）
        **details: 其他详细信息

    Examples:
        >>> log_entity_operation(logger, "create", "contract", 123, operator="张三")
        >>> log_entity_operation(logger, "update", "quote", 456, fields=["price", "discount"])
    """
    msg_parts = [f"{operation} {entity_type}:{entity_id}"]

    if operator:
        msg_parts.append(f"by {operator}")

    if details:
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        msg_parts.append(f"[{detail_str}]")

    logger.info(" ".join(msg_parts))


def log_status_change(
    logger: logging.Logger,
    entity_type: str,
    entity_id: Any,
    old_status: str,
    new_status: str,
    operator: Optional[str] = None,
    entity_code: Optional[str] = None
) -> None:
    """
    记录状态变更日志。

    Args:
        logger: Logger 实例
        entity_type: 实体类型
        entity_id: 实体 ID
        old_status: 原状态
        new_status: 新状态
        operator: 操作人（可选）
        entity_code: 实体编码（可选）

    Examples:
        >>> log_status_change(logger, "contract", 123, "draft", "approved", operator="李四")
    """
    identifier = f"{entity_code or entity_id}"
    msg = f"{entity_type} {identifier}: {old_status} → {new_status}"

    if operator:
        msg += f" by {operator}"

    logger.info(msg)


def log_validation_error(
    logger: logging.Logger,
    entity_type: str,
    validation_type: str,
    error_msg: str,
    entity_id: Optional[Any] = None
) -> None:
    """
    记录验证错误日志。

    Args:
        logger: Logger 实例
        entity_type: 实体类型
        validation_type: 验证类型（如 status, permission, data）
        error_msg: 错误消息
        entity_id: 实体 ID（可选）

    Examples:
        >>> log_validation_error(logger, "contract", "status", "只能删除草稿状态的合同", entity_id=123)
    """
    identifier = f":{entity_id}" if entity_id else ""
    logger.warning(f"[{validation_type}] {entity_type}{identifier}: {error_msg}")


def log_batch_operation(
    logger: logging.Logger,
    operation: str,
    entity_type: str,
    count: int,
    success_count: Optional[int] = None,
    **details: Any
) -> None:
    """
    记录批量操作日志。

    Args:
        logger: Logger 实例
        operation: 操作类型
        entity_type: 实体类型
        count: 总数量
        success_count: 成功数量（可选）
        **details: 其他详细信息
    """
    if success_count is not None:
        msg = f"批量 {operation} {entity_type}: {success_count}/{count} 成功"
    else:
        msg = f"批量 {operation} {entity_type}: {count} 条"

    if details:
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        msg += f" [{detail_str}]"

    logger.info(msg)


def log_service_error(
    logger: logging.Logger,
    service_name: str,
    method_name: str,
    error: Exception,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    记录服务错误日志。

    Args:
        logger: Logger 实例
        service_name: 服务名称
        method_name: 方法名称
        error: 异常对象
        context: 上下文信息（可选）
    """
    msg = f"{service_name}.{method_name} 失败: {error}"

    if context:
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        msg += f" [context: {context_str}]"

    logger.error(msg, exc_info=True)


def log_performance(
    logger: logging.Logger,
    operation: str,
    duration_ms: float,
    entity_count: Optional[int] = None,
    **details: Any
) -> None:
    """
    记录性能日志。

    Args:
        logger: Logger 实例
        operation: 操作名称
        duration_ms: 耗时（毫秒）
        entity_count: 处理的实体数量（可选）
        **details: 其他详细信息
    """
    msg_parts = [f"{operation} 耗时 {duration_ms:.2f}ms"]

    if entity_count:
        avg_time = duration_ms / entity_count if entity_count > 0 else 0
        msg_parts.append(f"({entity_count} 条, 平均 {avg_time:.2f}ms/条)")

    if details:
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        msg_parts.append(f"[{detail_str}]")

    logger.debug(" ".join(msg_parts))
