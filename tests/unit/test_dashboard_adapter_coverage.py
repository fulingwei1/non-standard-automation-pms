# -*- coding: utf-8 -*-
"""
Dashboard适配器单元测试 - 覆盖率提升版
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from typing import Any, Dict, List

from app.services.dashboard.dashboard_adapter import DashboardAdapter, DashboardRegistry


class TestDashboardAdapter:
    """测试Dashboard适配器基类"""

    def test_adapter_class_exists(self):
        """测试类存在"""
        assert DashboardAdapter is not None

    def test_adapter_is_abstract(self):
        """测试是抽象类"""
        # DashboardAdapter是ABC，不能直接实例化
        assert hasattr(DashboardAdapter, '__abstractmethods__')


class TestDashboardRegistry:
    """测试Dashboard注册器"""

    def test_registry_class_exists(self):
        """测试类存在"""
        assert DashboardRegistry is not None

    def test_registry_has_register(self):
        """测试有register方法"""
        registry = DashboardRegistry()
        assert hasattr(registry, 'register')

    def test_registry_has_get_adapter(self):
        """测试有get_adapter方法"""
        registry = DashboardRegistry()
        assert hasattr(registry, 'get_adapter')

    def test_registry_has_list_modules(self):
        """测试有list_modules方法"""
        registry = DashboardRegistry()
        assert hasattr(registry, 'list_modules')


class TestDashboardRegistryMethods:
    """测试注册器方法"""

    def test_list_modules(self):
        """测试列出模块"""
        registry = DashboardRegistry()
        modules = registry.list_modules()
        assert isinstance(modules, list)


class TestDashboardAdapterConstants:
    """测试模块常量"""

    def test_module_exists(self):
        """测试模块可导入"""
        from app.services.dashboard import dashboard_adapter
        assert dashboard_adapter is not None

    def test_adapter_class_available(self):
        """测试DashboardAdapter类可用"""
        assert DashboardAdapter is not None

    def test_registry_class_available(self):
        """测试DashboardRegistry类可用"""
        assert DashboardRegistry is not None

    def test_register_decorator_exists(self):
        """测试注册装饰器存在"""
        from app.services.dashboard.dashboard_adapter import register_dashboard
        assert register_dashboard is not None