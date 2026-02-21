# -*- coding: utf-8 -*-
"""
报告引擎单元测试

目标：
1. 只mock外部依赖（db、config_loader、data_resolver等）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, Mock, patch, PropertyMock
from datetime import datetime, date

from app.services.report_framework.engine import (
    ReportEngine,
    PermissionError,
    ParameterError,
)
from app.services.report_framework.models import (
    ReportConfig,
    ReportMeta,
    PermissionConfig,
    ParameterConfig,
    ParameterType,
    SectionConfig,
    SectionType,
    MetricItem,
    TableColumn,
    ChartType,
    ExportConfig,
    JsonExportConfig,
    PdfExportConfig,
    ExcelExportConfig,
    WordExportConfig,
)
from app.services.report_framework.renderers import ReportResult


class TestReportEngineInit(unittest.TestCase):
    """测试引擎初始化"""

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    @patch("app.services.report_framework.engine.ReportCacheManager")
    @patch("app.services.report_framework.engine.ExpressionParser")
    def test_init_with_defaults(
        self, mock_parser, mock_cache, mock_resolver, mock_loader
    ):
        """测试默认初始化"""
        db = MagicMock()
        engine = ReportEngine(db)

        self.assertEqual(engine.db, db)
        mock_loader.assert_called_once_with("app/report_configs")
        mock_resolver.assert_called_once_with(db)
        mock_cache.assert_called_once()
        mock_parser.assert_called_once()

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    @patch("app.services.report_framework.engine.ExpressionParser")
    def test_init_with_custom_params(self, mock_parser, mock_resolver, mock_loader):
        """测试自定义参数初始化"""
        db = MagicMock()
        cache = MagicMock()
        engine = ReportEngine(db, config_dir="custom/dir", cache_manager=cache)

        self.assertEqual(engine.db, db)
        self.assertEqual(engine.cache, cache)
        mock_loader.assert_called_once_with("custom/dir")

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    @patch("app.services.report_framework.engine.ReportCacheManager")
    @patch("app.services.report_framework.engine.ExpressionParser")
    def test_renderers_registered(
        self, mock_parser, mock_cache, mock_resolver, mock_loader
    ):
        """测试渲染器注册"""
        db = MagicMock()
        engine = ReportEngine(db)

        # JSON渲染器应该始终注册
        self.assertIn("json", engine.renderers)


class TestReportEngineGenerate(unittest.TestCase):
    """测试报告生成"""

    def setUp(self):
        """测试准备"""
        self.db = MagicMock()
        
        # Mock dependencies
        with patch("app.services.report_framework.engine.ConfigLoader"), \
             patch("app.services.report_framework.engine.DataResolver"), \
             patch("app.services.report_framework.engine.ReportCacheManager"), \
             patch("app.services.report_framework.engine.ExpressionParser"):
            self.engine = ReportEngine(self.db)

        # 创建测试配置
        self.test_config = ReportConfig(
            meta=ReportMeta(
                code="test_report",
                name="测试报告",
                description="测试用报告",
            ),
            permissions=PermissionConfig(roles=["admin"]),
            parameters=[
                ParameterConfig(
                    name="start_date",
                    type=ParameterType.DATE,
                    required=True,
                ),
                ParameterConfig(
                    name="end_date",
                    type=ParameterType.DATE,
                    required=False,
                    default="2024-12-31",
                ),
                ParameterConfig(
                    name="amount",
                    type=ParameterType.INTEGER,
                    default=1000,
                ),
            ],
            sections=[
                SectionConfig(
                    id="metrics",
                    title="关键指标",
                    type=SectionType.METRICS,
                    items=[
                        MetricItem(label="总数", value="{{ total }}"),
                        MetricItem(label="平均值", value="{{ average }}"),
                    ],
                ),
            ],
            exports=ExportConfig(
                json_export=JsonExportConfig(enabled=True),
            ),
        )

    @patch.object(ReportEngine, "_check_permission")
    @patch.object(ReportEngine, "_validate_params")
    @patch.object(ReportEngine, "_render_sections")
    def test_generate_success(self, mock_render, mock_validate, mock_check):
        """测试成功生成报告"""
        # Mock配置加载
        self.engine.config_loader.get = MagicMock(return_value=self.test_config)
        
        # Mock数据解析
        self.engine.data_resolver.resolve_all = MagicMock(
            return_value={"total": 100, "average": 50}
        )
        
        # Mock参数验证
        validated_params = {"start_date": date(2024, 1, 1)}
        mock_validate.return_value = validated_params
        
        # Mock section渲染
        mock_render.return_value = [
            {
                "id": "metrics",
                "title": "关键指标",
                "type": "metrics",
                "items": [
                    {"label": "总数", "value": 100},
                    {"label": "平均值", "value": 50},
                ],
            }
        ]
        
        # Mock渲染器
        mock_renderer = MagicMock()
        mock_result = ReportResult(
            data={"sections": []},
            format="json",
            file_name="test.json",
        )
        mock_renderer.render = MagicMock(return_value=mock_result)
        self.engine.renderers["json"] = mock_renderer
        
        # Mock缓存（未命中）
        self.engine.cache.get = MagicMock(return_value=None)
        self.engine.cache.set = MagicMock()

        # 执行生成
        user = MagicMock()
        result = self.engine.generate(
            "test_report",
            {"start_date": "2024-01-01"},
            format="json",
            user=user,
        )

        # 验证
        self.assertEqual(result, mock_result)
        mock_check.assert_called_once_with(self.test_config, user)
        mock_validate.assert_called_once()
        self.engine.data_resolver.resolve_all.assert_called_once()
        mock_render.assert_called_once()
        self.engine.cache.set.assert_called_once()

    def test_generate_use_cache(self):
        """测试使用缓存"""
        self.engine.config_loader.get = MagicMock(return_value=self.test_config)
        
        # Mock缓存命中
        cached_result = ReportResult(
            data={"cached": True},
            format="json",
            file_name="cached.json",
        )
        self.engine.cache.get = MagicMock(return_value=cached_result)

        result = self.engine.generate(
            "test_report",
            {"start_date": "2024-01-01"},
        )

        self.assertEqual(result, cached_result)
        # 不应该调用数据解析
        self.engine.data_resolver.resolve_all.assert_not_called()

    def test_generate_skip_cache(self):
        """测试跳过缓存"""
        self.engine.config_loader.get = MagicMock(return_value=self.test_config)
        self.engine.data_resolver.resolve_all = MagicMock(return_value={})
        
        mock_renderer = MagicMock()
        mock_result = ReportResult(data={}, format="json", file_name="test.json")
        mock_renderer.render = MagicMock(return_value=mock_result)
        self.engine.renderers["json"] = mock_renderer
        
        self.engine.cache.get = MagicMock(return_value=None)
        self.engine.cache.set = MagicMock()

        # Mock expression parser
        self.engine.expression_parser = MagicMock()
        self.engine.expression_parser.evaluate = MagicMock(return_value=0)

        result = self.engine.generate(
            "test_report",
            {"start_date": "2024-01-01"},
            skip_cache=True,
        )

        # cache.get 不应被调用（skip_cache=True）
        self.engine.cache.get.assert_not_called()
        # cache.set 也不应被调用（skip_cache=True）
        self.engine.cache.set.assert_not_called()

    def test_generate_unsupported_format(self):
        """测试不支持的格式"""
        self.engine.config_loader.get = MagicMock(return_value=self.test_config)
        self.engine.data_resolver.resolve_all = MagicMock(return_value={})
        self.engine.cache.get = MagicMock(return_value=None)

        with self.assertRaises(Exception) as ctx:
            self.engine.generate(
                "test_report",
                {"start_date": "2024-01-01"},
                format="unknown",
            )
        
        self.assertIn("Unsupported format", str(ctx.exception))


class TestCheckPermission(unittest.TestCase):
    """测试权限检查"""

    def setUp(self):
        with patch("app.services.report_framework.engine.ConfigLoader"), \
             patch("app.services.report_framework.engine.DataResolver"), \
             patch("app.services.report_framework.engine.ReportCacheManager"), \
             patch("app.services.report_framework.engine.ExpressionParser"):
            self.engine = ReportEngine(MagicMock())

    def test_superuser_always_allowed(self):
        """测试超级管理员无条件通过"""
        config = ReportConfig(
            meta=ReportMeta(code="test", name="Test"),
            permissions=PermissionConfig(roles=["admin"]),
        )
        user = MagicMock()
        user.is_superuser = True

        # 不应抛出异常
        self.engine._check_permission(config, user)

    def test_user_with_matching_role(self):
        """测试匹配角色的用户"""
        config = ReportConfig(
            meta=ReportMeta(code="test", name="Test"),
            permissions=PermissionConfig(roles=["admin", "manager"]),
        )
        
        role = MagicMock()
        role.role_code = "admin"
        
        user = MagicMock()
        user.is_superuser = False
        user.roles = [role]

        self.engine._check_permission(config, user)

    def test_user_with_nested_role(self):
        """测试嵌套角色结构"""
        config = ReportConfig(
            meta=ReportMeta(code="test", name="Test"),
            permissions=PermissionConfig(roles=["manager"]),
        )
        
        # 创建嵌套角色结构
        nested_role = MagicMock()
        nested_role.role_code = "manager"
        
        user_role = MagicMock()
        # 确保 hasattr(role, "role_code") 返回 False
        del user_role.role_code
        user_role.role = nested_role
        
        user = MagicMock()
        user.is_superuser = False
        user.roles = [user_role]

        self.engine._check_permission(config, user)

    def test_user_without_permission(self):
        """测试无权限用户"""
        config = ReportConfig(
            meta=ReportMeta(code="test", name="Test"),
            permissions=PermissionConfig(roles=["admin"]),
        )
        
        role = MagicMock()
        role.role_code = "guest"
        
        user = MagicMock()
        user.is_superuser = False
        user.roles = [role]

        with self.assertRaises(PermissionError) as ctx:
            self.engine._check_permission(config, user)
        
        self.assertIn("does not have permission", str(ctx.exception))

    def test_no_role_restriction(self):
        """测试无角色限制（允许所有人）"""
        config = ReportConfig(
            meta=ReportMeta(code="test", name="Test"),
            permissions=PermissionConfig(roles=[]),
        )
        
        user = MagicMock()
        user.is_superuser = False
        user.roles = []

        self.engine._check_permission(config, user)


class TestValidateParams(unittest.TestCase):
    """测试参数验证"""

    def setUp(self):
        with patch("app.services.report_framework.engine.ConfigLoader"), \
             patch("app.services.report_framework.engine.DataResolver"), \
             patch("app.services.report_framework.engine.ReportCacheManager"), \
             patch("app.services.report_framework.engine.ExpressionParser"):
            self.engine = ReportEngine(MagicMock())

    def test_validate_required_params(self):
        """测试必填参数"""
        config = ReportConfig(
            meta=ReportMeta(code="test", name="Test"),
            parameters=[
                ParameterConfig(name="user_id", type=ParameterType.INTEGER, required=True),
            ],
        )

        # 缺少必填参数
        with self.assertRaises(ParameterError) as ctx:
            self.engine._validate_params(config, {})
        
        self.assertIn("Required parameter missing", str(ctx.exception))

        # 提供必填参数
        result = self.engine._validate_params(config, {"user_id": "123"})
        self.assertEqual(result["user_id"], 123)

    def test_validate_with_defaults(self):
        """测试默认值"""
        config = ReportConfig(
            meta=ReportMeta(code="test", name="Test"),
            parameters=[
                ParameterConfig(
                    name="limit",
                    type=ParameterType.INTEGER,
                    default=10,
                ),
            ],
        )

        result = self.engine._validate_params(config, {})
        self.assertEqual(result["limit"], 10)

    def test_validate_type_conversion(self):
        """测试类型转换"""
        config = ReportConfig(
            meta=ReportMeta(code="test", name="Test"),
            parameters=[
                ParameterConfig(name="count", type=ParameterType.INTEGER),
                ParameterConfig(name="active", type=ParameterType.BOOLEAN),
                ParameterConfig(name="rate", type=ParameterType.FLOAT),
            ],
        )

        result = self.engine._validate_params(
            config,
            {"count": "42", "active": "true", "rate": "3.14"},
        )

        self.assertEqual(result["count"], 42)
        self.assertEqual(result["active"], True)
        self.assertAlmostEqual(result["rate"], 3.14)


class TestConvertParamType(unittest.TestCase):
    """测试参数类型转换"""

    def setUp(self):
        with patch("app.services.report_framework.engine.ConfigLoader"), \
             patch("app.services.report_framework.engine.DataResolver"), \
             patch("app.services.report_framework.engine.ReportCacheManager"), \
             patch("app.services.report_framework.engine.ExpressionParser"):
            self.engine = ReportEngine(MagicMock())

    def test_convert_integer(self):
        """测试整数转换"""
        result = self.engine._convert_param_type("123", ParameterType.INTEGER)
        self.assertEqual(result, 123)

    def test_convert_float(self):
        """测试浮点数转换"""
        result = self.engine._convert_param_type("3.14", ParameterType.FLOAT)
        self.assertAlmostEqual(result, 3.14)

    def test_convert_boolean_true(self):
        """测试布尔值转换 - True"""
        self.assertTrue(self.engine._convert_param_type("true", ParameterType.BOOLEAN))
        self.assertTrue(self.engine._convert_param_type("1", ParameterType.BOOLEAN))
        self.assertTrue(self.engine._convert_param_type("yes", ParameterType.BOOLEAN))
        self.assertTrue(self.engine._convert_param_type(True, ParameterType.BOOLEAN))

    def test_convert_boolean_false(self):
        """测试布尔值转换 - False"""
        self.assertFalse(self.engine._convert_param_type("false", ParameterType.BOOLEAN))
        self.assertFalse(self.engine._convert_param_type("0", ParameterType.BOOLEAN))
        self.assertFalse(self.engine._convert_param_type("no", ParameterType.BOOLEAN))

    def test_convert_date(self):
        """测试日期转换"""
        result = self.engine._convert_param_type("2024-01-15", ParameterType.DATE)
        self.assertEqual(result, date(2024, 1, 15))

    def test_convert_date_already_date(self):
        """测试已经是date对象"""
        input_date = date(2024, 1, 15)
        result = self.engine._convert_param_type(input_date, ParameterType.DATE)
        self.assertEqual(result, input_date)

    def test_convert_string(self):
        """测试字符串转换"""
        result = self.engine._convert_param_type(123, ParameterType.STRING)
        self.assertEqual(result, "123")

    def test_convert_list(self):
        """测试列表转换"""
        result = self.engine._convert_param_type([1, 2, 3], ParameterType.LIST)
        self.assertEqual(result, [1, 2, 3])

        result = self.engine._convert_param_type("single", ParameterType.LIST)
        self.assertEqual(result, ["single"])

    def test_convert_invalid_value(self):
        """测试无效值"""
        with self.assertRaises(ParameterError):
            self.engine._convert_param_type("invalid", ParameterType.INTEGER)

        with self.assertRaises(ParameterError):
            self.engine._convert_param_type("not-a-date", ParameterType.DATE)


class TestRenderSections(unittest.TestCase):
    """测试Section渲染"""

    def setUp(self):
        with patch("app.services.report_framework.engine.ConfigLoader"), \
             patch("app.services.report_framework.engine.DataResolver"), \
             patch("app.services.report_framework.engine.ReportCacheManager"), \
             patch("app.services.report_framework.engine.ExpressionParser"):
            self.engine = ReportEngine(MagicMock())

    def test_render_metrics_section(self):
        """测试指标类型Section"""
        section = SectionConfig(
            id="metrics",
            title="关键指标",
            type=SectionType.METRICS,
            items=[
                MetricItem(label="总数", value="{{ total }}"),
                MetricItem(label="平均值", value="{{ average }}"),
            ],
        )

        # Mock expression parser
        self.engine.expression_parser = MagicMock()
        self.engine.expression_parser.evaluate = MagicMock(side_effect=[100, 50])

        context = {"total": 100, "average": 50}
        result = self.engine._render_section(section, context)

        self.assertEqual(result["id"], "metrics")
        self.assertEqual(result["title"], "关键指标")
        self.assertEqual(result["type"], "metrics")
        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(result["items"][0]["label"], "总数")
        self.assertEqual(result["items"][0]["value"], 100)

    def test_render_table_section(self):
        """测试表格类型Section"""
        section = SectionConfig(
            id="table",
            title="数据列表",
            type=SectionType.TABLE,
            source="users",
            columns=[
                TableColumn(field="name", label="姓名"),
                TableColumn(field="age", label="年龄"),
            ],
        )

        context = {
            "users": [
                {"name": "张三", "age": 30},
                {"name": "李四", "age": 25},
            ]
        }

        result = self.engine._render_section(section, context)

        self.assertEqual(result["type"], "table")
        self.assertEqual(len(result["data"]), 2)
        self.assertEqual(len(result["columns"]), 2)
        self.assertEqual(result["data"][0]["name"], "张三")

    def test_render_chart_section(self):
        """测试图表类型Section"""
        section = SectionConfig(
            id="chart",
            title="统计图表",
            type=SectionType.CHART,
            chart_type=ChartType.PIE,
            source="stats",
        )

        context = {
            "stats": [
                {"category": "A", "value": 100},
                {"category": "B", "value": 200},
            ]
        }

        result = self.engine._render_section(section, context)

        self.assertEqual(result["type"], "chart")
        self.assertEqual(result["chart_type"], "pie")
        self.assertEqual(len(result["data"]), 2)

    def test_render_chart_with_dict_data(self):
        """测试图表处理字典数据"""
        section = SectionConfig(
            id="chart",
            type=SectionType.CHART,
            chart_type=ChartType.BAR,
            source="stats",
        )

        context = {
            "stats": {
                "A": 100,
                "B": 200,
                "C": [1, 2, 3],  # 非数字值
            }
        }

        result = self.engine._render_section(section, context)

        self.assertEqual(len(result["data"]), 3)
        # 字典转换为图表格式
        labels = [item["label"] for item in result["data"]]
        self.assertIn("A", labels)
        self.assertIn("B", labels)

    def test_render_table_empty_source(self):
        """测试空数据源"""
        section = SectionConfig(
            id="table",
            type=SectionType.TABLE,
            source=None,
        )

        result = self.engine._render_section(section, {})
        self.assertEqual(result["data"], [])


class TestGetContextValue(unittest.TestCase):
    """测试上下文值获取"""

    def setUp(self):
        with patch("app.services.report_framework.engine.ConfigLoader"), \
             patch("app.services.report_framework.engine.DataResolver"), \
             patch("app.services.report_framework.engine.ReportCacheManager"), \
             patch("app.services.report_framework.engine.ExpressionParser"):
            self.engine = ReportEngine(MagicMock())

    def test_get_simple_value(self):
        """测试简单值获取"""
        context = {"name": "张三"}
        result = self.engine._get_context_value(context, "name")
        self.assertEqual(result, "张三")

    def test_get_nested_value(self):
        """测试嵌套值获取"""
        context = {
            "user": {
                "profile": {
                    "name": "张三"
                }
            }
        }
        result = self.engine._get_context_value(context, "user.profile.name")
        self.assertEqual(result, "张三")

    def test_get_value_not_found(self):
        """测试值不存在"""
        context = {"name": "张三"}
        result = self.engine._get_context_value(context, "age")
        self.assertIsNone(result)

    def test_get_value_nested_not_found(self):
        """测试嵌套路径不存在"""
        context = {"user": {"name": "张三"}}
        result = self.engine._get_context_value(context, "user.profile.name")
        self.assertIsNone(result)

    def test_get_value_empty_key(self):
        """测试空键"""
        result = self.engine._get_context_value({"name": "张三"}, None)
        self.assertIsNone(result)

        result = self.engine._get_context_value({"name": "张三"}, "")
        self.assertIsNone(result)


class TestListAvailable(unittest.TestCase):
    """测试列出可用报告"""

    def setUp(self):
        with patch("app.services.report_framework.engine.ConfigLoader"), \
             patch("app.services.report_framework.engine.DataResolver"), \
             patch("app.services.report_framework.engine.ReportCacheManager"), \
             patch("app.services.report_framework.engine.ExpressionParser"):
            self.engine = ReportEngine(MagicMock())

    def test_list_all_for_no_user(self):
        """测试无用户时返回所有报告"""
        meta_list = [
            ReportMeta(code="report1", name="报告1"),
            ReportMeta(code="report2", name="报告2"),
        ]
        self.engine.config_loader.list_available = MagicMock(return_value=meta_list)

        result = self.engine.list_available()
        self.assertEqual(len(result), 2)

    def test_list_filtered_by_permission(self):
        """测试按权限过滤"""
        meta_list = [
            ReportMeta(code="admin_report", name="管理员报告"),
            ReportMeta(code="user_report", name="用户报告"),
        ]
        self.engine.config_loader.list_available = MagicMock(return_value=meta_list)

        # Mock配置和权限检查
        def mock_get(code):
            if code == "admin_report":
                return ReportConfig(
                    meta=ReportMeta(code=code, name="管理员报告"),
                    permissions=PermissionConfig(roles=["admin"]),
                )
            else:
                return ReportConfig(
                    meta=ReportMeta(code=code, name="用户报告"),
                    permissions=PermissionConfig(roles=[]),
                )

        self.engine.config_loader.get = mock_get

        # 普通用户
        user = MagicMock()
        user.is_superuser = False
        user.roles = []

        result = self.engine.list_available(user)
        # 只能看到无权限限制的报告
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].code, "user_report")


class TestGetSchema(unittest.TestCase):
    """测试获取报告Schema"""

    def setUp(self):
        with patch("app.services.report_framework.engine.ConfigLoader"), \
             patch("app.services.report_framework.engine.DataResolver"), \
             patch("app.services.report_framework.engine.ReportCacheManager"), \
             patch("app.services.report_framework.engine.ExpressionParser"):
            self.engine = ReportEngine(MagicMock())

    def test_get_schema(self):
        """测试获取Schema"""
        config = ReportConfig(
            meta=ReportMeta(
                code="test_report",
                name="测试报告",
                description="这是一个测试报告",
            ),
            parameters=[
                ParameterConfig(
                    name="user_id",
                    type=ParameterType.INTEGER,
                    required=True,
                    description="用户ID",
                ),
                ParameterConfig(
                    name="limit",
                    type=ParameterType.INTEGER,
                    default=10,
                ),
            ],
            exports=ExportConfig(
                json_export=JsonExportConfig(enabled=True),
                pdf=PdfExportConfig(enabled=False),
                excel=ExcelExportConfig(enabled=True),
                word=WordExportConfig(enabled=False),
            ),
        )

        self.engine.config_loader.get = MagicMock(return_value=config)

        schema = self.engine.get_schema("test_report")

        self.assertEqual(schema["report_code"], "test_report")
        self.assertEqual(schema["report_name"], "测试报告")
        self.assertEqual(len(schema["parameters"]), 2)
        self.assertTrue(schema["exports"]["json"])
        self.assertFalse(schema["exports"]["pdf"])
        self.assertTrue(schema["exports"]["excel"])


class TestRegisterRenderer(unittest.TestCase):
    """测试注册渲染器"""

    def setUp(self):
        with patch("app.services.report_framework.engine.ConfigLoader"), \
             patch("app.services.report_framework.engine.DataResolver"), \
             patch("app.services.report_framework.engine.ReportCacheManager"), \
             patch("app.services.report_framework.engine.ExpressionParser"):
            self.engine = ReportEngine(MagicMock())

    def test_register_custom_renderer(self):
        """测试注册自定义渲染器"""
        custom_renderer = MagicMock()
        self.engine.register_renderer("custom", custom_renderer)

        self.assertIn("custom", self.engine.renderers)
        self.assertEqual(self.engine.renderers["custom"], custom_renderer)


class TestExceptions(unittest.TestCase):
    """测试异常类"""

    def test_permission_error(self):
        """测试权限错误"""
        error = PermissionError("无权限")
        self.assertEqual(str(error), "无权限")
        self.assertIsInstance(error, Exception)

    def test_parameter_error(self):
        """测试参数错误"""
        error = ParameterError("参数无效")
        self.assertEqual(str(error), "参数无效")
        self.assertIsInstance(error, Exception)


if __name__ == "__main__":
    unittest.main()
