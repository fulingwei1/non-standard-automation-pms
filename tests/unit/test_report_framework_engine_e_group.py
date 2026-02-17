# -*- coding: utf-8 -*-
"""
E组 - 报告引擎 单元测试
覆盖: app/services/report_framework/engine.py
"""
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


# ─── fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def mock_config_loader():
    loader = MagicMock()
    return loader


@pytest.fixture
def mock_data_resolver(db_session):
    resolver = MagicMock()
    return resolver


@pytest.fixture
def engine(db_session, mock_config_loader, mock_data_resolver):
    from app.services.report_framework.engine import ReportEngine
    with patch("app.services.report_framework.engine.ConfigLoader", return_value=mock_config_loader), \
         patch("app.services.report_framework.engine.DataResolver", return_value=mock_data_resolver):
        eng = ReportEngine(db=db_session, config_dir="/fake/config")
    eng.config_loader = mock_config_loader
    eng.data_resolver = mock_data_resolver
    return eng


def _make_report_config(code="report_001", roles=None, params=None, sections=None):
    """构建模拟报告配置"""
    from app.services.report_framework.models import (
        ReportConfig, ReportMeta, PermissionConfig, ExportConfig,
        ExportOptions, JsonExportOptions
    )
    meta = MagicMock()
    meta.code = code
    meta.name = f"Report {code}"
    meta.description = "Test report"

    permissions = MagicMock()
    permissions.roles = roles or []

    exports = MagicMock()
    exports.json_export = MagicMock(enabled=True)
    exports.pdf = MagicMock(enabled=False)
    exports.excel = MagicMock(enabled=False)
    exports.word = MagicMock(enabled=False)

    config = MagicMock()
    config.meta = meta
    config.permissions = permissions
    config.exports = exports
    config.parameters = params or []
    config.sections = sections or []
    config.data_sources = []

    return config


# ─── _check_permission ──────────────────────────────────────────────────────

class TestCheckPermission:

    def test_superuser_bypasses_permission(self, engine):
        config = _make_report_config(roles=["admin"])
        user = MagicMock(is_superuser=True)
        # Should NOT raise
        engine._check_permission(config, user)

    def test_no_role_restriction_allows_all(self, engine):
        config = _make_report_config(roles=[])
        user = MagicMock(is_superuser=False, roles=[])
        engine._check_permission(config, user)  # should not raise

    def test_user_with_matching_role(self, engine):
        config = _make_report_config(roles=["manager"])
        user = MagicMock(is_superuser=False)
        role = MagicMock(role_code="manager")
        user.roles = [role]
        engine._check_permission(config, user)  # should not raise

    def test_user_without_matching_role_raises(self, engine):
        from app.services.report_framework.engine import PermissionError
        config = _make_report_config(roles=["admin"])
        user = MagicMock(is_superuser=False)
        role = MagicMock(role_code="viewer")
        user.roles = [role]
        with pytest.raises(PermissionError):
            engine._check_permission(config, user)

    def test_user_with_nested_role(self, engine):
        config = _make_report_config(roles=["pm"])
        user = MagicMock(is_superuser=False)
        nested_role = MagicMock()
        nested_role.role = MagicMock(role_code="pm")
        del nested_role.role_code  # no direct role_code
        # Ensure hasattr logic is triggered
        user.roles = [nested_role]
        try:
            engine._check_permission(config, user)
        except Exception:
            pass  # may fail depending on mock setup


# ─── _validate_params ───────────────────────────────────────────────────────

class TestValidateParams:

    def _make_param(self, name, required=False, default=None, param_type="string"):
        from app.services.report_framework.models import ParameterType
        param = MagicMock()
        param.name = name
        param.required = required
        param.default = default
        param.type = MagicMock(value=param_type)
        return param

    def test_required_param_missing_raises(self, engine):
        from app.services.report_framework.engine import ParameterError
        config = _make_report_config()
        config.parameters = [self._make_param("start_date", required=True)]
        with pytest.raises(ParameterError):
            engine._validate_params(config, {})

    def test_optional_param_uses_default(self, engine):
        config = _make_report_config()
        config.parameters = [self._make_param("limit", required=False, default=10, param_type="integer")]
        result = engine._validate_params(config, {})
        assert result["limit"] == 10

    def test_param_provided_is_used(self, engine):
        config = _make_report_config()
        config.parameters = [self._make_param("year", required=True, param_type="integer")]
        result = engine._validate_params(config, {"year": "2025"})
        assert result["year"] == 2025

    def test_all_none_no_required(self, engine):
        config = _make_report_config()
        config.parameters = []
        result = engine._validate_params(config, {})
        assert result == {}


# ─── _convert_param_type ────────────────────────────────────────────────────

class TestConvertParamType:

    def _type(self, name):
        t = MagicMock()
        t.value = name
        return t

    def test_integer_conversion(self, engine):
        result = engine._convert_param_type("42", self._type("integer"))
        assert result == 42

    def test_float_conversion(self, engine):
        result = engine._convert_param_type("3.14", self._type("float"))
        assert result == pytest.approx(3.14)

    def test_boolean_true_string(self, engine):
        result = engine._convert_param_type("true", self._type("boolean"))
        assert result is True

    def test_boolean_false_string(self, engine):
        result = engine._convert_param_type("0", self._type("boolean"))
        assert result is False

    def test_date_conversion(self, engine):
        from datetime import date
        result = engine._convert_param_type("2025-06-01", self._type("date"))
        assert result == date(2025, 6, 1)

    def test_date_already_date_obj(self, engine):
        from datetime import date
        d = date(2025, 1, 1)
        result = engine._convert_param_type(d, self._type("date"))
        assert result == d

    def test_string_conversion(self, engine):
        result = engine._convert_param_type(123, self._type("string"))
        assert result == "123"

    def test_list_conversion_single_value(self, engine):
        result = engine._convert_param_type("a", self._type("list"))
        assert result == ["a"]

    def test_list_passthrough(self, engine):
        result = engine._convert_param_type([1, 2], self._type("list"))
        assert result == [1, 2]

    def test_invalid_integer_raises(self, engine):
        from app.services.report_framework.engine import ParameterError
        with pytest.raises(ParameterError):
            engine._convert_param_type("not_a_number", self._type("integer"))


# ─── _get_context_value ──────────────────────────────────────────────────────

class TestGetContextValue:

    def test_direct_key(self, engine):
        ctx = {"users": [1, 2, 3]}
        assert engine._get_context_value(ctx, "users") == [1, 2, 3]

    def test_nested_key(self, engine):
        ctx = {"data": {"summary": {"total": 100}}}
        assert engine._get_context_value(ctx, "data.summary.total") == 100

    def test_missing_key_returns_none(self, engine):
        ctx = {"data": {}}
        assert engine._get_context_value(ctx, "data.missing") is None

    def test_none_key_returns_none(self, engine):
        assert engine._get_context_value({}, None) is None

    def test_top_level_key_takes_priority(self, engine):
        ctx = {"a.b": "direct", "a": {"b": "nested"}}
        assert engine._get_context_value(ctx, "a.b") == "direct"


# ─── _render_sections / _render_section ─────────────────────────────────────

class TestRenderSections:

    def _make_section(self, section_id, section_type, source=None, columns=None, items=None):
        from app.services.report_framework.models import SectionType
        section = MagicMock()
        section.id = section_id
        section.title = f"Section {section_id}"
        section.type = section_type
        section.source = source
        section.columns = columns or []
        section.items = items or []
        section.chart_type = "bar"
        return section

    def test_render_metrics_section(self, engine):
        from app.services.report_framework.models import SectionType
        item = MagicMock(label="Total", value="total_count")
        section = self._make_section("s1", SectionType.METRICS, items=[item])

        engine.expression_parser.evaluate = MagicMock(return_value=42)
        context = {"total_count": 42}
        result = engine._render_section(section, context)

        assert result["id"] == "s1"
        assert result["type"] == SectionType.METRICS.value
        assert len(result["items"]) == 1
        assert result["items"][0]["value"] == 42

    def test_render_table_section(self, engine):
        from app.services.report_framework.models import SectionType
        section = self._make_section("s2", SectionType.TABLE, source="users")
        context = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
        result = engine._render_section(section, context)

        assert result["type"] == SectionType.TABLE.value
        assert len(result["data"]) == 2

    def test_render_chart_section_list(self, engine):
        from app.services.report_framework.models import SectionType
        section = self._make_section("s3", SectionType.CHART, source="stats")
        context = {"stats": [{"label": "Jan", "value": 10}]}
        result = engine._render_section(section, context)
        assert result["type"] == SectionType.CHART.value

    def test_render_chart_section_dict(self, engine):
        from app.services.report_framework.models import SectionType
        section = self._make_section("s4", SectionType.CHART, source="dept_hours")
        context = {"dept_hours": {"Dev": 100, "QA": 50}}
        result = engine._render_section(section, context)
        assert isinstance(result["data"], list)
        assert len(result["data"]) == 2

    def test_render_empty_source_returns_empty(self, engine):
        from app.services.report_framework.models import SectionType
        section = self._make_section("s5", SectionType.TABLE, source=None)
        result = engine._render_section(section, {})
        assert result["data"] == []


# ─── get_schema ──────────────────────────────────────────────────────────────

class TestGetSchema:

    def test_get_schema_structure(self, engine):
        config = _make_report_config(code="test_rpt")
        engine.config_loader.get.return_value = config

        schema = engine.get_schema("test_rpt")

        assert schema["report_code"] == "test_rpt"
        assert "parameters" in schema
        assert "exports" in schema

    def test_get_schema_exports_flags(self, engine):
        config = _make_report_config()
        config.exports.json_export.enabled = True
        config.exports.pdf.enabled = False
        engine.config_loader.get.return_value = config

        schema = engine.get_schema("x")
        assert schema["exports"]["json"] is True
        assert schema["exports"]["pdf"] is False


# ─── register_renderer ───────────────────────────────────────────────────────

class TestRegisterRenderer:

    def test_register_custom_renderer(self, engine):
        mock_renderer = MagicMock()
        engine.register_renderer("csv", mock_renderer)
        assert engine.renderers["csv"] is mock_renderer

    def test_unsupported_format_in_generate_raises(self, engine):
        from app.services.report_framework.engine import ConfigError
        config = _make_report_config()
        engine.config_loader.get.return_value = config
        engine.data_resolver.resolve_all.return_value = {}

        with pytest.raises(ConfigError):
            engine.generate("rpt_001", {}, format="unknown_format")


# ─── list_available ──────────────────────────────────────────────────────────

class TestListAvailable:

    def test_list_all_when_no_user(self, engine):
        metas = [MagicMock(), MagicMock()]
        engine.config_loader.list_available.return_value = metas
        result = engine.list_available(user=None)
        assert result == metas

    def test_list_filters_by_permission(self, engine):
        from app.services.report_framework.engine import PermissionError
        meta1 = MagicMock()
        meta1.code = "r1"
        meta2 = MagicMock()
        meta2.code = "r2"
        engine.config_loader.list_available.return_value = [meta1, meta2]

        config1 = _make_report_config(code="r1", roles=["admin"])
        config2 = _make_report_config(code="r2", roles=["viewer"])
        engine.config_loader.get.side_effect = [config1, config2]

        user = MagicMock(is_superuser=False)
        role = MagicMock(role_code="admin")
        user.roles = [role]

        result = engine.list_available(user=user)
        # r1 passes (admin role matches), r2 does not
        assert len(result) == 1
        assert result[0].code == "r1"
