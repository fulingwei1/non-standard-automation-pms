# -*- coding: utf-8 -*-
"""
用户仪表盘自定义布局模型

支持用户按角色自定义仪表盘组件的排列顺序和显示/隐藏
"""

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class UserDashboardLayout(Base, TimestampMixin):
    """用户仪表盘自定义布局"""

    __tablename__ = "user_dashboard_layouts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    role_code = Column(String(50), nullable=False, comment="角色编码")
    layout_config = Column(Text, nullable=False, comment="布局配置JSON")
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 关系
    user = relationship("User", backref="dashboard_layouts")

    __table_args__ = (
        Index("idx_udl_user_role", "user_id", "role_code", unique=True),
    )

    def __repr__(self):
        return f"<UserDashboardLayout user={self.user_id} role={self.role_code}>"
