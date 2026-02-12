# -*- coding: utf-8 -*-
"""
文化墙配置模型
用于管理员配置文化墙的显示内容和可见角色
"""

from sqlalchemy import JSON, Boolean, Column, Index, Integer, String

from app.models.base import Base, TimestampMixin


class CultureWallConfig(Base, TimestampMixin):
    """文化墙配置表"""
    __tablename__ = 'culture_wall_config'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    # 配置名称
    config_name = Column(String(100), nullable=False, unique=True, comment='配置名称')
    description = Column(String(500), comment='配置描述')

    # 是否启用
    is_enabled = Column(Boolean, default=True, comment='是否启用此配置')
    is_default = Column(Boolean, default=False, comment='是否默认配置')

    # 内容类型配置（JSON格式）
    # 格式: {
    #   "STRATEGY": {"enabled": true, "max_count": 10, "priority": 1},
    #   "CULTURE": {"enabled": true, "max_count": 10, "priority": 2},
    #   "IMPORTANT": {"enabled": true, "max_count": 10, "priority": 3},
    #   "NOTICE": {"enabled": true, "max_count": 10, "priority": 4},
    #   "REWARD": {"enabled": true, "max_count": 10, "priority": 5},
    #   "PERSONAL_GOAL": {"enabled": true, "max_count": 5, "priority": 6},
    #   "NOTIFICATION": {"enabled": true, "max_count": 10, "priority": 7}
    # }
    content_types = Column(JSON, comment='内容类型配置')

    # 可见角色配置（JSON格式）
    # 格式: ["admin", "chairman", "gm", "manufacturing_director", ...]
    # 如果为空数组，表示所有角色可见
    visible_roles = Column(JSON, comment='可见角色列表（空数组表示所有角色）')

    # 播放设置（JSON格式）
    # 格式: {
    #   "auto_play": true,
    #   "interval": 5000,
    #   "show_controls": true,
    #   "show_indicators": true
    # }
    play_settings = Column(JSON, comment='播放设置')

    # 创建人
    created_by = Column(Integer, comment='创建人ID')

    __table_args__ = (
        Index('idx_culture_wall_config_enabled', 'is_enabled'),
        Index('idx_culture_wall_config_default', 'is_default'),
        {'comment': '文化墙配置表'},
    )

    def __repr__(self):
        return f"<CultureWallConfig {self.config_name}>"
