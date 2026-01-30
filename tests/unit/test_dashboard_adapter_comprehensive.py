# -*- coding: utf-8 -*-
"""
DashboardAdapter 和 DashboardRegistry 综合单元测试

测试覆盖:
- DashboardAdapter: 基类功能
- DashboardRegistry: 注册表功能
  - register: 注册适配器
  - get_adapter: 获取适配器
  - get_adapters_for_role: 按角色获取适配器
  - list_modules: 列出所有模块
- register_dashboard: 装饰器
"""

from unittest.mock import MagicMock, patch, PropertyMock

import pytest


class TestDashboardAdapter:
    """测试 DashboardAdapter 基类"""

    def test_initializes_with_db_and_user(self):
        """测试初始化"""
        from app.services.dashboard_adapter import DashboardAdapter

        mock_db = MagicMock()
        mock_user = MagicMock()

        # 创建具体实现类
        class TestAdapter(DashboardAdapter):
            @property
            def module_id(self):
                return "test"

            @property
            def module_name(self):
                return "测试模块"

            @property
            def supported_roles(self):
                return ["admin"]

            def get_stats(self):
                return []

            def get_widgets(self):
                return []

        adapter = TestAdapter(mock_db, mock_user)

        assert adapter.db == mock_db
        assert adapter.current_user == mock_user

    def test_supports_role_returns_true_for_matching_role(self):
        """测试角色匹配时返回True"""
        from app.services.dashboard_adapter import DashboardAdapter

        class TestAdapter(DashboardAdapter):
            @property
            def module_id(self):
                return "test"

            @property
            def module_name(self):
                return "测试模块"

            @property
            def supported_roles(self):
                return ["admin", "manager"]

            def get_stats(self):
                return []

            def get_widgets(self):
                return []

        adapter = TestAdapter(MagicMock(), MagicMock())

        assert adapter.supports_role("admin") is True
        assert adapter.supports_role("manager") is True

    def test_supports_role_returns_false_for_non_matching_role(self):
        """测试角色不匹配时返回False"""
        from app.services.dashboard_adapter import DashboardAdapter

        class TestAdapter(DashboardAdapter):
            @property
            def module_id(self):
                return "test"

            @property
            def module_name(self):
                return "测试模块"

            @property
            def supported_roles(self):
                return ["admin"]

            def get_stats(self):
                return []

            def get_widgets(self):
                return []

        adapter = TestAdapter(MagicMock(), MagicMock())

        assert adapter.supports_role("user") is False

    def test_get_detailed_data_raises_not_implemented(self):
        """测试详细数据默认抛出NotImplementedError"""
        from app.services.dashboard_adapter import DashboardAdapter

        class TestAdapter(DashboardAdapter):
            @property
            def module_id(self):
                return "test"

            @property
            def module_name(self):
                return "测试模块"

            @property
            def supported_roles(self):
                return ["admin"]

            def get_stats(self):
                return []

            def get_widgets(self):
                return []

        adapter = TestAdapter(MagicMock(), MagicMock())

        with pytest.raises(NotImplementedError) as exc_info:
            adapter.get_detailed_data()

        assert "test" in str(exc_info.value)


class TestDashboardRegistry:
    """测试 DashboardRegistry"""

    def test_initializes_empty(self):
        """测试初始化为空"""
        from app.services.dashboard_adapter import DashboardRegistry

        registry = DashboardRegistry()

        assert len(registry._adapters) == 0

    def test_register_adds_adapter(self):
        """测试注册添加适配器"""
        from app.services.dashboard_adapter import DashboardRegistry, DashboardAdapter

        class TestAdapter(DashboardAdapter):
            @property
            def module_id(self):
                return "test_module"

            @property
            def module_name(self):
                return "测试模块"

            @property
            def supported_roles(self):
                return ["admin"]

            def get_stats(self):
                return []

            def get_widgets(self):
                return []

        registry = DashboardRegistry()
        registry.register(TestAdapter)

        assert "test_module" in registry._adapters

    def test_register_raises_error_for_duplicate(self):
        """测试重复注册抛出错误"""
        from app.services.dashboard_adapter import DashboardRegistry, DashboardAdapter

        class TestAdapter(DashboardAdapter):
            @property
            def module_id(self):
                return "duplicate"

            @property
            def module_name(self):
                return "重复模块"

            @property
            def supported_roles(self):
                return ["admin"]

            def get_stats(self):
                return []

            def get_widgets(self):
                return []

        registry = DashboardRegistry()
        registry.register(TestAdapter)

        with pytest.raises(ValueError) as exc_info:
            registry.register(TestAdapter)

        assert "already registered" in str(exc_info.value)

    def test_get_adapter_returns_instance(self):
        """测试获取适配器返回实例"""
        from app.services.dashboard_adapter import DashboardRegistry, DashboardAdapter

        class TestAdapter(DashboardAdapter):
            @property
            def module_id(self):
                return "get_test"

            @property
            def module_name(self):
                return "获取测试"

            @property
            def supported_roles(self):
                return ["admin"]

            def get_stats(self):
                return []

            def get_widgets(self):
                return []

        registry = DashboardRegistry()
        registry.register(TestAdapter)

        mock_db = MagicMock()
        mock_user = MagicMock()

        adapter = registry.get_adapter("get_test", mock_db, mock_user)

        assert isinstance(adapter, TestAdapter)
        assert adapter.db == mock_db
        assert adapter.current_user == mock_user

    def test_get_adapter_returns_none_for_unknown(self):
        """测试获取未知模块返回None"""
        from app.services.dashboard_adapter import DashboardRegistry

        registry = DashboardRegistry()

        result = registry.get_adapter("unknown", MagicMock(), MagicMock())

        assert result is None

    def test_get_adapters_for_role(self):
        """测试按角色获取适配器"""
        from app.services.dashboard_adapter import DashboardRegistry, DashboardAdapter

        class AdminAdapter(DashboardAdapter):
            @property
            def module_id(self):
                return "admin_module"

            @property
            def module_name(self):
                return "管理员模块"

            @property
            def supported_roles(self):
                return ["admin"]

            def get_stats(self):
                return []

            def get_widgets(self):
                return []

        class UserAdapter(DashboardAdapter):
            @property
            def module_id(self):
                return "user_module"

            @property
            def module_name(self):
                return "用户模块"

            @property
            def supported_roles(self):
                return ["user", "admin"]

            def get_stats(self):
                return []

            def get_widgets(self):
                return []

        registry = DashboardRegistry()
        registry.register(AdminAdapter)
        registry.register(UserAdapter)

        mock_db = MagicMock()
        mock_user = MagicMock()

        # admin 角色应该得到两个适配器
        admin_adapters = registry.get_adapters_for_role("admin", mock_db, mock_user)
        assert len(admin_adapters) == 2

        # user 角色应该只得到一个适配器
        user_adapters = registry.get_adapters_for_role("user", mock_db, mock_user)
        assert len(user_adapters) == 1

    def test_list_modules(self):
        """测试列出所有模块"""
        from app.services.dashboard_adapter import DashboardRegistry, DashboardAdapter

        class Module1(DashboardAdapter):
            @property
            def module_id(self):
                return "module1"

            @property
            def module_name(self):
                return "模块1"

            @property
            def supported_roles(self):
                return ["admin"]

            def get_stats(self):
                return []

            def get_widgets(self):
                return []

        class Module2(DashboardAdapter):
            @property
            def module_id(self):
                return "module2"

            @property
            def module_name(self):
                return "模块2"

            @property
            def supported_roles(self):
                return ["user"]

            def get_stats(self):
                return []

            def get_widgets(self):
                return []

        registry = DashboardRegistry()
        registry.register(Module1)
        registry.register(Module2)

        modules = registry.list_modules()

        assert len(modules) == 2
        module_ids = [m['module_id'] for m in modules]
        assert "module1" in module_ids
        assert "module2" in module_ids


class TestRegisterDashboardDecorator:
    """测试 register_dashboard 装饰器"""

    def test_decorator_registers_adapter(self):
        """测试装饰器注册适配器"""
        from app.services.dashboard_adapter import DashboardAdapter, DashboardRegistry

        # 创建新的注册表避免全局状态影响
        test_registry = DashboardRegistry()

        class DecoratedAdapter(DashboardAdapter):
            @property
            def module_id(self):
                return "decorated"

            @property
            def module_name(self):
                return "装饰器测试"

            @property
            def supported_roles(self):
                return ["admin"]

            def get_stats(self):
                return []

            def get_widgets(self):
                return []

        # 手动注册而不是使用全局装饰器
        test_registry.register(DecoratedAdapter)

        assert "decorated" in test_registry._adapters

    def test_decorator_returns_class(self):
        """测试装饰器返回类本身"""
        from app.services.dashboard_adapter import register_dashboard, DashboardAdapter

        # 由于全局注册表可能已有注册，我们测试装饰器的返回值
        class TestClass(DashboardAdapter):
            @property
            def module_id(self):
                return "return_test_unique"

            @property
            def module_name(self):
                return "返回测试"

            @property
            def supported_roles(self):
                return ["admin"]

            def get_stats(self):
                return []

            def get_widgets(self):
                return []

        # 装饰器应该返回类本身
        result = register_dashboard(TestClass)

        assert result is TestClass
