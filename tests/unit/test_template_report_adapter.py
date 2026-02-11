# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock, patch


class TestTemplateReportAdapter:
    def setup_method(self):
        self.db = MagicMock()
        with patch("app.services.report_framework.adapters.template.BaseReportAdapter.__init__", return_value=None), \
             patch("app.services.report_framework.adapters.template.ConfigLoader"):
            from app.services.report_framework.adapters.template import TemplateReportAdapter
            self.adapter = TemplateReportAdapter(self.db)
            self.adapter.db = self.db
            self.adapter.engine = MagicMock()

    def test_get_report_code(self):
        assert self.adapter.get_report_code() == "TEMPLATE_REPORT"

    def test_generate_data_no_template_id(self):
        with pytest.raises(ValueError, match="template_id"):
            self.adapter.generate_data({})

    def test_generate_data_template_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="报表模板不存在"):
            self.adapter.generate_data({"template_id": 999})

    def test_generate_data_success(self):
        template = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = template

        with patch("app.services.template_report.template_report_service") as mock_svc:
            mock_svc.generate_from_template.return_value = {"data": "ok"}
            result = self.adapter.generate_data({"template_id": 1, "project_id": 10})

        assert result == {"data": "ok"}

    def test_generate_no_template_id(self):
        with pytest.raises(ValueError):
            self.adapter.generate({"no_id": True})

    def test_generate_uses_yaml_when_available(self):
        template = MagicMock(report_type="PROJECT_WEEKLY")
        self.db.query.return_value.filter.return_value.first.return_value = template
        self.adapter.engine.generate.return_value = {"yaml": "result"}

        result = self.adapter.generate({"template_id": 1}, format="json")
        assert result == {"yaml": "result"}

    def test_generate_falls_back_when_yaml_fails(self):
        template = MagicMock(report_type="PROJECT_WEEKLY")
        self.db.query.return_value.filter.return_value.first.return_value = template
        self.adapter.engine.generate.side_effect = Exception("no yaml")
        self.adapter.generate_data = MagicMock(return_value={"summary": {"a": 1}})
        self.adapter._convert_to_report_result = MagicMock(return_value={"fallback": True})

        result = self.adapter.generate({"template_id": 1})
        assert result == {"fallback": True}

    def test_convert_to_report_result(self):
        with patch("app.services.report_framework.renderers.JsonRenderer") as MockR:
            renderer = MagicMock()
            MockR.return_value = renderer
            renderer.render.return_value = {"rendered": True}

            result = self.adapter._convert_to_report_result(
                {"summary": {"k": "v"}, "sections": {"s1": [1, 2]}}, "json"
            )
        assert result == {"rendered": True}
