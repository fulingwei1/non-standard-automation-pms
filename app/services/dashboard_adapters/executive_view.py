# -*- coding: utf-8 -*-
"""
高管个性化视图 Dashboard 适配器

关注：
- 公司整体项目组合健康度
- 战略项目进度
- 重大风险/问题
- 投资回报率分析
"""

from typing import List

from sqlalchemy import func

from app.models.project import Project
from app.models.project_risk import ProjectRisk
from app.schemas.dashboard import (
    DashboardStatCard,
    DashboardWidget,
)
from app.services.dashboard_adapter import DashboardAdapter, register_dashboard


@register_dashboard
class ExecutiveViewDashboardAdapter(DashboardAdapter):
    """高管视图适配器"""

    @property
    def module_id(self) -> str:
        return "executive_view"

    @property
    def module_name(self) -> str:
        return "高管视图"

    @property
    def supported_roles(self) -> List[str]:
        return ["GM", "gm", "CHAIRMAN", "chairman", "VICE_CHAIRMAN", "DONGMI", "ADMIN", "admin"]

    def _get_all_active_projects(self):
        return (
            self.db.query(Project)
            .filter(Project.is_active == True)  # noqa: E712
            .all()
        )

    def get_stats(self) -> List[DashboardStatCard]:
        projects = self._get_all_active_projects()
        total = len(projects)

        if total == 0:
            return [DashboardStatCard(key="total_projects", title="活跃项目", value=0, unit="个")]

        # 健康度分布
        h1 = sum(1 for p in projects if p.health == "H1")
        h2 = sum(1 for p in projects if p.health == "H2")
        h3 = sum(1 for p in projects if p.health == "H3")
        h4 = sum(1 for p in projects if p.health == "H4")
        health_rate = round(h1 / total * 100, 1) if total > 0 else 0

        # 财务概览
        total_contract = sum(float(p.contract_amount or 0) for p in projects)
        total_budget = sum(float(p.budget_amount or 0) for p in projects)
        total_actual = sum(float(p.actual_cost or 0) for p in projects)
        gross_profit = total_contract - total_actual
        roi = round((gross_profit / total_actual * 100), 1) if total_actual > 0 else 0

        # 重大风险
        critical_risks = (
            self.db.query(func.count(ProjectRisk.id))
            .join(Project, ProjectRisk.project_id == Project.id)
            .filter(
                Project.is_active == True,  # noqa: E712
                ProjectRisk.risk_level.in_(["CRITICAL", "HIGH"]),
                ProjectRisk.status.in_(["IDENTIFIED", "ANALYZING", "MONITORING", "OCCURRED"]),
            )
            .scalar()
            or 0
        )

        # 战略项目（高优先级）
        strategic_count = sum(1 for p in projects if p.priority in ("HIGH", "CRITICAL"))

        return [
            DashboardStatCard(key="total_projects", title="活跃项目", value=total, unit="个"),
            DashboardStatCard(
                key="portfolio_health",
                title="组合健康率",
                value=health_rate,
                unit="%",
                trend="up" if health_rate >= 80 else ("down" if health_rate < 60 else "stable"),
            ),
            DashboardStatCard(
                key="health_distribution",
                title="健康/关注/风险/严重",
                value=f"{h1}/{h2}/{h3}/{h4}",
            ),
            DashboardStatCard(
                key="total_contract_value",
                title="合同总额",
                value=round(total_contract / 10000, 1),
                unit="万元",
            ),
            DashboardStatCard(
                key="roi",
                title="投资回报率",
                value=roi,
                unit="%",
                trend="up" if roi > 20 else ("down" if roi < 0 else "stable"),
            ),
            DashboardStatCard(key="critical_risks", title="重大风险", value=critical_risks, unit="个"),
            DashboardStatCard(key="strategic_projects", title="战略项目", value=strategic_count, unit="个"),
        ]

    def get_widgets(self) -> List[DashboardWidget]:
        projects = self._get_all_active_projects()

        # 1. 项目组合健康度分布（饼图）
        health_dist = {"H1": 0, "H2": 0, "H3": 0, "H4": 0}
        for p in projects:
            h = p.health or "H1"
            health_dist[h] = health_dist.get(h, 0) + 1

        # 2. 战略项目进度追踪
        strategic_projects = [p for p in projects if p.priority in ("HIGH", "CRITICAL")]
        strategic_data = [
            {
                "id": p.id,
                "project_code": p.project_code,
                "project_name": p.project_name,
                "health": p.health,
                "progress_pct": float(p.progress_pct or 0),
                "contract_amount": float(p.contract_amount or 0),
                "pm_name": p.pm_name,
                "priority": p.priority,
                "planned_end_date": str(p.planned_end_date) if p.planned_end_date else None,
            }
            for p in strategic_projects[:20]
        ]

        # 3. 重大风险列表
        major_risks = (
            self.db.query(ProjectRisk, Project.project_name, Project.project_code)
            .join(Project, ProjectRisk.project_id == Project.id)
            .filter(
                Project.is_active == True,  # noqa: E712
                ProjectRisk.risk_level.in_(["CRITICAL", "HIGH"]),
                ProjectRisk.status.in_(["IDENTIFIED", "ANALYZING", "MONITORING", "OCCURRED"]),
            )
            .order_by(ProjectRisk.risk_score.desc())
            .limit(15)
            .all()
        )
        risk_list = [
            {
                "id": r.id,
                "risk_name": r.risk_name,
                "risk_level": r.risk_level,
                "risk_score": r.risk_score,
                "risk_type": r.risk_type,
                "project_name": proj_name,
                "project_code": proj_code,
                "status": r.status,
            }
            for r, proj_name, proj_code in major_risks
        ]

        # 4. 投资回报分析（按部门）
        dept_financials = {}
        for p in projects:
            dept = p.dept_id or 0
            if dept not in dept_financials:
                dept_financials[dept] = {"contract": 0, "budget": 0, "actual": 0, "count": 0}
            dept_financials[dept]["contract"] += float(p.contract_amount or 0)
            dept_financials[dept]["budget"] += float(p.budget_amount or 0)
            dept_financials[dept]["actual"] += float(p.actual_cost or 0)
            dept_financials[dept]["count"] += 1

        roi_data = []
        for dept_id, fin in dept_financials.items():
            profit = fin["contract"] - fin["actual"]
            roi_val = round(profit / fin["actual"] * 100, 1) if fin["actual"] > 0 else 0
            roi_data.append({
                "dept_id": dept_id,
                "project_count": fin["count"],
                "contract_total": fin["contract"],
                "actual_total": fin["actual"],
                "profit": profit,
                "roi": roi_val,
            })

        # 5. 项目阶段分布
        stage_dist = {}
        for p in projects:
            s = p.stage or "未知"
            stage_dist[s] = stage_dist.get(s, 0) + 1

        return [
            DashboardWidget(
                widget_id="exec_portfolio_health",
                widget_type="chart",
                title="项目组合健康度",
                data={
                    "labels": ["健康(H1)", "关注(H2)", "风险(H3)", "严重(H4)"],
                    "values": [health_dist["H1"], health_dist["H2"], health_dist["H3"], health_dist["H4"]],
                },
                config={"chart_type": "pie"},
            ),
            DashboardWidget(
                widget_id="exec_strategic_projects",
                widget_type="table",
                title="战略项目进度",
                data={"items": strategic_data},
                config={"sortable": True, "highlight_field": "health"},
            ),
            DashboardWidget(
                widget_id="exec_major_risks",
                widget_type="list",
                title="重大风险/问题",
                data={"items": risk_list},
                config={"severity_colors": True},
            ),
            DashboardWidget(
                widget_id="exec_roi_analysis",
                widget_type="chart",
                title="投资回报率分析",
                data={"items": roi_data},
                config={"chart_type": "bar", "value_field": "roi"},
            ),
            DashboardWidget(
                widget_id="exec_stage_distribution",
                widget_type="chart",
                title="项目阶段分布",
                data={
                    "labels": list(stage_dist.keys()),
                    "values": list(stage_dist.values()),
                },
                config={"chart_type": "bar"},
            ),
        ]
