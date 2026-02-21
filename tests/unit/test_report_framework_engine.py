# -*- coding: utf-8 -*-
"""
报告引擎单元测试

目标:
1. 参考 test_condition_parser_rewrite.py 的mock策略
2. 只mock外部依赖（db.query, db.add, db.commit等）
3. 让业务逻辑真正执行
4. 覆盖主要方法和边界情况
5. 目标覆盖率: 70%+
"""

import unittest
from datetime import date, datetime
from unittest.mock import MagicMock, Mock, patch

from app.services.report_framework.engine import (
    ParameterError,
    PermissionError,
    ReportEngine,
)
from app.services.report_framework.models import (
    ChartType,
    MetricItem,
    ParameterConfig,
    ParameterType,
    PermissionConfig,
    ReportConfig,
    ReportMeta,
    SectionConfig,
    SectionType,
    TableColumn,
    DataSourceConfig,
    DataSourceType,
    ExportConfig,
)


class TestReportEngineInit(unittest.TestCase):
    """测试初始化"""

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    @patch("app.services.report_framework.engine.ReportCacheManager")
    def test_init_default(self, mock_cache_cls, mock_resolver_cls, mock_loader_cls):
        """测试默认初始化"""
        mock_db = MagicMock()
        engine = ReportEngine(db=mock_db)

        # 验证初始化
        self.assertEqual(engine.db, mock_db)
        mock_loader_cls.assert_called_once_with("app/report_configs")
        mock_resolver_cls.assert_called_once_with(mock_db)
        self.assertIsNotNone(engine.cache)
        self.assertIn("json", engine.renderers)

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_init_custom_config_dir(self, mock_resolver_cls, mock_loader_cls):
        """测试自定义配置目录"""
        mock_db = MagicMock()
        custom_dir = "/custom/configs"
        mock_cache = MagicMock()

        engine = ReportEngine(
            db=mock_db,
            config_dir=custom_dir,
            cache_manager=mock_cache,
        )

        mock_loader_cls.assert_called_once_with(custom_dir)
        self.assertEqual(engine.cache, mock_cache)

    def test_register_renderer(self):
        """测试注册渲染器"""
        mock_db = MagicMock()
        with patch("app.services.report_framework.engine.ConfigLoader"), \
             patch("app.services.report_framework.engine.DataResolver"):
            engine = ReportEngine(db=mock_db)

            mock_renderer = MagicMock()
            engine.register_renderer("custom", mock_renderer)

            self.assertIn("custom", engine.renderers)
            self.assertEqual(engine.renderers["custom"], mock_renderer)


class TestReportEngineGenerate(unittest.TestCase):
    """测试 generate() 主方法"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        
        # Mock配置
        self.mock_config = ReportConfig(
            meta=ReportMeta(
                code="TEST_REPORT",
                name="测试报告",
                description="测试用报告",
            ),
            permissions=PermissionConfig(roles=["admin"]),
            parameters=[
                ParameterConfig(
                    name="project_id",
                    type=ParameterType.INTEGER,
                    required=True,
                ),
                ParameterConfig(
                    name="start_date",
                    type=ParameterType.DATE,
                    default="2024-01-01",
                ),
            ],
            data_sources={
                "tasks": DataSourceConfig(
                    type=DataSourceType.QUERY,
                    sql="SELECT * FROM tasks WHERE project_id = :project_id",
                )
            },
            sections=[
                SectionConfig(
                    id="metrics",
                    title="指标",
                    type=SectionType.METRICS,
                    items=[
                        MetricItem(label="总数", value="{{ tasks | length }}"),
                    ],
                ),
            ],
            exports=ExportConfig(),
        )

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    @patch("app.services.report_framework.engine.ReportCacheManager")
    def test_generate_success_no_cache(self, mock_cache_cls, mock_resolver_cls, mock_loader_cls):
        """测试成功生成报告（无缓存）"""
        # Setup mocks
        mock_cache = MagicMock()
        mock_cache.get.return_value = None  # 无缓存
        mock_cache_cls.return_value = mock_cache

        mock_loader = MagicMock()
        mock_loader.get.return_value = self.mock_config
        mock_loader_cls.return_value = mock_loader

        mock_resolver = MagicMock()
        mock_resolver.resolve_all.return_value = {
            "tasks": [{"id": 1, "name": "任务1"}, {"id": 2, "name": "任务2"}]
        }
        mock_resolver_cls.return_value = mock_resolver

        # 创建引擎
        engine = ReportEngine(db=self.mock_db)

        # 执行生成
        params = {"project_id": 123}
        result = engine.generate(
            report_code="TEST_REPORT",
            params=params,
            format="json",
        )

        # 验证
        self.assertIsNotNone(result)
        mock_loader.get.assert_called_once_with("TEST_REPORT")
        mock_resolver.resolve_all.assert_called_once()
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_called_once()

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    @patch("app.services.report_framework.engine.ReportCacheManager")
    def test_generate_with_cache_hit(self, mock_cache_cls, mock_resolver_cls, mock_loader_cls):
        """测试缓存命中"""
        mock_cache = MagicMock()
        cached_result = MagicMock()
        mock_cache.get.return_value = cached_result
        mock_cache_cls.return_value = mock_cache

        mock_loader = MagicMock()
        mock_loader.get.return_value = self.mock_config
        mock_loader_cls.return_value = mock_loader

        mock_resolver = MagicMock()
        mock_resolver_cls.return_value = mock_resolver

        engine = ReportEngine(db=self.mock_db)

        result = engine.generate(
            report_code="TEST_REPORT",
            params={"project_id": 123},
        )

        # 应该返回缓存结果
        self.assertEqual(result, cached_result)
        # 不应该调用数据解析
        mock_resolver.resolve_all.assert_not_called()

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    @patch("app.services.report_framework.engine.ReportCacheManager")
    def test_generate_skip_cache(self, mock_cache_cls, mock_resolver_cls, mock_loader_cls):
        """测试跳过缓存"""
        mock_cache = MagicMock()
        mock_cache_cls.return_value = mock_cache

        mock_loader = MagicMock()
        mock_loader.get.return_value = self.mock_config
        mock_loader_cls.return_value = mock_loader

        mock_resolver = MagicMock()
        mock_resolver.resolve_all.return_value = {"tasks": []}
        mock_resolver_cls.return_value = mock_resolver

        engine = ReportEngine(db=self.mock_db)

        result = engine.generate(
            report_code="TEST_REPORT",
            params={"project_id": 123},
            skip_cache=True,
        )

        # 不应该查询缓存
        mock_cache.get.assert_not_called()
        # 应该调用数据解析
        mock_resolver.resolve_all.assert_called_once()

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    @patch("app.services.report_framework.engine.ReportCacheManager")
    def test_generate_with_permission_check(self, mock_cache_cls, mock_resolver_cls, mock_loader_cls):
        """测试权限检查"""
        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        mock_cache_cls.return_value = mock_cache

        mock_loader = MagicMock()
        mock_loader.get.return_value = self.mock_config
        mock_loader_cls.return_value = mock_loader

        mock_resolver = MagicMock()
        mock_resolver.resolve_all.return_value = {"tasks": []}
        mock_resolver_cls.return_value = mock_resolver

        engine = ReportEngine(db=self.mock_db)

        # 创建有权限的用户
        user = MagicMock()
        user.is_superuser = False
        role = MagicMock()
        role.role_code = "admin"
        user.roles = [role]

        result = engine.generate(
            report_code="TEST_REPORT",
            params={"project_id": 123},
            user=user,
        )

        self.assertIsNotNone(result)

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    @patch("app.services.report_framework.engine.ReportCacheManager")
    def test_generate_permission_denied(self, mock_cache_cls, mock_resolver_cls, mock_loader_cls):
        """测试权限拒绝"""
        mock_loader = MagicMock()
        mock_loader.get.return_value = self.mock_config
        mock_loader_cls.return_value = mock_loader

        mock_cache_cls.return_value = MagicMock()
        mock_resolver_cls.return_value = MagicMock()

        engine = ReportEngine(db=self.mock_db)

        # 创建无权限的用户
        user = MagicMock()
        user.is_superuser = False
        role = MagicMock()
        role.role_code = "guest"
        user.roles = [role]

        with self.assertRaises(PermissionError):
            engine.generate(
                report_code="TEST_REPORT",
                params={"project_id": 123},
                user=user,
            )

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    @patch("app.services.report_framework.engine.ReportCacheManager")
    def test_generate_unsupported_format(self, mock_cache_cls, mock_resolver_cls, mock_loader_cls):
        """测试不支持的导出格式"""
        from app.services.report_framework.config_loader import ConfigError

        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        mock_cache_cls.return_value = mock_cache

        mock_loader = MagicMock()
        mock_loader.get.return_value = self.mock_config
        mock_loader_cls.return_value = mock_loader

        mock_resolver = MagicMock()
        mock_resolver.resolve_all.return_value = {"tasks": []}
        mock_resolver_cls.return_value = mock_resolver

        engine = ReportEngine(db=self.mock_db)

        with self.assertRaises(ConfigError):
            engine.generate(
                report_code="TEST_REPORT",
                params={"project_id": 123},
                format="invalid_format",
            )


class TestPermissionCheck(unittest.TestCase):
    """测试权限检查"""

    def setUp(self):
        self.mock_db = MagicMock()

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_check_permission_superuser(self, mock_resolver_cls, mock_loader_cls):
        """测试超级管理员权限"""
        engine = ReportEngine(db=self.mock_db)

        config = ReportConfig(
            meta=ReportMeta(code="TEST", name="Test"),
            permissions=PermissionConfig(roles=["admin"]),
        )

        user = MagicMock()
        user.is_superuser = True

        # 超级管理员应该通过权限检查
        engine._check_permission(config, user)  # 不应该抛出异常

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_check_permission_no_roles_required(self, mock_resolver_cls, mock_loader_cls):
        """测试无角色限制"""
        engine = ReportEngine(db=self.mock_db)

        config = ReportConfig(
            meta=ReportMeta(code="TEST", name="Test"),
            permissions=PermissionConfig(roles=[]),  # 空角色列表
        )

        user = MagicMock()
        user.is_superuser = False
        user.roles = []

        # 无角色限制，应该通过
        engine._check_permission(config, user)

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_check_permission_user_has_role(self, mock_resolver_cls, mock_loader_cls):
        """测试用户有匹配角色"""
        engine = ReportEngine(db=self.mock_db)

        config = ReportConfig(
            meta=ReportMeta(code="TEST", name="Test"),
            permissions=PermissionConfig(roles=["admin", "manager"]),
        )

        user = MagicMock()
        user.is_superuser = False
        role = MagicMock()
        role.role_code = "admin"
        user.roles = [role]

        engine._check_permission(config, user)

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_check_permission_nested_role_object(self, mock_resolver_cls, mock_loader_cls):
        """测试嵌套的角色对象"""
        engine = ReportEngine(db=self.mock_db)

        config = ReportConfig(
            meta=ReportMeta(code="TEST", name="Test"),
            permissions=PermissionConfig(roles=["manager"]),
        )

        user = MagicMock()
        user.is_superuser = False
        
        # 创建嵌套的role对象，确保没有role_code属性
        user_role = MagicMock(spec=['role'])  # 只有role属性，没有role_code
        role_obj = MagicMock()
        role_obj.role_code = "manager"
        user_role.role = role_obj
        # 确保hasattr(user_role, "role_code") 返回 False
        del user_role.role_code
        user.roles = [user_role]

        engine._check_permission(config, user)

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_check_permission_denied(self, mock_resolver_cls, mock_loader_cls):
        """测试权限拒绝"""
        engine = ReportEngine(db=self.mock_db)

        config = ReportConfig(
            meta=ReportMeta(code="TEST", name="Test"),
            permissions=PermissionConfig(roles=["admin"]),
        )

        user = MagicMock()
        user.is_superuser = False
        role = MagicMock()
        role.role_code = "guest"
        user.roles = [role]

        with self.assertRaises(PermissionError):
            engine._check_permission(config, user)


class TestValidateParams(unittest.TestCase):
    """测试参数验证"""

    def setUp(self):
        self.mock_db = MagicMock()

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_validate_params_required_missing(self, mock_resolver_cls, mock_loader_cls):
        """测试必填参数缺失"""
        engine = ReportEngine(db=self.mock_db)

        config = ReportConfig(
            meta=ReportMeta(code="TEST", name="Test"),
            parameters=[
                ParameterConfig(
                    name="project_id",
                    type=ParameterType.INTEGER,
                    required=True,
                ),
            ],
        )

        with self.assertRaises(ParameterError) as ctx:
            engine._validate_params(config, {})

        self.assertIn("project_id", str(ctx.exception))

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_validate_params_use_default(self, mock_resolver_cls, mock_loader_cls):
        """测试使用默认值"""
        engine = ReportEngine(db=self.mock_db)

        config = ReportConfig(
            meta=ReportMeta(code="TEST", name="Test"),
            parameters=[
                ParameterConfig(
                    name="limit",
                    type=ParameterType.INTEGER,
                    default=10,
                ),
            ],
        )

        result = engine._validate_params(config, {})
        self.assertEqual(result["limit"], 10)

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_validate_params_type_conversion(self, mock_resolver_cls, mock_loader_cls):
        """测试类型转换"""
        engine = ReportEngine(db=self.mock_db)

        config = ReportConfig(
            meta=ReportMeta(code="TEST", name="Test"),
            parameters=[
                ParameterConfig(name="count", type=ParameterType.INTEGER),
                ParameterConfig(name="name", type=ParameterType.STRING),
                ParameterConfig(name="active", type=ParameterType.BOOLEAN),
            ],
        )

        result = engine._validate_params(
            config,
            {"count": "123", "name": "test", "active": "true"},
        )

        self.assertEqual(result["count"], 123)
        self.assertEqual(result["name"], "test")
        self.assertTrue(result["active"])


class TestConvertParamType(unittest.TestCase):
    """测试参数类型转换"""

    def setUp(self):
        self.mock_db = MagicMock()

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_convert_integer(self, mock_resolver_cls, mock_loader_cls):
        """测试整数转换"""
        engine = ReportEngine(db=self.mock_db)

        result = engine._convert_param_type("123", ParameterType.INTEGER)
        self.assertEqual(result, 123)

        result = engine._convert_param_type(456, ParameterType.INTEGER)
        self.assertEqual(result, 456)

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_convert_float(self, mock_resolver_cls, mock_loader_cls):
        """测试浮点数转换"""
        engine = ReportEngine(db=self.mock_db)

        result = engine._convert_param_type("3.14", ParameterType.FLOAT)
        self.assertAlmostEqual(result, 3.14)

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_convert_boolean(self, mock_resolver_cls, mock_loader_cls):
        """测试布尔值转换"""
        engine = ReportEngine(db=self.mock_db)

        self.assertTrue(engine._convert_param_type("true", ParameterType.BOOLEAN))
        self.assertTrue(engine._convert_param_type("True", ParameterType.BOOLEAN))
        self.assertTrue(engine._convert_param_type("1", ParameterType.BOOLEAN))
        self.assertTrue(engine._convert_param_type("yes", ParameterType.BOOLEAN))
        self.assertTrue(engine._convert_param_type(True, ParameterType.BOOLEAN))

        self.assertFalse(engine._convert_param_type("false", ParameterType.BOOLEAN))
        self.assertFalse(engine._convert_param_type("0", ParameterType.BOOLEAN))
        self.assertFalse(engine._convert_param_type(False, ParameterType.BOOLEAN))

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_convert_date(self, mock_resolver_cls, mock_loader_cls):
        """测试日期转换"""
        engine = ReportEngine(db=self.mock_db)

        result = engine._convert_param_type("2024-01-15", ParameterType.DATE)
        self.assertEqual(result, date(2024, 1, 15))

        # 已经是date对象
        existing_date = date(2024, 2, 20)
        result = engine._convert_param_type(existing_date, ParameterType.DATE)
        self.assertEqual(result, existing_date)

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_convert_string(self, mock_resolver_cls, mock_loader_cls):
        """测试字符串转换"""
        engine = ReportEngine(db=self.mock_db)

        result = engine._convert_param_type(123, ParameterType.STRING)
        self.assertEqual(result, "123")

        result = engine._convert_param_type("test", ParameterType.STRING)
        self.assertEqual(result, "test")

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_convert_list(self, mock_resolver_cls, mock_loader_cls):
        """测试列表转换"""
        engine = ReportEngine(db=self.mock_db)

        result = engine._convert_param_type([1, 2, 3], ParameterType.LIST)
        self.assertEqual(result, [1, 2, 3])

        # 单个值转列表
        result = engine._convert_param_type("item", ParameterType.LIST)
        self.assertEqual(result, ["item"])

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_convert_invalid_type(self, mock_resolver_cls, mock_loader_cls):
        """测试无效类型转换"""
        engine = ReportEngine(db=self.mock_db)

        with self.assertRaises(ParameterError):
            engine._convert_param_type("invalid", ParameterType.INTEGER)

        with self.assertRaises(ParameterError):
            engine._convert_param_type("invalid", ParameterType.FLOAT)

        with self.assertRaises(ParameterError):
            engine._convert_param_type("invalid-date", ParameterType.DATE)


class TestRenderSections(unittest.TestCase):
    """测试Section渲染"""

    def setUp(self):
        self.mock_db = MagicMock()

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_render_metrics_section(self, mock_resolver_cls, mock_loader_cls):
        """测试指标Section渲染"""
        engine = ReportEngine(db=self.mock_db)

        section = SectionConfig(
            id="metrics",
            title="关键指标",
            type=SectionType.METRICS,
            items=[
                MetricItem(label="总数", value="{{ items | length }}"),
                MetricItem(label="完成数", value="10"),
            ],
        )

        context = {"items": [1, 2, 3, 4, 5]}

        result = engine._render_section(section, context)

        self.assertEqual(result["id"], "metrics")
        self.assertEqual(result["title"], "关键指标")
        self.assertEqual(result["type"], "metrics")
        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(result["items"][0]["label"], "总数")
        self.assertEqual(result["items"][0]["value"], 5)

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_render_table_section(self, mock_resolver_cls, mock_loader_cls):
        """测试表格Section渲染"""
        engine = ReportEngine(db=self.mock_db)

        section = SectionConfig(
            id="tasks",
            title="任务列表",
            type=SectionType.TABLE,
            source="task_data",
            columns=[
                TableColumn(field="id", label="ID"),
                TableColumn(field="name", label="名称"),
            ],
        )

        context = {
            "task_data": [
                {"id": 1, "name": "任务1"},
                {"id": 2, "name": "任务2"},
            ]
        }

        result = engine._render_section(section, context)

        self.assertEqual(result["id"], "tasks")
        self.assertEqual(result["type"], "table")
        self.assertEqual(len(result["data"]), 2)
        self.assertEqual(len(result["columns"]), 2)

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_render_chart_section(self, mock_resolver_cls, mock_loader_cls):
        """测试图表Section渲染"""
        engine = ReportEngine(db=self.mock_db)

        section = SectionConfig(
            id="chart",
            title="状态分布",
            type=SectionType.CHART,
            chart_type=ChartType.PIE,
            source="status_data",
        )

        context = {
            "status_data": [
                {"status": "完成", "count": 10},
                {"status": "进行中", "count": 5},
            ]
        }

        result = engine._render_section(section, context)

        self.assertEqual(result["id"], "chart")
        self.assertEqual(result["type"], "chart")
        self.assertEqual(result["chart_type"], "pie")
        self.assertEqual(len(result["data"]), 2)

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_render_chart_dict_data(self, mock_resolver_cls, mock_loader_cls):
        """测试图表字典数据转换"""
        engine = ReportEngine(db=self.mock_db)

        section = SectionConfig(
            id="chart",
            type=SectionType.CHART,
            chart_type=ChartType.BAR,
            source="group_data",
        )

        context = {
            "group_data": {
                "A组": 10,
                "B组": 20,
                "C组": 15,
            }
        }

        result = engine._render_section(section, context)

        self.assertEqual(len(result["data"]), 3)
        # 验证转换为label/value格式
        labels = [item["label"] for item in result["data"]]
        self.assertIn("A组", labels)


class TestGetContextValue(unittest.TestCase):
    """测试上下文值获取"""

    def setUp(self):
        self.mock_db = MagicMock()

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_get_context_value_simple(self, mock_resolver_cls, mock_loader_cls):
        """测试简单键值获取"""
        engine = ReportEngine(db=self.mock_db)

        context = {"name": "测试", "count": 100}

        self.assertEqual(engine._get_context_value(context, "name"), "测试")
        self.assertEqual(engine._get_context_value(context, "count"), 100)

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_get_context_value_nested(self, mock_resolver_cls, mock_loader_cls):
        """测试嵌套路径"""
        engine = ReportEngine(db=self.mock_db)

        context = {
            "user": {
                "profile": {
                    "name": "张三",
                    "age": 30,
                }
            }
        }

        self.assertEqual(
            engine._get_context_value(context, "user.profile.name"),
            "张三"
        )
        self.assertEqual(
            engine._get_context_value(context, "user.profile.age"),
            30
        )

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_get_context_value_not_found(self, mock_resolver_cls, mock_loader_cls):
        """测试键不存在"""
        engine = ReportEngine(db=self.mock_db)

        context = {"name": "测试"}

        self.assertIsNone(engine._get_context_value(context, "invalid"))
        self.assertIsNone(engine._get_context_value(context, "name.invalid.path"))

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_get_context_value_none_key(self, mock_resolver_cls, mock_loader_cls):
        """测试空键"""
        engine = ReportEngine(db=self.mock_db)

        context = {"name": "测试"}

        self.assertIsNone(engine._get_context_value(context, None))
        self.assertIsNone(engine._get_context_value(context, ""))


class TestListAvailable(unittest.TestCase):
    """测试列出可用报告"""

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_list_available_no_user(self, mock_resolver_cls, mock_loader_cls):
        """测试无用户时列出所有报告"""
        mock_loader = MagicMock()
        mock_loader.list_available.return_value = [
            ReportMeta(code="REPORT1", name="报告1"),
            ReportMeta(code="REPORT2", name="报告2"),
        ]
        mock_loader_cls.return_value = mock_loader

        mock_db = MagicMock()
        engine = ReportEngine(db=mock_db)

        result = engine.list_available()

        self.assertEqual(len(result), 2)
        mock_loader.list_available.assert_called_once()

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_list_available_with_user_filter(self, mock_resolver_cls, mock_loader_cls):
        """测试按用户权限过滤"""
        # Mock配置
        config1 = ReportConfig(
            meta=ReportMeta(code="REPORT1", name="报告1"),
            permissions=PermissionConfig(roles=["admin"]),
        )
        config2 = ReportConfig(
            meta=ReportMeta(code="REPORT2", name="报告2"),
            permissions=PermissionConfig(roles=["guest"]),
        )

        mock_loader = MagicMock()
        mock_loader.list_available.return_value = [
            config1.meta,
            config2.meta,
        ]
        mock_loader.get.side_effect = lambda code: config1 if code == "REPORT1" else config2
        mock_loader_cls.return_value = mock_loader

        mock_db = MagicMock()
        engine = ReportEngine(db=mock_db)

        # 创建admin用户
        user = MagicMock()
        user.is_superuser = False
        role = MagicMock()
        role.role_code = "admin"
        user.roles = [role]

        result = engine.list_available(user=user)

        # 应该只返回REPORT1
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].code, "REPORT1")


class TestGetSchema(unittest.TestCase):
    """测试获取报告Schema"""

    @patch("app.services.report_framework.engine.ConfigLoader")
    @patch("app.services.report_framework.engine.DataResolver")
    def test_get_schema(self, mock_resolver_cls, mock_loader_cls):
        """测试获取Schema"""
        from app.services.report_framework.models import (
            ExportConfig,
            JsonExportConfig,
            PdfExportConfig,
        )

        config = ReportConfig(
            meta=ReportMeta(
                code="TEST_REPORT",
                name="测试报告",
                description="这是一个测试报告",
            ),
            parameters=[
                ParameterConfig(
                    name="project_id",
                    type=ParameterType.INTEGER,
                    required=True,
                    description="项目ID",
                ),
                ParameterConfig(
                    name="start_date",
                    type=ParameterType.DATE,
                    default="2024-01-01",
                ),
            ],
            exports=ExportConfig(
                json_export=JsonExportConfig(enabled=True),
                pdf=PdfExportConfig(enabled=False),
            ),
        )

        mock_loader = MagicMock()
        mock_loader.get.return_value = config
        mock_loader_cls.return_value = mock_loader

        mock_db = MagicMock()
        engine = ReportEngine(db=mock_db)

        schema = engine.get_schema("TEST_REPORT")

        self.assertEqual(schema["report_code"], "TEST_REPORT")
        self.assertEqual(schema["report_name"], "测试报告")
        self.assertEqual(schema["description"], "这是一个测试报告")
        self.assertEqual(len(schema["parameters"]), 2)
        self.assertEqual(schema["parameters"][0]["name"], "project_id")
        self.assertEqual(schema["parameters"][0]["type"], "integer")
        self.assertTrue(schema["parameters"][0]["required"])
        self.assertTrue(schema["exports"]["json"])
        self.assertFalse(schema["exports"]["pdf"])


if __name__ == "__main__":
    unittest.main()
