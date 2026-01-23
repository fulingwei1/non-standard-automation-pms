# -*- coding: utf-8 -*-
"""
ECN模型 - 影响分析
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


class EcnAffectedMaterial(Base, TimestampMixin):
    """ECN受影响物料表"""
    __tablename__ = 'ecn_affected_materials'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ecn_id = Column(Integer, ForeignKey('ecn.id'), nullable=False, comment='ECN ID')
    material_id = Column(Integer, ForeignKey('materials.id'), comment='物料ID')
    bom_item_id = Column(Integer, ForeignKey('bom_items.id'), comment='BOM行ID')

    # 物料信息
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), nullable=False, comment='物料名称')
    specification = Column(String(500), comment='规格型号')

    # 变更类型
    change_type = Column(String(20), nullable=False, comment='变更类型')

    # 变更前
    old_quantity = Column(Numeric(10, 4), comment='原数量')
    old_specification = Column(String(500), comment='原规格')
    old_supplier_id = Column(Integer, ForeignKey('vendors.id'), comment='原供应商')

    # 变更后
    new_quantity = Column(Numeric(10, 4), comment='新数量')
    new_specification = Column(String(500), comment='新规格')
    new_supplier_id = Column(Integer, ForeignKey('vendors.id'), comment='新供应商')

    # 影响
    cost_impact = Column(Numeric(12, 2), default=0, comment='成本影响')

    # BOM影响范围（JSON格式）
    bom_impact_scope = Column(JSON, comment='BOM影响范围，包含受影响的BOM项和设备')
    # 例如: {"affected_bom_items": [1, 2, 3], "affected_machines": [10, 11], "affected_projects": [5]}

    # 呆滞料风险
    is_obsolete_risk = Column(Boolean, default=False, comment='是否呆滞料风险')
    obsolete_risk_level = Column(String(20), comment='呆滞料风险级别：LOW/MEDIUM/HIGH/CRITICAL')
    obsolete_quantity = Column(Numeric(10, 4), comment='呆滞料数量')
    obsolete_cost = Column(Numeric(14, 2), comment='呆滞料成本')
    obsolete_analysis = Column(Text, comment='呆滞料分析说明')

    # 处理状态
    status = Column(String(20), default='PENDING', comment='处理状态')
    processed_at = Column(DateTime, comment='处理时间')

    remark = Column(Text, comment='备注')

    # 关系
    ecn = relationship('Ecn', back_populates='affected_materials')
    material = relationship('Material')

    __table_args__ = (
        Index('idx_affected_mat_ecn', 'ecn_id'),
        Index('idx_affected_mat_material', 'material_id'),
    )


class EcnAffectedOrder(Base, TimestampMixin):
    """ECN受影响订单表"""
    __tablename__ = 'ecn_affected_orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ecn_id = Column(Integer, ForeignKey('ecn.id'), nullable=False, comment='ECN ID')
    order_type = Column(String(20), nullable=False, comment='订单类型')
    order_id = Column(Integer, nullable=False, comment='订单ID')
    order_no = Column(String(50), nullable=False, comment='订单号')

    # 影响描述
    impact_description = Column(Text, comment='影响描述')

    # 处理方式
    action_type = Column(String(20), comment='处理方式')
    action_description = Column(Text, comment='处理说明')

    # 处理状态
    status = Column(String(20), default='PENDING', comment='处理状态')
    processed_by = Column(Integer, ForeignKey('users.id'), comment='处理人')
    processed_at = Column(DateTime, comment='处理时间')

    # 关系
    ecn = relationship('Ecn', back_populates='affected_orders')

    __table_args__ = (
        Index('idx_affected_order_ecn', 'ecn_id'),
    )


class EcnBomImpact(Base, TimestampMixin):
    """ECN BOM影响分析表"""
    __tablename__ = 'ecn_bom_impacts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ecn_id = Column(Integer, ForeignKey('ecn.id'), nullable=False, comment='ECN ID')

    # 关联信息
    bom_version_id = Column(Integer, ForeignKey('bom_headers.id'), comment='BOM版本ID')
    machine_id = Column(Integer, ForeignKey('machines.id'), comment='设备ID')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID')

    # 影响统计
    affected_item_count = Column(Integer, default=0, comment='受影响物料项数')
    total_cost_impact = Column(Numeric(14, 2), default=0, comment='总成本影响')
    schedule_impact_days = Column(Integer, default=0, comment='交期影响天数')

    # 影响分析详情（JSON格式）
    impact_analysis = Column(JSON, comment='影响分析详情')
    # 例如: {
    #   "direct_impact": [{"bom_item_id": 1, "material_code": "M001", "impact": "DELETE"}],
    #   "cascade_impact": [{"bom_item_id": 2, "material_code": "M002", "impact": "UPDATE"}],
    #   "affected_orders": [{"order_type": "PURCHASE", "order_id": 10}]
    # }

    # 分析状态
    analysis_status = Column(String(20), default='PENDING', comment='分析状态：PENDING/ANALYZING/COMPLETED/FAILED')
    analyzed_at = Column(DateTime, comment='分析时间')
    analyzed_by = Column(Integer, ForeignKey('users.id'), comment='分析人ID')

    remark = Column(Text, comment='备注')

    # 关系
    ecn = relationship('Ecn', back_populates='bom_impacts')
    bom_version = relationship('BomHeader')
    machine = relationship('Machine')
    project = relationship('Project')
    analyzer = relationship('User')

    __table_args__ = (
        Index('idx_bom_impact_ecn', 'ecn_id'),
        Index('idx_bom_impact_bom', 'bom_version_id'),
        Index('idx_bom_impact_machine', 'machine_id'),
    )
