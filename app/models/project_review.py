# -*- coding: utf-8 -*-
"""
项目复盘模块 ORM 模型
包含：项目复盘报告、经验教训、最佳实践
适用场景：项目结项后的复盘总结、经验沉淀、知识复用
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class ProjectReview(Base, TimestampMixin):
    """项目复盘报告表"""
    __tablename__ = 'project_reviews'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    review_no = Column(String(50), unique=True, nullable=False, comment='复盘编号')

    # 关联项目
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    project_code = Column(String(50), nullable=False, comment='项目编号')

    # 复盘信息
    review_date = Column(Date, nullable=False, comment='复盘日期')
    review_type = Column(String(20), default='POST_MORTEM', comment='复盘类型：POST_MORTEM/MID_TERM/QUARTERLY（结项复盘/中期复盘/季度复盘）')

    # 项目周期对比
    plan_duration = Column(Integer, comment='计划工期(天)')
    actual_duration = Column(Integer, comment='实际工期(天)')
    schedule_variance = Column(Integer, comment='进度偏差(天)')

    # 成本对比
    budget_amount = Column(Numeric(12, 2), comment='预算金额')
    actual_cost = Column(Numeric(12, 2), comment='实际成本')
    cost_variance = Column(Numeric(12, 2), comment='成本偏差')

    # 质量指标
    quality_issues = Column(Integer, default=0, comment='质量问题数')
    change_count = Column(Integer, default=0, comment='变更次数')
    customer_satisfaction = Column(Integer, comment='客户满意度1-5')

    # 复盘内容
    success_factors = Column(Text, comment='成功因素')
    problems = Column(Text, comment='问题与教训')
    improvements = Column(Text, comment='改进建议')
    best_practices = Column(Text, comment='最佳实践')
    conclusion = Column(Text, comment='复盘结论')

    # 参与人
    reviewer_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='复盘负责人ID')
    reviewer_name = Column(String(50), nullable=False, comment='复盘负责人')
    participants = Column(JSON, comment='参与人ID列表')
    participant_names = Column(String(500), comment='参与人姓名（逗号分隔）')

    # 附件
    attachment_ids = Column(JSON, comment='附件ID列表')

    # 状态
    status = Column(String(20), default='DRAFT', comment='状态：DRAFT/PUBLISHED/ARCHIVED')

    # 关系
    project = relationship('Project', backref='reviews')
    reviewer = relationship('User', foreign_keys=[reviewer_id])
    lessons = relationship('ProjectLesson', back_populates='review', cascade='all, delete-orphan')
    best_practices_list = relationship('ProjectBestPractice', back_populates='review', cascade='all, delete-orphan')

    __table_args__ = (
        Index('idx_project_review_project', 'project_id'),
        Index('idx_project_review_date', 'review_date'),
        Index('idx_project_review_status', 'status'),
        {'comment': '项目复盘报告表'}
    )

    def __repr__(self):
        return f'<ProjectReview {self.review_no}>'


class ProjectLesson(Base, TimestampMixin):
    """项目经验教训表"""
    __tablename__ = 'project_lessons'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    review_id = Column(Integer, ForeignKey('project_reviews.id'), nullable=False, comment='复盘报告ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')

    # 经验教训信息
    lesson_type = Column(String(20), nullable=False, comment='类型：SUCCESS/FAILURE（成功经验/失败教训）')
    title = Column(String(200), nullable=False, comment='标题')
    description = Column(Text, nullable=False, comment='问题/经验描述')

    # 根因分析
    root_cause = Column(Text, comment='根本原因')
    impact = Column(Text, comment='影响范围')

    # 改进措施
    improvement_action = Column(Text, comment='改进措施')
    responsible_person = Column(String(50), comment='责任人')
    due_date = Column(Date, comment='完成日期')

    # 分类标签
    category = Column(String(50), comment='分类：进度/成本/质量/沟通/技术/管理')
    tags = Column(JSON, comment='标签列表')

    # 优先级
    priority = Column(String(10), default='MEDIUM', comment='优先级：LOW/MEDIUM/HIGH')

    # 状态
    status = Column(String(20), default='OPEN', comment='状态：OPEN/IN_PROGRESS/RESOLVED/CLOSED')
    resolved_date = Column(Date, comment='解决日期')

    # 关系
    review = relationship('ProjectReview', back_populates='lessons')
    project = relationship('Project')

    __table_args__ = (
        Index('idx_project_lesson_review', 'review_id'),
        Index('idx_project_lesson_project', 'project_id'),
        Index('idx_project_lesson_type', 'lesson_type'),
        Index('idx_project_lesson_status', 'status'),
        {'comment': '项目经验教训表'}
    )

    def __repr__(self):
        return f'<ProjectLesson {self.title}>'


class ProjectBestPractice(Base, TimestampMixin):
    """项目最佳实践表"""
    __tablename__ = 'project_best_practices'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    review_id = Column(Integer, ForeignKey('project_reviews.id'), nullable=False, comment='复盘报告ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')

    # 最佳实践信息
    title = Column(String(200), nullable=False, comment='标题')
    description = Column(Text, nullable=False, comment='实践描述')
    context = Column(Text, comment='适用场景')
    implementation = Column(Text, comment='实施方法')
    benefits = Column(Text, comment='带来的收益')

    # 分类标签
    category = Column(String(50), comment='分类：流程/工具/技术/管理/沟通')
    tags = Column(JSON, comment='标签列表')

    # 可复用性
    is_reusable = Column(Boolean, default=True, comment='是否可复用')
    applicable_project_types = Column(JSON, comment='适用项目类型列表')
    applicable_stages = Column(JSON, comment='适用阶段列表（S1-S9）')

    # 验证信息
    validation_status = Column(String(20), default='PENDING', comment='验证状态：PENDING/VALIDATED/REJECTED')
    validation_date = Column(Date, comment='验证日期')
    validated_by = Column(Integer, ForeignKey('users.id'), comment='验证人ID')

    # 复用统计
    reuse_count = Column(Integer, default=0, comment='复用次数')
    last_reused_at = Column(DateTime, comment='最后复用时间')

    # 状态
    status = Column(String(20), default='ACTIVE', comment='状态：ACTIVE/ARCHIVED')

    # 关系
    review = relationship('ProjectReview', back_populates='best_practices_list')
    project = relationship('Project')
    validator = relationship('User', foreign_keys=[validated_by])

    __table_args__ = (
        Index('idx_project_bp_review', 'review_id'),
        Index('idx_project_bp_project', 'project_id'),
        Index('idx_project_bp_category', 'category'),
        Index('idx_project_bp_reusable', 'is_reusable'),
        Index('idx_project_bp_status', 'status'),
        {'comment': '项目最佳实践表'}
    )

    def __repr__(self):
        return f'<ProjectBestPractice {self.title}>'












