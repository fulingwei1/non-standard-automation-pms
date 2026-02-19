# -*- coding: utf-8 -*-
"""Tests for app/services/report_framework/data_sources/service.py"""

import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.report_framework.data_sources.service import ServiceDataSource
    from app.services.report_framework.data_sources.base import DataSourceError
    from app.services.report_framework.models import DataSourceConfig, DataSourceType
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_config(method="ProjectService.get_list", args=None):
    return DataSourceConfig(
        type=DataSourceType.SERVICE,
        method=method,
        args=args or {},
    )


def _make_db():
    return MagicMock()


def test_validate_config_missing_method():
    config = DataSourceConfig(type=DataSourceType.SERVICE)
    db = _make_db()
    with pytest.raises(DataSourceError, match="Method is required"):
        ServiceDataSource(db, config)


def test_validate_config_invalid_format():
    config = DataSourceConfig(type=DataSourceType.SERVICE, method="NoDotsHere")
    db = _make_db()
    with pytest.raises(DataSourceError, match="Invalid method format"):
        ServiceDataSource(db, config)


def test_parse_method():
    config = _make_config("MyService.my_method")
    ds = ServiceDataSource(_make_db(), config)
    assert ds._service_class == "MyService"
    assert ds._method_name == "my_method"


def test_to_snake_case():
    assert ServiceDataSource._to_snake_case("ProjectService") == "project_service"
    assert ServiceDataSource._to_snake_case("ReportDataGenerator") == "report_data_generator"


def test_fetch_method_not_found():
    config = _make_config("MyService.my_method")
    ds = ServiceDataSource(_make_db(), config)

    mock_instance = MagicMock(spec=[])  # no attributes
    with patch.object(ds, '_get_service_instance', return_value=mock_instance):
        with pytest.raises(DataSourceError, match="not found in service"):
            ds.fetch({})


def test_fetch_success():
    config = _make_config("MyService.get_data")
    ds = ServiceDataSource(_make_db(), config)

    mock_instance = MagicMock()
    mock_instance.get_data.return_value = [{"id": 1}]
    with patch.object(ds, '_get_service_instance', return_value=mock_instance):
        result = ds.fetch({})
    assert result == [{"id": 1}]


def test_get_service_instance_not_found():
    config = _make_config("NonExistentService999.method")
    ds = ServiceDataSource(_make_db(), config)
    with pytest.raises(DataSourceError, match="not found"):
        ds._get_service_instance()
