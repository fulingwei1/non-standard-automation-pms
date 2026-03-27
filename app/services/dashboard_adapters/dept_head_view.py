# -*- coding: utf-8 -*-
"""
部门负责人个性化视图 Dashboard 适配器

关注：
- 部门所有项目的绩效排行
- 部门资源负荷情况
- 部门项目风险汇总
- 预算执行率统计
"""

from typing import List

from sqlalchemy import func

from app.models.project import Project
from app.models.project.team import ProjectMember
from app.models.project_risk import ProjectRisk
from app.schemas.dashboard import (
    DashboardStatCard,
    DashboardWidget,
)
from app.services.dashboard_adapter import DashboardAdapter, register_dashboard


@register_dashboard
class DeptHeadViewDashboardAdapter(DashboardAdapter):
    """部门负责人视图适配器"""

    @property
    def module_id(self) -> str:
        return "dept_head_view"

    @property
    def module_name(self) -> str:
        return "部门负责人视图"

    @property
    def supported_roles(self) -> List[str]:
        return [
            "DEPT_HEAD", "dept_head",
            "SALES_DIR", "CTO", "CFO",
            "MANUFACTURING_DIR", "PRODUCTION_MGR",
            "QA_MGR", "PU_MGR", "HR_MGR",
            "WAREHOUSE_MGR", "PRESALES_MGR",
            "CUSTOMER_SERVICE_MGR",
        ]

    def _get_dept_id(self):
        """获取当前用户的部门ID"""
        return self.current_user.department_id

    def _get_dept_projects(self):
        """获取部门所有项目"""
        dept_id = self._get_dept_id()
        if not dept_id:
            return []
        return (
            self.db.query(Project)
            .filter(
                Project.is_active == True,  # noqa: E712
                Project.dept_id == dept_id,
            )
            .all()
        )

    def get_stats(self) -> List[DashboardStatCard]:
        projects = self._get_dept_projects()
        total = len(projects)

        if total == 0:
            return [
                DashboardStatCard(key="dept_projects", title="部门项目", value=0, unit="个"),
            ]

        # 健康度分布
        healthy = sum(1 for p in projects if p.health == "H1")
        at_risk = sum(1 for p in projects if p.health == "H2")
        critical = sum(1 for p in projects if p.health in ("H3", "H4"))

        # 预算执行率
        total_budget = sum(float(p.budget_amount or 0) for p in projects)
        total_actual = sum(float(p.actual_cost or 0) for p in projects)
        budget_exec_rate = (total_actual / total_budget * 100) if total_budget > 0 else 0

        # 平均进度
        avg_progress = sum(float(p.progress_pct or 0) for p in projects) / total

        # 部门资源数
        dept_id = self._get_dept_id()
        member_count = (
            self.db.query(func.count(func.distinct(ProjectMember.user_id)))
            .join(Project, ProjectMember.project_id == Project.id)
            .filter(
                Project.is_active == True,  # noqa: E712
                Project.dept_id == dept_id,
            )
            .scalar()
            or 0
        )

        # 部门风险总数
        risk_count = (
            self.db.query(func.count(ProjectRisk.id))
            .join(Project, ProjectRisk.project_id == Project.id)
            .filter(
                Project.is_active == True,  # noqa: E712
                Project.dept_id == dept_id,
                ProjectRisk.status.in_(["IDENTIFIED", "ANALYZING", "PLANNING", "MONITORING", "OCCURRED"]),
            )
            .scalar()
            or 0
        )

        return [
            DashboardStatCard(key="dept_projects", title="部门项目", value=total, unit="个"),
            DashboardStatCard(
                key="dept_health",
                title="健康/风险/严重",
                value=f"{healthy}/{at_risk}/{critical}",
            ),
            DashboardStatCard(
                key="dept_budget_rate",
                title="预算执行率",
                value=round(budget_exec_rate, 1),
                unit="%",
                trend="up" if budget_exec_rate > 90 else "stable",
            ),
            DashboardStatCard(
                key="dept_avg_progress",
                title="平均进度",
                value=round(avg_progress, 1),
                unit="%",
            ),
            DashboardStatCard(key="dept_members", title="参与人员", value=member_count, unit="人"),
            DashboardStatCard(key="dept_risks", title="活跃风险", value=risk_count, unit="个"),
        ]

    def get_widgets(self) -> List[DashboardWidget]:
        projects = self._get_dept_projects()
        dept_id = self._get_dept_id()

        # 1. 项目绩效排行（按进度和健康度排序）
        perf_data = sorted(
            [
                {
                    "id": p.id,
                    "project_code": p.project_code,
                    "project_name": p.project_name,
                    "health": p.health,
                    "progress_pct": float(p.progress_pct or 0),
                    "budget_amount": float(p.budget_amount or 0),
                    "actual_cost": float(p.actual_cost or 0),
                    "pm_name": p.pm_name,
                    "budget_exec_rate": round(
                        float(p.actual_cost or 0) / float(p.budget_amount) * 100, 1
                    ) if p.budget_amount and float(p.budget_amount) > 0 else 0,
                }
                for p in projects
            ],
            key=lambda x: (-x["progress_pct"], x["health"]),
        )

        # 2. 资源负荷统计（每人分配比例汇总）
        resource_load = (
            self.db.query(
                ProjectMember.user_id,
                func.sum(ProjectMember.allocation_pct).label("total_alloc"),
                func.count(ProjectMember.project_id).label("project_count"),
            )
            .join(Project, ProjectMember.project_id == Project.id)
            .filter(
                Project.is_active == True,  # noqa: E712
                Project.dept_id == dept_id,
            )
            .group_by(ProjectMember.user_id)
            .order_by(func.sum(ProjectMember.allocation_pct).desc())
            .limit(20)
            .all()
        )
        load_data = [
            {
                "user_id": r.user_id,
                "total_allocation": float(r.total_alloc or 0),
                "project_count": r.project_count,
                "overloaded": float(r.total_alloc or 0) > 100,
            }
            for r in resource_load
        ]

        # 3. 部门风险汇总（按风险等级分组）
        risk_summary = (
            self.db.query(
                ProjectRisk.risk_level,
                func.count(ProjectRisk.id).label("count"),
            )
            .join(Project, ProjectRisk.project_id == Project.id)
            .filter(
                Project.is_active == True,  # noqa: E712
                Project.dept_id == dept_id,
                ProjectRisk.status.in_(["IDENTIFIED", "ANALYZING", "PLANNING", "MONITORING", "OCCURRED"]),
            )
            .group_by(ProjectRisk.risk_level)
            .all()
        )
        risk_data = {r.risk_level: r.count for r in risk_summary}

        # 4. 预算执行对比（每个项目的预算 vs 实际）
        budget_data = [
            {
                "project_name": p.project_name[:20],
                "budget": float(p.budget_amount or 0),
                "actual": float(p.actual_cost or 0),
                "rate": round(
                    float(p.actual_cost or 0) / float(p.budget_amount) * 100, 1
                ) if p.budget_amount and float(p.budget_amount) > 0 else 0,
            }
            for p in projects[:15]
        ]

        return [
            DashboardWidget(
                widget_id="dept_project_ranking",
                widget_type="table",
                title="部门项目绩效排行",
                data={"items": perf_data[:20]},
                config={"sortable": True},
            ),
            DashboardWidget(
                widget_id="dept_resource_load",
                widget_type="chart",
                title="部门资源负荷",
                data={"items": load_data},
                config={"chart_type": "bar", "alert_threshold": 100},
            ),
            DashboardWidget(
                widget_id="dept_risk_summary",
                widget_type="chart",
                title="部门风险汇总",
                data={
                    "critical": risk_data.get("CRITICAL", 0),
                    "high": risk_data.get("HIGH", 0),
                    "medium": risk_data.get("MEDIUM", 0),
                    "low": risk_data.get("LOW", 0),
                },
                config={"chart_type": "pie"},
            ),
            DashboardWidget(
                widget_id="dept_budget_execution",
                widget_type="chart",
                title="预算执行率统计",
                data={"items": budget_data},
                config={"chart_type": "bar", "dual_axis": True},
            ),
        ]
