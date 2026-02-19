# -*- coding: utf-8 -*-
"""
第四十五批覆盖：report_framework/models.py
"""

import pytest

pytest.importorskip("app.services.report_framework.models")

from app.services.report_framework.models import (
    DataSourceType,
    SectionType,
    ChartType,
    ParameterType,
    ReportMeta,
    PermissionConfig,
    ParameterConfig,
    CacheConfig,
    ScheduleConfig,
    DataSourceConfig,
    SectionConfig,
    MetricItem,
    TableColumn,
    ExportConfig,
    ReportConfig,
)


class TestEnums:
    def test_data_source_type_values(self):
        assert DataSourceType.QUERY == "query"
        assert DataSourceType.SERVICE == "service"
        assert DataSourceType.AGGREGATE == "aggregate"

    def test_section_type_values(self):
        assert SectionType.METRICS == "metrics"
        assert SectionType.TABLE == "table"
        assert SectionType.CHART == "chart"

    def test_chart_type_values(self):
        assert ChartType.PIE == "pie"
        assert ChartType.BAR == "bar"
        assert ChartType.LINE == "line"

    def test_parameter_type_values(self):
        assert ParameterType.INTEGER == "integer"
        assert ParameterType.DATE == "date"


class TestReportMeta:
    def test_basic_creation(self):
        meta = ReportMeta(name="测试报告", code="TEST_001")
        assert meta.name == "测试报告"
        assert meta.code == "TEST_001"
        assert meta.version == "1.0"

    def test_with_description(self):
        meta = ReportMeta(name="报告", code="R001", description="描述", version="2.0")
        assert meta.description == "描述"
        assert meta.version == "2.0"


class TestPermissionConfig:
    def test_defaults(self):
        perm = PermissionConfig()
        assert perm.roles == []
        assert perm.data_scope == "project"

    def test_custom_roles(self):
        perm = PermissionConfig(roles=["admin", "manager"])
        assert "admin" in perm.roles


class TestCacheConfig:
    def test_defaults(self):
        cache = CacheConfig()
        assert cache.enabled is False
        assert cache.ttl == 3600

    def test_enabled_cache(self):
        cache = CacheConfig(enabled=True, ttl=7200, key_pattern="report:{id}")
        assert cache.enabled is True
        assert cache.ttl == 7200


class TestSectionConfig:
    def test_metrics_section(self):
        section = SectionConfig(
            id="s1",
            title="摘要",
            type=SectionType.METRICS,
            items=[MetricItem(label="总数", value="{{ total }}")],
        )
        assert section.id == "s1"
        assert section.items[0].label == "总数"

    def test_table_section(self):
        section = SectionConfig(
            id="s2",
            type=SectionType.TABLE,
            source="projects",
            columns=[TableColumn(field="name", label="名称")],
        )
        assert section.columns[0].field == "name"


class TestReportConfig:
    def test_minimal_config(self):
        config = ReportConfig(
            meta=ReportMeta(name="报告", code="R001"),
        )
        assert config.meta.name == "报告"
        assert config.parameters == []
        assert config.sections == []
        assert config.data_sources == {}

    def test_export_config_defaults(self):
        config = ReportConfig(meta=ReportMeta(name="R", code="R"))
        assert config.exports.pdf.enabled is False
        assert config.exports.excel.enabled is False
        assert config.exports.word.enabled is False
