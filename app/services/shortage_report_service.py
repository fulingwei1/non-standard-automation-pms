# -*- coding: utf-8 -*-
"""向后兼容 re-export wrapper — 实际实现在 shortage.shortage_reports_service"""

from app.services.shortage.shortage_reports_service import (  # noqa: F401
    ShortageReportsService,
    calculate_alert_statistics,
    calculate_arrival_statistics,
    calculate_kit_statistics,
    calculate_report_statistics,
    calculate_response_time_statistics,
    calculate_stoppage_statistics,
    build_daily_report_data,
)
