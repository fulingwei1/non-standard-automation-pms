# -*- coding: utf-8 -*-
"""
预警相关枚举定义
"""

from enum import Enum


class AlertLevelEnum(str, Enum):
    """预警级别枚举"""
    INFO = "INFO"  # 提示
    WARNING = "WARNING"  # 警告
    CRITICAL = "CRITICAL"  # 严重
    URGENT = "URGENT"  # 紧急


class AlertStatusEnum(str, Enum):
    """预警状态枚举"""
    PENDING = "PENDING"  # 待处理
    ACKNOWLEDGED = "ACKNOWLEDGED"  # 已确认
    PROCESSING = "PROCESSING"  # 处理中
    RESOLVED = "RESOLVED"  # 已解决
    CLOSED = "CLOSED"  # 已关闭
    IGNORED = "IGNORED"  # 已忽略


class AlertRuleTypeEnum(str, Enum):
    """预警规则类型枚举"""
    PROGRESS = "PROGRESS"  # 进度预警
    COST = "COST"  # 成本预警
    QUALITY = "QUALITY"  # 质量预警
    MILESTONE = "MILESTONE"  # 里程碑预警
    MATERIAL = "MATERIAL"  # 物料预警
    RESOURCE = "RESOURCE"  # 资源预警
    CUSTOM = "CUSTOM"  # 自定义预警
