# -*- coding: utf-8 -*-
"""
项目资源聚合服务

提供个人工作量、部门工作量以及全局资源概览等能力。
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.common.date_range import get_month_range, month_start, month_end
from app.models.organization import Department
from app.models.project.resource_plan import ProjectStageResourcePlan
from app.models.user import User
from app.schemas.workload import (
    UserWorkloadResponse,
    UserWorkloadSummary,
)
from app.services.project.core_service import ProjectCoreService
from app.services.timesheet_aggregation_service import TimesheetAggregationService
from app.services.user_workload_service import (
    build_daily_load,
    build_project_workload,
    build_task_list,
    calculate_total_actual_hours,
    calculate_total_assigned_hours,
    calculate_workdays,
    get_user_allocations,
    get_user_tasks,
)


class ProjectResourceService:
    """聚合成员工作量、部门资源分布等数据。"""

    def __init__(self, db: Session, core_service: Optional[ProjectCoreService] = None):
        self.db = db
        self.core_service = core_service or ProjectCoreService(db)

    # ------------------------------------------------------------------ #
    # 个人工作量
    # ------------------------------------------------------------------ #
    def get_user_workload(
        self,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> UserWorkloadResponse:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("user not found")

        start_date, end_date = self._normalize_range(start_date, end_date)
        tasks = get_user_tasks(self.db, user_id, start_date, end_date)
        allocations = get_user_allocations(self.db, user_id, start_date, end_date)

        assigned_hours = float(calculate_total_assigned_hours(tasks, allocations))
        actual_hours = float(calculate_total_actual_hours(allocations))
        workdays = calculate_workdays(start_date, end_date)
        standard_hours = workdays * 8.0

        allocation_rate = round((assigned_hours / standard_hours) * 100, 2) if standard_hours else 0.0
        efficiency = round((actual_hours / assigned_hours) * 100, 2) if assigned_hours else 0.0

        summary = UserWorkloadSummary(
            total_assigned_hours=round(assigned_hours, 2),
            standard_hours=round(standard_hours, 2),
            allocation_rate=allocation_rate,
            actual_hours=round(actual_hours, 2),
            efficiency=efficiency,
        )

        return UserWorkloadResponse(
            user_id=user.id,
            user_name=user.display_name,
            dept_name=getattr(user, "department", None),
            period={"start": start_date.isoformat(), "end": end_date.isoformat()},
            summary=summary,
            by_project=build_project_workload(tasks),
            daily_load=build_daily_load(tasks, start_date, end_date),
            tasks=build_task_list(tasks),
        )

    # ------------------------------------------------------------------ #
    # 部门工作量
    # ------------------------------------------------------------------ #
    def get_department_workload_summary(
        self,
        dept_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        department = self.db.query(Department).filter(Department.id == dept_id).first()
        if not department:
            raise ValueError("department not found")

        start_date, end_date = self._normalize_range(start_date, end_date)
        members = self._get_department_members(dept_id, department)
        member_ids = [m.id for m in members]

        if not member_ids:
            return {
                "department": {"id": department.id, "name": department.dept_name},
                "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
                "members": [],
                "summary": {
                    "total_members": 0,
                    "avg_allocation": 0,
                    "overloaded_count": 0,
                    "underutilized_count": 0,
                },
            }

        allocations = (
            self.db.query(ProjectStageResourcePlan)
            .filter(
                ProjectStageResourcePlan.assigned_employee_id.in_(member_ids),
                ProjectStageResourcePlan.planned_start <= end_date,
                ProjectStageResourcePlan.planned_end >= start_date,
            )
            .all()
        )

        member_summary = []
        overloaded = 0
        underutilized = 0
        total_allocation = 0.0

        allocations_by_member: Dict[int, List[ProjectStageResourcePlan]] = {}
        for alloc in allocations:
            allocations_by_member.setdefault(alloc.assigned_employee_id, []).append(alloc)

        for member in members:
            member_allocs = allocations_by_member.get(member.id, [])
            total_pct = sum(float(a.allocation_pct or 100) for a in member_allocs)
            status = "balanced"
            if total_pct > 100:
                status = "overloaded"
                overloaded += 1
            elif total_pct < 50:
                status = "underutilized"
                underutilized += 1
            total_allocation += total_pct

            member_summary.append(
                {
                    "id": member.id,
                    "name": member.display_name,
                    "total_allocation": round(total_pct, 2),
                    "status": status,
                    "project_count": len({alloc.project_id for alloc in member_allocs}),
                }
            )

        avg_allocation = round(total_allocation / len(members), 2) if members else 0.0

        return {
            "department": {"id": department.id, "name": department.dept_name},
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "members": sorted(member_summary, key=lambda m: m["total_allocation"], reverse=True),
            "summary": {
                "total_members": len(members),
                "avg_allocation": avg_allocation,
                "overloaded_count": overloaded,
                "underutilized_count": underutilized,
            },
        }

    def get_department_timesheet_summary(
        self,
        dept_id: int,
        year: int,
        month: int,
    ) -> Dict[str, Any]:
        """调用 TimesheetAggregationService 生成部门月度汇总。"""
        aggregator = TimesheetAggregationService(self.db)
        return aggregator.aggregate_monthly_timesheet(year, month, department_id=dept_id)

    # ------------------------------------------------------------------ #
    # 全局资源概览
    # ------------------------------------------------------------------ #
    def get_workload_overview(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        start_date, end_date = self._normalize_range(start_date, end_date)
        query = self.db.query(ProjectStageResourcePlan)
        if start_date:
            query = query.filter(ProjectStageResourcePlan.planned_end >= start_date)
        if end_date:
            query = query.filter(ProjectStageResourcePlan.planned_start <= end_date)

        plans = query.all()
        status_breakdown: Dict[str, int] = {}
        over_allocated = 0
        department_breakdown: Dict[str, int] = {}

        for plan in plans:
            status = plan.assignment_status or "PENDING"
            status_breakdown[status] = status_breakdown.get(status, 0) + 1

            if plan.allocation_pct and float(plan.allocation_pct) > 100:
                over_allocated += 1

            dept_name = "未分配"
            if plan.assigned_employee is not None:
                dept_name = getattr(plan.assigned_employee, "department", None) or dept_name
            department_breakdown[dept_name] = department_breakdown.get(dept_name, 0) + 1

        return {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "total_plans": len(plans),
            "status_breakdown": status_breakdown,
            "department_breakdown": department_breakdown,
            "over_allocated_roles": over_allocated,
        }

    # ------------------------------------------------------------------ #
    # 辅助方法
    # ------------------------------------------------------------------ #
    @staticmethod
    def _normalize_range(
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> Tuple[date, date]:
        today = date.today()
        if start_date is None and end_date is None:
            start_date, end_date = get_month_range(today)
        elif start_date is None and end_date is not None:
            start_date = month_start(end_date)
        elif start_date is not None and end_date is None:
            end_date = month_end(start_date)

        if start_date > end_date:
            raise ValueError("start_date must be before end_date")
        return start_date, end_date

    def _get_department_members(self, dept_id: int, dept: Department) -> List[User]:
        query = self.db.query(User).filter(User.is_active == True)  # noqa: E712
        if hasattr(User, "department_id"):
            query = query.filter(User.department_id == dept_id)
        else:
            query = query.filter(User.department == dept.dept_name)
        return query.all()
