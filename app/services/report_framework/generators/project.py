# -*- coding: utf-8 -*-
"""
项目报表数据生成器

统一的项目周报、月报数据生成逻辑
"""

from datetime import date, timedelta
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models.project import Machine, Project, ProjectMilestone
from app.models.timesheet import Timesheet


class ProjectReportGenerator:
    """项目报表数据生成器"""

    @staticmethod
    def generate_weekly(
        db: Session,
        project_id: int,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """
        生成项目周报数据

        Args:
            db: 数据库会话
            project_id: 项目ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            报表数据字典
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"error": "项目不存在", "project_id": project_id}

        # 基础信息
        summary = ProjectReportGenerator._build_project_summary(
            project, start_date, end_date
        )

        # 里程碑数据
        milestones = ProjectReportGenerator._get_milestone_data(
            db, project_id, start_date, end_date
        )

        # 工时数据
        timesheet_data = ProjectReportGenerator._get_timesheet_data(
            db, project_id, start_date, end_date
        )

        # 机台数据
        machines = ProjectReportGenerator._get_machine_data(db, project_id)

        # 风险提示
        risks = ProjectReportGenerator._assess_risks(summary, milestones)

        return {
            "summary": summary,
            "milestones": milestones,
            "timesheet": timesheet_data,
            "machines": machines,
            "risks": risks,
        }

    @staticmethod
    def generate_monthly(
        db: Session,
        project_id: int,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """
        生成项目月报数据

        Args:
            db: 数据库会话
            project_id: 项目ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            报表数据字典
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"error": "项目不存在", "project_id": project_id}

        # 基础信息
        summary = ProjectReportGenerator._build_project_summary(
            project, start_date, end_date
        )
        summary["report_type"] = "月报"

        # 里程碑数据
        milestones = ProjectReportGenerator._get_milestone_data(
            db, project_id, start_date, end_date
        )

        # 周度趋势数据
        weekly_trend = ProjectReportGenerator._get_weekly_trend(
            db, project_id, start_date, end_date
        )

        # 成本概况
        cost_summary = ProjectReportGenerator._get_cost_summary(project)

        return {
            "summary": summary,
            "milestones": milestones,
            "progress_trend": weekly_trend,
            "cost": cost_summary,
        }

    @staticmethod
    def _build_project_summary(
        project: Project,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """构建项目基础信息"""
        return {
            "project_id": project.id,
            "project_code": getattr(project, "project_code", ""),
            "project_name": project.project_name,
            "customer_name": getattr(project, "customer_name", ""),
            "current_stage": getattr(project, "current_stage", "S1"),
            "health_status": getattr(project, "health_status", "H1"),
            "progress": float(project.progress or 0),
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
        }

    @staticmethod
    def _get_milestone_data(
        db: Session,
        project_id: int,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """获取里程碑数据"""
        milestones = (
            db.query(ProjectMilestone)
            .filter(
                ProjectMilestone.project_id == project_id,
                ProjectMilestone.planned_date.between(start_date, end_date),
            )
            .all()
        )

        details = []
        completed = 0
        delayed = 0
        in_progress = 0

        for m in milestones:
            status = getattr(m, "status", "PENDING")
            if status == "COMPLETED":
                completed += 1
            elif status == "DELAYED":
                delayed += 1
            elif status == "IN_PROGRESS":
                in_progress += 1

            details.append(
                {
                    "id": m.id,
                    "name": getattr(m, "milestone_name", f"里程碑{m.id}"),
                    "planned_date": (
                        m.planned_date.isoformat()
                        if hasattr(m, "planned_date") and m.planned_date
                        else None
                    ),
                    "actual_date": (
                        m.actual_date.isoformat()
                        if hasattr(m, "actual_date") and m.actual_date
                        else None
                    ),
                    "status": status,
                }
            )

        return {
            "summary": {
                "total": len(milestones),
                "completed": completed,
                "delayed": delayed,
                "in_progress": in_progress,
            },
            "details": details,
        }

    @staticmethod
    def _get_timesheet_data(
        db: Session,
        project_id: int,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """获取工时数据"""
        timesheets = (
            db.query(Timesheet)
            .filter(
                Timesheet.project_id == project_id,
                Timesheet.work_date.between(start_date, end_date),
            )
            .all()
        )

        total_hours = sum(float(t.hours or 0) for t in timesheets)
        unique_workers = len(set(t.user_id for t in timesheets))

        return {
            "total_hours": round(total_hours, 2),
            "unique_workers": unique_workers,
            "avg_hours_per_worker": (
                round(total_hours / unique_workers, 2) if unique_workers > 0 else 0
            ),
            "timesheet_count": len(timesheets),
        }

    @staticmethod
    def _get_machine_data(db: Session, project_id: int) -> List[Dict[str, Any]]:
        """获取机台数据"""
        machines = db.query(Machine).filter(Machine.project_id == project_id).all()

        return [
            {
                "id": m.id,
                "machine_code": getattr(m, "machine_code", f"M-{m.id}"),
                "machine_name": getattr(m, "machine_name", f"机台{m.id}"),
                "status": getattr(m, "status", "PENDING"),
                "progress": float(m.progress or 0),
            }
            for m in machines
        ]

    @staticmethod
    def _get_weekly_trend(
        db: Session,
        project_id: int,
        start_date: date,
        end_date: date,
    ) -> List[Dict[str, Any]]:
        """获取周度趋势数据"""
        weeks = []
        current = start_date
        week_num = 1

        while current <= end_date:
            week_end = min(current + timedelta(days=6), end_date)
            week_timesheets = (
                db.query(Timesheet)
                .filter(
                    Timesheet.project_id == project_id,
                    Timesheet.work_date.between(current, week_end),
                )
                .all()
            )
            week_hours = sum(float(t.hours or 0) for t in week_timesheets)

            weeks.append(
                {
                    "week": week_num,
                    "start": current.isoformat(),
                    "end": week_end.isoformat(),
                    "hours": round(week_hours, 2),
                }
            )

            current = week_end + timedelta(days=1)
            week_num += 1

        return weeks

    @staticmethod
    def _get_cost_summary(project: Project) -> Dict[str, Any]:
        """获取成本概况"""
        budget = (
            float(project.budget_amount or 0)
            if hasattr(project, "budget_amount")
            else 0
        )

        return {
            "planned_cost": budget,
            "actual_cost": 0,  # 需要从成本模块获取
            "cost_variance": 0,
            "cost_variance_percent": 0,
        }

    @staticmethod
    def _assess_risks(
        summary: Dict[str, Any],
        milestones: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """评估风险"""
        risks = []

        # 健康度风险
        health = summary.get("health_status", "H1")
        if health in ["H2", "H3"]:
            risks.append(
                {
                    "type": "健康度",
                    "level": "HIGH" if health == "H3" else "MEDIUM",
                    "description": f"项目健康度为 {health}",
                }
            )

        # 里程碑延期风险
        delayed = milestones.get("summary", {}).get("delayed", 0)
        if delayed > 0:
            risks.append(
                {
                    "type": "里程碑延期",
                    "level": "HIGH",
                    "description": f"有 {delayed} 个里程碑延期",
                }
            )

        return risks
