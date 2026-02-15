# -*- coding: utf-8 -*-
"""
PDCA闭环记录模型
"""
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Boolean,
)
from sqlalchemy.orm import relationship
import enum

from app.models.base import Base, TimestampMixin


class PDCAStage(str, enum.Enum):
    """PDCA阶段枚举"""
    PLAN = "PLAN"  # 计划阶段
    DO = "DO"  # 执行阶段
    CHECK = "CHECK"  # 检查阶段
    ACT = "ACT"  # 改进阶段
    COMPLETED = "COMPLETED"  # 已完成


class ExceptionPDCA(Base, TimestampMixin):
    """PDCA闭环记录表"""
    __tablename__ = 'exception_pdca'
    __table_args__ = (
        Index('idx_pdca_exception_id', 'exception_id'),
        Index('idx_pdca_stage', 'current_stage'),
        Index('idx_pdca_is_completed', 'is_completed'),
        {'extend_existing': True, 'comment': 'PDCA闭环记录表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    
    # 关联异常
    exception_id = Column(
        Integer,
        ForeignKey('production_exception.id'),
        nullable=False,
        comment='异常ID'
    )
    
    # PDCA编号
    pdca_no = Column(String(50), unique=True, nullable=False, comment='PDCA编号')
    
    # 当前阶段
    current_stage = Column(
        Enum(PDCAStage),
        nullable=False,
        default=PDCAStage.PLAN,
        comment='当前阶段'
    )
    
    # Plan阶段
    plan_description = Column(Text, nullable=True, comment='问题描述')
    plan_root_cause = Column(Text, nullable=True, comment='根本原因分析')
    plan_target = Column(Text, nullable=True, comment='改善目标')
    plan_measures = Column(Text, nullable=True, comment='改善措施（JSON格式）')
    plan_owner_id = Column(
        Integer,
        ForeignKey('users.id'),
        nullable=True,
        comment='计划负责人ID'
    )
    plan_deadline = Column(DateTime, nullable=True, comment='计划完成期限')
    plan_completed_at = Column(DateTime, nullable=True, comment='Plan阶段完成时间')
    
    # Do阶段
    do_action_taken = Column(Text, nullable=True, comment='实施内容')
    do_resources_used = Column(Text, nullable=True, comment='使用资源')
    do_difficulties = Column(Text, nullable=True, comment='遇到的困难')
    do_owner_id = Column(
        Integer,
        ForeignKey('users.id'),
        nullable=True,
        comment='执行负责人ID'
    )
    do_completed_at = Column(DateTime, nullable=True, comment='Do阶段完成时间')
    
    # Check阶段
    check_result = Column(Text, nullable=True, comment='检查结果')
    check_effectiveness = Column(String(20), nullable=True, comment='有效性：EFFECTIVE/PARTIAL/INEFFECTIVE')
    check_data = Column(Text, nullable=True, comment='数据分析（JSON格式）')
    check_gap = Column(Text, nullable=True, comment='差距分析')
    check_owner_id = Column(
        Integer,
        ForeignKey('users.id'),
        nullable=True,
        comment='检查负责人ID'
    )
    check_completed_at = Column(DateTime, nullable=True, comment='Check阶段完成时间')
    
    # Act阶段
    act_standardization = Column(Text, nullable=True, comment='标准化措施')
    act_horizontal_deployment = Column(Text, nullable=True, comment='横向展开计划')
    act_remaining_issues = Column(Text, nullable=True, comment='遗留问题')
    act_next_cycle = Column(Text, nullable=True, comment='下一轮PDCA计划')
    act_owner_id = Column(
        Integer,
        ForeignKey('users.id'),
        nullable=True,
        comment='改进负责人ID'
    )
    act_completed_at = Column(DateTime, nullable=True, comment='Act阶段完成时间')
    
    # 完成状态
    is_completed = Column(Boolean, nullable=False, default=False, comment='是否完成')
    completed_at = Column(DateTime, nullable=True, comment='完成时间')
    
    # 总结
    summary = Column(Text, nullable=True, comment='总结')
    lessons_learned = Column(Text, nullable=True, comment='经验教训')
    
    remark = Column(Text, nullable=True, comment='备注')
    
    # 关系
    exception = relationship('ProductionException', backref='pdca_records')
    plan_owner = relationship('User', foreign_keys=[plan_owner_id], backref='pdca_plan_owned')
    do_owner = relationship('User', foreign_keys=[do_owner_id], backref='pdca_do_owned')
    check_owner = relationship('User', foreign_keys=[check_owner_id], backref='pdca_check_owned')
    act_owner = relationship('User', foreign_keys=[act_owner_id], backref='pdca_act_owned')
