# -*- coding: utf-8 -*-
"""
文化墙数据模型
"""

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)

from app.models.base import Base, TimestampMixin

# ==================== 文化墙内容 ====================

class CultureWallContent(Base, TimestampMixin):
    """文化墙内容表"""
    __tablename__ = 'culture_wall_content'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    # 内容类型
    content_type = Column(String(30), nullable=False, comment='内容类型:STRATEGY/CULTURE/IMPORTANT/NOTICE/REWARD')
    # STRATEGY: 战略规划
    # CULTURE: 企业文化
    # IMPORTANT: 重要事项
    # NOTICE: 通知公告
    # REWARD: 奖励通报

    # 内容信息
    title = Column(String(200), nullable=False, comment='标题')
    content = Column(Text, comment='内容')
    summary = Column(String(500), comment='摘要')

    # 媒体资源
    images = Column(JSON, comment='图片列表(JSON)')
    videos = Column(JSON, comment='视频列表(JSON)')
    attachments = Column(JSON, comment='附件列表(JSON)')

    # 显示设置
    is_published = Column(Boolean, default=False, comment='是否发布')
    publish_date = Column(Date, comment='发布日期')
    expire_date = Column(Date, comment='过期日期')
    priority = Column(Integer, default=0, comment='优先级(数字越大越优先)')
    display_order = Column(Integer, default=0, comment='显示顺序')

    # 阅读统计
    view_count = Column(Integer, default=0, comment='浏览次数')

    # 关联信息
    related_project_id = Column(Integer, ForeignKey('projects.id'), comment='关联项目ID')
    related_department_id = Column(Integer, ForeignKey('departments.id'), comment='关联部门ID')

    # 发布人
    published_by = Column(Integer, ForeignKey('users.id'), comment='发布人ID')
    published_by_name = Column(String(50), comment='发布人姓名')

    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')

    __table_args__ = (
        Index('idx_culture_wall_type', 'content_type'),
        Index('idx_culture_wall_published', 'is_published', 'publish_date'),
        Index('idx_culture_wall_expire', 'expire_date'),
        {'comment': '文化墙内容表'}
    )


# ==================== 个人目标 ====================

class PersonalGoal(Base, TimestampMixin):
    """个人目标表"""
    __tablename__ = 'personal_goal'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')

    # 目标信息
    goal_type = Column(String(20), nullable=False, comment='目标类型:MONTHLY/QUARTERLY/YEARLY')
    period = Column(String(20), nullable=False, comment='目标周期(如:2025-01/2025-Q1/2025)')
    title = Column(String(200), nullable=False, comment='目标标题')
    description = Column(Text, comment='目标描述')

    # 目标指标
    target_value = Column(String(50), comment='目标值')
    current_value = Column(String(50), comment='当前值')
    unit = Column(String(20), comment='单位')

    # 进度
    progress = Column(Integer, default=0, comment='进度百分比(0-100)')

    # 状态
    status = Column(String(20), default='IN_PROGRESS', comment='状态:IN_PROGRESS/COMPLETED/OVERDUE/CANCELLED')

    # 时间
    start_date = Column(Date, comment='开始日期')
    end_date = Column(Date, comment='结束日期')
    completed_date = Column(Date, comment='完成日期')

    # 备注
    notes = Column(Text, comment='备注')

    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')

    __table_args__ = (
        Index('idx_personal_goal_user', 'user_id'),
        Index('idx_personal_goal_type_period', 'goal_type', 'period'),
        Index('idx_personal_goal_status', 'status'),
        {'comment': '个人目标表'}
    )


# ==================== 文化墙阅读记录 ====================

class CultureWallReadRecord(Base, TimestampMixin):
    """文化墙阅读记录表"""
    __tablename__ = 'culture_wall_read_record'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    content_id = Column(Integer, ForeignKey('culture_wall_content.id', ondelete='CASCADE'), nullable=False, comment='内容ID')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')

    # 阅读时间
    read_at = Column(DateTime, nullable=False, comment='阅读时间')

    # 阅读时长(秒)
    read_duration = Column(Integer, default=0, comment='阅读时长(秒)')

    __table_args__ = (
        Index('idx_read_record_content', 'content_id'),
        Index('idx_read_record_user', 'user_id'),
        Index('idx_read_record_content_user', 'content_id', 'user_id', unique=True),
        {'comment': '文化墙阅读记录表'}
    )
