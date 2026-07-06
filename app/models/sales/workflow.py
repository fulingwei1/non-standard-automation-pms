# -*- coding: utf-8 -*-
"""
销售目标模型
"""

from sqlalchemy import (
    JSON,
    Column,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class SalesTarget(Base, TimestampMixin):
    """销售目标表"""

    __tablename__ = "sales_targets"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, comment="租户ID")
    target_scope = Column(String(20), nullable=False, comment="目标范围：PERSONAL/TEAM/DEPARTMENT")
    user_id = Column(Integer, ForeignKey("users.id"), comment="用户ID（个人目标）")
    department_id = Column(Integer, ForeignKey("departments.id"), comment="部门ID（部门目标）")
    team_id = Column(Integer, ForeignKey("sales_teams.id"), comment="团队ID（团队目标）")
    target_type = Column(
        String(20),
        nullable=False,
        comment="目标类型：LEAD_COUNT/OPPORTUNITY_COUNT/CONTRACT_AMOUNT/COLLECTION_AMOUNT",
    )
    target_period = Column(String(20), nullable=False, comment="目标周期：MONTHLY/QUARTERLY/YEARLY")
    period_value = Column(String(20), nullable=False, comment="周期标识：2025-01/2025-Q1/2025")
    target_value = Column(Numeric(14, 2), nullable=False, comment="目标值")
    description = Column(Text, comment="目标描述")
    status = Column(String(20), default="ACTIVE", comment="状态：ACTIVE/COMPLETED/CANCELLED")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")

    user = relationship("User", foreign_keys=[user_id])
    department = relationship("Department", foreign_keys=[department_id])
    team = relationship("SalesTeam", foreign_keys=[team_id])
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index("idx_sales_target_scope", "target_scope", "user_id", "department_id"),
        Index("idx_sales_target_type_period", "target_type", "target_period", "period_value"),
        Index("idx_sales_target_status", "status"),
        Index("idx_sales_target_user", "user_id"),
        Index("idx_sales_target_department", "department_id"),
        Index("idx_sales_target_team", "team_id"),
    )

    def __repr__(self):
        return f"<SalesTarget {self.target_type}-{self.period_value}>"


class SalesRankingConfig(Base, TimestampMixin):
    """销售排名权重配置"""

    __tablename__ = "sales_ranking_configs"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, comment="租户ID")
    metrics = Column(JSON, nullable=False, comment="指标配置(JSON数组)")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")
    updated_by = Column(Integer, ForeignKey("users.id"), comment="最后更新人ID")

    __table_args__ = (
        Index("idx_sales_ranking_config_updated_at", "updated_at"),
        {"comment": "销售排名权重配置表"},
    )

    def __repr__(self):
        return f"<SalesRankingConfig {self.id}>"
