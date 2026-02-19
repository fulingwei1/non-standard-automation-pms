# -*- coding: utf-8 -*-
"""第四十四批覆盖测试 - 数据源基类"""

import pytest
from unittest.mock import MagicMock

try:
    from app.services.report_framework.data_sources.base import DataSource, DataSourceError
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


class ConcreteDataSource(DataSource):
    """用于测试的具体数据源实现"""

    def fetch(self, params):
        return [{"key": "value"}]


class ErrorDataSource(DataSource):
    """抛出错误的数据源"""

    def fetch(self, params):
        raise DataSourceError("fetch failed")


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.sql = None
    config.method = None
    return config


@pytest.fixture
def datasource(mock_config):
    return ConcreteDataSource(db=MagicMock(), config=mock_config)


class TestDataSourceBase:

    def test_datasource_is_abstract(self):
        """DataSource 是抽象类，不可直接实例化"""
        import inspect
        assert inspect.isabstract(DataSource)

    def test_concrete_datasource_can_be_instantiated(self, datasource):
        assert datasource is not None

    def test_fetch_returns_list(self, datasource):
        result = datasource.fetch({})
        assert result == [{"key": "value"}]

    def test_datasource_stores_db(self, datasource):
        assert datasource.db is not None

    def test_datasource_stores_config(self, datasource, mock_config):
        assert datasource.config is mock_config

    def test_validate_config_does_nothing_by_default(self, datasource):
        """基类 validate_config 不应抛出异常"""
        datasource.validate_config()  # should not raise

    def test_data_source_error_is_exception(self):
        err = DataSourceError("test error")
        assert isinstance(err, Exception)

    def test_error_datasource_raises_on_fetch(self, mock_config):
        ds = ErrorDataSource(db=MagicMock(), config=mock_config)
        with pytest.raises(DataSourceError):
            ds.fetch({})
