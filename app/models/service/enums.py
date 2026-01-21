# -*- coding: utf-8 -*-
"""
服务模型 - 枚举定义
"""
from enum import Enum


class ServiceTicketStatusEnum(str, Enum):
    """服务工单状态"""
    PENDING = 'PENDING'          # 待分配
    IN_PROGRESS = 'IN_PROGRESS'  # 处理中
    RESOLVED = 'RESOLVED'        # 待验证
    CLOSED = 'CLOSED'            # 已关闭


class ServiceTicketUrgencyEnum(str, Enum):
    """服务工单紧急程度"""
    LOW = 'LOW'                  # 低
    MEDIUM = 'MEDIUM'            # 中
    HIGH = 'HIGH'                # 高
    URGENT = 'URGENT'            # 紧急


class ServiceTicketProblemTypeEnum(str, Enum):
    """问题类型"""
    SOFTWARE = 'SOFTWARE'        # 软件问题
    MECHANICAL = 'MECHANICAL'    # 机械问题
    ELECTRICAL = 'ELECTRICAL'    # 电气问题
    OPERATION = 'OPERATION'      # 操作问题
    OTHER = 'OTHER'              # 其他


class ServiceRecordTypeEnum(str, Enum):
    """服务记录类型"""
    INSTALLATION = 'INSTALLATION'  # 安装调试
    TRAINING = 'TRAINING'          # 操作培训
    MAINTENANCE = 'MAINTENANCE'     # 定期维护
    REPAIR = 'REPAIR'               # 故障维修
    OTHER = 'OTHER'                 # 其他


class ServiceRecordStatusEnum(str, Enum):
    """服务记录状态"""
    SCHEDULED = 'SCHEDULED'      # 已排期
    IN_PROGRESS = 'IN_PROGRESS'  # 进行中
    COMPLETED = 'COMPLETED'      # 已完成
    CANCELLED = 'CANCELLED'      # 已取消


class CommunicationTypeEnum(str, Enum):
    """沟通方式"""
    PHONE = 'PHONE'              # 电话
    EMAIL = 'EMAIL'              # 邮件
    ON_SITE = 'ON_SITE'          # 现场
    WECHAT = 'WECHAT'            # 微信
    MEETING = 'MEETING'          # 会议
    OTHER = 'OTHER'              # 其他


class SurveyStatusEnum(str, Enum):
    """满意度调查状态"""
    DRAFT = 'DRAFT'              # 待发送
    SENT = 'SENT'                # 已发送
    PENDING = 'PENDING'          # 待回复
    COMPLETED = 'COMPLETED'      # 已完成
    EXPIRED = 'EXPIRED'          # 已过期


class SurveyTypeEnum(str, Enum):
    """调查类型"""
    PROJECT = 'PROJECT'          # 项目满意度
    SERVICE = 'SERVICE'          # 服务满意度
    PRODUCT = 'PRODUCT'          # 产品满意度
