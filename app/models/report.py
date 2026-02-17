# -*- coding: utf-8 -*-
"""
工时报表自动生成系统 - 数据模型
包含：报表模板、报表归档、收件人配置
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


# ==================== 枚举定义 ====================

class ReportTypeEnum(str, Enum):
    """报表类型"""
    USER_MONTHLY = 'USER_MONTHLY'           # 人员月度工时报表
    DEPT_MONTHLY = 'DEPT_MONTHLY'           # 部门月度工时报表
    PROJECT_MONTHLY = 'PROJECT_MONTHLY'     # 项目月度工时报表
    COMPANY_MONTHLY = 'COMPANY_MONTHLY'     # 公司整体工时报表
    OVERTIME_MONTHLY = 'OVERTIME_MONTHLY'   # 加班统计报表


class OutputFormatEnum(str, Enum):
    """输出格式"""
    EXCEL = 'EXCEL'  # Excel格式
    PDF = 'PDF'      # PDF格式
    CSV = 'CSV'      # CSV格式


class FrequencyEnum(str, Enum):
    """生成频率"""
    MONTHLY = 'MONTHLY'      # 月度
    QUARTERLY = 'QUARTERLY'  # 季度
    YEARLY = 'YEARLY'        # 年度


class GeneratedByEnum(str, Enum):
    """生成方式"""
    SYSTEM = 'SYSTEM'  # 系统自动生成
    MANUAL = 'MANUAL'  # 手动生成


class ArchiveStatusEnum(str, Enum):
    """归档状态"""
    SUCCESS = 'SUCCESS'  # 成功
    FAILED = 'FAILED'    # 失败


class RecipientTypeEnum(str, Enum):
    """收件人类型"""
    USER = 'USER'      # 用户
    ROLE = 'ROLE'      # 角色
    DEPT = 'DEPT'      # 部门
    EMAIL = 'EMAIL'    # 外部邮箱


class DeliveryMethodEnum(str, Enum):
    """分发方式"""
    EMAIL = 'EMAIL'        # 邮件
    WECHAT = 'WECHAT'      # 企业微信
    DOWNLOAD = 'DOWNLOAD'  # 下载链接


# ==================== 报表模板表 ====================

class TimesheetReportTemplate(Base, TimestampMixin):
    """报表模板"""
    __tablename__ = 'report_template'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    # 基本信息
    name = Column(String(100), nullable=False, comment='模板名称')
    report_type = Column(String(50), nullable=False, comment='报表类型')
    description = Column(Text, comment='描述')

    # 配置信息
    config = Column(JSON, comment='模板配置（字段、筛选条件等）')
    """
    示例配置:
    {
        "fields": ["user_name", "hours", "projects"],  # 包含字段
        "filters": {                                    # 筛选条件
            "department_ids": [1, 2, 3],
            "role_ids": [10, 20]
        },
        "chart_types": ["bar", "pie"],                 # 图表类型
        "conditional_format": true                     # 条件格式
    }
    """

    # 输出设置
    output_format = Column(String(20), nullable=False, default='EXCEL', comment='输出格式')
    frequency = Column(String(20), nullable=False, default='MONTHLY', comment='生成频率')

    # 状态
    enabled = Column(Boolean, default=True, comment='是否启用')

    # 创建信息
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    # 关系
    archives = relationship('ReportArchive', back_populates='template', cascade='all, delete-orphan')
    recipients = relationship('ReportRecipient', back_populates='template', cascade='all, delete-orphan')

    __table_args__ = (
        Index('idx_ts_report_type', 'report_type'),
        Index('idx_enabled', 'enabled'),
        {'comment': '报表模板表', 'extend_existing': True}
    )


# ==================== 报表归档表 ====================

class ReportArchive(Base, TimestampMixin):
    """报表归档"""
    __tablename__ = 'report_archive'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    # 关联模板
    template_id = Column(Integer, ForeignKey('report_template.id'), nullable=False, comment='模板ID')
    report_type = Column(String(50), nullable=False, comment='报表类型')

    # 周期信息
    period = Column(String(20), nullable=False, comment='报表周期（如：2026-01）')

    # 文件信息
    file_path = Column(String(500), nullable=False, comment='文件路径')
    file_size = Column(Integer, comment='文件大小（字节）')
    row_count = Column(Integer, comment='数据行数')

    # 生成信息
    generated_at = Column(DateTime, default=datetime.utcnow, comment='生成时间')
    generated_by = Column(String(50), nullable=False, comment='生成方式（SYSTEM/用户ID）')

    # 状态
    status = Column(String(20), nullable=False, default='SUCCESS', comment='状态')
    error_message = Column(Text, comment='失败原因')

    # 统计
    download_count = Column(Integer, default=0, comment='下载次数')

    # 关系
    template = relationship('TimesheetReportTemplate', back_populates='archives')

    __table_args__ = (
        Index('idx_template_period', 'template_id', 'period'),
        Index('idx_archive_report_type', 'report_type'),
        Index('idx_report_period', 'period'),
        Index('idx_report_status', 'status'),
        {'comment': '报表归档表', 'extend_existing': True}
    )


# ==================== 报表收件人表 ====================

class ReportRecipient(Base, TimestampMixin):
    """报表收件人"""
    __tablename__ = 'report_recipient'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    # 关联模板
    template_id = Column(Integer, ForeignKey('report_template.id'), nullable=False, comment='模板ID')

    # 收件人信息
    recipient_type = Column(String(20), nullable=False, comment='收件人类型')
    recipient_id = Column(Integer, comment='用户/角色/部门ID')
    recipient_email = Column(String(200), comment='外部邮箱')

    # 分发方式
    delivery_method = Column(String(20), nullable=False, default='EMAIL', comment='分发方式')

    # 状态
    enabled = Column(Boolean, default=True, comment='是否启用')

    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    # 关系
    template = relationship('TimesheetReportTemplate', back_populates='recipients')

    __table_args__ = (
        Index('idx_report_template_id', 'template_id'),
        Index('idx_recipient_type', 'recipient_type'),
        {'comment': '报表收件人表', 'extend_existing': True}
    )
