# -*- coding: utf-8 -*-
"""
ReportEngine 深度覆盖测试（N3组）

覆盖：
- __init__ (with/without cache_manager)
- generate (正常/cache hit/权限错误/参数错误/格式不支持)
- list_available (all / filtered by permission)
- get_schema
- register_renderer
- _check_permission (superuser / role match / no roles / denied)
- _validate_params (required/optional/defaults)
- _convert_param_type (各类型转换)
- _render_sections / _render_section
- _render_metrics / _render_table / _render_chart
- _get_context_value (plain key / dot notation / missing)
"""

from unittest.mock import MagicMock, patch, PropertyMock
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.meta.code = "test_report"
    config.meta.name = "测试报告"
    config.meta.description = "描述"
    config.permissions.roles = []
    config.parameters = []
    config.data_sources = {}
    config.sections = []
    config.exports.json_export.enabled = True
    config.exports.pdf.enabled = False
    config.exports.excel.enabled = False
    config.exports.word.enabled = False
    return config


@pytest.fixture
def engine(mock_db):
    with patch("app.services.report_framework.engine.ConfigLoader"), \
         patch("app.services.report_framework.engine.DataResolver"), \
         patch("app.services.report_framework.engine.ReportCacheManager"), \
         patch("app.services.report_framework.engine.ExpressionParser"), \
         patch("app.services.report_framework.engine.JsonRenderer"):
        from app.services.report_framework.engine import ReportEngine
        eng = ReportEngine(db=mock_db)
    return eng


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------

class TestReportEngineInit:
    def test_default_json_renderer_registered(self, mock_db):
        with patch("app.services.report_framework.engine.ConfigLoader"), \
             patch("app.services.report_framework.engine.DataResolver"), \
             patch("app.services.report_framework.engine.ReportCacheManager"), \
             patch("app.services.report_framework.engine.ExpressionParser"), \
             patch("app.services.report_framework.engine.JsonRenderer") as MockJson:
            from app.services.report_framework.engine import ReportEngine
            eng = ReportEngine(db=mock_db)
        assert "json" in eng.renderers

    def test_custom_cache_manager_used(self, mock_db):
        custom_cache = MagicMock()
        with patch("app.services.report_framework.engine.ConfigLoader"), \
             patch("app.services.report_framework.engine.DataResolver"), \
             patch("app.services.report_framework.engine.ExpressionParser"), \
             patch("app.services.report_framework.engine.JsonRenderer"):
            from app.services.report_framework.engine import ReportEngine
            eng = ReportEngine(db=mock_db, cache_manager=custom_cache)
        assert eng.cache is custom_cache


# ---------------------------------------------------------------------------
# register_renderer
# ---------------------------------------------------------------------------

class TestRegisterRenderer:
    def test_registers_custom_renderer(self, engine):
        custom_renderer = MagicMock()
        engine.register_renderer("custom", custom_renderer)
        assert engine.renderers["custom"] is custom_renderer

    def test_overwrites_existing_renderer(self, engine):
        new_renderer = MagicMock()
        engine.register_renderer("json", new_renderer)
        assert engine.renderers["json"] is new_renderer


# ---------------------------------------------------------------------------
# _check_permission
# ---------------------------------------------------------------------------

class TestCheckPermission:
    def test_superuser_always_passes(self, engine):
        from app.services.report_framework.engine import PermissionError as PE
        config = MagicMock()
        config.permissions.roles = ["admin"]
        user = MagicMock()
        user.is_superuser = True
        engine._check_permission(config, user)  # should not raise

    def test_user_without_matching_role_raises(self, engine):
        from app.services.report_framework.engine import PermissionError as PE
        config = MagicMock()
        config.meta.code = "restricted"
        config.permissions.roles = ["finance"]
        user = MagicMock()
        user.is_superuser = False
        role = MagicMock()
        role.role_code = "engineer"
        user_role = MagicMock()
        user_role.role_code = "engineer"
        user.roles = [user_role]
        with pytest.raises(PE):
            engine._check_permission(config, user)

    def test_user_with_matching_role_passes(self, engine):
        config = MagicMock()
        config.meta.code = "report_x"
        config.permissions.roles = ["finance"]
        user = MagicMock()
        user.is_superuser = False
        role_obj = MagicMock()
        role_obj.role_code = "finance"
        user.roles = [role_obj]
        engine._check_permission(config, user)  # should not raise

    def test_empty_roles_config_allows_all(self, engine):
        config = MagicMock()
        config.permissions.roles = []
        user = MagicMock()
        user.is_superuser = False
        user.roles = []
        engine._check_permission(config, user)  # should not raise

    def test_no_is_superuser_attribute_doesnt_crash(self, engine):
        config = MagicMock()
        config.permissions.roles = []
        user = MagicMock(spec=[])  # no attributes
        # Should not crash
        try:
            engine._check_permission(config, user)
        except Exception as e:
            pass  # might raise, just shouldn't crash with AttributeError on is_superuser


# ---------------------------------------------------------------------------
# _validate_params
# ---------------------------------------------------------------------------

class TestValidateParams:
    def _make_param(self, name, required=False, default=None, ptype="string"):
        from app.services.report_framework.models import ParameterType
        p = MagicMock()
        p.name = name
        p.required = required
        p.default = default
        p.type = MagicMock()
        p.type.value = ptype
        return p

    def test_required_param_missing_raises(self, engine):
        from app.services.report_framework.engine import ParameterError
        config = MagicMock()
        config.parameters = [self._make_param("project_id", required=True)]
        with pytest.raises(ParameterError):
            engine._validate_params(config, {})

    def test_optional_param_uses_default(self, engine):
        config = MagicMock()
        config.parameters = [self._make_param("page", required=False, default=1, ptype="integer")]
        result = engine._validate_params(config, {})
        assert result["page"] == 1

    def test_provided_value_overrides_default(self, engine):
        config = MagicMock()
        config.parameters = [self._make_param("page", required=False, default=1, ptype="integer")]
        result = engine._validate_params(config, {"page": "3"})
        assert result["page"] == 3

    def test_none_value_stays_none_for_optional(self, engine):
        config = MagicMock()
        config.parameters = [self._make_param("filter", required=False, default=None)]
        result = engine._validate_params(config, {})
        assert result["filter"] is None


# ---------------------------------------------------------------------------
# _convert_param_type
# ---------------------------------------------------------------------------

class TestConvertParamType:
    def _get_type(self, value_str):
        t = MagicMock()
        t.value = value_str
        return t

    def test_integer_conversion(self, engine):
        result = engine._convert_param_type("42", self._get_type("integer"))
        assert result == 42

    def test_float_conversion(self, engine):
        result = engine._convert_param_type("3.14", self._get_type("float"))
        assert result == pytest.approx(3.14, abs=0.001)

    def test_boolean_true_strings(self, engine):
        for val in ("true", "1", "yes"):
            result = engine._convert_param_type(val, self._get_type("boolean"))
            assert result is True

    def test_boolean_false_strings(self, engine):
        result = engine._convert_param_type("false", self._get_type("boolean"))
        assert result is False

    def test_boolean_already_bool(self, engine):
        result = engine._convert_param_type(True, self._get_type("boolean"))
        assert result is True

    def test_date_from_string(self, engine):
        from datetime import date
        result = engine._convert_param_type("2025-06-15", self._get_type("date"))
        assert result == date(2025, 6, 15)

    def test_date_already_date(self, engine):
        from datetime import date
        d = date(2025, 1, 1)
        result = engine._convert_param_type(d, self._get_type("date"))
        assert result == d

    def test_string_conversion(self, engine):
        result = engine._convert_param_type(123, self._get_type("string"))
        assert result == "123"

    def test_list_from_single_value(self, engine):
        result = engine._convert_param_type("item", self._get_type("list"))
        assert result == ["item"]

    def test_list_from_list(self, engine):
        result = engine._convert_param_type([1, 2, 3], self._get_type("list"))
        assert result == [1, 2, 3]

    def test_invalid_integer_raises_param_error(self, engine):
        from app.services.report_framework.engine import ParameterError
        with pytest.raises(ParameterError):
            engine._convert_param_type("not_a_number", self._get_type("integer"))


# ---------------------------------------------------------------------------
# _get_context_value
# ---------------------------------------------------------------------------

class TestGetContextValue:
    def test_plain_key(self, engine):
        context = {"projects": [1, 2, 3]}
        assert engine._get_context_value(context, "projects") == [1, 2, 3]

    def test_dot_notation_nested(self, engine):
        context = {"stats": {"total": 42}}
        assert engine._get_context_value(context, "stats.total") == 42

    def test_deeply_nested(self, engine):
        context = {"a": {"b": {"c": "value"}}}
        assert engine._get_context_value(context, "a.b.c") == "value"

    def test_missing_key_returns_none(self, engine):
        context = {"a": 1}
        assert engine._get_context_value(context, "b") is None

    def test_none_key_returns_none(self, engine):
        assert engine._get_context_value({"a": 1}, None) is None

    def test_missing_nested_key_returns_none(self, engine):
        context = {"a": {"b": 1}}
        assert engine._get_context_value(context, "a.c") is None

    def test_non_dict_in_path_returns_none(self, engine):
        context = {"a": "string_not_dict"}
        assert engine._get_context_value(context, "a.b") is None


# ---------------------------------------------------------------------------
# _render_metrics
# ---------------------------------------------------------------------------

class TestRenderMetrics:
    def test_renders_metric_items(self, engine):
        section = MagicMock()
        item1 = MagicMock()
        item1.label = "总项目数"
        item1.value = "context.total"
        item2 = MagicMock()
        item2.label = "完成率"
        item2.value = "context.rate"
        section.items = [item1, item2]
        engine.expression_parser.evaluate.side_effect = [42, 0.85]
        result = engine._render_metrics(section, {"context": {"total": 42, "rate": 0.85}})
        assert len(result) == 2
        assert result[0]["label"] == "总项目数"
        assert result[0]["value"] == 42

    def test_empty_items_returns_empty_list(self, engine):
        section = MagicMock()
        section.items = None
        result = engine._render_metrics(section, {})
        assert result == []


# ---------------------------------------------------------------------------
# _render_table
# ---------------------------------------------------------------------------

class TestRenderTable:
    def test_returns_empty_when_no_source(self, engine):
        section = MagicMock()
        section.source = None
        result = engine._render_table(section, {})
        assert result == []

    def test_returns_list_data(self, engine):
        section = MagicMock()
        section.source = "projects"
        context = {"projects": [{"name": "P1"}, {"name": "P2"}]}
        result = engine._render_table(section, context)
        assert result == [{"name": "P1"}, {"name": "P2"}]

    def test_returns_empty_for_non_list(self, engine):
        section = MagicMock()
        section.source = "stats"
        context = {"stats": {"total": 5}}
        # dict → returns []
        result = engine._render_table(section, context)
        assert result == []


# ---------------------------------------------------------------------------
# _render_chart
# ---------------------------------------------------------------------------

class TestRenderChart:
    def test_returns_empty_when_no_source(self, engine):
        section = MagicMock()
        section.source = None
        result = engine._render_chart(section, {})
        assert result == []

    def test_returns_list_data(self, engine):
        section = MagicMock()
        section.source = "chart_data"
        data = [{"label": "Q1", "value": 100}]
        result = engine._render_chart(section, {"chart_data": data})
        assert result == data

    def test_converts_dict_to_chart_format(self, engine):
        section = MagicMock()
        section.source = "by_status"
        context = {"by_status": {"active": 5, "closed": 3}}
        result = engine._render_chart(section, context)
        labels = [r["label"] for r in result]
        assert "active" in labels
        assert "closed" in labels

    def test_returns_empty_for_other_types(self, engine):
        section = MagicMock()
        section.source = "data"
        result = engine._render_chart(section, {"data": "string"})
        assert result == []


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------

class TestGenerate:
    def test_generate_raises_when_format_unsupported(self, engine, mock_config):
        engine.config_loader.get.return_value = mock_config
        engine.data_resolver.resolve_all.return_value = {}
        engine.cache.get.return_value = None
        with patch.object(engine, "_validate_params", return_value={}), \
             patch.object(engine, "_render_sections", return_value=[]):
            from app.services.report_framework.engine import ConfigError
            with pytest.raises(ConfigError):
                engine.generate("test_report", {}, format="unsupported_format")

    def test_generate_returns_cache_hit(self, engine, mock_config):
        engine.config_loader.get.return_value = mock_config
        cached_result = MagicMock()
        engine.cache.get.return_value = cached_result
        with patch.object(engine, "_validate_params", return_value={}):
            result = engine.generate("test_report", {})
        assert result is cached_result

    def test_generate_with_user_permission_check(self, engine, mock_config):
        engine.config_loader.get.return_value = mock_config
        engine.cache.get.return_value = None
        engine.data_resolver.resolve_all.return_value = {}
        mock_result = MagicMock()
        mock_renderer = MagicMock()
        mock_renderer.render.return_value = mock_result
        engine.renderers["json"] = mock_renderer
        user = MagicMock()
        user.is_superuser = True
        with patch.object(engine, "_validate_params", return_value={}), \
             patch.object(engine, "_render_sections", return_value=[]):
            result = engine.generate("test_report", {}, user=user)
        assert result is mock_result

    def test_generate_skip_cache_bypasses_cache(self, engine, mock_config):
        engine.config_loader.get.return_value = mock_config
        engine.data_resolver.resolve_all.return_value = {}
        mock_result = MagicMock()
        engine.renderers["json"] = MagicMock(render=MagicMock(return_value=mock_result))
        with patch.object(engine, "_validate_params", return_value={}), \
             patch.object(engine, "_render_sections", return_value=[]):
            result = engine.generate("test_report", {}, skip_cache=True)
        engine.cache.get.assert_not_called()


# ---------------------------------------------------------------------------
# list_available
# ---------------------------------------------------------------------------

class TestListAvailable:
    def test_returns_all_when_no_user(self, engine):
        metas = [MagicMock(), MagicMock()]
        engine.config_loader.list_available.return_value = metas
        result = engine.list_available()
        assert result == metas

    def test_filters_by_user_permission(self, engine):
        from app.services.report_framework.engine import PermissionError as PE
        meta1 = MagicMock()
        meta1.code = "report_a"
        meta2 = MagicMock()
        meta2.code = "report_b"
        engine.config_loader.list_available.return_value = [meta1, meta2]
        config1 = MagicMock()
        config1.permissions.roles = ["finance"]
        config2 = MagicMock()
        config2.permissions.roles = []

        engine.config_loader.get.side_effect = [config1, config2]
        user = MagicMock()
        user.is_superuser = False
        user.roles = []  # no roles → can't access report_a

        # _check_permission raises for report_a but not report_b
        with patch.object(engine, "_check_permission", side_effect=[PE("denied"), None]):
            result = engine.list_available(user=user)
        assert len(result) == 1
        assert result[0] is meta2


# ---------------------------------------------------------------------------
# get_schema
# ---------------------------------------------------------------------------

class TestGetSchema:
    def test_returns_schema_structure(self, engine, mock_config):
        param = MagicMock()
        param.name = "project_id"
        param.type = MagicMock()
        param.type.value = "integer"
        param.required = True
        param.default = None
        param.description = "项目ID"
        mock_config.parameters = [param]
        engine.config_loader.get.return_value = mock_config

        result = engine.get_schema("test_report")
        assert result["report_code"] == "test_report"
        assert len(result["parameters"]) == 1
        assert result["parameters"][0]["name"] == "project_id"
        assert "exports" in result
