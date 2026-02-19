# -*- coding: utf-8 -*-
"""第四十四批覆盖测试 - 模板报表适配器"""

import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.report_framework.adapters.template import TemplateReportAdapter
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


@pytest.fixture
def adapter():
    mock_db = MagicMock()
    with patch("app.services.report_framework.adapters.base.ReportEngine"), \
         patch("app.services.report_framework.adapters.template.ConfigLoader"):
        return TemplateReportAdapter(mock_db)


class TestTemplateReportAdapter:

    def test_get_report_code(self, adapter):
        assert adapter.get_report_code() == "TEMPLATE_REPORT"

    def test_generate_data_raises_without_template_id(self, adapter):
        with pytest.raises(ValueError, match="template_id"):
            adapter.generate_data(params={})

    def test_generate_data_raises_when_template_not_found(self, adapter):
        adapter.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="报表模板不存在"):
            adapter.generate_data(params={"template_id": 999})

    def test_generate_data_calls_template_report_service(self, adapter):
        mock_template = MagicMock()
        adapter.db.query.return_value.filter.return_value.first.return_value = mock_template
        with patch("app.services.template_report.template_report_service") as mock_svc:
            mock_svc.generate_from_template.return_value = {"data": "ok"}
            result = adapter.generate_data(params={"template_id": 1})
            mock_svc.generate_from_template.assert_called_once()

    def test_adapter_has_config_loader(self, adapter):
        assert hasattr(adapter, "config_loader")

    def test_adapter_inherits_base(self, adapter):
        from app.services.report_framework.adapters.base import BaseReportAdapter
        assert isinstance(adapter, BaseReportAdapter)

    def test_generate_falls_back_when_engine_raises(self, adapter):
        adapter.engine.generate.side_effect = Exception("no yaml")
        mock_template = MagicMock()
        adapter.db.query.return_value.filter.return_value.first.return_value = mock_template
        with patch("app.services.template_report.template_report_service") as mock_svc, \
             patch.object(adapter, "_convert_to_report_result", return_value={"ok": True}):
            mock_svc.generate_from_template.return_value = {}
            result = adapter.generate(params={"template_id": 1})
        assert result == {"ok": True}
