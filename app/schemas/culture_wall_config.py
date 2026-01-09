# -*- coding: utf-8 -*-
"""
文化墙配置 Schema
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ContentTypeConfig(BaseModel):
    """内容类型配置"""
    enabled: bool = Field(default=True, description="是否启用")
    max_count: int = Field(default=10, ge=1, le=50, description="最大显示数量")
    priority: int = Field(default=0, description="优先级（数字越大越优先）")


class PlaySettings(BaseModel):
    """播放设置"""
    auto_play: bool = Field(default=True, description="是否自动播放")
    interval: int = Field(default=5000, ge=1000, le=60000, description="播放间隔（毫秒）")
    show_controls: bool = Field(default=True, description="是否显示控制按钮")
    show_indicators: bool = Field(default=True, description="是否显示指示器")


class CultureWallConfigBase(BaseModel):
    """文化墙配置基础模型"""
    config_name: str = Field(..., max_length=100, description="配置名称")
    description: Optional[str] = Field(None, max_length=500, description="配置描述")
    is_enabled: bool = Field(default=True, description="是否启用")
    is_default: bool = Field(default=False, description="是否默认配置")
    content_types: Dict[str, ContentTypeConfig] = Field(
        default_factory=lambda: {
            "STRATEGY": ContentTypeConfig(enabled=True, max_count=10, priority=1),
            "CULTURE": ContentTypeConfig(enabled=True, max_count=10, priority=2),
            "IMPORTANT": ContentTypeConfig(enabled=True, max_count=10, priority=3),
            "NOTICE": ContentTypeConfig(enabled=True, max_count=10, priority=4),
            "REWARD": ContentTypeConfig(enabled=True, max_count=10, priority=5),
            "PERSONAL_GOAL": ContentTypeConfig(enabled=True, max_count=5, priority=6),
            "NOTIFICATION": ContentTypeConfig(enabled=True, max_count=10, priority=7),
        },
        description="内容类型配置"
    )
    visible_roles: List[str] = Field(
        default_factory=list,
        description="可见角色列表（空数组表示所有角色）"
    )
    play_settings: PlaySettings = Field(
        default_factory=PlaySettings,
        description="播放设置"
    )


class CultureWallConfigCreate(CultureWallConfigBase):
    """创建文化墙配置"""
    pass


class CultureWallConfigUpdate(BaseModel):
    """更新文化墙配置"""
    config_name: Optional[str] = Field(None, max_length=100, description="配置名称")
    description: Optional[str] = Field(None, max_length=500, description="配置描述")
    is_enabled: Optional[bool] = Field(None, description="是否启用")
    is_default: Optional[bool] = Field(None, description="是否默认配置")
    content_types: Optional[Dict[str, ContentTypeConfig]] = Field(None, description="内容类型配置")
    visible_roles: Optional[List[str]] = Field(None, description="可见角色列表")
    play_settings: Optional[PlaySettings] = Field(None, description="播放设置")


class CultureWallConfigResponse(CultureWallConfigBase):
    """文化墙配置响应"""
    id: int
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
