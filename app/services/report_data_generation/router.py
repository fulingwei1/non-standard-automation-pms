# -*- coding: utf-8 -*-
"""
报表路由分发（根据报表类型调用对应的生成方法）
"""

from datetime import date, timedelta
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from .analysis_reports import AnalysisReportMixin
from .core import ReportDataGenerationCore
from .dept_reports import DeptReportMixin
from .project_reports import ProjectReportMixin


class ReportRouterMixin:
    """报表路由分发功能混入类"""

    @staticmethod
    def generate_report_by_type(
        db: Session,
        report_type: str,
        project_id: Optional[int] = None,
        department_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        根据报表类型生成数据

        Args:
            db: 数据库会话
            report_type: 报表类型
            project_id: 项目ID
            department_id: 部门ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            报表数据
        """
        if not start_date:
            start_date = date.today() - timedelta(days=7)
        if not end_date:
            end_date = date.today()

        if report_type == "PROJECT_WEEKLY":
            if not project_id:
                return {"error": "项目周报需要指定项目ID"}
            return ProjectReportMixin.generate_project_weekly_report(
                db, project_id, start_date, end_date
            )

        elif report_type == "PROJECT_MONTHLY":
            if not project_id:
                return {"error": "项目月报需要指定项目ID"}
            return ProjectReportMixin.generate_project_monthly_report(
                db, project_id, start_date, end_date
            )

        elif report_type == "DEPT_WEEKLY":
            if not department_id:
                return {"error": "部门周报需要指定部门ID"}
            return DeptReportMixin.generate_dept_weekly_report(
                db, department_id, start_date, end_date
            )

        elif report_type == "DEPT_MONTHLY":
            if not department_id:
                return {"error": "部门月报需要指定部门ID"}
            return DeptReportMixin.generate_dept_monthly_report(
                db, department_id, start_date, end_date
            )

        elif report_type == "WORKLOAD_ANALYSIS":
            return AnalysisReportMixin.generate_workload_analysis(
                db, department_id, start_date, end_date
            )

        elif report_type == "COST_ANALYSIS":
            return AnalysisReportMixin.generate_cost_analysis(
                db, project_id, start_date, end_date
            )

        else:
            return {
                "report_type": report_type,
                "summary": {},
                "details": [],
                "charts": [],
                "message": "该报表类型待实现"
            }
