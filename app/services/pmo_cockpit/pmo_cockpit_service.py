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

        return ResourceOverviewResponse(
            total_resources=total_resources,
            allocated_resources=allocated_resources,
            available_resources=available_resources,
            overloaded_resources=overloaded_resources,
            by_department=by_department,
        )

    # ==================== 私有辅助方法 ====================

    def _get_projects_by_status(self) -> Dict[str, int]:
        """按状态统计项目"""
        projects_by_status = {}
        status_counts = (
            self.db.query(Project.status, func.count(Project.id))
            .group_by(Project.status)
            .all()
        )
        for status, count in status_counts:
            projects_by_status[status] = count
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
            projects_by_stage[stage] = count
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

    def _get_resources_by_department(self) -> List[Dict[str, Any]]:
        """按部门统计资源"""
        by_department = []
        departments = self.db.query(Department).all()

        for dept in departments:
            dept_users = (
                self.db.query(User)
                .filter(User.department == dept.name, User.is_active)
                .count()
            )

            dept_allocated = (
                self.db.query(PmoResourceAllocation.resource_id)
                .join(User, PmoResourceAllocation.resource_id == User.id)
                .filter(
                    User.department == dept.name,
                    PmoResourceAllocation.status.in_(["PLANNED", "ACTIVE"]),
                )
                .distinct()
                .count()
            )

            by_department.append(
                {
                    "department_id": dept.id,
                    "department_name": dept.name,
                    "total_resources": dept_users,
                    "allocated_resources": dept_allocated,
                    "available_resources": dept_users - dept_allocated,
                }
            )

        return by_department
