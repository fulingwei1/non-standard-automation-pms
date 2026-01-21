# -*- coding: utf-8 -*-
"""
项目报表生成（项目周报、项目月报）
"""

from datetime import date, timedelta
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.models.project import Machine, Project, ProjectMilestone
from app.models.timesheet import Timesheet


class ProjectReportMixin:
    """项目报表生成功能混入类"""

    @staticmethod
    def generate_project_weekly_report(
        db: Session,
        project_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        生成项目周报数据

        Args:
            db: 数据库会话
            project_id: 项目ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            报表数据
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"error": "项目不存在"}

        # 获取项目基本信息
        summary = {
            "project_code": project.project_code if hasattr(project, 'project_code') else "",
            "project_name": project.project_name,
            "customer_name": project.customer_name if hasattr(project, 'customer_name') else "",
            "current_stage": project.current_stage if hasattr(project, 'current_stage') else "S1",
            "health_status": project.health_status if hasattr(project, 'health_status') else "H1",
            "progress": float(project.progress or 0),
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat()
        }

        # 获取本周的里程碑完成情况
        milestones = db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == project_id,
            ProjectMilestone.milestone_date.between(start_date, end_date)
        ).all()

        milestone_summary = {
            "total": len(milestones),
            "completed": sum(1 for m in milestones if m.status == "COMPLETED"),
            "delayed": sum(1 for m in milestones if m.status == "DELAYED"),
            "in_progress": sum(1 for m in milestones if m.status == "IN_PROGRESS")
        }

        # 获取工时数据
        timesheets = db.query(Timesheet).filter(
            Timesheet.project_id == project_id,
            Timesheet.work_date.between(start_date, end_date)
        ).all()

        total_hours = sum(float(t.hours or 0) for t in timesheets)
        unique_workers = len(set(t.user_id for t in timesheets))

        # 获取机台进度
        machines = db.query(Machine).filter(Machine.project_id == project_id).all()
        machine_summary = []
        for machine in machines:
            machine_summary.append({
                "machine_code": machine.machine_code if hasattr(machine, 'machine_code') else f"M-{machine.id}",
                "machine_name": machine.machine_name if hasattr(machine, 'machine_name') else f"机台{machine.id}",
                "status": machine.status if hasattr(machine, 'status') else "PENDING",
                "progress": float(machine.progress or 0)
            })

        # 风险提示
        risks = []
        if summary["health_status"] in ["H2", "H3"]:
            risks.append({
                "type": "健康度",
                "level": "HIGH" if summary["health_status"] == "H3" else "MEDIUM",
                "description": f"项目健康度为 {summary['health_status']}"
            })

        if milestone_summary["delayed"] > 0:
            risks.append({
                "type": "里程碑延期",
                "level": "HIGH",
                "description": f"有 {milestone_summary['delayed']} 个里程碑延期"
            })

        return {
            "summary": summary,
            "milestones": {
                "summary": milestone_summary,
                "details": [
                    {
                        "name": m.milestone_name if hasattr(m, 'milestone_name') else f"里程碑{m.id}",
                        "date": m.milestone_date.isoformat() if hasattr(m, 'milestone_date') and m.milestone_date else None,
                        "status": m.status if hasattr(m, 'status') else "PENDING"
                    }
                    for m in milestones
                ]
            },
            "timesheet": {
                "total_hours": round(total_hours, 2),
                "unique_workers": unique_workers,
                "avg_hours_per_worker": round(total_hours / unique_workers, 2) if unique_workers > 0 else 0
            },
            "machines": machine_summary,
            "risks": risks
        }

    @staticmethod
    def generate_project_monthly_report(
        db: Session,
        project_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        生成项目月报数据

        Args:
            db: 数据库会话
            project_id: 项目ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            报表数据
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"error": "项目不存在"}

        # 基础信息
        summary = {
            "project_code": project.project_code if hasattr(project, 'project_code') else "",
            "project_name": project.project_name,
            "current_stage": project.current_stage if hasattr(project, 'current_stage') else "S1",
            "health_status": project.health_status if hasattr(project, 'health_status') else "H1",
            "progress": float(project.progress or 0),
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat()
        }

        # 进度趋势（按周统计）
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

        # 里程碑完成情况
        milestones = db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == project_id,
            ProjectMilestone.milestone_date.between(start_date, end_date)
        ).all()

        milestone_details = []
        for m in milestones:
            milestone_details.append({
                "name": m.milestone_name if hasattr(m, 'milestone_name') else f"里程碑{m.id}",
                "planned_date": m.milestone_date.isoformat() if hasattr(m, 'milestone_date') and m.milestone_date else None,
                "actual_date": m.actual_date.isoformat() if hasattr(m, 'actual_date') and m.actual_date else None,
                "status": m.status if hasattr(m, 'status') else "PENDING"
            })

        # 成本概况
        cost_summary = {
            "planned_cost": float(project.budget_amount or 0) if hasattr(project, 'budget_amount') else 0,
            "actual_cost": 0,  # 需要从成本模块获取
            "cost_variance": 0,
            "cost_variance_percent": 0
        }

        return {
            "summary": summary,
            "progress_trend": weeks,
            "milestones": milestone_details,
            "cost": cost_summary
        }
