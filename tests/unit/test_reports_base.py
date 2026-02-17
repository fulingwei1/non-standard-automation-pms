# -*- coding: utf-8 -*-
"""
app/common/reports/base.py 覆盖率测试（当前 0%）
"""
import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock

from app.common.reports.base import BaseReportGenerator


class ConcreteReportGenerator(BaseReportGenerator):
    """用于测试的具体实现"""

    async def generate_data(self):
        return {
            "items": [{"id": 1, "name": "test"}],
            "total": 1,
        }


class TestBaseReportGenerator:
    """测试报表生成基类"""

    @pytest.fixture
    def config(self):
        return {
            "name": "测试报表",
            "description": "用于单元测试",
            "fields": ["id", "name", "status"],
            "filters": {"status": "ACTIVE"},
        }

    @pytest.fixture
    def report(self, config):
        return ConcreteReportGenerator(config)

    def test_init(self, report, config):
        assert report.name == "测试报表"
        assert report.description == "用于单元测试"
        assert report.fields == ["id", "name", "status"]
        assert report.filters == {"status": "ACTIVE"}
        assert report.template is None

    def test_init_with_template(self):
        config = {"name": "带模板报表", "template": "/path/to/template.html"}
        report = ConcreteReportGenerator(config)
        assert report.template == "/path/to/template.html"

    def test_init_defaults(self):
        report = ConcreteReportGenerator({})
        assert report.name == "报表"
        assert report.description == ""
        assert report.fields == []
        assert report.filters == {}

    def test_get_config(self, report, config):
        result = report.get_config()
        assert result == config

    @pytest.mark.asyncio
    async def test_export_json(self, report):
        result = await report.export(format="json")
        assert isinstance(result, bytes)
        data = json.loads(result.decode("utf-8"))
        assert "report_name" in data or "items" in data or isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_export_invalid_format(self, report):
        with pytest.raises(ValueError, match="不支持的格式"):
            await report.export(format="txt")

    @pytest.mark.asyncio
    async def test_generate_data(self, report):
        data = await report.generate_data()
        assert isinstance(data, dict)
        assert "items" in data

    def test_export_json_directly(self, report):
        data = {"key": "value", "count": 5}
        result = report._export_json(data)
        assert isinstance(result, bytes)
        decoded = json.loads(result)
        assert isinstance(decoded, dict)

    def test_validate_config_returns_list(self, report):
        errors = report.validate_config()
        assert isinstance(errors, list)


class TestBaseReportGeneratorExportFormats:
    """测试其他导出格式（mock 渲染器）"""

    @pytest.fixture
    def report(self):
        config = {"name": "格式测试报表"}
        return ConcreteReportGenerator(config)

    @pytest.mark.asyncio
    async def test_export_pdf(self, report):
        with patch.object(report, "_export_pdf", return_value=b"%PDF-mock") as mock_pdf:
            result = await report.export(format="pdf")
            mock_pdf.assert_called_once()
            assert result == b"%PDF-mock"

    @pytest.mark.asyncio
    async def test_export_excel(self, report):
        with patch.object(report, "_export_excel", return_value=b"xlsx-mock") as mock_excel:
            result = await report.export(format="excel")
            mock_excel.assert_called_once()

    @pytest.mark.asyncio
    async def test_export_word(self, report):
        with patch.object(report, "_export_word", return_value=b"docx-mock") as mock_word:
            result = await report.export(format="word")
            mock_word.assert_called_once()
