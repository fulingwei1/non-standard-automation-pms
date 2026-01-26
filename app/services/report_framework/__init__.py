# -*- coding: utf-8 -*-
"""
统一报告框架

配置驱动的报告生成系统，支持：
- YAML 配置定义报告
- 多数据源（SQL查询、服务调用）
- 多导出格式（JSON、PDF、Excel、Word）
- 缓存与定时预生成
- 统一的数据生成器（整合原有 template_report 和 report_data_generation）

使用示例：
    # 方式1：使用适配器（推荐）
    from app.services.report_framework.adapters import ProjectWeeklyAdapter

    adapter = ProjectWeeklyAdapter(db)
    result = adapter.generate(
        params={"project_id": 1, "start_date": "2025-01-01", "end_date": "2025-01-07"},
        format="json"
    )

    # 方式2：直接使用生成器
    from app.services.report_framework.generators import ProjectReportGenerator

    data = ProjectReportGenerator.generate_weekly(db, project_id=1, start_date, end_date)

    # 方式3：使用 YAML 配置 + ReportEngine
    from app.services.report_framework import ReportEngine

    engine = ReportEngine(db)
    result = engine.generate("PROJECT_WEEKLY", params={"project_id": 1})
"""

from app.services.report_framework.config_loader import ConfigError, ConfigLoader
from app.services.report_framework.engine import ReportEngine
from app.services.report_framework.generators import (
    AnalysisReportGenerator,
    DeptReportGenerator,
    ProjectReportGenerator,
)
from app.services.report_framework.models import (
    DataSourceType,
    ReportConfig,
    ReportMeta,
    SectionType,
)

__all__ = [
    # 配置加载
    "ConfigLoader",
    "ConfigError",
    # 引擎
    "ReportEngine",
    # 数据模型
    "ReportConfig",
    "ReportMeta",
    "DataSourceType",
    "SectionType",
    # 数据生成器
    "ProjectReportGenerator",
    "DeptReportGenerator",
    "AnalysisReportGenerator",
]
