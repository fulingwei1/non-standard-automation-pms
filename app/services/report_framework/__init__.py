# -*- coding: utf-8 -*-
"""
统一报告框架

配置驱动的报告生成系统，支持：
- YAML 配置定义报告
- 多数据源（SQL查询、服务调用）
- 多导出格式（JSON、PDF、Excel、Word）
- 缓存与定时预生成
"""

from app.services.report_framework.config_loader import ConfigLoader, ConfigError
from app.services.report_framework.engine import ReportEngine
from app.services.report_framework.models import (
    ReportConfig,
    ReportMeta,
    DataSourceType,
    SectionType,
)

__all__ = [
    "ConfigLoader",
    "ConfigError",
    "ReportConfig",
    "ReportMeta",
    "DataSourceType",
    "SectionType",
    "ReportEngine",
]
