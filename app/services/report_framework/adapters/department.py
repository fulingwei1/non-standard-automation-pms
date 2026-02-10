# -*- coding: utf-8 -*-
"""
部门报表适配器

将部门报表数据生成器适配到统一报表框架
"""

from datetime import date, timedelta
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.common.date_range import month_start
from app.models.user import User
from app.services.report_framework.adapters.base import BaseReportAdapter
from app.services.report_framework.generators import DeptReportGenerator


class DeptReportAdapter(BaseReportAdapter):
    """部门报表适配器"""

    def __init__(self, db: Session, report_type: str = "weekly"):
        """
        初始化适配器

        Args:
            db: 数据库会话
            report_type: 报表类型（weekly/monthly）
        """
        super().__init__(db)
        self.report_type = report_type

    def get_report_code(self) -> str:
        """返回报表代码"""
        if self.report_type == "monthly":
            return "DEPT_MONTHLY"
        return "DEPT_WEEKLY"

    def generate_data(
        self,
        params: Dict[str, Any],
        user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """
        生成部门报表数据

        Args:
            params: 报表参数（department_id, start_date, end_date）
            user: 当前用户

        Returns:
            报表数据字典
        """
        department_id = params.get("department_id")
        if not department_id:
            raise ValueError("department_id 参数是必需的")

        # 处理日期参数
        start_date = params.get("start_date")
        end_date = params.get("end_date")

        if not end_date:
            end_date = date.today()
        elif isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)

        if not start_date:
            if self.report_type == "monthly":
                start_date = month_start(end_date)
            else:
                start_date = end_date - timedelta(days=6)
        elif isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)

        # 使用统一生成器
        if self.report_type == "monthly":
            data = DeptReportGenerator.generate_monthly(
                self.db, department_id, start_date, end_date
            )
        else:
            data = DeptReportGenerator.generate_weekly(
                self.db, department_id, start_date, end_date
            )

        # 添加报表元信息
        data["title"] = f"部门{'月' if self.report_type == 'monthly' else '周'}报"
        data["report_type"] = self.get_report_code()

        return data


class DeptWeeklyAdapter(DeptReportAdapter):
    """部门周报适配器"""

    def __init__(self, db: Session):
        super().__init__(db, report_type="weekly")


class DeptMonthlyAdapter(DeptReportAdapter):
    """部门月报适配器"""

    def __init__(self, db: Session):
        super().__init__(db, report_type="monthly")
