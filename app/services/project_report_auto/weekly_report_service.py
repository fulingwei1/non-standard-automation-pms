# -*- coding: utf-8 -*-
"""
项目周报自动生成服务

基于本周数据自动生成：
- 本周完成
- 下周计划
- 风险/问题汇总
- 资源负荷情况
- 成本执行情况
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
from app.models.project_risk import ProjectRisk, RiskStatusEnum
from app.models.report_center import ReportGeneration, ReportTemplate
from app.models.timesheet import Timesheet
from app.models.user import User

logger = logging.getLogger(__name__)


def _decimal_to_float(val: Any) -> float:
    if val is None:
        return 0.0
    if isinstance(val, Decimal):
        return float(val)
    return float(val)


class WeeklyReportService:
    """项目周报自动生成服务"""

    def __init__(self, db: Session):
        self.db = db

    def generate(
        self,
        project_id: int,
        report_date: Optional[date] = None,
        template_id: Optional[int] = None,
        generated_by: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        自动生成项目周报

        Args:
            project_id: 项目ID
            report_date: 报告日期（默认今天，自动计算本周范围）
            template_id: 报告模板ID（可选，用于自定义 sections）
            generated_by: 生成人ID

        Returns:
            完整的周报数据字典
        """
        report_date = report_date or date.today()
        # 本周一 ~ 本周日
        week_start = report_date - timedelta(days=report_date.weekday())
        week_end = week_start + timedelta(days=6)
        # 下周范围
        next_week_start = week_end + timedelta(days=1)
        next_week_end = next_week_start + timedelta(days=6)

        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        # 加载模板配置（决定包含哪些 section）
        sections_config = self._load_sections_config(template_id)

        report_data: Dict[str, Any] = {
            "report_type": "PROJECT_WEEKLY",
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "period": {
                "start_date": week_start.isoformat(),
                "end_date": week_end.isoformat(),
                "label": f"{week_start.isoformat()} ~ {week_end.isoformat()}",
            },
            "generated_at": report_date.isoformat(),
            "summary": self._build_summary(project),
            "sections": {},
        }

        section_builders = {
            "completed_this_week": lambda: self._completed_this_week(
                project_id, week_start, week_end
            ),
            "next_week_plan": lambda: self._next_week_plan(
                project_id, next_week_start, next_week_end
            ),
            "risks_and_issues": lambda: self._risks_and_issues(project_id),
            "resource_workload": lambda: self._resource_workload(
                project_id, week_start, week_end
            ),
            "cost_execution": lambda: self._cost_execution(project_id),
        }

        for section_key, builder in section_builders.items():
            if sections_config.get(section_key, True):
                try:
                    report_data["sections"][section_key] = builder()
                except Exception as e:
                    logger.warning(f"生成周报 section [{section_key}] 失败: {e}")
                    report_data["sections"][section_key] = {
                        "title": section_key,
                        "error": str(e),
                    }

        # 持久化到 report_generation 表
        generation = self._save_generation(
            report_data, project_id, template_id, week_start, week_end, generated_by
        )
        report_data["report_id"] = generation.id

        logger.info(f"项目周报生成成功: project={project_id}, id={generation.id}")
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
            "progress_pct": _decimal_to_float(getattr(project, "progress_pct", 0)),
            "budget_amount": _decimal_to_float(getattr(project, "budget_amount", 0)),
            "actual_cost": _decimal_to_float(getattr(project, "actual_cost", 0)),
        }

    def _completed_this_week(
        self, project_id: int, start: date, end: date
    ) -> Dict[str, Any]:
        """本周完成的里程碑与工作"""
        # 本周完成的里程碑
        milestones = (
            self.db.query(ProjectMilestone)
            .filter(
                ProjectMilestone.project_id == project_id,
                ProjectMilestone.actual_date.between(start, end),
            )
            .all()
        )
        milestones_data = [
            {
                "milestone_code": getattr(m, "milestone_code", ""),
                "milestone_name": getattr(m, "milestone_name", ""),
                "planned_date": m.planned_date.isoformat() if m.planned_date else None,
                "actual_date": m.actual_date.isoformat() if m.actual_date else None,
                "status": getattr(m, "status", ""),
                "is_key": getattr(m, "is_key", False),
            }
            for m in milestones
        ]

        # 本周工时汇总（按人）
        timesheet_rows = (
            self.db.query(
                Timesheet.user_id,
                func.sum(Timesheet.hours).label("total_hours"),
            )
            .filter(
                Timesheet.project_id == project_id,
                Timesheet.work_date.between(start, end),
            )
            .group_by(Timesheet.user_id)
            .all()
        )

        user_ids = [r.user_id for r in timesheet_rows]
        user_map = {}
        if user_ids:
            users = self.db.query(User).filter(User.id.in_(user_ids)).all()
            user_map = {u.id: getattr(u, "real_name", str(u.id)) for u in users}

        worklog = [
            {
                "user_id": r.user_id,
                "user_name": user_map.get(r.user_id, str(r.user_id)),
                "hours": _decimal_to_float(r.total_hours),
            }
            for r in timesheet_rows
        ]

        return {
            "title": "本周完成",
            "type": "mixed",
            "milestones_completed": milestones_data,
            "worklog_summary": worklog,
            "total_hours": sum(w["hours"] for w in worklog),
            "total_workers": len(worklog),
        }

    def _next_week_plan(
        self, project_id: int, start: date, end: date
    ) -> Dict[str, Any]:
        """下周计划：即将到期的里程碑"""
        milestones = (
            self.db.query(ProjectMilestone)
            .filter(
                ProjectMilestone.project_id == project_id,
                ProjectMilestone.planned_date.between(start, end),
                ProjectMilestone.status != "COMPLETED",
            )
            .order_by(ProjectMilestone.planned_date)
            .all()
        )

        items = [
            {
                "milestone_code": getattr(m, "milestone_code", ""),
                "milestone_name": getattr(m, "milestone_name", ""),
                "planned_date": m.planned_date.isoformat() if m.planned_date else None,
                "status": getattr(m, "status", ""),
                "is_key": getattr(m, "is_key", False),
                "owner_id": getattr(m, "owner_id", None),
            }
            for m in milestones
        ]

        return {
            "title": "下周计划",
            "type": "table",
            "data": items,
            "count": len(items),
        }

    def _risks_and_issues(self, project_id: int) -> Dict[str, Any]:
        """风险/问题汇总：未关闭的风险和问题"""
        active_statuses = [
            RiskStatusEnum.IDENTIFIED.value,
            RiskStatusEnum.ANALYZING.value,
            RiskStatusEnum.PLANNING.value,
            RiskStatusEnum.MONITORING.value,
            RiskStatusEnum.OCCURRED.value,
        ]
        risks = (
            self.db.query(ProjectRisk)
            .filter(
                ProjectRisk.project_id == project_id,
                ProjectRisk.status.in_(active_statuses),
            )
            .order_by(ProjectRisk.risk_score.desc().nullslast())
            .all()
        )

        risks_data = [
            {
                "risk_code": r.risk_code,
                "risk_name": r.risk_name,
                "risk_type": getattr(r, "risk_type", ""),
                "probability": getattr(r, "probability", None),
                "impact": getattr(r, "impact", None),
                "risk_score": getattr(r, "risk_score", None),
                "risk_level": getattr(r, "risk_level", ""),
                "status": r.status if isinstance(r.status, str) else r.status.value,
                "mitigation_plan": getattr(r, "mitigation_plan", ""),
                "owner_id": getattr(r, "owner_id", None),
            }
            for r in risks
        ]

        # 未关闭问题
        issues = (
            self.db.query(Issue)
            .filter(
                Issue.project_id == project_id,
                Issue.status.notin_(["CLOSED", "RESOLVED"]),
            )
            .order_by(Issue.severity.desc().nullslast())
            .all()
        )

        issues_data = [
            {
                "issue_no": getattr(i, "issue_no", ""),
                "title": getattr(i, "title", ""),
                "category": getattr(i, "category", ""),
                "severity": getattr(i, "severity", ""),
                "priority": getattr(i, "priority", ""),
                "status": getattr(i, "status", ""),
                "assignee_id": getattr(i, "assignee_id", None),
                "due_date": i.due_date.isoformat() if getattr(i, "due_date", None) else None,
            }
            for i in issues
        ]

        return {
            "title": "风险与问题",
            "type": "mixed",
            "risks": risks_data,
            "risk_count": len(risks_data),
            "high_risks": sum(
                1 for r in risks_data if r.get("risk_level") in ("HIGH", "CRITICAL")
            ),
            "issues": issues_data,
            "issue_count": len(issues_data),
            "critical_issues": sum(
                1 for i in issues_data if i.get("severity") in ("CRITICAL", "BLOCKER")
            ),
        }

    def _resource_workload(
        self, project_id: int, start: date, end: date
    ) -> Dict[str, Any]:
        """资源负荷情况"""
        members = (
            self.db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.is_active == True,  # noqa: E712
            )
            .all()
        )

        member_user_ids = [m.user_id for m in members]
        user_map = {}
        if member_user_ids:
            users = self.db.query(User).filter(User.id.in_(member_user_ids)).all()
            user_map = {u.id: getattr(u, "real_name", str(u.id)) for u in users}

        # 本周工时
        timesheet_map: Dict[int, float] = {}
        if member_user_ids:
            rows = (
                self.db.query(
                    Timesheet.user_id,
                    func.sum(Timesheet.hours).label("total"),
                )
                .filter(
                    Timesheet.project_id == project_id,
                    Timesheet.user_id.in_(member_user_ids),
                    Timesheet.work_date.between(start, end),
                )
                .group_by(Timesheet.user_id)
                .all()
            )
            timesheet_map = {r.user_id: _decimal_to_float(r.total) for r in rows}

        standard_weekly_hours = 40.0
        workload_items = []
        for m in members:
            allocation = _decimal_to_float(getattr(m, "allocation_pct", 100))
            expected = standard_weekly_hours * (allocation / 100.0)
            actual = timesheet_map.get(m.user_id, 0.0)
            utilization = round(actual / expected * 100, 1) if expected > 0 else 0.0

            workload_items.append(
                {
                    "user_id": m.user_id,
                    "user_name": user_map.get(m.user_id, str(m.user_id)),
                    "role_code": getattr(m, "role_code", ""),
                    "allocation_pct": allocation,
                    "expected_hours": round(expected, 1),
                    "actual_hours": round(actual, 1),
                    "utilization_pct": utilization,
                }
            )

        total_expected = sum(w["expected_hours"] for w in workload_items)
        total_actual = sum(w["actual_hours"] for w in workload_items)
        avg_utilization = (
            round(total_actual / total_expected * 100, 1) if total_expected > 0 else 0.0
        )

        return {
            "title": "资源负荷情况",
            "type": "table",
            "data": workload_items,
            "member_count": len(workload_items),
            "total_expected_hours": round(total_expected, 1),
            "total_actual_hours": round(total_actual, 1),
            "avg_utilization_pct": avg_utilization,
        }

    def _cost_execution(self, project_id: int) -> Dict[str, Any]:
        """成本执行情况"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        budget = _decimal_to_float(getattr(project, "budget_amount", 0))
        actual = _decimal_to_float(getattr(project, "actual_cost", 0))
        contract = _decimal_to_float(getattr(project, "contract_amount", 0))

        variance = budget - actual if budget > 0 else 0
        variance_pct = round(variance / budget * 100, 1) if budget > 0 else 0.0
        cost_performance = round(budget / actual, 2) if actual > 0 else 0.0

        # 成本明细（按类型汇总）
        cost_breakdown: List[Dict[str, Any]] = []
        try:
            rows = (
                self.db.query(
                    ProjectCost.cost_type,
                    func.sum(ProjectCost.amount).label("total"),
                )
                .filter(ProjectCost.project_id == project_id)
                .group_by(ProjectCost.cost_type)
                .all()
            )
            cost_breakdown = [
                {
                    "cost_type": r.cost_type or "OTHER",
                    "amount": _decimal_to_float(r.total),
                }
                for r in rows
            ]
        except Exception as e:
            logger.warning(f"成本明细查询失败: {e}")

        return {
            "title": "成本执行情况",
            "type": "summary",
            "data": {
                "contract_amount": contract,
                "budget_amount": budget,
                "actual_cost": actual,
                "variance": round(variance, 2),
                "variance_pct": variance_pct,
                "cost_performance_index": cost_performance,
                "cost_breakdown": cost_breakdown,
            },
        }

    # ===================== helpers =====================

    def _load_sections_config(self, template_id: Optional[int]) -> Dict[str, bool]:
        """加载模板 sections 配置，决定包含哪些板块"""
        default = {
            "completed_this_week": True,
            "next_week_plan": True,
            "risks_and_issues": True,
            "resource_workload": True,
            "cost_execution": True,
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

        # sections 是 JSON 字段，可存储 {"completed_this_week": false, ...}
        if isinstance(template.sections, dict):
            merged = {**default, **template.sections}
            return merged
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
            report_type="PROJECT_WEEKLY",
            template_id=template_id,
            report_title=f"{report_data['project_name']} - 项目周报 ({report_data['period']['label']})",
            period_type="WEEKLY",
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
