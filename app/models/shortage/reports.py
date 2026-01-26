# -*- coding: utf-8 -*-
"""
缺料管理 - 缺料上报模型
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class ShortageReport(Base, TimestampMixin):
    """缺料上报表"""
    __tablename__ = 'shortage_reports'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    report_no = Column(String(50), unique=True, nullable=False, comment='上报单号')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    machine_id = Column(Integer, ForeignKey('machines.id'), nullable=True, comment='机台ID')
    work_order_id = Column(Integer, ForeignKey('work_order.id'), nullable=True, comment='工单ID')

    # 上报信息
    reporter_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='上报人ID')
    report_time = Column(DateTime, nullable=False, default=datetime.now, comment='上报时间')
    report_location = Column(String(200), comment='上报地点（车间/工位）')

    # 物料信息
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False, comment='物料ID')
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), nullable=False, comment='物料名称')
    required_qty = Column(Numeric(10, 4), nullable=False, comment='需求数量')
    shortage_qty = Column(Numeric(10, 4), nullable=False, comment='缺料数量')
    urgent_level = Column(String(20), default='NORMAL', comment='紧急程度')

    # 状态
    status = Column(String(20), default='REPORTED', comment='状态：REPORTED/CONFIRMED/HANDLING/RESOLVED')
    confirmed_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='确认人ID（仓管）')
    confirmed_at = Column(DateTime, nullable=True, comment='确认时间')
    handler_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='处理人ID')
    resolved_at = Column(DateTime, nullable=True, comment='解决时间')

    # 处理信息
    solution_type = Column(String(20), comment='解决方案类型：PURCHASE/SUBSTITUTE/TRANSFER/OTHER')
    solution_note = Column(Text, comment='解决方案说明')

    remark = Column(Text, comment='备注')

    # 关系
    project = relationship('Project')
    machine = relationship('Machine')
    material = relationship('Material')

    __table_args__ = (
        Index('idx_shortage_report_no', 'report_no'),
        Index('idx_shortage_report_project', 'project_id'),
        Index('idx_shortage_report_status', 'status'),
        {'comment': '缺料上报表'}
    )
