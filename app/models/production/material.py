# -*- coding: utf-8 -*-
"""
领料管理模型
"""
from datetime import datetime

from sqlalchemy import (
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

from app.models.base import Base, TimestampMixin


class MaterialRequisition(Base, TimestampMixin):
    """领料单
    
    【状态】未启用 - 物料申请"""
    __tablename__ = 'material_requisition'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    requisition_no = Column(String(50), unique=True, nullable=False, comment='领料单号')
    work_order_id = Column(Integer, ForeignKey('work_order.id'), nullable=True, comment='关联工单ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, comment='项目ID')

    # 申请信息
    applicant_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='申请人ID')
    apply_time = Column(DateTime, nullable=False, default=datetime.now, comment='申请时间')
    apply_reason = Column(Text, nullable=True, comment='申请原因')

    # 审批信息
    status = Column(String(20), nullable=False, default='DRAFT', comment='状态')
    approved_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='审批人ID')
    approved_at = Column(DateTime, nullable=True, comment='审批时间')
    approve_comment = Column(Text, nullable=True, comment='审批意见')

    # 发料信息
    issued_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='发料人ID')
    issued_at = Column(DateTime, nullable=True, comment='发料时间')

    remark = Column(Text, nullable=True, comment='备注')

    # 关系
    work_order = relationship('WorkOrder', back_populates='material_requisitions')
    items = relationship('MaterialRequisitionItem', back_populates='requisition')

    __table_args__ = (
        Index('idx_mat_req_no', 'requisition_no'),
        Index('idx_mat_req_work_order', 'work_order_id'),
        Index('idx_mat_req_project', 'project_id'),
        Index('idx_mat_req_status', 'status'),
        {'comment': '领料单表'}
    )


class MaterialRequisitionItem(Base, TimestampMixin):
    """领料单明细
    
    【状态】未启用 - 物料申请明细"""
    __tablename__ = 'material_requisition_item'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    requisition_id = Column(Integer, ForeignKey('material_requisition.id'), nullable=False, comment='领料单ID')
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False, comment='物料ID')

    request_qty = Column(Numeric(14, 4), nullable=False, comment='申请数量')
    approved_qty = Column(Numeric(14, 4), nullable=True, comment='批准数量')
    issued_qty = Column(Numeric(14, 4), nullable=True, comment='发放数量')
    unit = Column(String(20), nullable=True, comment='单位')

    remark = Column(Text, nullable=True, comment='备注')

    # 关系
    requisition = relationship('MaterialRequisition', back_populates='items')

    __table_args__ = (
        Index('idx_mat_req_item_requisition', 'requisition_id'),
        Index('idx_mat_req_item_material', 'material_id'),
        {'comment': '领料单明细表'}
    )


class ProductionDailyReport(Base, TimestampMixin):
    """生产日报"""
    __tablename__ = 'production_daily_report'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    report_date = Column(Date, nullable=False, comment='报告日期')
    workshop_id = Column(Integer, ForeignKey('workshop.id'), nullable=True, comment='车间ID(空表示全厂)')

    # 生产统计
    plan_qty = Column(Integer, default=0, comment='计划数量')
    completed_qty = Column(Integer, default=0, comment='完成数量')
    completion_rate = Column(Numeric(5, 2), default=0, comment='完成率(%)')

    # 工时统计
    plan_hours = Column(Numeric(10, 2), default=0, comment='计划工时')
    actual_hours = Column(Numeric(10, 2), default=0, comment='实际工时')
    overtime_hours = Column(Numeric(10, 2), default=0, comment='加班工时')
    efficiency = Column(Numeric(5, 2), default=0, comment='效率(%)')

    # 出勤统计
    should_attend = Column(Integer, default=0, comment='应出勤人数')
    actual_attend = Column(Integer, default=0, comment='实际出勤')
    leave_count = Column(Integer, default=0, comment='请假人数')

    # 质量统计
    total_qty = Column(Integer, default=0, comment='生产总数')
    qualified_qty = Column(Integer, default=0, comment='合格数量')
    pass_rate = Column(Numeric(5, 2), default=0, comment='合格率(%)')

    # 异常统计
    new_exception_count = Column(Integer, default=0, comment='新增异常数')
    resolved_exception_count = Column(Integer, default=0, comment='解决异常数')

    summary = Column(Text, nullable=True, comment='日报总结')
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='创建人ID')

    __table_args__ = (
        Index('idx_prod_daily_date', 'report_date'),
        Index('idx_prod_daily_workshop', 'workshop_id'),
        Index('idx_prod_daily_date_workshop', 'report_date', 'workshop_id', unique=True),
        {'comment': '生产日报表'}
    )
