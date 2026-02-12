# -*- coding: utf-8 -*-
"""数据源解析器 单元测试"""
from unittest.mock import MagicMock, patch

import pytest

from app.services.report_framework.data_resolver import DataResolver
from app.services.report_framework.models import DataSourceConfig, DataSourceType


class TestDataResolver:
    def test_init(self):
        db = MagicMock()
        resolver = DataResolver(db)
        assert resolver.db is db

    def test_resolve_one_unsupported_type(self):
        db = MagicMock()
        resolver = DataResolver(db)
        config = MagicMock()
        config.type = "UNSUPPORTED"
        with pytest.raises(Exception):
            resolver.resolve_one(config, {})

    def test_resolve_all_handles_error(self):
        db = MagicMock()
        resolver = DataResolver(db)
        config = MagicMock()
        config.type = "UNSUPPORTED"
        config.args = {}

        # Should not raise, should set empty list for failed source
        with patch.object(resolver, '_resolve_config_expressions', return_value=config):
            with patch.object(resolver, 'resolve_one', side_effect=Exception("fail")):
                # DataSourceError handling
                from app.services.report_framework.data_sources.base import DataSourceError
                with patch.object(resolver, 'resolve_one', side_effect=DataSourceError("fail")):
                    result = resolver.resolve_all({"src1": config}, {"p": 1})
                    assert result.get("src1") == []

    def test_resolve_all_populates_context(self):
        db = MagicMock()
        resolver = DataResolver(db)
        config1 = MagicMock()
        config1.args = {}
        config2 = MagicMock()
        config2.args = {}

        with patch.object(resolver, '_resolve_config_expressions', side_effect=lambda c, ctx: c):
            with patch.object(resolver, 'resolve_one', side_effect=[["data1"], ["data2"]]):
                result = resolver.resolve_all(
                    {"src1": config1, "src2": config2}, {}
                )
                assert result["src1"] == ["data1"]
                assert result["src2"] == ["data2"]

    def test_register_data_source(self):
        db = MagicMock()
        resolver = DataResolver(db)
        mock_class = MagicMock()
        resolver.register_data_source(DataSourceType.QUERY, mock_class)
        assert resolver.DATA_SOURCE_TYPES[DataSourceType.QUERY] is mock_class

    def test_resolve_config_expressions(self):
        db = MagicMock()
        resolver = DataResolver(db)
        config = DataSourceConfig(
            type=DataSourceType.QUERY,
            source="test",
            args={"key": "{{params.val}}"},
        )
        resolver._expression_parser = MagicMock()
        resolver._expression_parser.evaluate.return_value = "resolved"
        result = resolver._resolve_config_expressions(config, {"params": {"val": "x"}})
        assert result.args["key"] == "resolved"
