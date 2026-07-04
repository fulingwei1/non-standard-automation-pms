# -*- coding: utf-8 -*-
"""
PMO Cockpit Service - 业务逻辑层
处理驾驶舱、风险墙、周报和资源总览的核心业务逻辑
"""
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.organization import Department
from app.models.pmo import PmoProjectRisk, PmoResourceAllocation
from app.models.project import Project
from app.models.user import User
from app.schemas.pmo import (
    DashboardResponse,
    DashboardSummary,
    ResourceOverviewResponse,
    RiskResponse,
    RiskWallResponse,
    WeeklyReportResponse,
)
from app.services.project_status_normalization import project_status_bucket


class PmoCockpitService:
    """PMO驾驶舱服务类"""

    def __init__(self, db: Session):
        self.db = db

    def get_dashboard(self) -> DashboardResponse:
        """
        获取PMO驾驶舱数据
        """
        # 统计项目
        total_projects = self.db.query(func.count(Project.id)).scalar() or 0
        active_projects = (
            self.db.query(func.count(Project.id)).filter(Project.is_active).scalar()
            or 0
        )
        completed_projects = (
            self.db.query(func.count(Project.id))
            .filter(Project.stage == "S9")
            .scalar()
            or 0
        )

        # 统计延期项目（简化：计划结束日期已过但未完成）
        today = date.today()
        delayed_projects = (
            self.db.query(func.count(Project.id))
            .filter(
                Project.planned_end_date.isnot(None),
                Project.planned_end_date < today,
                Project.stage != "S9",
                Project.is_active,
            )
            .scalar()
            or 0
        )

        # 统计预算和成本
        budget_result = self.db.query(func.sum(Project.budget_amount)).scalar() or 0
        cost_result = self.db.query(func.sum(Project.actual_cost)).scalar() or 0

        # 统计风险
        total_risks = (
            self.db.query(func.count(PmoProjectRisk.id))
            .filter(PmoProjectRisk.status != "CLOSED")
            .scalar()
            or 0
        )
        high_risks = (
            self.db.query(func.count(PmoProjectRisk.id))
            .filter(
                PmoProjectRisk.risk_level == "HIGH",
                PmoProjectRisk.status != "CLOSED",
            )
            .scalar()
            or 0
        )
        critical_risks = (
            self.db.query(func.count(PmoProjectRisk.id))
            .filter(
                PmoProjectRisk.risk_level == "CRITICAL",
                PmoProjectRisk.status != "CLOSED",
            )
            .scalar()
            or 0
        )

        # 按状态统计项目
        projects_by_status = self._get_projects_by_status()

        # 按阶段统计项目
        projects_by_stage = self._get_projects_by_stage()

        # 最近的风险
        recent_risks = self._get_recent_risks(limit=10)

        return DashboardResponse(
            summary=DashboardSummary(
                total_projects=total_projects,
                active_projects=active_projects,
                completed_projects=completed_projects,
                delayed_projects=delayed_projects,
                total_budget=float(budget_result),
                total_cost=float(cost_result),
                total_risks=total_risks,
                high_risks=high_risks,
                critical_risks=critical_risks,
            ),
            projects_by_status=projects_by_status,
            projects_by_stage=projects_by_stage,
            recent_risks=recent_risks,
        )

    def get_risk_wall(self) -> RiskWallResponse:
        """
        获取风险预警墙数据
        """
        # 统计风险
        total_risks = (
            self.db.query(PmoProjectRisk)
            .filter(PmoProjectRisk.status != "CLOSED")
            .count()
        )

        # 严重风险
        critical_risks_data = (
            self.db.query(PmoProjectRisk)
            .filter(
                PmoProjectRisk.risk_level == "CRITICAL",
                PmoProjectRisk.status != "CLOSED",
            )
            .order_by(desc(PmoProjectRisk.created_at))
            .all()
        )

        # 高风险
        high_risks_data = (
            self.db.query(PmoProjectRisk)
            .filter(
                PmoProjectRisk.risk_level == "HIGH",
                PmoProjectRisk.status != "CLOSED",
            )
            .order_by(desc(PmoProjectRisk.created_at))
            .limit(20)
            .all()
        )

        # 按类别统计
        by_category = self._get_risks_by_category()

        # 按项目统计
        by_project = self._get_risks_by_project(limit=10)

        # 转换风险列表
        critical_list = [self._convert_risk_to_response(risk) for risk in critical_risks_data]
        high_list = [self._convert_risk_to_response(risk) for risk in high_risks_data]

        return RiskWallResponse(
            total_risks=total_risks,
            critical_risks=critical_list,
            high_risks=high_list,
            by_category=by_category,
            by_project=by_project,
        )

    def get_weekly_report(self, week_start: Optional[date] = None) -> WeeklyReportResponse:
        """
        获取项目状态周报
        """
        # 默认使用当前周
        today = date.today()
        if not week_start:
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday)

        week_end = week_start + timedelta(days=6)

        # 统计新项目（本周创建）
        new_projects = (
            self.db.query(Project)
            .filter(
                Project.created_at >= datetime.combine(week_start, datetime.min.time()),
                Project.created_at <= datetime.combine(week_end, datetime.max.time()),
            )
            .count()
        )

        # 统计完成项目（本周完成）
        completed_projects = (
            self.db.query(Project)
            .filter(
                Project.actual_end_date >= week_start,
                Project.actual_end_date <= week_end,
                Project.stage == "S9",
            )
            .count()
        )

        # 统计延期项目
        delayed_projects = (
            self.db.query(Project)
            .filter(
                Project.planned_end_date < today,
                Project.stage != "S9",
                Project.is_active,
            )
            .count()
        )

        # 统计新风险
        new_risks = (
            self.db.query(PmoProjectRisk)
            .filter(
                PmoProjectRisk.created_at
                >= datetime.combine(week_start, datetime.min.time()),
                PmoProjectRisk.created_at
                <= datetime.combine(week_end, datetime.max.time()),
            )
            .count()
        )

        # 统计解决风险
        resolved_risks = (
            self.db.query(PmoProjectRisk)
            .filter(
                PmoProjectRisk.closed_date >= week_start,
                PmoProjectRisk.closed_date <= week_end,
                PmoProjectRisk.status == "CLOSED",
            )
            .count()
        )

        # 项目更新列表
        project_updates = self._get_project_updates(week_start, week_end, limit=10)

        return WeeklyReportResponse(
            report_date=today,
            week_start=week_start,
            week_end=week_end,
            new_projects=new_projects,
            completed_projects=completed_projects,
            delayed_projects=delayed_projects,
            new_risks=new_risks,
            resolved_risks=resolved_risks,
            project_updates=project_updates,
        )

    def get_resource_overview(self) -> ResourceOverviewResponse:
        """
        获取资源负荷总览
        """
        # 统计资源分配
        total_resources = self.db.query(User).filter(User.is_active).count()

        # 统计已分配资源
        allocated_resource_ids = (
            self.db.query(PmoResourceAllocation.resource_id)
            .filter(PmoResourceAllocation.status.in_(["PLANNED", "ACTIVE"]))
            .distinct()
            .all()
        )
        allocated_resources = len([r[0] for r in allocated_resource_ids])

        available_resources = total_resources - allocated_resources

        # 统计超负荷资源
        overloaded_resources = self._calculate_overloaded_resources()

        # 按部门统计
        by_department = self._get_resources_by_department()
        employees = self._get_resource_overview_employees()
        employees_with_conflicts = sum(1 for employee in employees if employee["has_conflict"])
        total_conflicts = sum(len(employee["conflicts"]) for employee in employees)
        avg_utilization = (
            round(
                sum(employee["current_allocation"] for employee in employees) / len(employees),
                1,
            )
            if employees
            else 0.0
        )

        return ResourceOverviewResponse(
            total_resources=total_resources,
            allocated_resources=allocated_resources,
            available_resources=available_resources,
            overloaded_resources=overloaded_resources,
            by_department=by_department,
            total_employees=len(employees),
            employees_with_conflicts=employees_with_conflicts,
            total_conflicts=total_conflicts,
            avg_utilization=avg_utilization,
            employees=employees,
        )

    # ==================== 私有辅助方法 ====================

    def _get_projects_by_status(self) -> Dict[str, int]:
        """按状态统计项目"""
        projects_by_status = {}
        status_counts = (
            self.db.query(Project.status, Project.stage, Project.is_archived, func.count(Project.id))
            .group_by(Project.status, Project.stage, Project.is_archived)
            .all()
        )
        for status, stage, is_archived, count in status_counts:
            bucket = project_status_bucket(status, stage, is_archived)
            projects_by_status[bucket] = projects_by_status.get(bucket, 0) + count
        return projects_by_status

    def _get_projects_by_stage(self) -> Dict[str, int]:
        """按阶段统计项目"""
        projects_by_stage = {}
        stage_counts = (
            self.db.query(Project.stage, func.count(Project.id))
            .group_by(Project.stage)
            .all()
        )
        for stage, count in stage_counts:
            projects_by_stage[stage or "UNKNOWN"] = count
        return projects_by_stage

    def _get_recent_risks(self, limit: int = 10) -> List[RiskResponse]:
        """获取最近的风险"""
        recent_risks = (
            self.db.query(PmoProjectRisk)
            .filter(PmoProjectRisk.status != "CLOSED")
            .order_by(desc(PmoProjectRisk.created_at))
            .limit(limit)
            .all()
        )

        return [self._convert_risk_to_response(risk) for risk in recent_risks]

    def _convert_risk_to_response(self, risk: PmoProjectRisk) -> RiskResponse:
        """将风险模型转换为响应对象"""
        return RiskResponse(
            id=risk.id,
            project_id=risk.project_id,
            risk_no=risk.risk_no,
            risk_category=risk.risk_category,
            risk_name=risk.risk_name,
            description=risk.description,
            probability=risk.probability,
            impact=risk.impact,
            risk_level=risk.risk_level,
            response_strategy=risk.response_strategy,
            response_plan=risk.response_plan,
            owner_id=risk.owner_id,
            owner_name=risk.owner_name,
            status=risk.status,
            follow_up_date=risk.follow_up_date,
            last_update=risk.last_update,
            trigger_condition=risk.trigger_condition,
            is_triggered=risk.is_triggered,
            triggered_date=risk.triggered_date,
            closed_date=risk.closed_date,
            closed_reason=risk.closed_reason,
            created_at=risk.created_at,
            updated_at=risk.updated_at,
        )

    def _get_risks_by_category(self) -> Dict[str, int]:
        """按类别统计风险"""
        by_category = {}
        category_counts = (
            self.db.query(PmoProjectRisk.risk_category, func.count(PmoProjectRisk.id))
            .filter(PmoProjectRisk.status != "CLOSED")
            .group_by(PmoProjectRisk.risk_category)
            .all()
        )

        for category, count in category_counts:
            by_category[category] = count

        return by_category

    def _get_risks_by_project(self, limit: int = 10) -> List[Dict[str, Any]]:
        """按项目统计风险"""
        by_project = []
        project_risks = (
            self.db.query(
                PmoProjectRisk.project_id,
                func.count(PmoProjectRisk.id).label("risk_count"),
            )
            .filter(PmoProjectRisk.status != "CLOSED")
            .group_by(PmoProjectRisk.project_id)
            .order_by(desc("risk_count"))
            .limit(limit)
            .all()
        )

        for project_id, risk_count in project_risks:
            project = (
                self.db.query(Project).filter(Project.id == project_id).first()
            )
            if project:
                by_project.append(
                    {
                        "project_id": project_id,
                        "project_code": project.project_code,
                        "project_name": project.project_name,
                        "risk_count": risk_count,
                    }
                )

        return by_project

    def _get_project_updates(
        self, week_start: date, week_end: date, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取项目更新列表"""
        project_updates = []
        updated_projects = (
            self.db.query(Project)
            .filter(
                Project.updated_at >= datetime.combine(week_start, datetime.min.time()),
                Project.updated_at <= datetime.combine(week_end, datetime.max.time()),
            )
            .order_by(desc(Project.updated_at))
            .limit(limit)
            .all()
        )

        for proj in updated_projects:
            project_updates.append(
                {
                    "project_id": proj.id,
                    "project_code": proj.project_code,
                    "project_name": proj.project_name,
                    "stage": proj.stage,
                    "status": proj.status,
                    "progress": float(proj.progress_pct) if proj.progress_pct else 0.0,
                    "updated_at": proj.updated_at,
                }
            )

        return project_updates

    def _calculate_overloaded_resources(self, standard_workload: int = 160) -> int:
        """
        计算超负荷资源数量
        
        Args:
            standard_workload: 标准工作负荷（小时/月），默认160小时
            
        Returns:
            超负荷资源数量
        """
        resource_workload = defaultdict(float)

        # 统计每个资源的分配工时
        allocations = (
            self.db.query(PmoResourceAllocation)
            .filter(PmoResourceAllocation.status.in_(["PLANNED", "ACTIVE"]))
            .all()
        )

        for alloc in allocations:
            # 计算该分配的预估工时（使用分配比例）
            if alloc.allocation_percent:
                # 假设每个项目的标准工时为160小时
                estimated_hours = (
                    alloc.allocation_percent / 100
                ) * standard_workload
                resource_workload[alloc.resource_id] += estimated_hours

        # 统计超负荷资源数量
        overloaded_count = 0
        for resource_id, total_hours in resource_workload.items():
            if total_hours > standard_workload:
                overloaded_count += 1

        return overloaded_count

    def _get_resource_overview_employees(self) -> List[Dict[str, Any]]:
        """Build timeline rows consumed by the PMO resource overview page."""
        rows = (
            self.db.query(PmoResourceAllocation, User, Project)
            .join(User, PmoResourceAllocation.resource_id == User.id)
            .join(Project, PmoResourceAllocation.project_id == Project.id)
            .filter(PmoResourceAllocation.status.in_(["PLANNED", "ACTIVE"]))
            .order_by(User.real_name, User.username, PmoResourceAllocation.start_date)
            .all()
        )

        employees_by_id: Dict[int, Dict[str, Any]] = {}
        for allocation, user, project in rows:
            employee = employees_by_id.setdefault(
                user.id,
                {
                    "user_id": user.id,
                    "real_name": allocation.resource_name or user.real_name or user.username,
                    "department": allocation.resource_dept or user.department or "未分配",
                    "current_allocation": 0,
                    "total_projects": 0,
                    "has_conflict": False,
                    "conflicts": [],
                    "allocations": [],
                },
            )
            employee["allocations"].append(
                {
                    "id": allocation.id,
                    "project_id": project.id,
                    "project_name": project.project_name,
                    "project_code": project.project_code,
                    "role": allocation.resource_role,
                    "stage": project.stage,
                    "status": allocation.status,
                    "start_date": self._date_to_iso(allocation.start_date),
                    "end_date": self._date_to_iso(allocation.end_date),
                    "allocation_pct": int(allocation.allocation_percent or 0),
                    "planned_hours": allocation.planned_hours or 0,
                    "actual_hours": allocation.actual_hours or 0,
                }
            )

        employees = list(employees_by_id.values())
        for employee in employees:
            allocations = employee["allocations"]
            employee["total_projects"] = len({item["project_id"] for item in allocations})
            employee["current_allocation"] = self._calculate_current_allocation(allocations)
            employee["conflicts"] = self._calculate_allocation_conflicts(allocations)
            employee["has_conflict"] = bool(employee["conflicts"])

        return sorted(employees, key=lambda item: (item["department"], item["real_name"]))

    @staticmethod
    def _date_to_iso(value: Optional[date]) -> Optional[str]:
        return value.isoformat() if value else None

    @staticmethod
    def _parse_iso_date(value: Optional[str]) -> Optional[date]:
        if not value:
            return None
        return date.fromisoformat(value)

    @classmethod
    def _calculate_current_allocation(cls, allocations: List[Dict[str, Any]]) -> int:
        today = date.today()
        current_allocations = []
        for allocation in allocations:
            start = cls._parse_iso_date(allocation.get("start_date"))
            end = cls._parse_iso_date(allocation.get("end_date"))
            if start and end and start <= today <= end:
                current_allocations.append(allocation)

        target_allocations = current_allocations or allocations
        return sum(int(item.get("allocation_pct") or 0) for item in target_allocations)

    @classmethod
    def _calculate_allocation_conflicts(
        cls, allocations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        dated_allocations = []
        for allocation in allocations:
            start = cls._parse_iso_date(allocation.get("start_date"))
            end = cls._parse_iso_date(allocation.get("end_date"))
            if start and end and start <= end:
                dated_allocations.append((allocation, start, end))

        if not dated_allocations:
            total = sum(int(item.get("allocation_pct") or 0) for item in allocations)
            if total <= 100:
                return []
            return [
                {
                    "start_date": None,
                    "end_date": None,
                    "total_allocation": total,
                    "projects": [item["project_name"] for item in allocations],
                }
            ]

        boundaries = set()
        for _, start, end in dated_allocations:
            boundaries.add(start)
            boundaries.add(end + timedelta(days=1))

        conflicts = []
        ordered_boundaries = sorted(boundaries)
        for segment_start, next_boundary in zip(ordered_boundaries, ordered_boundaries[1:]):
            segment_end = next_boundary - timedelta(days=1)
            active = [
                allocation
                for allocation, start, end in dated_allocations
                if start <= segment_start and end >= segment_end
            ]
            total = sum(int(item.get("allocation_pct") or 0) for item in active)
            if total > 100:
                conflicts.append(
                    {
                        "start_date": segment_start.isoformat(),
                        "end_date": segment_end.isoformat(),
                        "total_allocation": total,
                        "projects": [item["project_name"] for item in active],
                    }
                )

        return conflicts

    def _get_resources_by_department(self) -> List[Dict[str, Any]]:
        """按部门统计资源"""
        by_department = []
        departments = self.db.query(Department).all()

        for dept in departments:
            dept_users = (
                self.db.query(User)
                .filter(User.department == dept.dept_name, User.is_active)
                .count()
            )

            dept_allocated = (
                self.db.query(PmoResourceAllocation.resource_id)
                .join(User, PmoResourceAllocation.resource_id == User.id)
                .filter(
                    User.department == dept.dept_name,
                    PmoResourceAllocation.status.in_(["PLANNED", "ACTIVE"]),
                )
                .distinct()
                .count()
            )

            by_department.append(
                {
                    "department_id": dept.id,
                    "department_name": dept.dept_name,
                    "total_resources": dept_users,
                    "allocated_resources": dept_allocated,
                    "available_resources": dept_users - dept_allocated,
                }
            )

        return by_department
