# -*- coding: utf-8 -*-
"""
工程师绩效评价模块 - 机械工程师专属模型
"""
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class DesignReview(Base, TimestampMixin):
    """设计评审记录（机械工程师）"""
    __tablename__ = 'design_review'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID')
    designer_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='设计者ID')

    # 设计信息
    design_name = Column(String(200), nullable=False, comment='设计名称')
    design_type = Column(String(50), comment='设计类型')
    design_code = Column(String(50), comment='设计编号')
    version = Column(String(20), comment='版本号')

    # 评审信息
    review_date = Column(Date, comment='评审日期')
    reviewer_id = Column(Integer, ForeignKey('users.id'), comment='评审人ID')
    result = Column(String(20), comment='评审结果')
    is_first_pass = Column(Boolean, comment='是否一次通过')
    issues_found = Column(Integer, default=0, comment='发现问题数')
    review_comments = Column(Text, comment='评审意见')

    # 附件
    attachments = Column(JSON, comment='附件')

    # 关系
    designer = relationship('User', foreign_keys=[designer_id])
    reviewer = relationship('User', foreign_keys=[reviewer_id])
    project = relationship('Project', foreign_keys=[project_id])

    __table_args__ = (
        Index('idx_design_review_project', 'project_id'),
        Index('idx_design_review_designer', 'designer_id'),
        Index('idx_design_review_date', 'review_date'),
        {'comment': '设计评审记录表'}
    )


class MechanicalDebugIssue(Base, TimestampMixin):
    """机械调试问题记录"""
    __tablename__ = 'mechanical_debug_issue'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID')
    responsible_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='责任人ID')
    reporter_id = Column(Integer, ForeignKey('users.id'), comment='报告人ID')

    # 问题信息
    issue_code = Column(String(50), comment='问题编号')
    issue_description = Column(Text, nullable=False, comment='问题描述')
    severity = Column(String(20), comment='严重程度')
    root_cause = Column(String(50), comment='根本原因')
    affected_part = Column(String(200), comment='受影响零件')

    # 处理状态
    status = Column(String(20), default='open', comment='状态')
    found_date = Column(Date, comment='发现日期')
    resolved_date = Column(Date, comment='解决日期')
    resolution = Column(Text, comment='解决方案')

    # 影响评估
    cost_impact = Column(Numeric(12, 2), comment='成本影响')
    time_impact_hours = Column(Numeric(6, 2), comment='时间影响(小时)')

    # 关系
    responsible = relationship('User', foreign_keys=[responsible_id])
    reporter = relationship('User', foreign_keys=[reporter_id])
    project = relationship('Project', foreign_keys=[project_id])

    __table_args__ = (
        Index('idx_mech_debug_project', 'project_id'),
        Index('idx_mech_debug_responsible', 'responsible_id'),
        Index('idx_mech_debug_severity', 'severity'),
        {'comment': '机械调试问题记录表'}
    )


class DesignReuseRecord(Base, TimestampMixin):
    """设计复用记录"""
    __tablename__ = 'design_reuse_record'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='目标项目ID')
    designer_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='设计者ID')

    # 复用信息
    source_design_id = Column(Integer, comment='源设计ID')
    source_design_name = Column(String(200), comment='源设计名称')
    source_project_id = Column(Integer, ForeignKey('projects.id'), comment='源项目ID')

    # 复用程度
    reuse_type = Column(String(30), comment='复用类型')
    reuse_percentage = Column(Numeric(5, 2), comment='复用比例')

    # 节省评估
    saved_hours = Column(Numeric(6, 2), comment='节省工时')

    # 关系
    designer = relationship('User', foreign_keys=[designer_id])
    project = relationship('Project', foreign_keys=[project_id])

    __table_args__ = (
        Index('idx_design_reuse_project', 'project_id'),
        Index('idx_design_reuse_designer', 'designer_id'),
        {'comment': '设计复用记录表'}
    )
