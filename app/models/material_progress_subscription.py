# -*- coding: utf-8 -*-
"""
物料进度通知订阅模型
"""

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class MaterialProgressSubscription(Base, TimestampMixin):
    """物料进度通知订阅表"""

    __tablename__ = "material_progress_subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")

    # 订阅选项
    notify_kitting_change = Column(Boolean, default=True, comment="齐套率变化通知")
    notify_key_material_arrival = Column(Boolean, default=True, comment="关键物料到货通知")
    notify_shortage_alert = Column(Boolean, default=True, comment="缺料预警通知")
    kitting_change_threshold = Column(
        Numeric(5, 2), default=5, comment="齐套率变化阈值(%)"
    )

    is_active = Column(Boolean, default=True, comment="是否启用")

    # 关系
    project = relationship("Project")
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_mps_project_user", "project_id", "user_id", unique=True),
        Index("idx_mps_project", "project_id"),
    )

    def __repr__(self):
        return f"<MaterialProgressSubscription project={self.project_id} user={self.user_id}>"
