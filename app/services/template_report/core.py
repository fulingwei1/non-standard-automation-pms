# -*- coding: utf-8 -*-
"""
模板报表生成服务 - 核心类
"""

from datetime import date, timedelta
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.report_center import ReportTemplate


class TemplateReportCore:
    """模板报表生成服务核心类"""

    @staticmethod
    def generate_from_template(
        db: Session,
        template: ReportTemplate,
        project_id: Optional[int] = None,
        department_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        根据模板配置生成报表数据

        Args:
            db: 数据库会话
            template: 报表模板
            project_id: 项目ID
            department_id: 部门ID
            start_date: 开始日期
            end_date: 结束日期
            filters: 额外过滤条件

        Returns:
            报表数据
        """
        # 设置默认日期范围
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # 解析模板配置
        sections_config = template.sections or {}
        metrics_config = template.metrics_config or {}

        # 生成报表数据
        report_data = {
            "template_id": template.id,
            "template_code": template.template_code,
            "template_name": template.template_name,
            "report_type": template.report_type,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "sections": {},
            "metrics": {},
            "charts": []
        }

        # 根据报表类型生成数据
        from .project_reports import ProjectReportMixin
        from .dept_reports import DeptReportMixin
        from .analysis_reports import AnalysisReportMixin
        from .company_reports import CompanyReportMixin
        from .generic_report import GenericReportMixin

        if template.report_type == "PROJECT_WEEKLY":
            report_data.update(ProjectReportMixin._generate_project_weekly(
                db, project_id, start_date, end_date, sections_config, metrics_config
            ))
        elif template.report_type == "PROJECT_MONTHLY":
            report_data.update(ProjectReportMixin._generate_project_monthly(
                db, project_id, start_date, end_date, sections_config, metrics_config
            ))
        elif template.report_type == "DEPT_WEEKLY":
            report_data.update(DeptReportMixin._generate_dept_weekly(
                db, department_id, start_date, end_date, sections_config, metrics_config
            ))
        elif template.report_type == "DEPT_MONTHLY":
            report_data.update(DeptReportMixin._generate_dept_monthly(
                db, department_id, start_date, end_date, sections_config, metrics_config
            ))
        elif template.report_type == "WORKLOAD_ANALYSIS":
            report_data.update(AnalysisReportMixin._generate_workload_analysis(
                db, department_id, start_date, end_date, sections_config, metrics_config
            ))
        elif template.report_type == "COST_ANALYSIS":
            report_data.update(AnalysisReportMixin._generate_cost_analysis(
                db, project_id, start_date, end_date, sections_config, metrics_config
            ))
        elif template.report_type == "COMPANY_MONTHLY":
            report_data.update(CompanyReportMixin._generate_company_monthly(
                db, start_date, end_date, sections_config, metrics_config
            ))
        else:
            # 通用报表生成
            report_data.update(GenericReportMixin._generate_generic_report(
                db, template.report_type, project_id, department_id, start_date, end_date
            ))

        return report_data
