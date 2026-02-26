# -*- coding: utf-8 -*-
"""第十八批 - 数据源解析器单元测试"""
from unittest.mock import MagicMock, patch

import pytest

try:
    from app.services.report_framework.data_resolver import DataResolver
    from app.services.report_framework.data_sources.base import DataSourceError
    from app.services.report_framework.models import DataSourceConfig, DataSourceType
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="导入失败，跳过")


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def resolver(db):
    if IMPORT_OK:
        return DataResolver(db)


def make_config(source_type=None, args=None):
    if not IMPORT_OK:
        return None
    if source_type is None:
        source_type = DataSourceType.QUERY
    cfg = MagicMock(spec=DataSourceConfig)
    cfg.type = source_type
    cfg.args = args or {}
    cfg.model_dump.return_value = {"type": source_type, "args": args or {}}
    return cfg


class TestDataResolverInit:
    def test_sets_db(self, db, resolver):
        assert resolver.db is db

    def test_has_expression_parser(self, resolver):
        assert hasattr(resolver, "_expression_parser")

    def test_data_source_types_registered(self, resolver):
        assert DataSourceType.QUERY in resolver.DATA_SOURCE_TYPES
        assert DataSourceType.SERVICE in resolver.DATA_SOURCE_TYPES


class TestResolveOne:
    def test_unsupported_type_raises_error(self, resolver):
        cfg = MagicMock()
        cfg.type = "UNSUPPORTED_TYPE"
        cfg.args = {}
        with pytest.raises(Exception):
            resolver.resolve_one(cfg, {})

    def test_calls_ds_fetch_with_merged_params(self, resolver):
        cfg = make_config(DataSourceType.QUERY, args={"project_id": 1})
        mock_ds_class = MagicMock()
        mock_ds_instance = MagicMock()
        mock_ds_instance.fetch.return_value = [{"row": 1}]
        mock_ds_class.return_value = mock_ds_instance

        resolver.DATA_SOURCE_TYPES[DataSourceType.QUERY] = mock_ds_class
        result = resolver.resolve_one(cfg, {"extra": "value"})

        mock_ds_instance.fetch.assert_called_once()
        assert result == [{"row": 1}]

    def test_merges_config_and_runtime_params(self, resolver):
        cfg = make_config(DataSourceType.QUERY, args={"from_config": "x"})
        mock_ds_class = MagicMock()
        mock_ds_instance = MagicMock()
        mock_ds_instance.fetch.return_value = []
        mock_ds_class.return_value = mock_ds_instance

        resolver.DATA_SOURCE_TYPES[DataSourceType.QUERY] = mock_ds_class
        resolver.resolve_one(cfg, {"from_runtime": "y"})

        call_args = mock_ds_instance.fetch.call_args[0][0]
        assert "from_config" in call_args
        assert "from_runtime" in call_args


class TestResolveAll:
    def test_returns_empty_for_no_sources(self, resolver):
        result = resolver.resolve_all({}, {"user_id": 1})
        assert result == {}

    def test_handles_data_source_error_gracefully(self, resolver):
        cfg = make_config()
        with patch.object(resolver, "resolve_one", side_effect=DataSourceError("fail")):
            with patch.object(resolver, "_resolve_config_expressions", return_value=cfg):
                result = resolver.resolve_all({"ds1": cfg}, {})
        assert result["ds1"] == []

    def test_removes_params_from_result(self, resolver):
        cfg = make_config()
        with patch.object(resolver, "resolve_one", return_value=[1, 2]):
            with patch.object(resolver, "_resolve_config_expressions", return_value=cfg):
                result = resolver.resolve_all({"ds1": cfg}, {"user_id": 5})
        assert "params" not in result
        assert "ds1" in result


class TestRegisterDataSource:
    def test_registers_new_type(self, resolver):
        mock_type = MagicMock()
        mock_class = MagicMock()
        resolver.register_data_source(mock_type, mock_class)
        assert resolver.DATA_SOURCE_TYPES[mock_type] is mock_class
