# -*- coding: utf-8 -*-
"""
技术评审管理模块 ORM 模型
包含：评审主表、评审参与人、评审材料、评审检查项记录、评审问题
适用场景：项目各阶段的技术评审（PDR/DDR/PRR/FRR/ARR）
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Text,
    ForeignKey, Numeric, Index, BigInteger
)
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base, TimestampMixin
from .enums import (
    ReviewTypeEnum, ReviewStatusEnum, MeetingTypeEnum, ReviewConclusionEnum,
    ParticipantRoleEnum, AttendanceStatusEnum, MaterialTypeEnumReview,
    ChecklistResultEnum, IssueLevelEnum, ReviewIssueStatusEnum, VerifyResultEnum
)


class TechnicalReview(Base, TimestampMixin):
    """技术评审主表"""
    __tablename__ = 'technical_reviews'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    review_no = Column(String(50), unique=True, nullable=False, comment='评审编号：RV-PDR-202501-0001')
    review_type = Column(String(20), nullable=False, comment='评审类型：PDR/DDR/PRR/FRR/ARR')
    review_name = Column(String(200), nullable=False, comment='评审名称')
    
    # 关联项目
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='关联项目ID')
    project_no = Column(String(50), nullable=False, comment='项目编号')
    equipment_id = Column(Integer, ForeignKey('machines.id'), nullable=True, comment='关联设备ID（多设备项目）')
    
    # 评审基本信息
    status = Column(String(20), nullable=False, default='DRAFT', comment='状态：draft/pending/in_progress/completed/cancelled')
    scheduled_date = Column(DateTime, nullable=False, comment='计划评审时间')
    actual_date = Column(DateTime, nullable=True, comment='实际评审时间')
    location = Column(String(200), nullable=True, comment='评审地点')
    meeting_type = Column(String(20), nullable=False, default='ONSITE', comment='会议形式：onsite/online/hybrid')
    
    # 评审人员
    host_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='主持人ID')
    presenter_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='汇报人ID')
    recorder_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='记录人ID')
    
    # 评审结论
    conclusion = Column(String(30), nullable=True, comment='评审结论：pass/pass_with_condition/reject/abort')
    conclusion_summary = Column(Text, nullable=True, comment='结论说明')
    condition_deadline = Column(Date, nullable=True, comment='有条件通过的整改期限')
    next_review_date = Column(Date, nullable=True, comment='下次复审日期')
    
    # 问题统计
    issue_count_a = Column(Integer, default=0, comment='A类问题数')
    issue_count_b = Column(Integer, default=0, comment='B类问题数')
    issue_count_c = Column(Integer, default=0, comment='C类问题数')
    issue_count_d = Column(Integer, default=0, comment='D类问题数')
    
    # 创建人
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False, comment='创建人')
    
    # 关系
    participants = relationship('ReviewParticipant', back_populates='review', lazy='dynamic', cascade='all, delete-orphan')
    materials = relationship('ReviewMaterial', back_populates='review', lazy='dynamic', cascade='all, delete-orphan')
    checklist_records = relationship('ReviewChecklistRecord', back_populates='review', lazy='dynamic', cascade='all, delete-orphan')
    issues = relationship('ReviewIssue', back_populates='review', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (
        Index('idx_review_no', 'review_no'),
        Index('idx_review_project', 'project_id'),
        Index('idx_review_type', 'review_type'),
        Index('idx_tech_review_status', 'status'),
        Index('idx_review_scheduled_date', 'scheduled_date'),
    )


class ReviewParticipant(Base):
    """评审参与人表"""
    __tablename__ = 'review_participants'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    review_id = Column(Integer, ForeignKey('technical_reviews.id'), nullable=False, comment='评审ID')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    role = Column(String(20), nullable=False, comment='角色：host/expert/presenter/recorder/observer')
    is_required = Column(Boolean, default=True, nullable=False, comment='是否必须参与')
    
    # 出席信息
    attendance = Column(String(20), nullable=True, comment='出席状态：pending/confirmed/absent/delegated')
    delegate_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='代理人ID（请假时）')
    sign_time = Column(DateTime, nullable=True, comment='签到时间')
    signature = Column(String(500), nullable=True, comment='电子签名')
    
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment='创建时间')
    
    # 关系
    review = relationship('TechnicalReview', back_populates='participants')
    
    __table_args__ = (
        Index('idx_participant_review', 'review_id'),
        Index('idx_participant_user', 'user_id'),
        Index('idx_participant_role', 'role'),
    )


class ReviewMaterial(Base, TimestampMixin):
    """评审材料表"""
    __tablename__ = 'review_materials'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    review_id = Column(Integer, ForeignKey('technical_reviews.id'), nullable=False, comment='评审ID')
    material_type = Column(String(20), nullable=False, comment='材料类型：drawing/bom/report/document/other')
    material_name = Column(String(200), nullable=False, comment='材料名称')
    file_path = Column(String(500), nullable=False, comment='文件路径')
    file_size = Column(BigInteger, nullable=False, comment='文件大小（字节）')
    version = Column(String(20), nullable=True, comment='版本号')
    is_required = Column(Boolean, default=True, nullable=False, comment='是否必须材料')
    upload_by = Column(Integer, ForeignKey('users.id'), nullable=False, comment='上传人')
    upload_at = Column(DateTime, default=datetime.now, nullable=False, comment='上传时间')
    
    # 关系
    review = relationship('TechnicalReview', back_populates='materials')
    
    __table_args__ = (
        Index('idx_material_review', 'review_id'),
        Index('idx_review_material_type', 'material_type'),
    )


class ReviewChecklistRecord(Base):
    """评审检查项记录表"""
    __tablename__ = 'review_checklist_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    review_id = Column(Integer, ForeignKey('technical_reviews.id'), nullable=False, comment='评审ID')
    checklist_item_id = Column(Integer, nullable=True, comment='检查项ID（关联模板，可为空）')
    category = Column(String(50), nullable=False, comment='检查类别')
    check_item = Column(String(500), nullable=False, comment='检查项内容')
    result = Column(String(20), nullable=False, comment='检查结果：pass/fail/na')
    
    # 问题信息（不通过时）
    issue_level = Column(String(10), nullable=True, comment='问题等级：A/B/C/D（不通过时）')
    issue_desc = Column(Text, nullable=True, comment='问题描述')
    issue_id = Column(Integer, ForeignKey('review_issues.id'), nullable=True, comment='关联问题ID（自动创建的问题）')
    
    checker_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='检查人ID')
    remark = Column(String(500), nullable=True, comment='备注')
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment='创建时间')
    
    # 关系
    review = relationship('TechnicalReview', back_populates='checklist_records')
    issue = relationship('ReviewIssue', foreign_keys=[issue_id])
    
    __table_args__ = (
        Index('idx_checklist_review', 'review_id'),
        Index('idx_checklist_result', 'result'),
    )


class ReviewIssue(Base, TimestampMixin):
    """评审问题表"""
    __tablename__ = 'review_issues'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    review_id = Column(Integer, ForeignKey('technical_reviews.id'), nullable=False, comment='评审ID')
    issue_no = Column(String(50), unique=True, nullable=False, comment='问题编号：RV-ISSUE-202501-0001')
    issue_level = Column(String(10), nullable=False, comment='问题等级：A/B/C/D')
    category = Column(String(50), nullable=False, comment='问题类别')
    description = Column(Text, nullable=False, comment='问题描述')
    suggestion = Column(Text, nullable=True, comment='改进建议')
    
    # 责任与期限
    assignee_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='责任人ID')
    deadline = Column(Date, nullable=False, comment='整改期限')
    
    # 状态与处理
    status = Column(String(20), nullable=False, default='OPEN', comment='状态：open/processing/resolved/verified/closed')
    solution = Column(Text, nullable=True, comment='解决方案')
    
    # 验证信息
    verify_result = Column(String(20), nullable=True, comment='验证结果：pass/fail')
    verifier_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='验证人')
    verify_time = Column(DateTime, nullable=True, comment='验证时间')
    
    # 关联
    linked_issue_id = Column(Integer, nullable=True, comment='关联问题管理系统ID')
    
    # 关系
    review = relationship('TechnicalReview', back_populates='issues')
    
    __table_args__ = (
        Index('idx_issue_no', 'issue_no'),
        Index('idx_issue_review', 'review_id'),
        Index('idx_issue_level', 'issue_level'),
        Index('idx_review_issue_status', 'status'),
        Index('idx_issue_assignee', 'assignee_id'),
        Index('idx_issue_deadline', 'deadline'),
    )

