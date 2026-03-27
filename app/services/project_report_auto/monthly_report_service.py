# -*- coding: utf-8 -*-
"""
项目月报自动生成服务

基于本月数据自动生成：
- 里程碑进度
- 成本偏差分析
- 质量指标
- 干系人变更
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.issue import Issue
from app.models.project.core import Project
from app.models.project.financial import ProjectCost, ProjectMilestone
from app.models.project.team import ProjectMember
from app.models.project_risk import ProjectRisk
from app.models.report_center import ReportGeneration, ReportTemplate
from app.models.timesheet import Timesheet
from app.models.user import User

logger = logging.getLogger(__name__)


def _d2f(val: Any) -> float:
    if val is None:
        return 0.0
    if isinstance(val, Decimal):
        return float(val)
    return float(val)


class MonthlyReportService:
    """项目月报自动生成服务"""

    def __init__(self, db: Session):
        self.db = db

    def generate(
        self,
        project_id: int,
        year: Optional[int] = None,
        month: Optional[int] = None,
        template_id: Optional[int] = None,
        generated_by: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        自动生成项目月报

        Args:
            project_id: 项目ID
            year: 年份（默认当月）
            month: 月份（默认当月）
            template_id: 模板ID
            generated_by: 生成人ID

        Returns:
            完整的月报数据字典
        """
        today = date.today()
        year = year or today.year
        month = month or today.month

        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)

        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        sections_config = self._load_sections_config(template_id)

        report_data: Dict[str, Any] = {
            "report_type": "PROJECT_MONTHLY",
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "period": {
                "year": year,
                "month": month,
                "start_date": month_start.isoformat(),
                "end_date": month_end.isoformat(),
                "label": f"{year}年{month:02d}月",
            },
            "generated_at": today.isoformat(),
            "summary": self._build_summary(project),
            "sections": {},
        }

        section_builders = {
            "milestone_progress": lambda: self._milestone_progress(
                project_id, month_start, month_end
            ),
            "cost_variance_analysis": lambda: self._cost_variance_analysis(
                project_id, month_start, month_end
            ),
            "quality_metrics": lambda: self._quality_metrics(
                project_id, month_start, month_end
            ),
            "stakeholder_changes": lambda: self._stakeholder_changes(
                project_id, month_start, month_end
            ),
            "weekly_trend": lambda: self._weekly_trend(
                project_id, month_start, month_end
            ),
        }

        for key, builder in section_builders.items():
            if sections_config.get(key, True):
                try:
                    report_data["sections"][key] = builder()
                except Exception as e:
                    logger.warning(f"生成月报 section [{key}] 失败: {e}")
                    report_data["sections"][key] = {"title": key, "error": str(e)}

        generation = self._save_generation(
            report_data, project_id, template_id, month_start, month_end, generated_by
        )
        report_data["report_id"] = generation.id

        logger.info(f"项目月报生成成功: project={project_id}, id={generation.id}")
        return report_data

    # ===================== section builders =====================

    def _build_summary(self, project: Project) -> Dict[str, Any]:
        return {
            "project_code": project.project_code,
            "project_name": project.project_name,
            "customer_name": getattr(project, "customer_name", "") or "",
            "pm_name": getattr(project, "pm_name", "") or "",
            "stage": getattr(project, "stage", ""),
            "health": getattr(project, "health", ""),
            "progress_pct": _d2f(getattr(project, "progress_pct", 0)),
            "planned_start_date": (
                project.planned_start_date.isoformat()
                if getattr(project, "planned_start_date", None)
                else None
            ),
            "planned_end_date": (
                project.planned_end_date.isoformat()
                if getattr(project, "planned_end_date", None)
                else None
            ),
            "budget_amount": _d2f(getattr(project, "budget_amount", 0)),
            "actual_cost": _d2f(getattr(project, "actual_cost", 0)),
            "contract_amount": _d2f(getattr(project, "contract_amount", 0)),
        }

    def _milestone_progress(
        self, project_id: int, start: date, end: date
    ) -> Dict[str, Any]:
        """里程碑进度"""
        all_milestones = (
            self.db.query(ProjectMilestone)
            .filter(ProjectMilestone.project_id == project_id)
            .order_by(ProjectMilestone.planned_date)
            .all()
        )

        items = []
        for m in all_milestones:
            planned = m.planned_date
            actual = m.actual_date
            status = getattr(m, "status", "PENDING")

            # 偏差天数
            delay_days = None
            if actual and planned:
                delay_days = (actual - planned).days
            elif status != "COMPLETED" and planned and planned < end:
                delay_days = (end - planned).days

            in_period = False
            if planned and start <= planned <= end:
                in_period = True
            if actual and start <= actual <= end:
                in_period = True

            items.append(
                {
                    "milestone_code": getattr(m, "milestone_code", ""),
                    "milestone_name": getattr(m, "milestone_name", ""),
                    "milestone_type": getattr(m, "milestone_type", "CUSTOM"),
                    "planned_date": planned.isoformat() if planned else None,
                    "actual_date": actual.isoformat() if actual else None,
                    "status": status,
                    "is_key": getattr(m, "is_key", False),
                    "delay_days": delay_days,
                    "in_current_period": in_period,
                }
            )

        total = len(items)
        completed = sum(1 for i in items if i["status"] == "COMPLETED")
        delayed = sum(1 for i in items if (i["delay_days"] or 0) > 0)

        return {
            "title": "里程碑进度",
            "type": "table",
            "data": items,
            "total": total,
            "completed": completed,
            "delayed": delayed,
            "completion_rate": round(completed / max(total, 1) * 100, 1),
            "on_track": total - completed - delayed,
        }

    def _cost_variance_analysis(
        self, project_id: int, start: date, end: date
    ) -> Dict[str, Any]:
        """成本偏差分析"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        budget = _d2f(getattr(project, "budget_amount", 0))
        actual_total = _d2f(getattr(project, "actual_cost", 0))
        contract = _d2f(getattr(project, "contract_amount", 0))

        # 本月新增成本
        month_cost_rows = (
            self.db.query(
                ProjectCost.cost_type,
                func.sum(ProjectCost.amount).label("total"),
            )
            .filter(
                ProjectCost.project_id == project_id,
                ProjectCost.cost_date.between(start, end),
            )
            .group_by(ProjectCost.cost_type)
            .all()
        )
        month_cost_by_type = [
            {"cost_type": r.cost_type or "OTHER", "amount": _d2f(r.total)}
            for r in month_cost_rows
        ]
        month_cost_total = sum(c["amount"] for c in month_cost_by_type)

        # 累计偏差
        cv = budget - actual_total  # Cost Variance
        cv_pct = round(cv / budget * 100, 1) if budget > 0 else 0.0
        cpi = round(budget / actual_total, 3) if actual_total > 0 else 0.0

        # EAC 估算 (简化公式: BAC / CPI)
        eac = round(budget / cpi, 2) if cpi > 0 else budget

        return {
            "title": "成本偏差分析",
            "type": "summary",
            "data": {
                "contract_amount": contract,
                "budget_amount": budget,
                "actual_cost_total": actual_total,
                "month_cost_total": round(month_cost_total, 2),
                "month_cost_by_type": month_cost_by_type,
                "cost_variance": round(cv, 2),
                "cost_variance_pct": cv_pct,
                "cost_performance_index": cpi,
                "estimate_at_completion": eac,
                "budget_remaining": round(budget - actual_total, 2),
                "budget_consumed_pct": round(
                    actual_total / budget * 100, 1
                ) if budget > 0 else 0.0,
            },
        }

    def _quality_metrics(
        self, project_id: int, start: date, end: date
    ) -> Dict[str, Any]:
        """质量指标：基于问题数据统计"""
        # 本月新增问题
        new_issues = (
            self.db.query(Issue)
            .filter(
                Issue.project_id == project_id,
                Issue.created_at.between(start, end),
            )
            .all()
        )

        # 本月解决的问题
        resolved_issues = (
            self.db.query(Issue)
            .filter(
                Issue.project_id == project_id,
                Issue.resolved_at.between(start, end),
            )
            .all()
        )

        # 仍然 open 的问题
        open_issues = (
            self.db.query(Issue)
            .filter(
                Issue.project_id == project_id,
                Issue.status.notin_(["CLOSED", "RESOLVED"]),
            )
            .all()
        )

        # 按严重程度统计
        severity_dist = {}
        for i in open_issues:
            sev = getattr(i, "severity", "UNKNOWN") or "UNKNOWN"
            severity_dist[sev] = severity_dist.get(sev, 0) + 1

        # 按类别统计
        category_dist = {}
        for i in new_issues:
            cat = getattr(i, "category", "OTHER") or "OTHER"
            category_dist[cat] = category_dist.get(cat, 0) + 1

        return {
            "title": "质量指标",
            "type": "summary",
            "data": {
                "new_issues_count": len(new_issues),
                "resolved_issues_count": len(resolved_issues),
                "open_issues_count": len(open_issues),
                "resolution_rate": round(
                    len(resolved_issues) / max(len(new_issues), 1) * 100, 1
                ),
                "severity_distribution": severity_dist,
                "category_distribution": category_dist,
                "overdue_issues": sum(
                    1
                    for i in open_issues
                    if getattr(i, "due_date", None) and i.due_date < end
                ),
            },
        }

    def _stakeholder_changes(
        self, project_id: int, start: date, end: date
    ) -> Dict[str, Any]:
        """干系人变更"""
        # 本月新增成员
        new_members = (
            self.db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.created_at.between(start, end),
            )
            .all()
        )

        # 本月退出成员（end_date 在本月内）
        departed_members = (
            self.db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.end_date.between(start, end),
            )
            .all()
        )

        # 当前活跃成员
        active_members = (
            self.db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.is_active == True,  # noqa: E712
            )
            .all()
        )

        # 获取用户名
        all_ids = list(
            set(
                [m.user_id for m in new_members]
                + [m.user_id for m in departed_members]
            )
        )
        user_map = {}
        if all_ids:
            users = self.db.query(User).filter(User.id.in_(all_ids)).all()
            user_map = {u.id: getattr(u, "real_name", str(u.id)) for u in users}

        return {
            "title": "干系人变更",
            "type": "mixed",
            "new_members": [
                {
                    "user_id": m.user_id,
                    "user_name": user_map.get(m.user_id, str(m.user_id)),
                    "role_code": getattr(m, "role_code", ""),
                    "start_date": m.start_date.isoformat() if m.start_date else None,
                }
                for m in new_members
            ],
            "departed_members": [
                {
                    "user_id": m.user_id,
                    "user_name": user_map.get(m.user_id, str(m.user_id)),
                    "role_code": getattr(m, "role_code", ""),
                    "end_date": m.end_date.isoformat() if m.end_date else None,
                }
                for m in departed_members
            ],
            "active_member_count": len(active_members),
            "new_count": len(new_members),
            "departed_count": len(departed_members),
        }

    def _weekly_trend(
        self, project_id: int, start: date, end: date
    ) -> Dict[str, Any]:
        """月内周度趋势"""
        weeks = []
        current = start
        week_num = 1
        while current <= end:
            week_end = min(current + timedelta(days=6), end)

            rows = (
                self.db.query(func.sum(Timesheet.hours).label("total"))
                .filter(
                    Timesheet.project_id == project_id,
                    Timesheet.work_date.between(current, week_end),
                )
                .first()
            )
            hours = _d2f(rows.total) if rows and rows.total else 0.0

            weeks.append(
                {
                    "week": week_num,
                    "start": current.isoformat(),
                    "end": week_end.isoformat(),
                    "hours": round(hours, 2),
                }
            )
            current = week_end + timedelta(days=1)
            week_num += 1

        return {
            "title": "周度趋势",
            "type": "line",
            "data": weeks,
        }

    # ===================== helpers =====================

    def _load_sections_config(self, template_id: Optional[int]) -> Dict[str, bool]:
        default = {
            "milestone_progress": True,
            "cost_variance_analysis": True,
            "quality_metrics": True,
            "stakeholder_changes": True,
            "weekly_trend": True,
        }
        if not template_id:
            return default

        template = (
            self.db.query(ReportTemplate)
            .filter(ReportTemplate.id == template_id, ReportTemplate.is_active == True)  # noqa: E712
            .first()
        )
        if not template or not template.sections:
            return default

        if isinstance(template.sections, dict):
            return {**default, **template.sections}
        return default

    def _save_generation(
        self,
        report_data: Dict[str, Any],
        project_id: int,
        template_id: Optional[int],
        period_start: date,
        period_end: date,
        generated_by: Optional[int],
    ) -> ReportGeneration:
        generation = ReportGeneration(
            report_type="PROJECT_MONTHLY",
            template_id=template_id,
            report_title=f"{report_data['project_name']} - 项目月报 ({report_data['period']['label']})",
            period_type="MONTHLY",
            period_start=period_start,
            period_end=period_end,
            scope_type="PROJECT",
            scope_id=project_id,
            report_data=report_data,
            status="DRAFT",
            generated_by=generated_by,
        )
        self.db.add(generation)
        self.db.commit()
        self.db.refresh(generation)
        return generation
