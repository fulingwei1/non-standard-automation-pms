# -*- coding: utf-8 -*-
"""
服务模型 - 枚举定义
"""
from enum import Enum
from typing import Optional, Union


class ServiceTicketStatusEnum(str, Enum):
    """服务工单状态"""

    PENDING = "PENDING"  # 待分配
    IN_PROGRESS = "IN_PROGRESS"  # 处理中
    RESOLVED = "RESOLVED"  # 待验证
    CLOSED = "CLOSED"  # 已关闭


class ServiceTicketUrgencyEnum(str, Enum):
    """服务工单紧急程度"""

    LOW = "LOW"  # 低
    MEDIUM = "MEDIUM"  # 中
    HIGH = "HIGH"  # 高
    URGENT = "URGENT"  # 紧急


class ServiceTicketProblemTypeEnum(str, Enum):
    """问题类型"""

    SOFTWARE = "SOFTWARE"  # 软件问题
    MECHANICAL = "MECHANICAL"  # 机械问题
    ELECTRICAL = "ELECTRICAL"  # 电气问题
    OPERATION = "OPERATION"  # 操作问题
    OTHER = "OTHER"  # 其他


class ServiceRecordTypeEnum(str, Enum):
    """服务记录类型"""

    INSTALLATION = "INSTALLATION"  # 安装调试
    TRAINING = "TRAINING"  # 操作培训
    MAINTENANCE = "MAINTENANCE"  # 定期维护
    REPAIR = "REPAIR"  # 故障维修
    OTHER = "OTHER"  # 其他


class ServiceRecordStatusEnum(str, Enum):
    """服务记录状态"""

    SCHEDULED = "SCHEDULED"  # 已排期
    IN_PROGRESS = "IN_PROGRESS"  # 进行中
    COMPLETED = "COMPLETED"  # 已完成
    CANCELLED = "CANCELLED"  # 已取消


class CommunicationTypeEnum(str, Enum):
    """沟通方式"""

    PHONE = "PHONE"  # 电话
    EMAIL = "EMAIL"  # 邮件
    ON_SITE = "ON_SITE"  # 现场
    WECHAT = "WECHAT"  # 微信
    MEETING = "MEETING"  # 会议
    OTHER = "OTHER"  # 其他


class SurveyStatusEnum(str, Enum):
    """满意度调查状态"""

    DRAFT = "DRAFT"  # 待发送
    SENT = "SENT"  # 已发送
    PENDING = "PENDING"  # 待回复
    COMPLETED = "COMPLETED"  # 已完成
    EXPIRED = "EXPIRED"  # 已过期


class SurveyTypeEnum(str, Enum):
    """调查类型"""

    PROJECT = "PROJECT"  # 项目满意度
    SERVICE = "SERVICE"  # 服务满意度
    PRODUCT = "PRODUCT"  # 产品满意度


class KnowledgeBaseStatusEnum(str, Enum):
    """知识库文章状态"""

    DRAFT = "DRAFT"  # 草稿
    PUBLISHED = "PUBLISHED"  # 已发布
    ARCHIVED = "ARCHIVED"  # 已归档


def _normalize_enum_value(
    value: Optional[Union[str, Enum]], aliases: dict[str, str]
) -> Optional[Union[str, Enum]]:
    if value is None or isinstance(value, Enum):
        return value
    raw_value = str(value)
    normalized = aliases.get(
        raw_value,
        aliases.get(raw_value.upper(), aliases.get(raw_value.lower(), raw_value)),
    )
    return normalized


def normalize_service_ticket_status(value: Optional[Union[str, Enum]]) -> Optional[Union[str, Enum]]:
    return _normalize_enum_value(
        value,
        {
            "pending": ServiceTicketStatusEnum.PENDING.value,
            "draft": ServiceTicketStatusEnum.PENDING.value,
            "assigned": ServiceTicketStatusEnum.IN_PROGRESS.value,
            "in_progress": ServiceTicketStatusEnum.IN_PROGRESS.value,
            "active": ServiceTicketStatusEnum.IN_PROGRESS.value,
            "resolved": ServiceTicketStatusEnum.RESOLVED.value,
            "approved": ServiceTicketStatusEnum.RESOLVED.value,
            "closed": ServiceTicketStatusEnum.CLOSED.value,
            "completed": ServiceTicketStatusEnum.CLOSED.value,
        },
    )


def normalize_service_record_status(value: Optional[Union[str, Enum]]) -> Optional[Union[str, Enum]]:
    return _normalize_enum_value(
        value,
        {
            "scheduled": ServiceRecordStatusEnum.SCHEDULED.value,
            "draft": ServiceRecordStatusEnum.SCHEDULED.value,
            "pending": ServiceRecordStatusEnum.SCHEDULED.value,
            "in_progress": ServiceRecordStatusEnum.IN_PROGRESS.value,
            "active": ServiceRecordStatusEnum.IN_PROGRESS.value,
            "approved": ServiceRecordStatusEnum.COMPLETED.value,
            "completed": ServiceRecordStatusEnum.COMPLETED.value,
            "cancelled": ServiceRecordStatusEnum.CANCELLED.value,
            "canceled": ServiceRecordStatusEnum.CANCELLED.value,
        },
    )


def normalize_survey_status(value: Optional[Union[str, Enum]]) -> Optional[Union[str, Enum]]:
    return _normalize_enum_value(
        value,
        {
            "draft": SurveyStatusEnum.DRAFT.value,
            "sent": SurveyStatusEnum.SENT.value,
            "pending": SurveyStatusEnum.PENDING.value,
            "active": SurveyStatusEnum.PENDING.value,
            "approved": SurveyStatusEnum.SENT.value,
            "completed": SurveyStatusEnum.COMPLETED.value,
            "expired": SurveyStatusEnum.EXPIRED.value,
        },
    )


def normalize_knowledge_base_status(value: Optional[Union[str, Enum]]) -> Optional[Union[str, Enum]]:
    return _normalize_enum_value(
        value,
        {
            "draft": KnowledgeBaseStatusEnum.DRAFT.value,
            "草稿": KnowledgeBaseStatusEnum.DRAFT.value,
            "published": KnowledgeBaseStatusEnum.PUBLISHED.value,
            "已发布": KnowledgeBaseStatusEnum.PUBLISHED.value,
            "archived": KnowledgeBaseStatusEnum.ARCHIVED.value,
            "已归档": KnowledgeBaseStatusEnum.ARCHIVED.value,
        },
    )
