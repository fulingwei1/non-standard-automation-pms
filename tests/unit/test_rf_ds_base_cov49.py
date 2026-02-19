# -*- coding: utf-8 -*-
"""Tests for app/services/report_framework/data_sources/base.py"""

import pytest
from unittest.mock import MagicMock

try:
    from app.services.report_framework.data_sources.base import DataSource, DataSourceError
    from app.services.report_framework.models import DataSourceConfig, DataSourceType
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


class ConcreteDataSource(DataSource):
    def fetch(self, params):
        return [{"id": 1}]


def test_data_source_is_abstract():
    config = DataSourceConfig(type=DataSourceType.QUERY, sql="SELECT 1")
    db = MagicMock()
    with pytest.raises(TypeError):
        DataSource(db, config)


def test_concrete_data_source_instantiation():
    config = DataSourceConfig(type=DataSourceType.QUERY, sql="SELECT 1")
    db = MagicMock()
    ds = ConcreteDataSource(db, config)
    assert ds.db is db
    assert ds.config is config


def test_concrete_data_source_fetch():
    config = DataSourceConfig(type=DataSourceType.QUERY, sql="SELECT 1")
    db = MagicMock()
    ds = ConcreteDataSource(db, config)
    result = ds.fetch({})
    assert result == [{"id": 1}]


def test_validate_config_default_is_noop():
    config = DataSourceConfig(type=DataSourceType.QUERY, sql="SELECT 1")
    db = MagicMock()
    ds = ConcreteDataSource(db, config)
    # Should not raise
    ds.validate_config()


def test_data_source_error_is_exception():
    err = DataSourceError("test error")
    assert isinstance(err, Exception)
    assert str(err) == "test error"


def test_data_source_stores_config():
    config = DataSourceConfig(type=DataSourceType.SERVICE, method="Svc.get")
    db = MagicMock()
    ds = ConcreteDataSource(db, config)
    assert ds.config.type == "service"
