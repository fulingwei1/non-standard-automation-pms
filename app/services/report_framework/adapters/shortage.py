# -*- coding: utf-8 -*-
"""
缺料报表适配器 (#42)

将 shortage_reports_service 适配到统一报表框架。
当前阶段：委托到原有 ShortageReportsService。
"""

from datetime import date
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.report_framework.adapters.base import BaseReportAdapter
from app.services.shortage.shortage_reports_service import ShortageReportsService


class ShortageReportAdapter(BaseReportAdapter):
    """缺料报表适配器"""

    def __init__(self, db: Session):
        super().__init__(db)
        self._service = ShortageReportsService(db)

    def fetch_data(
        self,
        params: Dict[str, Any],
        user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """委托到原有服务获取数据"""
        target_date = params.get("target_date") or date.today()

        if hasattr(self._service, "generate_daily_report"):
            return self._service.generate_daily_report(target_date)

        # Fallback
        return {"report_type": "SHORTAGE", "data": {}, "status": "adapter_fallback"}
