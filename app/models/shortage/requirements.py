# -*- coding: utf-8 -*-
"""
缺料管理 - 需求与检查模型
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class WorkOrderBom(Base, TimestampMixin):
    """工单BOM明细表"""
    __tablename__ = 'mat_work_order_bom'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    work_order_id = Column(Integer, ForeignKey('work_order.id'), nullable=False, comment='工单ID')
    work_order_no = Column(String(32), comment='工单号')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, comment='项目ID')

    # 物料信息
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=True, comment='物料ID')
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), nullable=False, comment='物料名称')
    specification = Column(String(200), comment='规格型号')
    unit = Column(String(20), default='件', comment='单位')

    # 数量信息
    bom_qty = Column(Numeric(12, 4), nullable=False, comment='BOM用量')
    required_qty = Column(Numeric(12, 4), nullable=False, comment='需求数量')
    required_date = Column(Date, nullable=False, comment='需求日期')

    # 物料类型
    material_type = Column(String(20), default='purchase', comment='物料类型：purchase/make/outsource')
    lead_time = Column(Integer, default=0, comment='采购提前期(天)')
    is_key_material = Column(Boolean, default=False, comment='是否关键物料')

    # 关系
    work_order = relationship('WorkOrder')
    project = relationship('Project')
    material = relationship('Material')

    __table_args__ = (
        Index('idx_work_order_bom_wo', 'work_order_id'),
        Index('idx_work_order_bom_material', 'material_code'),
        Index('idx_work_order_bom_date', 'required_date'),
        {'comment': '工单BOM明细表'}
    )


class MaterialRequirement(Base, TimestampMixin):
    """物料需求汇总表"""
    __tablename__ = 'mat_material_requirement'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    requirement_no = Column(String(32), unique=True, nullable=False, comment='需求编号')

    # 来源信息
    source_type = Column(String(20), nullable=False, comment='来源类型：work_order/project/manual')
    work_order_id = Column(Integer, ForeignKey('work_order.id'), nullable=True, comment='工单ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, comment='项目ID')

    # 物料信息
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=True, comment='物料ID')
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), nullable=False, comment='物料名称')
    specification = Column(String(200), comment='规格型号')
    unit = Column(String(20), comment='单位')

    # 数量信息
    required_qty = Column(Numeric(12, 4), nullable=False, comment='需求数量')
    stock_qty = Column(Numeric(12, 4), default=0, comment='库存可用')
    allocated_qty = Column(Numeric(12, 4), default=0, comment='已分配')
    in_transit_qty = Column(Numeric(12, 4), default=0, comment='在途数量')
    shortage_qty = Column(Numeric(12, 4), default=0, comment='缺料数量')
    required_date = Column(Date, nullable=False, comment='需求日期')

    # 状态
    status = Column(String(20), default='pending', comment='状态：pending/partial/fulfilled/cancelled')
    fulfill_method = Column(String(20), nullable=True, comment='满足方式：stock/purchase/substitute/transfer')

    # 关系
    work_order = relationship('WorkOrder')
    project = relationship('Project')
    material = relationship('Material')

    __table_args__ = (
        Index('idx_requirement_no', 'requirement_no'),
        Index('idx_requirement_wo', 'work_order_id'),
        Index('idx_requirement_material', 'material_code'),
        Index('idx_requirement_status', 'status'),
        Index('idx_requirement_date', 'required_date'),
        {'comment': '物料需求汇总表'}
    )


class KitCheck(Base, TimestampMixin):
    """齐套检查记录表"""
    __tablename__ = 'mat_kit_check'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    check_no = Column(String(32), unique=True, nullable=False, comment='检查编号')

    # 检查对象
    check_type = Column(String(20), nullable=False, comment='检查类型：work_order/project/batch')
    work_order_id = Column(Integer, ForeignKey('work_order.id'), nullable=True, comment='工单ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, comment='项目ID')

    # 检查结果
    total_items = Column(Integer, default=0, comment='物料总项')
    fulfilled_items = Column(Integer, default=0, comment='已齐套项')
    shortage_items = Column(Integer, default=0, comment='缺料项')
    in_transit_items = Column(Integer, default=0, comment='在途项')
    kit_rate = Column(Numeric(5, 2), default=0, comment='齐套率(%)')
    kit_status = Column(String(20), default='shortage', comment='齐套状态：complete/partial/shortage')
    shortage_summary = Column(JSON, comment='缺料汇总JSON')

    # 检查信息
    check_time = Column(DateTime, nullable=False, default=datetime.now, comment='检查时间')
    check_method = Column(String(20), default='auto', comment='检查方式：auto/manual')
    checked_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='检查人ID')

    # 开工确认
    can_start = Column(Boolean, default=False, comment='是否可开工')
    start_confirmed = Column(Boolean, default=False, comment='已确认开工')
    confirm_time = Column(DateTime, nullable=True, comment='确认时间')
    confirmed_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='确认人ID')
    confirm_remark = Column(Text, comment='确认备注')

    # 关系
    work_order = relationship('WorkOrder')
    project = relationship('Project')
    checker = relationship('User', foreign_keys=[checked_by])
    confirmer = relationship('User', foreign_keys=[confirmed_by])

    __table_args__ = (
        Index('idx_kit_check_no', 'check_no'),
        Index('idx_kit_check_wo', 'work_order_id'),
        Index('idx_kit_check_project', 'project_id'),
        Index('idx_kit_check_status', 'kit_status'),
        Index('idx_kit_check_time', 'check_time'),
        {'comment': '齐套检查记录表'}
    )
