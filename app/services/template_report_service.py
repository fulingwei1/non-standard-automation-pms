# -*- coding: utf-8 -*-
"""
模板报表生成服务

根据预定义模板生成各类报表（项目周报、部门周报、工作量分析、成本分析、公司月报）
"""

import logging
from datetime import date
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class TemplateReportService:
    """模板报表生成服务"""

    @staticmethod
    def generate_from_template(
        db: Session,
        template: Any,
        project_id: Optional[int] = None,
        department_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        根据模板生成报表

        Args:
            db: 数据库会话
            template: 报表模板对象
            project_id: 项目ID（项目报表使用）
            department_id: 部门ID（部门报表使用）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            报表数据字典
        """
        report_type = getattr(template, 'report_type', '')

        generators = {
            "PROJECT_WEEKLY": TemplateReportService._generate_project_weekly,
            "DEPT_WEEKLY": TemplateReportService._generate_dept_weekly,
            "WORKLOAD_ANALYSIS": TemplateReportService._generate_workload_analysis,
            "COST_ANALYSIS": TemplateReportService._generate_cost_analysis,
            "COMPANY_MONTHLY": TemplateReportService._generate_company_monthly,
        }

        generator = generators.get(report_type)
        if generator:
            return generator(db, template, project_id, department_id, start_date, end_date)

        return {
            "template_code": template.template_code,
            "template_name": template.template_name,
            "summary": {},
            "sections": {},
        }

    @staticmethod
    def _generate_project_weekly(
        db: Session,
        template: Any,
        project_id: Optional[int],
        department_id: Optional[int],
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> Dict[str, Any]:
        """生成项目周报"""
        from app.models.project import Project, ProjectMilestone, Machine

        project = db.query(Project).filter(Project.id == project_id).first()

        milestones = db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == project_id,
        ).all() if project_id else []

        machines = db.query(Machine).filter(
            Machine.project_id == project_id,
        ).all() if project_id else []

        summary = {}
        if project:
            summary = {
                "project_name": project.project_name,
                "customer_name": getattr(project, 'customer_name', ''),
                "current_stage": getattr(project, 'current_stage', ''),
                "health_status": getattr(project, 'health_status', ''),
                "progress": getattr(project, 'progress', 0),
            }

        return {
            "template_code": template.template_code,
            "template_name": template.template_name,
            "summary": summary,
            "sections": {
                "milestones": [{"name": m.milestone_name} for m in milestones],
                "machines": [{"code": m.machine_code} for m in machines],
            },
        }

    @staticmethod
    def _generate_dept_weekly(
        db: Session,
        template: Any,
        project_id: Optional[int],
        department_id: Optional[int],
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> Dict[str, Any]:
        """生成部门周报"""
        from app.models.organization import Department
        from app.models.user import User

        dept = db.query(Department).filter(
            Department.id == department_id,
        ).first() if department_id else None

        users = db.query(User).filter(
            User.department_id == department_id,
            User.is_active,
        ).all() if department_id else []

        summary = {
            "department_name": dept.name if dept else "",
            "member_count": len(users),
        }

        return {
            "template_code": template.template_code,
            "template_name": template.template_name,
            "summary": summary,
            "sections": {
                "members": [{"name": u.real_name} for u in users],
            },
        }

    @staticmethod
    def _generate_workload_analysis(
        db: Session,
        template: Any,
        project_id: Optional[int],
        department_id: Optional[int],
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> Dict[str, Any]:
        """生成工作量分析报表"""
        from app.models.organization import Department

        dept = db.query(Department).filter(
            Department.id == department_id,
        ).first() if department_id else None

        return {
            "template_code": template.template_code,
            "template_name": template.template_name,
            "summary": {
                "scope": dept.name if dept else "",
            },
            "sections": {
                "workload": [],
            },
            "metrics": {},
        }

    @staticmethod
    def _generate_cost_analysis(
        db: Session,
        template: Any,
        project_id: Optional[int],
        department_id: Optional[int],
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> Dict[str, Any]:
        """生成成本分析报表"""
        from app.models.project import Project

        projects = db.query(Project).filter(
            Project.id == project_id,
        ).all() if project_id else db.query(Project).all()

        return {
            "template_code": template.template_code,
            "template_name": template.template_name,
            "summary": {
                "project_count": len(projects),
            },
            "sections": {
                "cost_breakdown": [],
            },
        }

    @staticmethod
    def _generate_company_monthly(
        db: Session,
        template: Any,
        project_id: Optional[int],
        department_id: Optional[int],
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> Dict[str, Any]:
        """生成公司月报"""
        from app.models.project import Project

        projects = db.query(Project).filter().all()

        return {
            "template_code": template.template_code,
            "template_name": template.template_name,
            "summary": {
                "total_projects": len(projects),
            },
            "sections": {
                "project_status": [],
                "health_status": [],
                "department_hours": [],
            },
        }
