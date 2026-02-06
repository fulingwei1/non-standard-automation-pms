# -*- coding: utf-8 -*-
"""
ECN模型 - 责任分摊和解决方案模板
"""
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class EcnResponsibility(Base, TimestampMixin):
    """ECN责任分摊表"""
    __tablename__ = 'ecn_responsibilities'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ecn_id = Column(Integer, ForeignKey('ecn.id'), nullable=False, comment='ECN ID')

    # 责任部门
    dept = Column(String(50), nullable=False, comment='责任部门')
    responsibility_ratio = Column(Numeric(5, 2), default=0, comment='责任比例(0-100)')
    responsibility_type = Column(String(20), default='PRIMARY', comment='责任类型：PRIMARY/SECONDARY/SUPPORT')

    # 成本分摊
    cost_allocation = Column(Numeric(14, 2), default=0, comment='成本分摊金额')

    # 影响描述
    impact_description = Column(Text, comment='影响描述')
    responsibility_scope = Column(Text, comment='责任范围')

    # 确认信息
    confirmed = Column(Boolean, default=False, comment='是否已确认')
    confirmed_by = Column(Integer, ForeignKey('users.id'), comment='确认人ID')
    confirmed_at = Column(DateTime, comment='确认时间')

    remark = Column(Text, comment='备注')

    # 关系
    ecn = relationship('Ecn', back_populates='responsibilities')
    confirmer = relationship('User')

    __table_args__ = (
        Index('idx_resp_ecn', 'ecn_id'),
        Index('idx_resp_dept', 'dept'),
    )


class EcnSolutionTemplate(Base, TimestampMixin):
    """ECN解决方案模板表"""
    __tablename__ = 'ecn_solution_templates'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 模板基本信息
    template_code = Column(String(50), unique=True, nullable=False, comment='模板编码')
    template_name = Column(String(200), nullable=False, comment='模板名称')
    template_category = Column(String(50), comment='模板分类')

    # 适用场景
    ecn_type = Column(String(20), comment='适用的ECN类型')
    root_cause_category = Column(String(50), comment='适用的根本原因分类')
    keywords = Column(JSON, comment='关键词列表（用于匹配）')

    # 解决方案内容
    solution_description = Column(Text, nullable=False, comment='解决方案描述')
    solution_steps = Column(JSON, comment='解决步骤（JSON数组）')
    required_resources = Column(JSON, comment='所需资源（JSON数组）')
    estimated_cost = Column(Numeric(14, 2), comment='预估成本')
    estimated_days = Column(Integer, comment='预估天数')

    # 效果评估
    success_rate = Column(Numeric(5, 2), default=0, comment='成功率（0-100）')
    usage_count = Column(Integer, default=0, comment='使用次数')
    avg_cost_saving = Column(Numeric(14, 2), comment='平均成本节省')
    avg_time_saving = Column(Integer, comment='平均时间节省（天）')

    # 来源信息
    source_ecn_id = Column(Integer, ForeignKey('ecn.id'), comment='来源ECN ID')
    created_from = Column(String(20), default='MANUAL', comment='创建来源：MANUAL/AUTO_EXTRACT')

    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    is_verified = Column(Boolean, default=False, comment='是否已验证')
    verified_by = Column(Integer, ForeignKey('users.id'), comment='验证人ID')
    verified_at = Column(DateTime, comment='验证时间')

    remark = Column(Text, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')

    # 关系
    source_ecn = relationship('Ecn', foreign_keys=[source_ecn_id], back_populates='solution_template')
    verifier = relationship('User', foreign_keys=[verified_by])
    creator = relationship('User', foreign_keys=[created_by])

    __table_args__ = (
        Index('idx_ecn_solution_template_type', 'ecn_type'),
        Index('idx_ecn_solution_template_category', 'template_category'),
        Index('idx_solution_template_active', 'is_active'),
    )
