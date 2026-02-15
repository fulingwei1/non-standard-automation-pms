# -*- coding: utf-8 -*-
"""
异常知识库模型
"""
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Boolean,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class ExceptionKnowledge(Base, TimestampMixin):
    """异常知识库表"""
    __tablename__ = 'exception_knowledge'
    __table_args__ = (
        Index('idx_ek_exception_type', 'exception_type'),
        Index('idx_ek_exception_level', 'exception_level'),
        Index('idx_ek_keywords', 'keywords', mysql_length=100),
        Index('idx_ek_is_approved', 'is_approved'),
        {'extend_existing': True, 'comment': '异常知识库表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    
    # 知识条目基本信息
    title = Column(String(200), nullable=False, comment='知识标题')
    exception_type = Column(String(20), nullable=False, comment='异常类型')
    exception_level = Column(String(20), nullable=False, comment='异常级别')
    
    # 异常描述
    symptom_description = Column(Text, nullable=False, comment='异常症状描述')
    
    # 解决方案
    solution = Column(Text, nullable=False, comment='解决方案')
    solution_steps = Column(Text, nullable=True, comment='处理步骤（JSON格式）')
    
    # 预防措施
    prevention_measures = Column(Text, nullable=True, comment='预防措施')
    
    # 关键词（用于搜索匹配）
    keywords = Column(String(500), nullable=True, comment='关键词（逗号分隔）')
    
    # 关联信息
    source_exception_id = Column(
        Integer,
        ForeignKey('production_exception.id'),
        nullable=True,
        comment='来源异常ID'
    )
    
    # 使用统计
    reference_count = Column(Integer, nullable=False, default=0, comment='引用次数')
    success_count = Column(Integer, nullable=False, default=0, comment='成功解决次数')
    last_referenced_at = Column(DateTime, nullable=True, comment='最后引用时间')
    
    # 审核信息
    is_approved = Column(Boolean, nullable=False, default=False, comment='是否已审核')
    approver_id = Column(
        Integer,
        ForeignKey('users.id'),
        nullable=True,
        comment='审核人ID'
    )
    approved_at = Column(DateTime, nullable=True, comment='审核时间')
    
    # 创建者
    creator_id = Column(
        Integer,
        ForeignKey('users.id'),
        nullable=False,
        comment='创建人ID'
    )
    
    # 附件
    attachments = Column(Text, nullable=True, comment='附件URL（JSON格式）')
    
    remark = Column(Text, nullable=True, comment='备注')
    
    # 关系
    source_exception = relationship('ProductionException', backref='knowledge_entries')
    creator = relationship('User', foreign_keys=[creator_id], backref='created_knowledge')
    approver = relationship('User', foreign_keys=[approver_id], backref='approved_knowledge')
