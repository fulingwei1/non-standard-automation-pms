# -*- coding: utf-8 -*-
"""
插件系统

提供可扩展的插件架构，支持：
- 插件注册和发现
- 插件生命周期管理
- 事件钩子系统
- 插件配置管理
"""

from .core import (
    Plugin,
    PluginConfig,
    PluginManager,
    PluginMetadata,
    PluginStatus,
    get_plugin_manager,
)
from .hooks import EventHook, HookManager, hook

__all__ = [
    # 核心
    "Plugin",
    "PluginConfig",
    "PluginManager",
    "PluginMetadata",
    "PluginStatus",
    "get_plugin_manager",
    # 钩子
    "EventHook",
    "HookManager",
    "hook",
]
