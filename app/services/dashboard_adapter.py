# -*- coding: utf-8 -*-
"""
统一工作台 Dashboard 适配器基类和注册表
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.dashboard import (
    DashboardStatCard,
    DashboardWidget,
    DetailedDashboardResponse,
)


class DashboardAdapter(ABC):
    """Dashboard 适配器基类

    每个模块的dashboard需要实现此接口，将原有数据转换为统一格式
    """

    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

    @property
    @abstractmethod
    def module_id(self) -> str:
        """模块ID"""
        pass

    @property
    @abstractmethod
    def module_name(self) -> str:
        """模块名称"""
        pass

    @property
    @abstractmethod
    def supported_roles(self) -> List[str]:
        """支持的角色列表"""
        pass

    @abstractmethod
    def get_stats(self) -> List[DashboardStatCard]:
        """获取统计卡片"""
        pass

    @abstractmethod
    def get_widgets(self) -> List[DashboardWidget]:
        """获取Widget列表"""
        pass

    def get_detailed_data(self) -> DetailedDashboardResponse:
        """获取详细数据（可选实现）"""
        raise NotImplementedError(f"{self.module_id} 未实现详细数据接口")

    def supports_role(self, role_code: str) -> bool:
        """检查是否支持指定角色"""
        return role_code in self.supported_roles


class DashboardRegistry:
    """Dashboard 注册表

    管理所有已注册的dashboard适配器
    """

    def __init__(self):
        self._adapters: Dict[str, type[DashboardAdapter]] = {}

    def register(self, adapter_class: type[DashboardAdapter]) -> None:
        """注册一个dashboard适配器

        Args:
            adapter_class: 适配器类（不是实例）
        """
        # 创建临时实例获取module_id
        temp_instance = adapter_class.__new__(adapter_class)
        module_id = adapter_class.module_id.fget(temp_instance)

        if module_id in self._adapters:
            raise ValueError(f"Dashboard adapter '{module_id}' already registered")

        self._adapters[module_id] = adapter_class

    def get_adapter(
        self, module_id: str, db: Session, current_user: User
    ) -> Optional[DashboardAdapter]:
        """获取指定模块的适配器实例

        Args:
            module_id: 模块ID
            db: 数据库会话
            current_user: 当前用户

        Returns:
            适配器实例，如果未注册则返回None
        """
        adapter_class = self._adapters.get(module_id)
        if adapter_class is None:
            return None

        return adapter_class(db, current_user)

    def get_adapters_for_role(
        self, role_code: str, db: Session, current_user: User
    ) -> List[DashboardAdapter]:
        """获取指定角色的所有适配器

        Args:
            role_code: 角色代码
            db: 数据库会话
            current_user: 当前用户

        Returns:
            适配器实例列表
        """
        adapters = []
        for adapter_class in self._adapters.values():
            # 创建临时实例检查角色支持
            temp = adapter_class.__new__(adapter_class)
            if role_code in adapter_class.supported_roles.fget(temp):
                adapters.append(adapter_class(db, current_user))

        return adapters

    def list_modules(self) -> List[Dict[str, Any]]:
        """列出所有已注册的模块

        Returns:
            模块信息列表
        """
        modules = []
        for adapter_class in self._adapters.values():
            temp = adapter_class.__new__(adapter_class)
            modules.append({
                "module_id": adapter_class.module_id.fget(temp),
                "module_name": adapter_class.module_name.fget(temp),
                "supported_roles": adapter_class.supported_roles.fget(temp),
            })
        return modules


# 全局注册表实例
dashboard_registry = DashboardRegistry()


# ==================== 装饰器：注册适配器 ====================

def register_dashboard(adapter_class: type[DashboardAdapter]) -> type[DashboardAdapter]:
    """装饰器：注册dashboard适配器

    用法：
        @register_dashboard
        class MyDashboardAdapter(DashboardAdapter):
            ...
    """
    dashboard_registry.register(adapter_class)
    return adapter_class
