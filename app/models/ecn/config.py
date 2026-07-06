# -*- coding: utf-8 -*-
"""
ECN模型 - 配置类
"""
from sqlalchemy import Boolean, Column, ForeignKey, Integer, JSON, String, Text

from ..base import Base, TimestampMixin


class EcnType(Base, TimestampMixin):
    """ECN类型配置表"""

    __tablename__ = "ecn_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, comment="租户ID")
    type_code = Column(String(20), unique=True, nullable=False, comment="类型编码")
    type_name = Column(String(50), nullable=False, comment="类型名称")
    description = Column(Text, comment="描述")
    required_depts = Column(JSON, comment="必需评估部门")
    optional_depts = Column(JSON, comment="可选评估部门")
    approval_matrix = Column(JSON, comment="审批矩阵")
    is_active = Column(Boolean, default=True, comment="是否启用")

    def __repr__(self):
        return f"<EcnType {self.type_code}>"


class EcnApprovalMatrix(Base):
    """Retired ECN approval matrix compatibility shell.

    ECN routing is configured through the unified approval template/flow tables.
    The old `ecn_approval_matrix` table is archived and not mapped anymore.
    """

    __abstract__ = True

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
