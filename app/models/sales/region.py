# -*- coding: utf-8 -*-
"""
销售区域管理模型
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    JSON,
    Boolean,
    Index,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class SalesRegion(Base, TimestampMixin):
    """
    销售区域表
    
    用于管理销售区域的划分和负责关系
    """
    __tablename__ = "sales_regions"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="区域ID")
    region_code = Column(
        String(50),
        unique=True,
        nullable=False,
        comment="区域编码"
    )
    region_name = Column(String(100), nullable=False, comment="区域名称")
    parent_region_id = Column(
        Integer,
        ForeignKey("sales_regions.id", ondelete="SET NULL"),
        nullable=True,
        comment="上级区域ID"
    )
    level = Column(Integer, default=1, comment="区域层级")
    
    # 区域范围
    provinces = Column(JSON, comment="包含的省份(JSON数组)")
    cities = Column(JSON, comment="包含的城市(JSON数组)")
    
    # 负责团队和负责人
    team_id = Column(
        Integer,
        ForeignKey("sales_teams.id", ondelete="SET NULL"),
        nullable=True,
        comment="负责团队ID"
    )
    leader_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="负责人ID"
    )
    
    # 区域描述
    description = Column(Text, comment="区域描述")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 排序
    sort_order = Column(Integer, default=0, comment="排序序号")
    
    # 创建人
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")

    # 关系
    parent_region = relationship(
        "SalesRegion",
        remote_side=[id],
        backref="sub_regions",
        foreign_keys=[parent_region_id]
    )
    team = relationship("SalesTeam", foreign_keys=[team_id])
    leader = relationship("User", foreign_keys=[leader_id])
    creator = relationship("User", foreign_keys=[created_by])

    # 索引
    __table_args__ = (
        Index("idx_sales_region_code", "region_code"),
        Index("idx_sales_region_parent", "parent_region_id"),
        Index("idx_sales_region_team", "team_id"),
        Index("idx_sales_region_leader", "leader_id"),
        Index("idx_sales_region_active", "is_active"),
    )

    def __repr__(self):
        return f"<SalesRegion(id={self.id}, code={self.region_code}, name={self.region_name})>"
