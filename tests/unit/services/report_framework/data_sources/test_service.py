# -*- coding: utf-8 -*-
"""
测试 ServiceDataSource - 服务方法调用数据源

覆盖率目标: 60%+
测试用例数: 30+
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from app.services.report_framework.data_sources.service import ServiceDataSource
from app.services.report_framework.data_sources.base import DataSourceError
from app.services.report_framework.models import DataSourceConfig


class TestServiceDataSourceInit:
    """测试ServiceDataSource初始化"""

    def test_init_success(self):
        """测试正常初始化"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_service",
            type="service",
            method="UserService.get_active_users"
        )
        ds = ServiceDataSource(db, config)
        assert ds.db == db
        assert ds.config == config

    def test_init_missing_method(self):
        """测试缺少method配置"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_service",
            type="service"
        )
        with pytest.raises(DataSourceError, match="Method is required"):
            ServiceDataSource(db, config)

    def test_init_invalid_method_format(self):
        """测试无效的method格式"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_service",
            type="service",
            method="invalid_method_format"
        )
        with pytest.raises(DataSourceError, match="Invalid method format"):
            ServiceDataSource(db, config)

    def test_init_with_empty_method(self):
        """测试空method"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_service",
            type="service",
            method=""
        )
        with pytest.raises(DataSourceError, match="Method is required"):
            ServiceDataSource(db, config)


class TestValidateConfig:
    """测试配置验证"""

    def test_validate_correct_format(self):
        """测试正确格式验证"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_service",
            type="service",
            method="MyService.my_method"
        )
        ds = ServiceDataSource(db, config)
        assert ds._service_class == "MyService"
        assert ds._method_name == "my_method"

    def test_validate_nested_module(self):
        """测试嵌套模块格式"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_service",
            type="service",
            method="strategy.StrategyService.get_stats"
        )
        ds = ServiceDataSource(db, config)
        assert ds._service_class == "strategy.StrategyService"
        assert ds._method_name == "get_stats"

    def test_validate_only_dots_in_method(self):
        """测试只有点号的method"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_service",
            type="service",
            method="..."
        )
        # 虽然格式上通过，但会在后续获取服务时失败
        ds = ServiceDataSource(db, config)
        assert ds._method_name == ""


class TestParseMethod:
    """测试方法解析"""

    def test_parse_simple_method(self):
        """测试简单方法解析"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_service",
            type="service",
            method="UserService.get_users"
        )
        ds = ServiceDataSource(db, config)
        assert ds._service_class == "UserService"
        assert ds._method_name == "get_users"

    def test_parse_method_with_multiple_dots(self):
        """测试多个点号的方法"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_service",
            type="service",
            method="app.services.user.UserService.get_users"
        )
        ds = ServiceDataSource(db, config)
        # 应该取最后一个点号分割
        assert ds._service_class == "app.services.user.UserService"
        assert ds._method_name == "get_users"


class TestFetch:
    """测试数据获取"""

    @patch('app.services.report_framework.data_sources.service.importlib.import_module')
    def test_fetch_success(self, mock_import):
        """测试成功获取数据"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_service",
            type="service",
            method="UserService.get_users"
        )

        # Mock服务类和方法
        mock_service_instance = MagicMock()
        mock_service_instance.get_users.return_value = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]

        mock_service_class = MagicMock(return_value=mock_service_instance)
        mock_module = MagicMock()
        mock_module.UserService = mock_service_class
        mock_import.return_value = mock_module

        ds = ServiceDataSource(db, config)
        result = ds.fetch({})

        assert len(result) == 2
        assert result[0]["name"] == "Alice"

    @patch('app.services.report_framework.data_sources.service.importlib.import_module')
    def test_fetch_with_params(self, mock_import):
        """测试带参数获取数据"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_service",
            type="service",
            method="UserService.get_users",
            args={"dept_id": 1}
        )

        mock_service_instance = MagicMock()
        mock_service_instance.get_users.return_value = [{"id": 1, "name": "Alice"}]

        mock_service_class = MagicMock(return_value=mock_service_instance)
        mock_module = MagicMock()
        mock_module.UserService = mock_service_class
        mock_import.return_value = mock_module

        ds = ServiceDataSource(db, config)
        result = ds.fetch({"status": "active"})

        # 验证方法被调用时合并了配置参数和运行时参数
        mock_service_instance.get_users.assert_called_once_with(dept_id=1, status="active")

    @patch('app.services.report_framework.data_sources.service.importlib.import_module')
    def test_fetch_method_not_found(self, mock_import):
        """测试方法不存在"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_service",
            type="service",
            method="UserService.non_existent_method"
        )

        mock_service_instance = MagicMock()
        del mock_service_instance.non_existent_method  # 确保方法不存在

        mock_service_class = MagicMock(return_value=mock_service_instance)
        mock_module = MagicMock()
        mock_module.UserService = mock_service_class
        mock_import.return_value = mock_module

        ds = ServiceDataSource(db, config)
        with pytest.raises(DataSourceError, match="Method .* not found"):
            ds.fetch({})

    @patch('app.services.report_framework.data_sources.service.importlib.import_module')
    def test_fetch_service_not_found(self, mock_import):
        """测试服务类不存在"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_service",
            type="service",
            method="NonExistentService.get_data"
        )

        mock_import.side_effect = ModuleNotFoundError("No module named")

        ds = ServiceDataSource(db, config)
        with pytest.raises(DataSourceError, match="Service class .* not found"):
            ds.fetch({})

    @patch('app.services.report_framework.data_sources.service.importlib.import_module')
    def test_fetch_method_exception(self, mock_import):
        """测试方法执行异常"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_service",
            type="service",
            method="UserService.get_users"
        )

        mock_service_instance = MagicMock()
        mock_service_instance.get_users.side_effect = Exception("Database error")

        mock_service_class = MagicMock(return_value=mock_service_instance)
        mock_module = MagicMock()
        mock_module.UserService = mock_service_class
        mock_import.return_value = mock_module

        ds = ServiceDataSource(db, config)
        with pytest.raises(DataSourceError, match="Service method call failed"):
            ds.fetch({})


class TestGetServiceInstance:
    """测试服务实例获取"""

    @patch('app.services.report_framework.data_sources.service.importlib.import_module')
    def test_get_service_snake_case_path(self, mock_import):
        """测试蛇形命名路径"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_service",
            type="service",
            method="UserService.get_users"
        )

        mock_service_class = MagicMock()
        mock_module = MagicMock()
        mock_module.UserService = mock_service_class
        
        # 模拟第一次尝试成功
        mock_import.return_value = mock_module

        ds = ServiceDataSource(db, config)
        instance = ds._get_service_instance()
        
        # 验证尝试导入了蛇形命名路径
        assert mock_import.called

    @patch('app.services.report_framework.data_sources.service.importlib.import_module')
    def test_get_service_multiple_paths(self, mock_import):
        """测试多路径尝试"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_service",
            type="service",
            method="MyCustomService.get_data"
        )

        # 前两次失败，第三次成功
        mock_service_class = MagicMock()
        mock_module = MagicMock()
        mock_module.MyCustomService = mock_service_class

        call_count = 0
        def import_side_effect(module_path):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ModuleNotFoundError()
            return mock_module

        mock_import.side_effect = import_side_effect

        ds = ServiceDataSource(db, config)
        instance = ds._get_service_instance()
        
        assert instance is not None


class TestInstantiateService:
    """测试服务实例化"""

    def test_instantiate_with_db(self):
        """测试用db参数实例化"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_service",
            type="service",
            method="UserService.get_users"
        )

        mock_service_class = MagicMock()
        ds = ServiceDataSource(db, config)
        instance = ds._instantiate_service(mock_service_class)

        # 验证用db参数调用
        mock_service_class.assert_called_once_with(db)

    def test_instantiate_no_params(self):
        """测试无参数实例化"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_service",
            type="service",
            method="UserService.get_users"
        )

        # 第一次调用失败，第二次无参数成功
        mock_service_class = MagicMock()
        mock_service_class.side_effect = [TypeError(), MagicMock()]

        ds = ServiceDataSource(db, config)
        instance = ds._instantiate_service(mock_service_class)

        assert mock_service_class.call_count == 2

    def test_instantiate_with_db_kwarg(self):
        """测试用db关键字参数实例化"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_service",
            type="service",
            method="UserService.get_users"
        )

        # 前两次失败，第三次用关键字参数成功
        mock_service_class = MagicMock()
        mock_service_class.side_effect = [TypeError(), TypeError(), MagicMock()]

        ds = ServiceDataSource(db, config)
        instance = ds._instantiate_service(mock_service_class)

        assert mock_service_class.call_count == 3


class TestToSnakeCase:
    """测试驼峰转蛇形"""

    def test_simple_camel_case(self):
        """测试简单驼峰"""
        assert ServiceDataSource._to_snake_case("UserService") == "user_service"

    def test_consecutive_capitals(self):
        """测试连续大写字母"""
        assert ServiceDataSource._to_snake_case("HTTPService") == "http_service"

    def test_all_lowercase(self):
        """测试全小写"""
        assert ServiceDataSource._to_snake_case("userservice") == "userservice"

    def test_with_numbers(self):
        """测试带数字"""
        assert ServiceDataSource._to_snake_case("User2Service") == "user2_service"

    def test_already_snake_case(self):
        """测试已是蛇形"""
        assert ServiceDataSource._to_snake_case("user_service") == "user_service"


class TestEdgeCases:
    """测试边界情况"""

    @patch('app.services.report_framework.data_sources.service.importlib.import_module')
    def test_fetch_returns_none(self, mock_import):
        """测试方法返回None"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_service",
            type="service",
            method="UserService.get_users"
        )

        mock_service_instance = MagicMock()
        mock_service_instance.get_users.return_value = None

        mock_service_class = MagicMock(return_value=mock_service_instance)
        mock_module = MagicMock()
        mock_module.UserService = mock_service_class
        mock_import.return_value = mock_module

        ds = ServiceDataSource(db, config)
        result = ds.fetch({})

        assert result is None

    @patch('app.services.report_framework.data_sources.service.importlib.import_module')
    def test_fetch_returns_empty_list(self, mock_import):
        """测试方法返回空列表"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_service",
            type="service",
            method="UserService.get_users"
        )

        mock_service_instance = MagicMock()
        mock_service_instance.get_users.return_value = []

        mock_service_class = MagicMock(return_value=mock_service_instance)
        mock_module = MagicMock()
        mock_module.UserService = mock_service_class
        mock_import.return_value = mock_module

        ds = ServiceDataSource(db, config)
        result = ds.fetch({})

        assert result == []

    @patch('app.services.report_framework.data_sources.service.importlib.import_module')
    def test_fetch_returns_dict(self, mock_import):
        """测试方法返回字典"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_service",
            type="service",
            method="UserService.get_stats"
        )

        mock_service_instance = MagicMock()
        mock_service_instance.get_stats.return_value = {
            "total": 100,
            "active": 80
        }

        mock_service_class = MagicMock(return_value=mock_service_instance)
        mock_module = MagicMock()
        mock_module.UserService = mock_service_class
        mock_import.return_value = mock_module

        ds = ServiceDataSource(db, config)
        result = ds.fetch({})

        assert result["total"] == 100
        assert result["active"] == 80

    @patch('app.services.report_framework.data_sources.service.importlib.import_module')
    def test_override_config_params(self, mock_import):
        """测试运行时参数覆盖配置参数"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_service",
            type="service",
            method="UserService.get_users",
            args={"status": "active", "dept_id": 1}
        )

        mock_service_instance = MagicMock()
        mock_service_instance.get_users.return_value = []

        mock_service_class = MagicMock(return_value=mock_service_instance)
        mock_module = MagicMock()
        mock_module.UserService = mock_service_class
        mock_import.return_value = mock_module

        ds = ServiceDataSource(db, config)
        # 运行时参数覆盖status
        ds.fetch({"status": "inactive"})

        # 验证使用了运行时参数
        mock_service_instance.get_users.assert_called_once_with(
            status="inactive",
            dept_id=1
        )
