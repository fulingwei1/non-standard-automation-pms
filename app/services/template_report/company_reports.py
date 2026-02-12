# -*- coding: utf-8 -*-
"""
公司报表生成模块
提供公司月报等公司级报表的生成功能
"""

from datetime import date
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.models.organization import Department
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.user import User


class CompanyReportMixin:
    """公司报表生成功能混入类"""

    @staticmethod
    def _generate_company_monthly(
        db: Session,
        start_date: date,
        end_date: date,
        sections_config: Dict,
        metrics_config: Dict
    ) -> Dict[str, Any]:
        """生成公司月报"""
        # 获取所有活跃项目
        projects = db.query(Project).filter(
            Project.is_active
        ).all()

        # 项目状态统计
        status_counts = {}
        for p in projects:
            status = p.status or "UNKNOWN"
            status_counts[status] = status_counts.get(status, 0) + 1

        # 健康度统计
        health_counts = {}
        for p in projects:
            health = getattr(p, 'health_status', 'H1')
            health_counts[health] = health_counts.get(health, 0) + 1

        # 部门工时
        departments = db.query(Department).all()
        dept_hours = []
        for dept in departments:
            users = db.query(User).filter(
                User.department_id == dept.id,
                User.is_active
            ).all()
            user_ids = [u.id for u in users]

            timesheets = db.query(Timesheet).filter(
                Timesheet.user_id.in_(user_ids),
                Timesheet.work_date.between(start_date, end_date)
            ).all()

            total_hours = sum(float(t.hours or 0) for t in timesheets)
            if total_hours > 0:
                dept_hours.append({
                    "department": dept.name,
                    "hours": round(total_hours, 2)
                })

        return {
            "summary": {
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "total_projects": len(projects)
            },
            "sections": {
                "project_status": {
                    "title": "项目状态分布",
                    "type": "summary",
                    "data": status_counts
                },
                "health_status": {
                    "title": "项目健康度分布",
                    "type": "summary",
                    "data": health_counts
                },
                "department_hours": {
                    "title": "部门工时统计",
                    "type": "table",
                    "data": dept_hours
                }
            },
            "metrics": {
                "total_projects": len(projects),
                "active_projects": status_counts.get("IN_PROGRESS", 0),
                "health_projects": sum(
                    v for k, v in health_counts.items() if k in ["H1", "H2"]
                )
            }
        }
