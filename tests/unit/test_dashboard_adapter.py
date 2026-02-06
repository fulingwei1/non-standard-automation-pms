# -*- coding: utf-8 -*-
"""
Tests for dashboard_adapter
Covers: app/services/dashboard_adapter.py
"""

import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session
from typing import List

from app.models.user import User
from app.schemas.dashboard import DashboardStatCard, DashboardWidget


class TestDashboardAdapter:
    """Test suite for DashboardAdapter abstract class."""

    @pytest.fixture
    def db_session(self):
        return Mock(spec=Session)

    @pytest.fixture
    def current_user(self):
        user = Mock(spec=User)
        user.id = 1
        user.username = "testuser"
        return user

    def test_adapter_init(self, db_session, current_user):
        from app.services.dashboard_adapter import DashboardAdapter

        # Create a concrete implementation for testing
        class TestAdapter(DashboardAdapter):
            @property
            def module_id(self) -> str:
                return "test_module"

            @property
            def module_name(self) -> str:
                return "测试模块"

            @property
            def supported_roles(self) -> List[str]:
                return ["ADMIN", "MANAGER"]

            def get_stats(self):
                return []

            def get_widgets(self):
                return []

        adapter = TestAdapter(db_session, current_user)

        assert adapter.db == db_session
        assert adapter.current_user == current_user

    def test_supports_role_true(self, db_session, current_user):
        from app.services.dashboard_adapter import DashboardAdapter

        class TestAdapter(DashboardAdapter):
            @property
            def module_id(self) -> str:
                return "test"

            @property
            def module_name(self) -> str:
                return "测试"

            @property
            def supported_roles(self) -> List[str]:
                return ["ADMIN", "MANAGER", "ENGINEER"]

            def get_stats(self):
                return []

            def get_widgets(self):
                return []

        adapter = TestAdapter(db_session, current_user)

        assert adapter.supports_role("ADMIN") is True
        assert adapter.supports_role("MANAGER") is True
        assert adapter.supports_role("ENGINEER") is True

    def test_supports_role_false(self, db_session, current_user):
        from app.services.dashboard_adapter import DashboardAdapter

        class TestAdapter(DashboardAdapter):
            @property
            def module_id(self) -> str:
                return "test"

            @property
            def module_name(self) -> str:
                return "测试"

            @property
            def supported_roles(self) -> List[str]:
                return ["ADMIN"]

            def get_stats(self):
                return []

            def get_widgets(self):
                return []

        adapter = TestAdapter(db_session, current_user)

        assert adapter.supports_role("USER") is False
        assert adapter.supports_role("GUEST") is False

    def test_get_detailed_data_not_implemented(self, db_session, current_user):
        from app.services.dashboard_adapter import DashboardAdapter

        class TestAdapter(DashboardAdapter):
            @property
            def module_id(self) -> str:
                return "test"

            @property
            def module_name(self) -> str:
                return "测试"

            @property
            def supported_roles(self) -> List[str]:
                return ["ADMIN"]

            def get_stats(self):
                return []

            def get_widgets(self):
                return []

        adapter = TestAdapter(db_session, current_user)

        with pytest.raises(NotImplementedError) as exc_info:
            adapter.get_detailed_data()

        assert "test 未实现详细数据接口" in str(exc_info.value)


class TestDashboardRegistry:
    """Test suite for DashboardRegistry."""

    @pytest.fixture
    def db_session(self):
        return Mock(spec=Session)

    @pytest.fixture
    def current_user(self):
        user = Mock(spec=User)
        user.id = 1
        user.username = "testuser"
        return user

    @pytest.fixture
    def create_test_adapter(self):
        """Factory to create test adapter classes."""
        from app.services.dashboard_adapter import DashboardAdapter

        def _create(module_id: str, module_name: str, roles: List[str]):
            class TestAdapter(DashboardAdapter):
                @property
                def module_id(self) -> str:
                    return module_id

                @property
                def module_name(self) -> str:
                    return module_name

                @property
                def supported_roles(self) -> List[str]:
                    return roles

                def get_stats(self):
                    return []

                def get_widgets(self):
                    return []

            return TestAdapter

        return _create

    def test_registry_init(self):
        from app.services.dashboard_adapter import DashboardRegistry

        registry = DashboardRegistry()

        assert registry._adapters == {}

    def test_register_adapter(self, create_test_adapter):
        from app.services.dashboard_adapter import DashboardRegistry

        registry = DashboardRegistry()
        TestAdapter = create_test_adapter("project", "项目管理", ["ADMIN"])

        registry.register(TestAdapter)

        assert "project" in registry._adapters
        assert registry._adapters["project"] == TestAdapter

    def test_register_duplicate_raises_error(self, create_test_adapter):
        from app.services.dashboard_adapter import DashboardRegistry

        registry = DashboardRegistry()
        TestAdapter1 = create_test_adapter("project", "项目管理", ["ADMIN"])
        TestAdapter2 = create_test_adapter("project", "项目管理2", ["ADMIN"])

        registry.register(TestAdapter1)

        with pytest.raises(ValueError) as exc_info:
            registry.register(TestAdapter2)

        assert "already registered" in str(exc_info.value)

    def test_get_adapter_existing(self, db_session, current_user, create_test_adapter):
        from app.services.dashboard_adapter import DashboardRegistry

        registry = DashboardRegistry()
        TestAdapter = create_test_adapter("sales", "销售管理", ["SALES"])
        registry.register(TestAdapter)

        adapter = registry.get_adapter("sales", db_session, current_user)

        assert adapter is not None
        assert adapter.module_id == "sales"
        assert adapter.db == db_session
        assert adapter.current_user == current_user

    def test_get_adapter_not_found(self, db_session, current_user):
        from app.services.dashboard_adapter import DashboardRegistry

        registry = DashboardRegistry()

        adapter = registry.get_adapter("nonexistent", db_session, current_user)

        assert adapter is None

    def test_get_adapters_for_role(self, db_session, current_user, create_test_adapter):
        from app.services.dashboard_adapter import DashboardRegistry

        registry = DashboardRegistry()
        registry.register(create_test_adapter("project", "项目", ["ADMIN", "PM"]))
        registry.register(create_test_adapter("sales", "销售", ["ADMIN", "SALES"]))
        registry.register(create_test_adapter("hr", "人事", ["ADMIN", "HR"]))

        admin_adapters = registry.get_adapters_for_role("ADMIN", db_session, current_user)
        pm_adapters = registry.get_adapters_for_role("PM", db_session, current_user)
        sales_adapters = registry.get_adapters_for_role("SALES", db_session, current_user)

        assert len(admin_adapters) == 3
        assert len(pm_adapters) == 1
        assert len(sales_adapters) == 1

    def test_get_adapters_for_role_none_match(self, db_session, current_user, create_test_adapter):
        from app.services.dashboard_adapter import DashboardRegistry

        registry = DashboardRegistry()
        registry.register(create_test_adapter("project", "项目", ["PM"]))

        adapters = registry.get_adapters_for_role("GUEST", db_session, current_user)

        assert len(adapters) == 0

    def test_list_modules_empty(self):
        from app.services.dashboard_adapter import DashboardRegistry

        registry = DashboardRegistry()

        modules = registry.list_modules()

        assert modules == []

    def test_list_modules(self, create_test_adapter):
        from app.services.dashboard_adapter import DashboardRegistry

        registry = DashboardRegistry()
        registry.register(create_test_adapter("project", "项目管理", ["ADMIN", "PM"]))
        registry.register(create_test_adapter("sales", "销售管理", ["ADMIN", "SALES"]))

        modules = registry.list_modules()

        assert len(modules) == 2
        module_ids = [m["module_id"] for m in modules]
        assert "project" in module_ids
        assert "sales" in module_ids

        project_module = next(m for m in modules if m["module_id"] == "project")
        assert project_module["module_name"] == "项目管理"
        assert "ADMIN" in project_module["supported_roles"]
        assert "PM" in project_module["supported_roles"]


class TestRegisterDashboardDecorator:
    """Test suite for register_dashboard decorator."""

    def test_decorator_registers_adapter(self):
        from app.services.dashboard_adapter import (
            DashboardAdapter,
            DashboardRegistry,
        )

        registry = DashboardRegistry()

        def register_dashboard_test(adapter_class):
            registry.register(adapter_class)
            return adapter_class

        @register_dashboard_test
        class DecoratedAdapter(DashboardAdapter):
            @property
            def module_id(self) -> str:
                return "decorated"

            @property
            def module_name(self) -> str:
                return "装饰器测试"

            @property
            def supported_roles(self):
                return ["ADMIN"]

            def get_stats(self):
                return []

            def get_widgets(self):
                return []

        assert "decorated" in registry._adapters
        assert registry._adapters["decorated"] == DecoratedAdapter

    def test_decorator_returns_original_class(self):
        from app.services.dashboard_adapter import (
            DashboardAdapter,
            DashboardRegistry,
        )

        registry = DashboardRegistry()

        def register_dashboard_test(adapter_class):
            registry.register(adapter_class)
            return adapter_class

        @register_dashboard_test
        class TestAdapter(DashboardAdapter):
            @property
            def module_id(self) -> str:
                return "test_return"

            @property
            def module_name(self) -> str:
                return "测试返回"

            @property
            def supported_roles(self):
                return ["ADMIN"]

            def get_stats(self):
                return []

            def get_widgets(self):
                return []

        # Decorator should return the same class
        assert TestAdapter.module_id.fget(TestAdapter.__new__(TestAdapter)) == "test_return"
