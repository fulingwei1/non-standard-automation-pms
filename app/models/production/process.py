# -*- coding: utf-8 -*-
"""
工序字典模型
"""
from sqlalchemy import Boolean, Column, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class ProcessDict(Base, TimestampMixin):
    """工序字典"""
    __tablename__ = 'process_dict'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    process_code = Column(String(50), unique=True, nullable=False, comment='工序编码')
    process_name = Column(String(100), nullable=False, comment='工序名称')
    process_type = Column(String(20), nullable=False, default='OTHER', comment='工序类型')
    standard_hours = Column(Numeric(10, 2), nullable=True, comment='标准工时(小时)')
    description = Column(Text, nullable=True, comment='描述')
    work_instruction = Column(Text, nullable=True, comment='作业指导')
    is_active = Column(Boolean, default=True, nullable=False, comment='是否启用')

    # 关系
    worker_skills = relationship('WorkerSkill', back_populates='process')
    work_orders = relationship('WorkOrder', back_populates='process')

    __table_args__ = (
        Index('idx_process_code', 'process_code'),
        Index('idx_process_type', 'process_type'),
        {'comment': '工序字典表'}
    )
