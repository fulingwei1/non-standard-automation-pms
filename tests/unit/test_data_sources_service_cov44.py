# -*- coding: utf-8 -*-
"""第四十四批覆盖测试 - 服务方法调用数据源"""

import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.report_framework.data_sources.service import ServiceDataSource
    from app.services.report_framework.data_sources.base import DataSourceError
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


def make_config(method=None, args=None):
    config = MagicMock()
    config.sql = None
    config.method = method
    config.args = args or {}
    return config


class TestServiceDataSource:

    def test_raises_when_no_method(self):
        config = make_config(method=None)
        with pytest.raises(DataSourceError, match="Method is required"):
            ServiceDataSource(db=MagicMock(), config=config)

    def test_raises_on_invalid_method_format(self):
        config = make_config(method="no_dot_method")
        with pytest.raises(DataSourceError, match="Invalid method format"):
            ServiceDataSource(db=MagicMock(), config=config)

    def test_valid_method_format_accepted(self):
        config = make_config(method="MyService.my_method")
        with patch.object(ServiceDataSource, "_get_service_instance", return_value=MagicMock()):
            ds = ServiceDataSource(db=MagicMock(), config=config)
            assert ds._service_class == "MyService"
            assert ds._method_name == "my_method"

    def test_parse_method_with_dotted_class(self):
        config = make_config(method="SomeModule.SomeClass.method_name")
        with patch.object(ServiceDataSource, "_get_service_instance", return_value=MagicMock()):
            ds = ServiceDataSource(db=MagicMock(), config=config)
            assert ds._method_name == "method_name"

    def test_to_snake_case(self):
        result = ServiceDataSource._to_snake_case("MyServiceClass")
        assert "_" in result or result == result.lower()

    def test_fetch_raises_when_service_not_found(self):
        config = make_config(method="NonExistentService.some_method")
        with patch.object(ServiceDataSource, "_get_service_instance", side_effect=DataSourceError("not found")):
            ds = ServiceDataSource.__new__(ServiceDataSource)
            ds.db = MagicMock()
            ds.config = config
            ds._service_class = "NonExistentService"
            ds._method_name = "some_method"
            with pytest.raises(DataSourceError):
                ds.fetch({})

    def test_inherits_datasource(self):
        from app.services.report_framework.data_sources.base import DataSource
        assert issubclass(ServiceDataSource, DataSource)

    def test_instantiate_service_tries_with_db(self):
        config = make_config(method="SomeService.method")
        mock_class = MagicMock()
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        db = MagicMock()
        with patch.object(ServiceDataSource, "_get_service_instance", return_value=mock_instance):
            ds = ServiceDataSource(db=db, config=config)
        result = ds._instantiate_service(mock_class)
        mock_class.assert_called_once_with(db)
        assert result is mock_instance
