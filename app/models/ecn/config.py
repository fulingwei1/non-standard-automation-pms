# -*- coding: utf-8 -*-
"""
ECN模型 - 配置类
"""
from sqlalchemy import Boolean, Column, Index, Integer, JSON, Numeric, String, Text

from ..base import Base, TimestampMixin


class EcnType(Base, TimestampMixin):
    """ECN类型配置表"""
    __tablename__ = 'ecn_types'

    id = Column(Integer, primary_key=True, autoincrement=True)
    type_code = Column(String(20), unique=True, nullable=False, comment='类型编码')
    type_name = Column(String(50), nullable=False, comment='类型名称')
    description = Column(Text, comment='描述')
    required_depts = Column(JSON, comment='必需评估部门')
    optional_depts = Column(JSON, comment='可选评估部门')
    approval_matrix = Column(JSON, comment='审批矩阵')
    is_active = Column(Boolean, default=True, comment='是否启用')

    def __repr__(self):
        return f'<EcnType {self.type_code}>'


class EcnApprovalMatrix(Base, TimestampMixin):
    """ECN审批矩阵配置表"""
    __tablename__ = 'ecn_approval_matrix'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ecn_type = Column(String(20), comment='ECN类型')
    condition_type = Column(String(20), nullable=False, comment='条件类型')
    condition_min = Column(Numeric(14, 2), comment='条件下限')
    condition_max = Column(Numeric(14, 2), comment='条件上限')
    approval_level = Column(Integer, nullable=False, comment='审批层级')
    approval_role = Column(String(50), nullable=False, comment='审批角色')
    is_active = Column(Boolean, default=True, comment='是否启用')

    __table_args__ = (
        Index('idx_matrix_type', 'ecn_type'),
    )
