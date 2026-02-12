# -*- coding: utf-8 -*-
"""
部门报表生成模块
提供部门周报、月报的生成功能
"""

from datetime import date
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.models.organization import Department
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.user import User


class DeptReportMixin:
    """部门报表生成功能混入类"""

    @staticmethod
    def _generate_dept_weekly(
        db: Session,
        department_id: int,
        start_date: date,
        end_date: date,
        sections_config: Dict,
        metrics_config: Dict
    ) -> Dict[str, Any]:
        """生成部门周报"""
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            return {"error": "部门不存在"}

        # 部门人员
        users = db.query(User).filter(
            User.department_id == department_id,
            User.is_active
        ).all()

        user_ids = [u.id for u in users]

        # 工时统计
        timesheets = db.query(Timesheet).filter(
            Timesheet.user_id.in_(user_ids),
            Timesheet.work_date.between(start_date, end_date)
        ).all()

        total_hours = sum(float(t.hours or 0) for t in timesheets)

        # 按项目统计
        project_stats = {}
        for ts in timesheets:
            pid = ts.project_id or 0
            if pid == 0:
                continue
            if pid not in project_stats:
                project_stats[pid] = {"hours": 0, "count": 0}
            project_stats[pid]["hours"] += float(ts.hours or 0)
            project_stats[pid]["count"] += 1

        project_list = []
        for pid, stats in sorted(project_stats.items(), key=lambda x: x[1]["hours"], reverse=True)[:10]:
            proj = db.query(Project).filter(Project.id == pid).first()
            project_list.append({
                "project_id": pid,
                "project_name": proj.project_name if proj else "未知项目",
                "hours": round(stats["hours"], 2),
                "timesheet_count": stats["count"]
            })

        return {
            "summary": {
                "department_name": department.name,
                "member_count": len(users),
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat()
            },
            "sections": {
                "projects": {
                    "title": "项目工时分布",
                    "type": "table",
                    "data": project_list
                },
                "timesheet": {
                    "title": "工时汇总",
                    "type": "summary",
                    "data": {
                        "total_hours": round(total_hours, 2),
                        "avg_hours_per_user": round(total_hours / len(users), 2) if users else 0
                    }
                }
            },
            "metrics": {
                "total_hours": round(total_hours, 2),
                "active_projects": len(project_stats),
                "active_members": len(users)
            }
        }

    @staticmethod
    def _generate_dept_monthly(
        db: Session,
        department_id: int,
        start_date: date,
        end_date: date,
        sections_config: Dict,
        metrics_config: Dict
    ) -> Dict[str, Any]:
        """生成部门月报"""
        # 复用周报逻辑
        data = DeptReportMixin._generate_dept_weekly(
            db, department_id, start_date, end_date, sections_config, metrics_config
        )

        return data
