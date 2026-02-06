# -*- coding: utf-8 -*-
"""
ReportEngine 综合单元测试

测试覆盖:
- __init__: 初始化报告引擎
- generate: 生成报告
- list_available: 列出可用报告
- get_schema: 获取报告参数模式
- register_renderer: 注册渲染器
- _check_permission: 检查权限
- _validate_params: 验证参数
- _convert_param_type: 转换参数类型
- _render_sections: 渲染sections
- _render_section: 渲染单个section
- _get_context_value: 获取上下文值
"""

from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, date
from decimal import Decimal

import pytest


class TestReportEngineInit:
    """测试 ReportEngine 初始化"""

    def test_initializes_with_db(self):
        """测试使用数据库会话初始化"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

        assert engine.db == mock_db

    def test_initializes_config_loader(self):
        """测试初始化配置加载器"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()

        with patch('app.services.report_framework.engine.ConfigLoader') as MockConfigLoader:
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db, config_dir="test_configs")

        MockConfigLoader.assert_called_once_with("test_configs")

    def test_initializes_with_custom_cache_manager(self):
        """测试使用自定义缓存管理器初始化"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()
        mock_cache = MagicMock()

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                engine = ReportEngine(mock_db, cache_manager=mock_cache)

        assert engine.cache == mock_cache

    def test_registers_json_renderer(self):
        """测试注册JSON渲染器"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

        assert "json" in engine.renderers


class TestGenerate:
    """测试 generate 方法"""

    def test_generates_report_successfully(self):
        """测试成功生成报告"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.meta.code = "test_report"
        mock_config.meta.name = "测试报告"
        mock_config.parameters = []
        mock_config.data_sources = []
        mock_config.sections = []

        mock_result = MagicMock()

        with patch('app.services.report_framework.engine.ConfigLoader') as MockConfigLoader:
            with patch('app.services.report_framework.engine.DataResolver') as MockDataResolver:
                with patch('app.services.report_framework.engine.CacheManager') as MockCacheManager:
                    mock_loader_instance = MockConfigLoader.return_value
                    mock_loader_instance.get.return_value = mock_config

                    mock_resolver_instance = MockDataResolver.return_value
                    mock_resolver_instance.resolve_all.return_value = {}

                    mock_cache_instance = MockCacheManager.return_value
                    mock_cache_instance.get.return_value = None

                    engine = ReportEngine(mock_db)

                    mock_renderer = MagicMock()
                    mock_renderer.render.return_value = mock_result
                    engine.renderers["json"] = mock_renderer

                    result = engine.generate("test_report", {}, format="json", skip_cache=True)

        assert result == mock_result

    def test_returns_cached_result(self):
        """测试返回缓存结果"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.parameters = []

        mock_cached_result = MagicMock()

        with patch('app.services.report_framework.engine.ConfigLoader') as MockConfigLoader:
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager') as MockCacheManager:
                    mock_loader_instance = MockConfigLoader.return_value
                    mock_loader_instance.get.return_value = mock_config

                    mock_cache_instance = MockCacheManager.return_value
                    mock_cache_instance.get.return_value = mock_cached_result

                    engine = ReportEngine(mock_db)

                    result = engine.generate("test_report", {})

        assert result == mock_cached_result

    def test_checks_user_permission(self):
        """测试检查用户权限"""
        from app.services.report_framework.engine import ReportEngine, PermissionError

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.meta.code = "test_report"
        mock_config.parameters = []
        mock_config.permissions.roles = ["admin"]

        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.roles = []

        with patch('app.services.report_framework.engine.ConfigLoader') as MockConfigLoader:
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager') as MockCacheManager:
                    mock_loader_instance = MockConfigLoader.return_value
                    mock_loader_instance.get.return_value = mock_config

                    mock_cache_instance = MockCacheManager.return_value
                    mock_cache_instance.get.return_value = None

                    engine = ReportEngine(mock_db)

                    with pytest.raises(PermissionError):
                        engine.generate("test_report", {}, user=mock_user)


class TestListAvailable:
    """测试 list_available 方法"""

    def test_returns_all_reports_without_user(self):
        """测试无用户时返回所有报告"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()

        mock_meta1 = MagicMock()
        mock_meta1.code = "report1"
        mock_meta2 = MagicMock()
        mock_meta2.code = "report2"

        with patch('app.services.report_framework.engine.ConfigLoader') as MockConfigLoader:
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    mock_loader_instance = MockConfigLoader.return_value
                    mock_loader_instance.list_available.return_value = [mock_meta1, mock_meta2]

                    engine = ReportEngine(mock_db)

                    result = engine.list_available()

        assert len(result) == 2

    def test_filters_by_user_permission(self):
        """测试按用户权限过滤"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()

        mock_meta1 = MagicMock()
        mock_meta1.code = "report1"

        mock_config = MagicMock()
        mock_config.permissions.roles = []

        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.roles = []

        with patch('app.services.report_framework.engine.ConfigLoader') as MockConfigLoader:
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    mock_loader_instance = MockConfigLoader.return_value
                    mock_loader_instance.list_available.return_value = [mock_meta1]
                    mock_loader_instance.get.return_value = mock_config

                    engine = ReportEngine(mock_db)

                    result = engine.list_available(user=mock_user)

        assert len(result) == 1


class TestGetSchema:
    """测试 get_schema 方法"""

    def test_returns_schema_dict(self):
        """测试返回模式字典"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()

        mock_param = MagicMock()
        mock_param.name = "start_date"
        mock_param.type = MagicMock()
        mock_param.type.value = "date"
        mock_param.required = True
        mock_param.default = None
        mock_param.description = "开始日期"

        mock_exports = MagicMock()
        mock_exports.json_export.enabled = True
        mock_exports.pdf.enabled = True
        mock_exports.excel.enabled = True
        mock_exports.word.enabled = False

        mock_config = MagicMock()
        mock_config.meta.code = "test_report"
        mock_config.meta.name = "测试报告"
        mock_config.meta.description = "测试报告描述"
        mock_config.parameters = [mock_param]
        mock_config.exports = mock_exports

        with patch('app.services.report_framework.engine.ConfigLoader') as MockConfigLoader:
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    mock_loader_instance = MockConfigLoader.return_value
                    mock_loader_instance.get.return_value = mock_config

                    engine = ReportEngine(mock_db)

                    result = engine.get_schema("test_report")

        assert result["report_code"] == "test_report"
        assert result["report_name"] == "测试报告"
        assert len(result["parameters"]) == 1
        assert "exports" in result


class TestRegisterRenderer:
    """测试 register_renderer 方法"""

    def test_registers_new_renderer(self):
        """测试注册新渲染器"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()
        mock_renderer = MagicMock()

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

                    engine.register_renderer("custom", mock_renderer)

        assert engine.renderers["custom"] == mock_renderer


class TestCheckPermission:
    """测试 _check_permission 方法"""

    def test_allows_superuser(self):
        """测试允许超级管理员"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.permissions.roles = ["admin"]

        mock_user = MagicMock()
        mock_user.is_superuser = True

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

                    # Should not raise
                    engine._check_permission(mock_config, mock_user)

    def test_allows_matching_role(self):
        """测试允许匹配角色"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.permissions.roles = ["admin", "manager"]

        mock_role = MagicMock()
        mock_role.role_code = "manager"

        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.roles = [mock_role]

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

                    # Should not raise
                    engine._check_permission(mock_config, mock_user)

    def test_raises_for_no_permission(self):
        """测试无权限时抛出异常"""
        from app.services.report_framework.engine import ReportEngine, PermissionError

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.meta.code = "test_report"
        mock_config.permissions.roles = ["admin"]

        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.roles = []

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

                    with pytest.raises(PermissionError):
                        engine._check_permission(mock_config, mock_user)

    def test_allows_empty_role_config(self):
        """测试允许空角色配置"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.permissions.roles = []

        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.roles = []

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

                    # Should not raise - no role restriction
                    engine._check_permission(mock_config, mock_user)


class TestValidateParams:
    """测试 _validate_params 方法"""

    def test_validates_required_params(self):
        """测试验证必填参数"""
        from app.services.report_framework.engine import ReportEngine, ParameterError

        mock_db = MagicMock()

        mock_param = MagicMock()
        mock_param.name = "project_id"
        mock_param.required = True
        mock_param.default = None
        mock_param.type = "integer"

        mock_config = MagicMock()
        mock_config.parameters = [mock_param]

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

                    with pytest.raises(ParameterError):
                        engine._validate_params(mock_config, {})

    def test_uses_default_value(self):
        """测试使用默认值"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()

        mock_param = MagicMock()
        mock_param.name = "page_size"
        mock_param.required = False
        mock_param.default = 20
        mock_param.type = MagicMock()
        mock_param.type.value = "integer"

        mock_config = MagicMock()
        mock_config.parameters = [mock_param]

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

                    result = engine._validate_params(mock_config, {})

        assert result["page_size"] == 20


class TestConvertParamType:
    """测试 _convert_param_type 方法"""

    def test_converts_integer(self):
        """测试转换整数"""
        from app.services.report_framework.engine import ReportEngine, ParameterType

        mock_db = MagicMock()

        mock_param_type = MagicMock()
        mock_param_type.value = "integer"

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

                    result = engine._convert_param_type("42", mock_param_type)

        assert result == 42

    def test_converts_float(self):
        """测试转换浮点数"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()

        mock_param_type = MagicMock()
        mock_param_type.value = "float"

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

                    result = engine._convert_param_type("3.14", mock_param_type)

        assert result == 3.14

    def test_converts_boolean_true(self):
        """测试转换布尔值true"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()

        mock_param_type = MagicMock()
        mock_param_type.value = "boolean"

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

                    result = engine._convert_param_type("true", mock_param_type)

        assert result is True

    def test_converts_boolean_false(self):
        """测试转换布尔值false"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()

        mock_param_type = MagicMock()
        mock_param_type.value = "boolean"

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

                    result = engine._convert_param_type("false", mock_param_type)

        assert result is False

    def test_converts_date(self):
        """测试转换日期"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()

        mock_param_type = MagicMock()
        mock_param_type.value = "date"

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

                    result = engine._convert_param_type("2024-01-15", mock_param_type)

        assert result == date(2024, 1, 15)

    def test_converts_string(self):
        """测试转换字符串"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()

        mock_param_type = MagicMock()
        mock_param_type.value = "string"

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

                    result = engine._convert_param_type(123, mock_param_type)

        assert result == "123"

    def test_converts_list(self):
        """测试转换列表"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()

        mock_param_type = MagicMock()
        mock_param_type.value = "list"

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

                    result = engine._convert_param_type("single", mock_param_type)

        assert result == ["single"]

    def test_raises_for_invalid_value(self):
        """测试无效值时抛出异常"""
        from app.services.report_framework.engine import ReportEngine, ParameterError

        mock_db = MagicMock()

        mock_param_type = MagicMock()
        mock_param_type.value = "integer"

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

                    with pytest.raises(ParameterError):
                        engine._convert_param_type("not_a_number", mock_param_type)


class TestRenderSections:
    """测试 _render_sections 方法"""

    def test_renders_all_sections(self):
        """测试渲染所有sections"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()

        mock_section1 = MagicMock()
        mock_section1.id = "section1"
        mock_section1.title = "Section 1"
        mock_section1.type = "metrics"
        mock_section1.items = []

        mock_section2 = MagicMock()
        mock_section2.id = "section2"
        mock_section2.title = "Section 2"
        mock_section2.type = "table"
        mock_section2.source = None
        mock_section2.columns = []

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

                    result = engine._render_sections([mock_section1, mock_section2], {})

        assert len(result) == 2


class TestRenderSection:
    """测试 _render_section 方法"""

    def test_renders_metrics_section(self):
        """测试渲染指标section"""
        from app.services.report_framework.engine import ReportEngine
        from app.services.report_framework.models import SectionType

        mock_db = MagicMock()

        mock_item = MagicMock()
        mock_item.label = "总数"
        mock_item.value = "data.count"

        mock_section = MagicMock()
        mock_section.id = "metrics"
        mock_section.title = "关键指标"
        mock_section.type = SectionType.METRICS
        mock_section.items = [mock_item]

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)
                    engine.expression_parser = MagicMock()
                    engine.expression_parser.evaluate.return_value = 100

                    result = engine._render_section(mock_section, {"data": {"count": 100}})

        assert result["id"] == "metrics"
        assert result["type"] == "metrics"
        assert "items" in result

    def test_renders_table_section(self):
        """测试渲染表格section"""
        from app.services.report_framework.engine import ReportEngine
        from app.services.report_framework.models import SectionType

        mock_db = MagicMock()

        mock_column = MagicMock()
        mock_column.field = "name"
        mock_column.label = "名称"
        mock_column.format = None

        mock_section = MagicMock()
        mock_section.id = "table1"
        mock_section.title = "数据表"
        mock_section.type = SectionType.TABLE
        mock_section.source = "projects"
        mock_section.columns = [mock_column]

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

                    result = engine._render_section(
                        mock_section,
                        {"projects": [{"name": "项目A"}, {"name": "项目B"}]}
                    )

        assert result["id"] == "table1"
        assert result["type"] == "table"
        assert "data" in result
        assert "columns" in result

    def test_renders_chart_section(self):
        """测试渲染图表section"""
        from app.services.report_framework.engine import ReportEngine
        from app.services.report_framework.models import SectionType

        mock_db = MagicMock()

        mock_section = MagicMock()
        mock_section.id = "chart1"
        mock_section.title = "统计图"
        mock_section.type = SectionType.CHART
        mock_section.chart_type = "bar"
        mock_section.source = "stats"

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

                    result = engine._render_section(
                        mock_section,
                        {"stats": [{"label": "A", "value": 10}]}
                    )

        assert result["id"] == "chart1"
        assert result["type"] == "chart"
        assert result["chart_type"] == "bar"


class TestGetContextValue:
    """测试 _get_context_value 方法"""

    def test_returns_direct_value(self):
        """测试返回直接值"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

                    result = engine._get_context_value({"key": "value"}, "key")

        assert result == "value"

    def test_returns_nested_value(self):
        """测试返回嵌套值"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()

        context = {
            "data": {
                "nested": {
                    "value": 42
                }
            }
        }

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

                    result = engine._get_context_value(context, "data.nested.value")

        assert result == 42

    def test_returns_none_for_missing(self):
        """测试缺失时返回None"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

                    result = engine._get_context_value({}, "nonexistent")

        assert result is None

    def test_returns_none_for_none_key(self):
        """测试空key返回None"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

                    result = engine._get_context_value({"key": "value"}, None)

        assert result is None


class TestRenderChart:
    """测试 _render_chart 方法"""

    def test_returns_list_data(self):
        """测试返回列表数据"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()

        mock_section = MagicMock()
        mock_section.source = "chart_data"

        chart_data = [{"label": "A", "value": 10}, {"label": "B", "value": 20}]

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

                    result = engine._render_chart(mock_section, {"chart_data": chart_data})

        assert result == chart_data

    def test_converts_dict_to_chart_format(self):
        """测试将字典转换为图表格式"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()

        mock_section = MagicMock()
        mock_section.source = "grouped_data"

        grouped_data = {"Category A": 10, "Category B": 20}

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

                    result = engine._render_chart(mock_section, {"grouped_data": grouped_data})

        assert len(result) == 2
        labels = [item["label"] for item in result]
        assert "Category A" in labels
        assert "Category B" in labels

    def test_returns_empty_for_no_source(self):
        """测试无来源时返回空列表"""
        from app.services.report_framework.engine import ReportEngine

        mock_db = MagicMock()

        mock_section = MagicMock()
        mock_section.source = None

        with patch('app.services.report_framework.engine.ConfigLoader'):
            with patch('app.services.report_framework.engine.DataResolver'):
                with patch('app.services.report_framework.engine.CacheManager'):
                    engine = ReportEngine(mock_db)

                    result = engine._render_chart(mock_section, {})

        assert result == []
