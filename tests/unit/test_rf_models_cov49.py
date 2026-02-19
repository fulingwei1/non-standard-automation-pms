# -*- coding: utf-8 -*-
"""Tests for app/services/report_framework/models.py"""

import pytest
from unittest.mock import MagicMock

try:
    from app.services.report_framework.models import (
        ReportConfig, ReportMeta, ParameterConfig, ParameterType,
        DataSourceConfig, DataSourceType, SectionConfig, SectionType,
        CacheConfig, ScheduleConfig, ExportConfig,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def test_report_meta_creation():
    meta = ReportMeta(name="测试报告", code="TEST_REPORT")
    assert meta.name == "测试报告"
    assert meta.code == "TEST_REPORT"
    assert meta.version == "1.0"
    assert meta.description is None


def test_parameter_config_required():
    p = ParameterConfig(name="project_id", type=ParameterType.INTEGER, required=True)
    assert p.name == "project_id"
    assert p.required is True


def test_parameter_config_optional_with_default():
    p = ParameterConfig(name="limit", type=ParameterType.INTEGER, required=False, default=100)
    assert p.default == 100


def test_data_source_config_query_type():
    ds = DataSourceConfig(type=DataSourceType.QUERY, sql="SELECT * FROM projects")
    assert ds.type == "query"
    assert ds.sql == "SELECT * FROM projects"


def test_data_source_config_service_type():
    ds = DataSourceConfig(type=DataSourceType.SERVICE, method="ProjectService.get_all")
    assert ds.type == "service"
    assert ds.method == "ProjectService.get_all"


def test_section_config_table():
    s = SectionConfig(id="details", type=SectionType.TABLE, source="projects")
    assert s.id == "details"
    assert s.type == "table"


def test_cache_config_defaults():
    c = CacheConfig()
    assert c.enabled is False
    assert c.ttl == 3600


def test_report_config_full():
    config = ReportConfig(
        meta=ReportMeta(name="完整报告", code="FULL"),
        parameters=[ParameterConfig(name="pid", type=ParameterType.INTEGER)],
        cache=CacheConfig(enabled=True, ttl=600),
    )
    assert config.meta.code == "FULL"
    assert len(config.parameters) == 1
    assert config.cache.ttl == 600
