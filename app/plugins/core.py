# -*- coding: utf-8 -*-
"""
插件系统核心

定义插件的基础架构：
- Plugin: 插件基类
- PluginManager: 插件管理器
- PluginConfig: 插件配置
"""

import importlib
import inspect
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


class PluginStatus(str, Enum):
    """插件状态"""

    DISCOVERED = "discovered"  # 已发现
    LOADED = "loaded"  # 已加载
    ENABLED = "enabled"  # 已启用
    DISABLED = "disabled"  # 已禁用
    ERROR = "error"  # 错误


@dataclass
class PluginMetadata:
    """插件元数据"""

    name: str  # 插件名称
    version: str  # 版本号
    description: str = ""  # 描述
    author: str = ""  # 作者
    dependencies: List[str] = field(default_factory=list)  # 依赖的其他插件
    required_permissions: List[str] = field(default_factory=list)  # 所需权限
    settings_schema: Optional[Dict[str, Any]] = None  # 配置 schema


@dataclass
class PluginConfig:
    """插件配置"""

    enabled: bool = True  # 是否启用
    settings: Dict[str, Any] = field(default_factory=dict)  # 插件设置
    priority: int = 100  # 优先级（数字越小优先级越高）


class Plugin(ABC):
    """
    插件基类

    所有插件必须继承此类并实现必要的方法。

    生命周期：
    1. __init__: 插件实例化
    2. on_load: 插件加载（注册钩子、初始化资源）
    3. on_enable: 插件启用
    4. on_disable: 插件禁用
    5. on_unload: 插件卸载（清理资源）

    Example:
        class MyPlugin(Plugin):
            @property
            def metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="my_plugin",
                    version="1.0.0",
                    description="我的插件",
                )

            def on_load(self) -> None:
                # 注册钩子
                self.hook_manager.register("contract.created", self.on_contract_created)

            def on_contract_created(self, contract):
                # 处理合同创建事件
                pass
    """

    def __init__(self):
        self.status = PluginStatus.DISCOVERED
        self.config = PluginConfig()
        self._hook_manager = None
        self._db = None

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """返回插件元数据"""
        pass

    @property
    def name(self) -> str:
        """插件名称"""
        return self.metadata.name

    @property
    def version(self) -> str:
        """插件版本"""
        return self.metadata.version

    @property
    def hook_manager(self):
        """获取钩子管理器"""
        return self._hook_manager

    @hook_manager.setter
    def hook_manager(self, value):
        """设置钩子管理器"""
        self._hook_manager = value

    @property
    def db(self):
        """获取数据库会话"""
        return self._db

    @db.setter
    def db(self, value):
        """设置数据库会话"""
        self._db = value

    def on_load(self) -> None:
        """
        插件加载时调用

        在此方法中：
        - 注册事件钩子
        - 初始化资源
        - 验证依赖
        """
        pass

    def on_enable(self) -> None:
        """
        插件启用时调用

        在此方法中：
        - 激活功能
        - 开始监听事件
        """
        pass

    def on_disable(self) -> None:
        """
        插件禁用时调用

        在此方法中：
        - 停止功能
        - 取消事件监听
        """
        pass

    def on_unload(self) -> None:
        """
        插件卸载时调用

        在此方法中：
        - 清理资源
        - 关闭连接
        """
        pass

    def get_settings(self) -> Dict[str, Any]:
        """获取插件设置"""
        return self.config.settings

    def update_settings(self, settings: Dict[str, Any]) -> None:
        """更新插件设置"""
        self.config.settings.update(settings)

    def __repr__(self) -> str:
        return f"<Plugin {self.name} v{self.version} ({self.status.value})>"


class PluginManager:
    """
    插件管理器

    负责插件的发现、加载、启用/禁用、卸载等生命周期管理。

    Usage:
        manager = PluginManager()
        manager.discover_plugins("/path/to/plugins")
        manager.load_all()
        manager.enable_all()
    """

    def __init__(self, plugin_dir: Optional[str] = None):
        self._plugins: Dict[str, Plugin] = {}
        self._plugin_classes: Dict[str, Type[Plugin]] = {}
        self._hook_manager = None
        self._db = None
        self.plugin_dir = plugin_dir or self._get_default_plugin_dir()

    def _get_default_plugin_dir(self) -> str:
        """获取默认插件目录"""
        # 默认为 app/plugins/installed
        return os.path.join(os.path.dirname(__file__), "installed")

    @property
    def hook_manager(self):
        """获取钩子管理器"""
        if self._hook_manager is None:
            from .hooks import HookManager

            self._hook_manager = HookManager()
        return self._hook_manager

    @hook_manager.setter
    def hook_manager(self, value):
        """设置钩子管理器"""
        self._hook_manager = value

    def set_db(self, db) -> None:
        """设置数据库会话"""
        self._db = db
        # 更新所有已加载插件的数据库会话
        for plugin in self._plugins.values():
            plugin.db = db

    def discover_plugins(self, plugin_dir: Optional[str] = None) -> List[str]:
        """
        发现插件目录中的所有插件

        Args:
            plugin_dir: 插件目录路径

        Returns:
            发现的插件名称列表
        """
        plugin_dir = plugin_dir or self.plugin_dir
        discovered = []

        if not os.path.exists(plugin_dir):
            os.makedirs(plugin_dir, exist_ok=True)
            logger.info(f"创建插件目录: {plugin_dir}")
            return discovered

        # 遍历插件目录
        for item in os.listdir(plugin_dir):
            item_path = os.path.join(plugin_dir, item)

            # 跳过非目录和特殊目录
            if not os.path.isdir(item_path) or item.startswith("_"):
                continue

            # 检查是否有 __init__.py
            init_file = os.path.join(item_path, "__init__.py")
            if not os.path.exists(init_file):
                continue

            try:
                # 动态导入插件模块
                module_name = f"app.plugins.installed.{item}"
                module = importlib.import_module(module_name)

                # 查找 Plugin 子类
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, Plugin) and obj is not Plugin:
                        self._plugin_classes[item] = obj
                        discovered.append(item)
                        logger.info(f"发现插件: {item} ({obj.__name__})")
                        break

            except Exception as e:
                logger.error(f"发现插件 {item} 失败: {e}")

        return discovered

    def load_plugin(self, name: str) -> Optional[Plugin]:
        """
        加载指定插件

        Args:
            name: 插件名称

        Returns:
            加载的插件实例，失败返回 None
        """
        if name in self._plugins:
            logger.warning(f"插件 {name} 已加载")
            return self._plugins[name]

        if name not in self._plugin_classes:
            logger.error(f"插件 {name} 未发现，请先调用 discover_plugins()")
            return None

        try:
            # 实例化插件
            plugin_class = self._plugin_classes[name]
            plugin = plugin_class()

            # 设置钩子管理器和数据库
            plugin.hook_manager = self.hook_manager
            plugin.db = self._db

            # 调用加载钩子
            plugin.on_load()
            plugin.status = PluginStatus.LOADED

            self._plugins[name] = plugin
            logger.info(f"加载插件: {plugin}")
            return plugin

        except Exception as e:
            logger.error(f"加载插件 {name} 失败: {e}", exc_info=True)
            return None

    def load_all(self) -> Dict[str, Plugin]:
        """加载所有发现的插件"""
        for name in self._plugin_classes:
            self.load_plugin(name)
        return self._plugins

    def enable_plugin(self, name: str) -> bool:
        """
        启用指定插件

        Args:
            name: 插件名称

        Returns:
            是否成功
        """
        plugin = self._plugins.get(name)
        if not plugin:
            logger.error(f"插件 {name} 未加载")
            return False

        if plugin.status == PluginStatus.ENABLED:
            logger.warning(f"插件 {name} 已启用")
            return True

        try:
            # 检查依赖
            for dep in plugin.metadata.dependencies:
                dep_plugin = self._plugins.get(dep)
                if not dep_plugin or dep_plugin.status != PluginStatus.ENABLED:
                    logger.error(f"插件 {name} 依赖的插件 {dep} 未启用")
                    return False

            plugin.on_enable()
            plugin.status = PluginStatus.ENABLED
            plugin.config.enabled = True
            logger.info(f"启用插件: {plugin}")
            return True

        except Exception as e:
            logger.error(f"启用插件 {name} 失败: {e}", exc_info=True)
            plugin.status = PluginStatus.ERROR
            return False

    def enable_all(self) -> int:
        """启用所有已加载的插件"""
        enabled_count = 0
        # 按优先级排序
        sorted_plugins = sorted(
            self._plugins.items(), key=lambda x: x[1].config.priority
        )
        for name, _ in sorted_plugins:
            if self.enable_plugin(name):
                enabled_count += 1
        return enabled_count

    def disable_plugin(self, name: str) -> bool:
        """
        禁用指定插件

        Args:
            name: 插件名称

        Returns:
            是否成功
        """
        plugin = self._plugins.get(name)
        if not plugin:
            logger.error(f"插件 {name} 未加载")
            return False

        if plugin.status == PluginStatus.DISABLED:
            logger.warning(f"插件 {name} 已禁用")
            return True

        try:
            plugin.on_disable()
            plugin.status = PluginStatus.DISABLED
            plugin.config.enabled = False
            logger.info(f"禁用插件: {plugin}")
            return True

        except Exception as e:
            logger.error(f"禁用插件 {name} 失败: {e}", exc_info=True)
            return False

    def unload_plugin(self, name: str) -> bool:
        """
        卸载指定插件

        Args:
            name: 插件名称

        Returns:
            是否成功
        """
        plugin = self._plugins.get(name)
        if not plugin:
            logger.error(f"插件 {name} 未加载")
            return False

        try:
            # 先禁用
            if plugin.status == PluginStatus.ENABLED:
                self.disable_plugin(name)

            # 卸载
            plugin.on_unload()
            del self._plugins[name]
            logger.info(f"卸载插件: {name}")
            return True

        except Exception as e:
            logger.error(f"卸载插件 {name} 失败: {e}", exc_info=True)
            return False

    def get_plugin(self, name: str) -> Optional[Plugin]:
        """获取指定插件实例"""
        return self._plugins.get(name)

    def get_all_plugins(self) -> Dict[str, Plugin]:
        """获取所有已加载的插件"""
        return self._plugins.copy()

    def get_plugin_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取插件信息"""
        plugin = self._plugins.get(name)
        if not plugin:
            return None

        return {
            "name": plugin.name,
            "version": plugin.version,
            "description": plugin.metadata.description,
            "author": plugin.metadata.author,
            "status": plugin.status.value,
            "enabled": plugin.config.enabled,
            "priority": plugin.config.priority,
            "dependencies": plugin.metadata.dependencies,
            "settings": plugin.get_settings(),
        }

    def list_plugins(self) -> List[Dict[str, Any]]:
        """列出所有插件信息"""
        return [
            self.get_plugin_info(name)
            for name in self._plugins
            if self.get_plugin_info(name)
        ]


# 全局插件管理器实例
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """获取全局插件管理器实例"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager
