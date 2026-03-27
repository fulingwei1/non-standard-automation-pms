# -*- coding: utf-8 -*-
"""
成员个性化视图 Dashboard 适配器

关注：
- 分配给自己的任务
- 参与项目的进度
- 个人工时统计
- 待办事项
"""

from datetime import date, timedelta
from typing import List

from sqlalchemy import func

from app.models.project import Project
from app.models.project.team import ProjectMember
from app.models.progress import Task
from app.models.timesheet import Timesheet
from app.schemas.dashboard import (
    DashboardStatCard,
    DashboardWidget,
)
from app.services.dashboard_adapter import DashboardAdapter, register_dashboard


@register_dashboard
class MemberViewDashboardAdapter(DashboardAdapter):
    """项目成员视图适配器"""

    @property
    def module_id(self) -> str:
        return "member_view"

    @property
    def module_name(self) -> str:
        return "成员视图"

    @property
    def supported_roles(self) -> List[str]:
        return [
            "ME", "EE", "SW", "DEBUG",
            "QA", "PU", "FI", "SA",
            "ASSEMBLER", "WAREHOUSE",
            "HR", "PRESALES",
            "CUSTOMER_SERVICE", "BUSINESS_SUPPORT",
            "DEFAULT",
        ]

    def get_stats(self) -> List[DashboardStatCard]:
        user_id = self.current_user.id

        # 我参与的项目
        my_projects_count = (
            self.db.query(func.count(func.distinct(ProjectMember.project_id)))
            .join(Project, ProjectMember.project_id == Project.id)
            .filter(
                ProjectMember.user_id == user_id,
                Project.is_active == True,  # noqa: E712
            )
            .scalar()
            or 0
        )

        # 我的任务统计
        my_tasks = (
            self.db.query(Task.status, func.count(Task.id))
            .filter(Task.owner_id == user_id)
            .group_by(Task.status)
            .all()
        )
        task_stats = {s: c for s, c in my_tasks}
        total_tasks = sum(task_stats.values())
        todo_tasks = task_stats.get("TODO", 0)
        in_progress_tasks = task_stats.get("IN_PROGRESS", 0)
        done_tasks = task_stats.get("DONE", 0)
        blocked_tasks = task_stats.get("BLOCKED", 0)

        # 本月工时（简化查询）
        today = date.today()
        month_start = today.replace(day=1)
        monthly_hours = (
            self.db.query(func.sum(Timesheet.hours))
            .filter(
                Timesheet.user_id == user_id,
                Timesheet.work_date >= month_start,
                Timesheet.work_date <= today,
            )
            .scalar()
        )
        monthly_hours = float(monthly_hours or 0)

        return [
            DashboardStatCard(key="my_projects", title="参与项目", value=my_projects_count, unit="个"),
            DashboardStatCard(key="total_tasks", title="我的任务", value=total_tasks, unit="个"),
            DashboardStatCard(
                key="todo_tasks",
                title="待办/进行中",
                value=f"{todo_tasks}/{in_progress_tasks}",
            ),
            DashboardStatCard(
                key="blocked_tasks",
                title="阻塞任务",
                value=blocked_tasks,
                unit="个",
                trend="up" if blocked_tasks > 0 else "stable",
            ),
            DashboardStatCard(
                key="done_tasks",
                title="已完成",
                value=done_tasks,
                unit="个",
            ),
            DashboardStatCard(
                key="monthly_hours",
                title="本月工时",
                value=round(monthly_hours, 1),
                unit="小时",
            ),
        ]

    def get_widgets(self) -> List[DashboardWidget]:
        user_id = self.current_user.id
        today = date.today()

        # 1. 我的任务列表（待办 + 进行中）
        my_tasks = (
            self.db.query(Task, Project.project_name, Project.project_code)
            .join(Project, Task.project_id == Project.id)
            .filter(
                Task.owner_id == user_id,
                Task.status.in_(["TODO", "IN_PROGRESS", "BLOCKED"]),
            )
            .order_by(
                Task.status.desc(),  # IN_PROGRESS first
                Task.plan_end,
            )
            .limit(20)
            .all()
        )
        task_list = [
            {
                "id": t.id,
                "task_name": t.task_name,
                "status": t.status,
                "progress_percent": t.progress_percent,
                "plan_start": str(t.plan_start) if t.plan_start else None,
                "plan_end": str(t.plan_end) if t.plan_end else None,
                "project_name": proj_name,
                "project_code": proj_code,
                "overdue": t.plan_end < today if t.plan_end else False,
            }
            for t, proj_name, proj_code in my_tasks
        ]

        # 2. 参与项目进度
        my_memberships = (
            self.db.query(Project, ProjectMember.role_code, ProjectMember.allocation_pct)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .filter(
                ProjectMember.user_id == user_id,
                Project.is_active == True,  # noqa: E712
            )
            .all()
        )
        project_list = [
            {
                "id": p.id,
                "project_code": p.project_code,
                "project_name": p.project_name,
                "health": p.health,
                "progress_pct": float(p.progress_pct or 0),
                "my_role": role_code,
                "my_allocation": float(allocation or 0),
                "planned_end_date": str(p.planned_end_date) if p.planned_end_date else None,
            }
            for p, role_code, allocation in my_memberships
        ]

        # 3. 个人工时趋势（最近4周）
        four_weeks_ago = today - timedelta(weeks=4)
        weekly_hours = (
            self.db.query(
                func.strftime("%Y-W%W", Timesheet.work_date).label("week"),
                func.sum(Timesheet.hours).label("hours"),
            )
            .filter(
                Timesheet.user_id == user_id,
                Timesheet.work_date >= four_weeks_ago,
            )
            .group_by(func.strftime("%Y-W%W", Timesheet.work_date))
            .order_by(func.strftime("%Y-W%W", Timesheet.work_date))
            .all()
        )
        hours_data = [
            {"week": w, "hours": float(h or 0)}
            for w, h in weekly_hours
        ]

        # 4. 逾期任务告警
        overdue_tasks = [t for t in task_list if t.get("overdue")]

        return [
            DashboardWidget(
                widget_id="member_task_list",
                widget_type="list",
                title="我的任务",
                data={"items": task_list},
                config={"show_status": True, "highlight_overdue": True},
            ),
            DashboardWidget(
                widget_id="member_project_progress",
                widget_type="table",
                title="参与项目进度",
                data={"items": project_list},
                config={"columns": ["project_name", "health", "progress_pct", "my_role"]},
            ),
            DashboardWidget(
                widget_id="member_timesheet_trend",
                widget_type="chart",
                title="个人工时趋势",
                data={"items": hours_data},
                config={"chart_type": "line", "y_axis": "hours"},
            ),
            DashboardWidget(
                widget_id="member_overdue_alert",
                widget_type="list",
                title="逾期任务告警",
                data={"items": overdue_tasks},
                config={"alert_style": True},
            ),
        ]
