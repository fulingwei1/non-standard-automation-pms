# -*- coding: utf-8 -*-
"""
项目报表生成模块
提供项目周报、月报的生成功能
"""

from datetime import date, timedelta
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.models.project import Machine, Project, ProjectMilestone
from app.models.timesheet import Timesheet


class ProjectReportMixin:
    """项目报表生成功能混入类"""

    @staticmethod
    def _generate_project_weekly(
        db: Session,
        project_id: int,
        start_date: date,
        end_date: date,
        sections_config: Dict,
        metrics_config: Dict
    ) -> Dict[str, Any]:
        """生成项目周报"""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"error": "项目不存在"}

        # 基础信息
        summary = {
            "project_code": getattr(project, 'project_code', ''),
            "project_name": project.project_name,
            "customer_name": getattr(project, 'customer_name', ''),
            "current_stage": getattr(project, 'current_stage', 'S1'),
            "health_status": getattr(project, 'health_status', 'H1'),
            "progress": float(project.progress or 0)
        }

        # 里程碑
        milestones_data = []
        milestones = db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == project_id,
            ProjectMilestone.milestone_date.between(start_date, end_date)
        ).all()

        for m in milestones:
            milestones_data.append({
                "name": getattr(m, 'milestone_name', f"里程碑{m.id}"),
                "date": getattr(m, 'milestone_date', None),
                "status": getattr(m, 'status', 'PENDING'),
                "actual_date": getattr(m, 'actual_date', None)
            })

        # 工时统计
        timesheets = db.query(Timesheet).filter(
            Timesheet.project_id == project_id,
            Timesheet.work_date.between(start_date, end_date)
        ).all()

        total_hours = sum(float(t.hours or 0) for t in timesheets)
        unique_workers = len(set(t.user_id for t in timesheets))

        # 机台进度
        machines = db.query(Machine).filter(Machine.project_id == project_id).all()
        machine_data = []
        for m in machines:
            machine_data.append({
                "machine_code": getattr(m, 'machine_code', f"M-{m.id}"),
                "machine_name": getattr(m, 'machine_name', f"机台{m.id}"),
                "status": getattr(m, 'status', 'PENDING'),
                "progress": float(m.progress or 0)
            })

        return {
            "summary": summary,
            "sections": {
                "milestones": {
                    "title": "里程碑完成情况",
                    "type": "table",
                    "data": milestones_data,
                    "summary": {
                        "total": len(milestones),
                        "completed": sum(1 for m in milestones if getattr(m, 'status', '') == 'COMPLETED'),
                        "delayed": sum(1 for m in milestones if getattr(m, 'status', '') == 'DELAYED')
                    }
                },
                "timesheet": {
                    "title": "工时统计",
                    "type": "summary",
                    "data": {
                        "total_hours": round(total_hours, 2),
                        "unique_workers": unique_workers,
                        "avg_hours": round(total_hours / unique_workers, 2) if unique_workers > 0 else 0
                    }
                },
                "machines": {
                    "title": "机台进度",
                    "type": "list",
                    "data": machine_data
                }
            },
            "metrics": {
                "total_hours": round(total_hours, 2),
                "active_workers": unique_workers,
                "milestone_completion_rate": round(
                    sum(1 for m in milestones if getattr(m, 'status', '') == 'COMPLETED') / max(len(milestones), 1) * 100,
                    2
                ) if milestones else 0
            }
        }

    @staticmethod
    def _generate_project_monthly(
        db: Session,
        project_id: int,
        start_date: date,
        end_date: date,
        sections_config: Dict,
        metrics_config: Dict
    ) -> Dict[str, Any]:
        """生成项目月报"""
        # 复用周报逻辑，增加趋势数据
        data = ProjectReportMixin._generate_project_weekly(
            db, project_id, start_date, end_date, sections_config, metrics_config
        )

        # 添加周度趋势
        weeks = []
        current = start_date
        week_num = 1
        while current <= end_date:
            week_end = min(current + timedelta(days=6), end_date)
            week_timesheets = db.query(Timesheet).filter(
                Timesheet.project_id == project_id,
                Timesheet.work_date.between(current, week_end)
            ).all()
            week_hours = sum(float(t.hours or 0) for t in week_timesheets)

            weeks.append({
                "week": week_num,
                "start": current.isoformat(),
                "end": week_end.isoformat(),
                "hours": round(week_hours, 2)
            })

            current = week_end + timedelta(days=1)
            week_num += 1

        data["sections"]["weekly_trend"] = {
            "title": "周度趋势",
            "type": "line",
            "data": weeks
        }

        return data
