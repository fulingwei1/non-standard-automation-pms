# -*- coding: utf-8 -*-
"""
项目报表适配器

将项目报表数据生成器适配到统一报表框架
"""

from datetime import date, timedelta
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.report_framework.adapters.base import BaseReportAdapter
from app.services.report_framework.generators import ProjectReportGenerator


class ProjectReportAdapter(BaseReportAdapter):
    """项目报表适配器"""

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
            return "PROJECT_MONTHLY"
        return "PROJECT_WEEKLY"

    def generate_data(
        self,
        params: Dict[str, Any],
        user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """
        生成项目报表数据

        Args:
            params: 报表参数（project_id, start_date, end_date）
            user: 当前用户

        Returns:
            报表数据字典
        """
        project_id = params.get("project_id")
        if not project_id:
            raise ValueError("project_id 参数是必需的")

        # 处理日期参数
        start_date = params.get("start_date")
        end_date = params.get("end_date")

        if not end_date:
            end_date = date.today()
        elif isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)

        if not start_date:
            if self.report_type == "monthly":
                start_date = end_date.replace(day=1)
            else:
                start_date = end_date - timedelta(days=6)
        elif isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)

        # 使用统一生成器
        if self.report_type == "monthly":
            data = ProjectReportGenerator.generate_monthly(
                self.db, project_id, start_date, end_date
            )
        else:
            data = ProjectReportGenerator.generate_weekly(
                self.db, project_id, start_date, end_date
            )

        # 添加报表元信息
        data["title"] = f"项目{'月' if self.report_type == 'monthly' else '周'}报"
        data["report_type"] = self.get_report_code()

        return data


class ProjectWeeklyAdapter(ProjectReportAdapter):
    """项目周报适配器"""

    def __init__(self, db: Session):
        super().__init__(db, report_type="weekly")


class ProjectMonthlyAdapter(ProjectReportAdapter):
    """项目月报适配器"""

    def __init__(self, db: Session):
        super().__init__(db, report_type="monthly")
