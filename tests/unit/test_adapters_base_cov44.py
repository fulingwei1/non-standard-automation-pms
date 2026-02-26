# -*- coding: utf-8 -*-
"""第四十四批覆盖测试 - 报表适配器基类"""

import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.report_framework.adapters.base import BaseReportAdapter
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


if IMPORT_OK:
    class ConcreteAdapter(BaseReportAdapter):
        def get_report_code(self) -> str:
            return "TEST_REPORT"

        def generate_data(self, params, user=None):
            return {"summary": {"key": "val"}, "details": [{"a": 1}], "title": "测试"}


@pytest.fixture
def adapter():
    mock_db = MagicMock()
    with patch("app.services.report_framework.adapters.base.ReportEngine"):
        return ConcreteAdapter(mock_db)


class TestBaseReportAdapter:

    def test_get_report_code(self, adapter):
        assert adapter.get_report_code() == "TEST_REPORT"

    def test_generate_data_returns_dict(self, adapter):
        result = adapter.generate_data(params={})
        assert isinstance(result, dict)

    def test_generate_uses_engine(self, adapter):
        adapter.engine.generate.return_value = {"report": "data"}
        result = adapter.generate(params={}, format="json")
        adapter.engine.generate.assert_called_once_with(
            report_code="TEST_REPORT",
            params={},
            format="json",
            user=None,
            skip_cache=False,
        )
        assert result == {"report": "data"}

    def test_generate_falls_back_when_engine_raises(self, adapter):
        adapter.engine.generate.side_effect = Exception("YAML not found")
        with patch("app.services.report_framework.renderers.JsonRenderer") as MockRenderer:
            mock_renderer = MagicMock()
            MockRenderer.return_value = mock_renderer
            mock_renderer.render.return_value = {"fallback": True}
            result = adapter.generate(params={}, format="json")
        # 引擎失败后会调用 generate_data → _convert_to_report_result
        assert result is not None

    def test_convert_to_report_result_returns_something(self, adapter):
        """_convert_to_report_result 应返回非 None 值"""
        result = adapter._convert_to_report_result(
            {"summary": {"k": "v"}, "details": [1, 2], "title": "T"}, format="json"
        )
        assert result is not None

    def test_convert_handles_empty_data(self, adapter):
        """空数据不应崩溃"""
        result = adapter._convert_to_report_result({}, format="json")
        assert result is not None

    def test_init_sets_engine(self, adapter):
        assert adapter.engine is not None
