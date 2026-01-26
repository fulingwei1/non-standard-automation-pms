# -*- coding: utf-8 -*-
"""
缺料管理 - 物料处理模型（替代、调拨）
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class MaterialSubstitution(Base, TimestampMixin):
    """物料替代表"""
    __tablename__ = 'material_substitutions'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    substitution_no = Column(String(50), unique=True, nullable=False, comment='替代单号')
    shortage_report_id = Column(Integer, ForeignKey('shortage_reports.id'), nullable=True, comment='关联缺料上报ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    bom_item_id = Column(Integer, ForeignKey('bom_items.id'), nullable=True, comment='BOM行ID')

    # 原物料
    original_material_id = Column(Integer, ForeignKey('materials.id'), nullable=False, comment='原物料ID')
    original_material_code = Column(String(50), nullable=False, comment='原物料编码')
    original_material_name = Column(String(200), nullable=False, comment='原物料名称')
    original_qty = Column(Numeric(10, 4), nullable=False, comment='原物料数量')

    # 替代物料
    substitute_material_id = Column(Integer, ForeignKey('materials.id'), nullable=False, comment='替代物料ID')
    substitute_material_code = Column(String(50), nullable=False, comment='替代物料编码')
    substitute_material_name = Column(String(200), nullable=False, comment='替代物料名称')
    substitute_qty = Column(Numeric(10, 4), nullable=False, comment='替代物料数量')

    # 替代原因
    substitution_reason = Column(Text, nullable=False, comment='替代原因')
    technical_impact = Column(Text, comment='技术影响分析')
    cost_impact = Column(Numeric(14, 2), default=0, comment='成本影响')

    # 审批
    status = Column(String(20), default='DRAFT', comment='状态：DRAFT/TECH_PENDING/PROD_PENDING/APPROVED/REJECTED/EXECUTED')
    tech_approver_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='技术审批人ID')
    tech_approved_at = Column(DateTime, nullable=True, comment='技术审批时间')
    tech_approval_note = Column(Text, comment='技术审批意见')
    prod_approver_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='生产审批人ID')
    prod_approved_at = Column(DateTime, nullable=True, comment='生产审批时间')
    prod_approval_note = Column(Text, comment='生产审批意见')

    # 执行
    executed_at = Column(DateTime, nullable=True, comment='执行时间')
    executed_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='执行人ID')
    execution_note = Column(Text, comment='执行说明')

    remark = Column(Text, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False, comment='创建人ID')

    # 关系
    project = relationship('Project')
    original_material = relationship('Material', foreign_keys=[original_material_id])
    substitute_material = relationship('Material', foreign_keys=[substitute_material_id])

    __table_args__ = (
        Index('idx_substitution_no', 'substitution_no'),
        Index('idx_substitution_project', 'project_id'),
        Index('idx_substitution_status', 'status'),
        {'comment': '物料替代表'}
    )


class MaterialTransfer(Base, TimestampMixin):
    """物料调拨表"""
    __tablename__ = 'material_transfers'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    transfer_no = Column(String(50), unique=True, nullable=False, comment='调拨单号')
    shortage_report_id = Column(Integer, ForeignKey('shortage_reports.id'), nullable=True, comment='关联缺料上报ID')

    # 调拨信息
    from_project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, comment='调出项目ID')
    from_location = Column(String(200), comment='调出位置')
    to_project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='调入项目ID')
    to_location = Column(String(200), comment='调入位置')

    # 物料信息
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False, comment='物料ID')
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), nullable=False, comment='物料名称')
    transfer_qty = Column(Numeric(10, 4), nullable=False, comment='调拨数量')
    available_qty = Column(Numeric(10, 4), default=0, comment='可调拨数量')

    # 调拨原因
    transfer_reason = Column(Text, nullable=False, comment='调拨原因')
    urgent_level = Column(String(20), default='NORMAL', comment='紧急程度')

    # 审批
    status = Column(String(20), default='DRAFT', comment='状态：DRAFT/PENDING/APPROVED/REJECTED/EXECUTED/CANCELLED')
    approver_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='审批人ID')
    approved_at = Column(DateTime, nullable=True, comment='审批时间')
    approval_note = Column(Text, comment='审批意见')

    # 执行
    executed_at = Column(DateTime, nullable=True, comment='执行时间')
    executed_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='执行人ID')
    actual_qty = Column(Numeric(10, 4), nullable=True, comment='实际调拨数量')
    execution_note = Column(Text, comment='执行说明')

    remark = Column(Text, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False, comment='创建人ID')

    # 关系
    from_project = relationship('Project', foreign_keys=[from_project_id])
    to_project = relationship('Project', foreign_keys=[to_project_id])
    material = relationship('Material')

    __table_args__ = (
        Index('idx_transfer_no', 'transfer_no'),
        Index('idx_transfer_from_project', 'from_project_id'),
        Index('idx_transfer_to_project', 'to_project_id'),
        Index('idx_transfer_status', 'status'),
        {'comment': '物料调拨表'}
    )
