# -*- coding: utf-8 -*-
"""
商务支持报表适配器 (#42)

将 business_support_reports 服务适配到统一报表框架。
当前阶段：委托到原有 BusinessSupportReportsService，
后续可迁移到 YAML 配置驱动。
"""

from datetime import date
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.business_support_reports.business_support_reports_service import (
    BusinessSupportReportsService,
)
from app.services.report_framework.adapters.base import BaseReportAdapter


class BusinessSupportReportAdapter(BaseReportAdapter):
    """商务支持报表适配器"""

    REPORT_TYPE_MAP = {
        "SALES_DAILY": "sales_daily",
        "SALES_WEEKLY": "sales_weekly",
        "SALES_MONTHLY": "sales_monthly",
    }

    def __init__(self, db: Session, report_type: str = "SALES_DAILY"):
        super().__init__(db)
        self.report_type = report_type
        self._service = BusinessSupportReportsService(db)

    def fetch_data(
        self,
        params: Dict[str, Any],
        user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """委托到原有服务获取数据"""
        method_name = self.REPORT_TYPE_MAP.get(self.report_type)
        if not method_name:
            raise ValueError(f"Unsupported business support report type: {self.report_type}")

        if method_name == "sales_daily":
            target_date = params.get("target_date") or date.today()
            if hasattr(self._service, "generate_daily_report"):
                return self._service.generate_daily_report(target_date)
        elif method_name == "sales_weekly":
            week = params.get("week")
            if hasattr(self._service, "generate_weekly_report"):
                return self._service.generate_weekly_report(week)
        elif method_name == "sales_monthly":
            month = params.get("month")
            if hasattr(self._service, "generate_monthly_report"):
                return self._service.generate_monthly_report(month)

        return {"report_type": self.report_type, "data": {}, "status": "adapter_fallback"}
