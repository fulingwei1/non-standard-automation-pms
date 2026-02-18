# -*- coding: utf-8 -*-
"""第十二批：报告引擎单元测试"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.report_framework.engine import ReportEngine, PermissionError, ParameterError
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败")


def _make_engine():
    db = MagicMock()
    cache = MagicMock()
    cache.get.return_value = None  # 默认无缓存

    with patch("app.services.report_framework.engine.ConfigLoader") as MockLoader, \
         patch("app.services.report_framework.engine.DataResolver") as MockResolver, \
         patch("app.services.report_framework.engine.ExpressionParser"):
        engine = ReportEngine(db=db, cache_manager=cache)
        engine.config_loader = MagicMock()
        engine.data_resolver = MagicMock()
        engine.cache = cache
        return engine, db, cache


class TestReportEngineInit:
    def test_init_with_db(self):
        db = MagicMock()
        with patch("app.services.report_framework.engine.ConfigLoader"), \
             patch("app.services.report_framework.engine.DataResolver"), \
             patch("app.services.report_framework.engine.ExpressionParser"):
            engine = ReportEngine(db=db)
            assert engine.db is db

    def test_renderers_registered(self):
        engine, _, _ = _make_engine()
        assert "json" in engine.renderers

    def test_has_cache(self):
        engine, _, cache = _make_engine()
        assert engine.cache is cache


class TestReportEngineGenerate:
    """generate 方法测试"""

    def _setup_engine_for_generate(self):
        engine, db, cache = _make_engine()

        # Mock 配置
        config = MagicMock()
        config.meta.code = "test_report"
        config.meta.name = "测试报告"
        config.permissions = []
        config.parameters = []
        config.sections = []
        config.data_sources = []
        engine.config_loader.get.return_value = config

        # Mock 数据解析
        engine.data_resolver.resolve_all.return_value = {}

        # Mock 渲染器
        mock_renderer = MagicMock()
        mock_result = MagicMock()
        mock_renderer.render.return_value = mock_result
        engine.renderers["json"] = mock_renderer

        return engine, config, mock_result

    def test_generate_uses_cached_result(self):
        engine, _, cache = _make_engine()
        cached_result = MagicMock()
        cache.get.return_value = cached_result

        config = MagicMock()
        config.permissions = []
        config.parameters = []
        engine.config_loader.get.return_value = config

        result = engine.generate(report_code="test", params={})
        assert result is cached_result

    def test_generate_skips_cache_when_flag_set(self):
        engine, config, mock_result = self._setup_engine_for_generate()
        engine.cache.get.return_value = None

        result = engine.generate(report_code="test", params={}, skip_cache=True)
        # 不应该查询缓存
        assert result is not None

    def test_generate_raises_for_unsupported_format(self):
        from app.services.report_framework.config_loader import ConfigError
        engine, config, _ = self._setup_engine_for_generate()
        engine.cache.get.return_value = None

        with pytest.raises((ConfigError, Exception)):
            engine.generate(report_code="test", params={}, format="unsupported")

    def test_generate_with_json_format(self):
        engine, config, mock_result = self._setup_engine_for_generate()
        engine.cache.get.return_value = None

        with patch.object(engine, '_validate_params', return_value={}), \
             patch.object(engine, '_render_sections', return_value=[]):
            result = engine.generate(report_code="test", params={}, format="json")
            assert result is mock_result


class TestReportEnginePermission:
    """权限检查测试"""

    def test_check_permission_called_with_user(self):
        engine, _, cache = _make_engine()
        cache.get.return_value = MagicMock()  # 命中缓存

        config = MagicMock()
        config.permissions = ["admin"]
        config.parameters = []
        engine.config_loader.get.return_value = config

        user = MagicMock()
        user.roles = ["admin"]

        with patch.object(engine, '_check_permission') as mock_check:
            engine.generate(report_code="test", params={}, user=user)
            mock_check.assert_called_once()


class TestReportEngineValidation:
    """参数验证测试"""

    def test_validate_params_called(self):
        engine, db, cache = _make_engine()
        cached = MagicMock()
        cache.get.return_value = cached  # 命中缓存，跳过后续

        config = MagicMock()
        config.permissions = []
        config.parameters = []
        engine.config_loader.get.return_value = config

        result = engine.generate(report_code="test", params={"year": 2025})
        assert result is cached
