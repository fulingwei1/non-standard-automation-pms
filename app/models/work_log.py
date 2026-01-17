# -*- coding: utf-8 -*-
"""
工作日志模块 ORM 模型
包含：工作日志、工作日志配置、工作日志提及关联
"""

from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin

# ==================== 枚举定义 ====================

class WorkLogStatusEnum(str, Enum):
    """工作日志状态"""
    DRAFT = 'DRAFT'          # 草稿
    SUBMITTED = 'SUBMITTED'  # 已提交


class MentionTypeEnum(str, Enum):
    """提及类型"""
    PROJECT = 'PROJECT'  # 项目
    MACHINE = 'MACHINE'  # 设备
    USER = 'USER'        # 人员


# ==================== 工作日志 ====================

class WorkLog(Base, TimestampMixin):
    """工作日志表"""
    __tablename__ = 'work_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    # 人员信息
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='提交人ID')
    user_name = Column(String(50), comment='提交人姓名（冗余字段）')

    # 工作信息
    work_date = Column(Date, nullable=False, comment='工作日期')
    content = Column(Text, nullable=False, comment='工作内容（限制300字）')

    # 状态
    status = Column(String(20), default='DRAFT', comment='状态：DRAFT/SUBMITTED')

    # 工时记录关联
    timesheet_id = Column(Integer, ForeignKey('timesheet.id'), nullable=True, comment='关联的工时记录ID')

    # 关系
    user = relationship('User', foreign_keys=[user_id])
    mentions = relationship('WorkLogMention', back_populates='work_log', cascade='all, delete-orphan')
    timesheet = relationship('Timesheet', foreign_keys=[timesheet_id])

    __table_args__ = (
        Index('idx_work_log_user', 'user_id'),
        Index('idx_work_log_date', 'work_date'),
        Index('idx_work_log_status', 'status'),
        Index('idx_work_log_user_date', 'user_id', 'work_date'),
        UniqueConstraint('user_id', 'work_date', name='uq_work_log_user_date'),
        {'comment': '工作日志表'}
    )

    def __repr__(self):
        return f"<WorkLog {self.user_name} {self.work_date}>"


# ==================== 工作日志配置 ====================

class WorkLogConfig(Base, TimestampMixin):
    """工作日志配置表"""
    __tablename__ = 'work_log_configs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    # 适用范围
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='用户ID（NULL表示全员）')
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=True, comment='部门ID（可选）')

    # 配置项
    is_required = Column(Boolean, default=True, comment='是否必须提交')
    is_active = Column(Boolean, default=True, comment='是否启用')
    remind_time = Column(String(10), default='18:00', comment='提醒时间（HH:mm格式）')

    # 关系
    user = relationship('User', foreign_keys=[user_id])
    department = relationship('Department', foreign_keys=[department_id])

    __table_args__ = (
        Index('idx_work_log_config_user', 'user_id'),
        Index('idx_work_log_config_dept', 'department_id'),
        Index('idx_work_log_config_active', 'is_active'),
        {'comment': '工作日志配置表'}
    )

    def __repr__(self):
        scope = f"用户{self.user_id}" if self.user_id else "全员"
        return f"<WorkLogConfig {scope}>"


# ==================== 工作日志提及关联 ====================

class WorkLogMention(Base, TimestampMixin):
    """工作日志提及关联表"""
    __tablename__ = 'work_log_mentions'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    # 关联工作日志
    work_log_id = Column(Integer, ForeignKey('work_logs.id'), nullable=False, comment='工作日志ID')

    # 提及信息
    mention_type = Column(String(20), nullable=False, comment='提及类型：PROJECT/MACHINE/USER')
    mention_id = Column(Integer, nullable=False, comment='被提及对象ID')
    mention_name = Column(String(200), comment='被提及对象名称（冗余字段）')

    # 关系
    work_log = relationship('WorkLog', back_populates='mentions')

    __table_args__ = (
        Index('idx_work_log_mention_log', 'work_log_id'),
        Index('idx_work_log_mention_type', 'mention_type'),
        Index('idx_work_log_mention_id', 'mention_id'),
        Index('idx_work_log_mention_type_id', 'mention_type', 'mention_id'),
        {'comment': '工作日志提及关联表'}
    )

    def __repr__(self):
        return f"<WorkLogMention {self.mention_type}:{self.mention_id}>"
