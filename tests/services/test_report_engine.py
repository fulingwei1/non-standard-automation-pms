# -*- coding: utf-8 -*-
"""Tests for app.services.report_framework.engine"""

from datetime import date
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


def _make_config(**overrides):
    """Create a mock ReportConfig."""
    from app.services.report_framework.models import (
        ExportConfig, ParameterType, PermissionConfig, ReportMeta,
    )
    config = MagicMock()
    config.meta = MagicMock(code="test_report", name="测试报告", description="desc")
    config.permissions = MagicMock(roles=[])
    config.parameters = []
    config.data_sources = {}
    config.sections = []
    config.exports = MagicMock()
    config.exports.json_export = MagicMock(enabled=True)
    config.exports.pdf = MagicMock(enabled=False)
    config.exports.excel = MagicMock(enabled=False)
    config.exports.word = MagicMock(enabled=False)
    for k, v in overrides.items():
        setattr(config, k, v)
    return config


def _make_engine(db=None):
    """Create ReportEngine with mocked dependencies."""
    db = db or MagicMock()
    with patch("app.services.report_framework.engine.ConfigLoader") as MockCL, \
         patch("app.services.report_framework.engine.DataResolver") as MockDR, \
         patch("app.services.report_framework.engine.ReportCacheManager") as MockCM, \
         patch("app.services.report_framework.engine.ExpressionParser") as MockEP:
        # Prevent optional renderer imports from failing
        with patch.dict("sys.modules", {
            "app.services.report_framework.renderers.pdf_renderer": MagicMock(),
            "app.services.report_framework.renderers.excel_renderer": MagicMock(),
            "app.services.report_framework.renderers.word_renderer": MagicMock(),
        }):
            from app.services.report_framework.engine import ReportEngine
            engine = ReportEngine(db)
    return engine


class TestReportEngineGenerate:
    def test_generate_json_basic(self):
        engine = _make_engine()
        config = _make_config()
        engine.config_loader.get.return_value = config
        engine.cache.get.return_value = None
        engine.data_resolver.resolve_all.return_value = {"params": {}}

        mock_result = MagicMock()
        json_renderer = MagicMock()
        json_renderer.render.return_value = mock_result
        engine.renderers["json"] = json_renderer

        result = engine.generate("test_report", {})
        assert result == mock_result
        engine.cache.set.assert_called_once()

    def test_generate_returns_cache(self):
        engine = _make_engine()
        config = _make_config()
        engine.config_loader.get.return_value = config
        cached = MagicMock()
        engine.cache.get.return_value = cached

        result = engine.generate("test_report", {})
        assert result == cached

    def test_generate_skip_cache(self):
        engine = _make_engine()
        config = _make_config()
        engine.config_loader.get.return_value = config
        engine.data_resolver.resolve_all.return_value = {}

        json_renderer = MagicMock()
        json_renderer.render.return_value = MagicMock()
        engine.renderers["json"] = json_renderer

        engine.generate("test_report", {}, skip_cache=True)
        engine.cache.get.assert_not_called()

    def test_generate_unsupported_format(self):
        from app.services.report_framework.config_loader import ConfigError
        engine = _make_engine()
        config = _make_config()
        engine.config_loader.get.return_value = config
        engine.cache.get.return_value = None
        engine.data_resolver.resolve_all.return_value = {}

        with pytest.raises(ConfigError):
            engine.generate("test_report", {}, format="unknown_format")

    def test_generate_with_permission_check(self):
        engine = _make_engine()
        config = _make_config()
        config.permissions.roles = ["admin"]
        engine.config_loader.get.return_value = config

        user = MagicMock()
        user.is_superuser = True
        engine.cache.get.return_value = None
        engine.data_resolver.resolve_all.return_value = {}

        json_renderer = MagicMock()
        json_renderer.render.return_value = MagicMock()
        engine.renderers["json"] = json_renderer

        # Superuser should pass
        engine.generate("test_report", {}, user=user)


class TestReportEnginePermissions:
    def test_superuser_passes(self):
        from app.services.report_framework.engine import ReportEngine
        engine = _make_engine()
        config = _make_config()
        config.permissions.roles = ["admin"]

        user = MagicMock()
        user.is_superuser = True
        # Should not raise
        engine._check_permission(config, user)

    def test_no_roles_configured_passes(self):
        engine = _make_engine()
        config = _make_config()
        config.permissions.roles = []

        user = MagicMock()
        user.is_superuser = False
        user.roles = []
        engine._check_permission(config, user)

    def test_matching_role_passes(self):
        engine = _make_engine()
        config = _make_config()
        config.permissions.roles = ["admin", "manager"]

        user = MagicMock()
        user.is_superuser = False
        role = MagicMock()
        role.role_code = "admin"
        user.roles = [role]
        engine._check_permission(config, user)

    def test_no_matching_role_raises(self):
        from app.services.report_framework.engine import PermissionError
        engine = _make_engine()
        config = _make_config()
        config.permissions.roles = ["admin"]

        user = MagicMock()
        user.is_superuser = False
        role = MagicMock()
        role.role_code = "viewer"
        user.roles = [role]

        with pytest.raises(PermissionError):
            engine._check_permission(config, user)


class TestReportEngineValidateParams:
    def test_required_missing(self):
        from app.services.report_framework.engine import ParameterError
        engine = _make_engine()
        config = _make_config()
        param = MagicMock(name="year", required=True, default=None, type=MagicMock(value="integer"))
        config.parameters = [param]

        with pytest.raises(ParameterError):
            engine._validate_params(config, {})

    def test_default_value(self):
        engine = _make_engine()
        config = _make_config()
        param = MagicMock(required=False, default=2025, type=MagicMock(value="integer"))
        param.name = "year"
        config.parameters = [param]

        result = engine._validate_params(config, {})
        assert result["year"] == 2025

    def test_type_conversion(self):
        engine = _make_engine()
        config = _make_config()
        param = MagicMock(required=True, default=None, type=MagicMock(value="integer"))
        param.name = "year"
        config.parameters = [param]

        result = engine._validate_params(config, {"year": "2025"})
        assert result["year"] == 2025


class TestConvertParamType:
    def test_integer(self):
        engine = _make_engine()
        assert engine._convert_param_type("42", MagicMock(value="integer")) == 42

    def test_float(self):
        engine = _make_engine()
        assert engine._convert_param_type("3.14", MagicMock(value="float")) == 3.14

    def test_boolean_true(self):
        engine = _make_engine()
        assert engine._convert_param_type("true", MagicMock(value="boolean")) is True

    def test_boolean_false(self):
        engine = _make_engine()
        assert engine._convert_param_type("no", MagicMock(value="boolean")) is False

    def test_date(self):
        engine = _make_engine()
        result = engine._convert_param_type("2025-01-01", MagicMock(value="date"))
        assert result == date(2025, 1, 1)

    def test_string(self):
        engine = _make_engine()
        assert engine._convert_param_type(42, MagicMock(value="string")) == "42"

    def test_list_from_value(self):
        engine = _make_engine()
        assert engine._convert_param_type("x", MagicMock(value="list")) == ["x"]

    def test_list_passthrough(self):
        engine = _make_engine()
        assert engine._convert_param_type([1, 2], MagicMock(value="list")) == [1, 2]

    def test_invalid_raises(self):
        from app.services.report_framework.engine import ParameterError
        engine = _make_engine()
        with pytest.raises(ParameterError):
            engine._convert_param_type("abc", MagicMock(value="integer"))


class TestRenderSections:
    def test_render_metrics(self):
        from app.services.report_framework.models import SectionType
        engine = _make_engine()

        item = MagicMock(label="总数", value="data.count")
        section = MagicMock(
            id="s1", title="指标", type=SectionType.METRICS,
            items=[item], columns=None, chart_type=None, source=None,
        )

        engine.expression_parser.evaluate.return_value = 42
        result = engine._render_section(section, {"data": {"count": 42}})
        assert result["type"] == "metrics"
        assert result["items"][0]["value"] == 42

    def test_render_table(self):
        from app.services.report_framework.models import SectionType
        engine = _make_engine()

        col = MagicMock(field="name", label="名称", format=None)
        section = MagicMock(
            id="s2", title="表格", type=SectionType.TABLE,
            items=None, columns=[col], chart_type=None, source="projects",
        )

        ctx = {"projects": [{"name": "P1"}, {"name": "P2"}]}
        result = engine._render_section(section, ctx)
        assert result["type"] == "table"
        assert len(result["data"]) == 2

    def test_render_chart_dict(self):
        from app.services.report_framework.models import SectionType, ChartType
        engine = _make_engine()

        section = MagicMock(
            id="s3", title="图表", type=SectionType.CHART,
            items=None, columns=None, chart_type=ChartType.PIE, source="status_counts",
        )

        ctx = {"status_counts": {"active": 5, "closed": 3}}
        result = engine._render_section(section, ctx)
        assert result["type"] == "chart"
        assert len(result["data"]) == 2


class TestGetContextValue:
    def test_simple_key(self):
        engine = _make_engine()
        assert engine._get_context_value({"a": 1}, "a") == 1

    def test_dot_notation(self):
        engine = _make_engine()
        assert engine._get_context_value({"a": {"b": {"c": 3}}}, "a.b.c") == 3

    def test_missing(self):
        engine = _make_engine()
        assert engine._get_context_value({"a": 1}, "b") is None

    def test_none_key(self):
        engine = _make_engine()
        assert engine._get_context_value({"a": 1}, None) is None


class TestListAvailable:
    def test_no_user(self):
        engine = _make_engine()
        meta1 = MagicMock(code="r1")
        engine.config_loader.list_available.return_value = [meta1]

        result = engine.list_available()
        assert len(result) == 1

    def test_with_user_filters(self):
        from app.services.report_framework.engine import PermissionError as PE
        engine = _make_engine()
        meta1 = MagicMock(code="r1")
        meta2 = MagicMock(code="r2")
        engine.config_loader.list_available.return_value = [meta1, meta2]

        config1 = _make_config()
        config1.permissions.roles = []
        config2 = _make_config()
        config2.permissions.roles = ["admin"]

        def get_side_effect(code):
            return config1 if code == "r1" else config2

        engine.config_loader.get.side_effect = get_side_effect

        user = MagicMock()
        user.is_superuser = False
        user.roles = []

        # Patch _check_permission to raise for r2
        original = engine._check_permission

        def check(config, u):
            if config.permissions.roles and not u.is_superuser:
                raise PE("no")
        engine._check_permission = check

        result = engine.list_available(user=user)
        assert len(result) == 1


class TestGetSchema:
    def test_schema(self):
        engine = _make_engine()
        config = _make_config()
        param = MagicMock(name="year", type=MagicMock(value="integer"), required=True, default=None, description="年度")
        config.parameters = [param]
        engine.config_loader.get.return_value = config

        schema = engine.get_schema("test_report")
        assert schema["report_code"] == "test_report"
        assert len(schema["parameters"]) == 1


class TestRegisterRenderer:
    def test_register(self):
        engine = _make_engine()
        renderer = MagicMock()
        engine.register_renderer("custom", renderer)
        assert engine.renderers["custom"] == renderer
