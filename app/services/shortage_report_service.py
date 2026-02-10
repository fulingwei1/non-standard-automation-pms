# -*- coding: utf-8 -*-
"""
[DEPRECATED] 缺料日报生成服务

此模块已合并到 app.services.shortage.shortage_reports_service 中。
请直接从 app.services.shortage.shortage_reports_service 导入相关函数。
保留此文件仅为向后兼容。
"""
import warnings

from app.services.shortage.shortage_reports_service import (
 calculate_alert_statistics,
 calculate_report_statistics,
 calculate_kit_statistics,
 calculate_arrival_statistics,
 calculate_response_time_statistics,
 calculate_stoppage_statistics,
 build_daily_report_data,
)

warnings.warn(
 "shortage_report_service 模块已废弃，请改用 "
 "app.services.shortage.shortage_reports_service",
  DeprecationWarning,
 stacklevel=2,
)

__all__ = [
 "calculate_alert_statistics",
 "calculate_report_statistics",
 "calculate_kit_statistics",
 "calculate_arrival_statistics",
 "calculate_response_time_statistics",
 "calculate_stoppage_statistics",
  "build_daily_report_data",
]
