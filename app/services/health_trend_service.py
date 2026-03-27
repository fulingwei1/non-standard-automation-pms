# -*- coding: utf-8 -*-
"""
项目健康度可视化服务

提供健康度趋势、风险因素拆解、改进建议等可视化增强能力。
输出格式：health_trend{dates, scores, dimensions, events}
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.alert import AlertRecord, AlertRule, ProjectHealthSnapshot
from app.models.enums import AlertLevelEnum
from app.models.issue import Issue, IssueTypeEnum
from app.models.progress import Task
from app.models.project import Project, ProjectMilestone


# ── 维度权重 ──────────────────────────────────────────────
DIMENSION_WEIGHTS = {
    "schedule": 0.30,
    "cost": 0.25,
    "resource": 0.20,
    "quality": 0.25,
}

# ── 健康度等级 → 数值映射 ──────────────────────────────────
HEALTH_SCORE_MAP = {"H1": 90, "H2": 65, "H3": 35, "H4": 0}


class HealthTrendService:
    """项目健康度可视化服务"""

    def __init__(self, db: Session):
        self.db = db

    # ================================================================
    #  1. 健康度趋势
    # ================================================================
    def get_health_trend(
        self,
        project_id: int,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        获取近 N 天健康度变化趋势

        Returns:
            health_trend {dates, scores, dimensions, events}
        """
        project = self._get_project(project_id)
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        # 获取快照数据
        snapshots = (
            self.db.query(ProjectHealthSnapshot)
            .filter(
                ProjectHealthSnapshot.project_id == project_id,
                ProjectHealthSnapshot.snapshot_date >= start_date,
                ProjectHealthSnapshot.snapshot_date <= end_date,
            )
            .order_by(ProjectHealthSnapshot.snapshot_date)
            .all()
        )

        # 构建日期序列
        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current.isoformat())
            current += timedelta(days=1)

        # 快照按日期索引
        snap_map = {s.snapshot_date.isoformat(): s for s in snapshots}

        # 构建各维度得分序列
        scores = []
        dim_schedule = []
        dim_cost = []
        dim_resource = []
        dim_quality = []

        for d in dates:
            snap = snap_map.get(d)
            if snap:
                overall = snap.health_score or HEALTH_SCORE_MAP.get(snap.overall_health, 50)
                scores.append(overall)
                dim_schedule.append(HEALTH_SCORE_MAP.get(snap.schedule_health, 50))
                dim_cost.append(HEALTH_SCORE_MAP.get(snap.cost_health, 50))
                dim_resource.append(HEALTH_SCORE_MAP.get(snap.resource_health, 50))
                dim_quality.append(HEALTH_SCORE_MAP.get(snap.quality_health, 50))
            else:
                # 无快照时用当前健康度填充
                fallback = HEALTH_SCORE_MAP.get(project.health or "H1", 50)
                scores.append(fallback)
                dim_schedule.append(fallback)
                dim_cost.append(fallback)
                dim_resource.append(fallback)
                dim_quality.append(fallback)

        # 获取预警事件标记
        events = self._get_alert_events(project_id, start_date, end_date)

        return {
            "project_id": project_id,
            "project_name": project.project_name,
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat(), "days": days},
            "dates": dates,
            "scores": scores,
            "dimensions": {
                "schedule": dim_schedule,
                "cost": dim_cost,
                "resource": dim_resource,
                "quality": dim_quality,
            },
            "events": events,
        }

    # ================================================================
    #  2. 风险因素拆解
    # ================================================================
    def get_risk_breakdown(self, project_id: int) -> Dict[str, Any]:
        """
        拆解各维度权重、得分，识别拉低健康度的主要因素，
        并模拟改进后的效果。
        """
        project = self._get_project(project_id)

        # 计算各维度得分
        schedule_score = self._calc_schedule_score(project)
        cost_score = self._calc_cost_score(project)
        resource_score = self._calc_resource_score(project)
        quality_score = self._calc_quality_score(project)

        dimensions = [
            {
                "key": "schedule",
                "label": "进度",
                "weight": DIMENSION_WEIGHTS["schedule"],
                "score": schedule_score,
                "weighted_score": round(schedule_score * DIMENSION_WEIGHTS["schedule"], 1),
            },
            {
                "key": "cost",
                "label": "成本",
                "weight": DIMENSION_WEIGHTS["cost"],
                "score": cost_score,
                "weighted_score": round(cost_score * DIMENSION_WEIGHTS["cost"], 1),
            },
            {
                "key": "resource",
                "label": "资源",
                "weight": DIMENSION_WEIGHTS["resource"],
                "score": resource_score,
                "weighted_score": round(resource_score * DIMENSION_WEIGHTS["resource"], 1),
            },
            {
                "key": "quality",
                "label": "质量",
                "weight": DIMENSION_WEIGHTS["quality"],
                "score": quality_score,
                "weighted_score": round(quality_score * DIMENSION_WEIGHTS["quality"], 1),
            },
        ]

        overall_score = round(sum(d["weighted_score"] for d in dimensions), 1)

        # 找出拉低健康度的主要因素（得分低于 70 的维度）
        weak_factors = sorted(
            [d for d in dimensions if d["score"] < 70],
            key=lambda x: x["score"],
        )

        # 模拟改进效果：将最弱维度提升到 80 分后的总分
        simulations = []
        for factor in weak_factors:
            improved_score = overall_score + (80 - factor["score"]) * factor["weight"]
            simulations.append(
                {
                    "dimension": factor["key"],
                    "label": factor["label"],
                    "current_score": factor["score"],
                    "target_score": 80,
                    "current_overall": overall_score,
                    "simulated_overall": round(improved_score, 1),
                    "improvement": round(improved_score - overall_score, 1),
                }
            )

        return {
            "project_id": project_id,
            "overall_score": overall_score,
            "current_health": project.health or "H1",
            "dimensions": dimensions,
            "weak_factors": weak_factors,
            "simulations": simulations,
        }

    # ================================================================
    #  3. 改进建议
    # ================================================================
    def get_improvement_suggestions(self, project_id: int) -> Dict[str, Any]:
        """
        基于当前最弱维度和历史改进案例，给出优先级排序的建议。
        """
        breakdown = self.get_risk_breakdown(project_id)
        project = self._get_project(project_id)

        suggestions = []
        priority = 1

        for factor in breakdown["weak_factors"]:
            dim = factor["key"]
            score = factor["score"]
            actions = self._get_dimension_actions(dim, score, project)
            for action in actions:
                action["priority"] = priority
                action["dimension"] = dim
                action["dimension_label"] = factor["label"]
                action["current_score"] = score
                suggestions.append(action)
                priority += 1

        # 补充通用建议（如果没有弱维度）
        if not suggestions:
            suggestions.append(
                {
                    "priority": 1,
                    "dimension": "overall",
                    "dimension_label": "综合",
                    "current_score": breakdown["overall_score"],
                    "title": "保持当前节奏",
                    "description": "各维度表现良好，建议保持当前管理节奏，持续监控关键指标。",
                    "impact": "low",
                    "effort": "low",
                    "category": "maintain",
                }
            )

        # 查找历史改进成功案例
        success_cases = self._get_success_cases(project_id)

        return {
            "project_id": project_id,
            "overall_score": breakdown["overall_score"],
            "suggestions": suggestions,
            "success_cases": success_cases,
        }

    # ================================================================
    #  内部方法
    # ================================================================

    def _get_project(self, project_id: int) -> Project:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        return project

    def _get_alert_events(
        self, project_id: int, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        """获取时间范围内的预警事件（用于标记在趋势图上）"""
        alerts = (
            self.db.query(AlertRecord)
            .filter(
                AlertRecord.project_id == project_id,
                AlertRecord.triggered_at >= start_date,
                AlertRecord.triggered_at <= end_date,
            )
            .order_by(AlertRecord.triggered_at)
            .all()
        )

        events = []
        for a in alerts:
            events.append(
                {
                    "date": a.triggered_at.date().isoformat() if a.triggered_at else None,
                    "level": a.alert_level,
                    "title": a.alert_title,
                    "status": a.status,
                }
            )
        return events

    def _calc_schedule_score(self, project: Project) -> int:
        """计算进度维度得分（0-100）"""
        score = 100

        # 逾期里程碑扣分
        today = date.today()
        overdue = (
            self.db.query(ProjectMilestone)
            .filter(
                ProjectMilestone.project_id == project.id,
                ProjectMilestone.planned_date < today,
                ProjectMilestone.status != "COMPLETED",
                ProjectMilestone.is_key,
            )
            .count()
        )
        score -= overdue * 15

        # 进度偏差扣分
        if project.planned_start_date and project.planned_end_date:
            total_days = (project.planned_end_date - project.planned_start_date).days
            elapsed = (today - project.planned_start_date).days
            if total_days > 0:
                planned = min(max((elapsed / total_days) * 100, 0), 100)
                actual = float(project.progress_pct or 0)
                variance = planned - actual
                if variance > 0:
                    score -= int(variance * 1.5)

        # 阻塞任务扣分
        blocked = (
            self.db.query(Task)
            .filter(Task.project_id == project.id, Task.status == "BLOCKED")
            .count()
        )
        score -= blocked * 10

        return max(score, 0)

    def _calc_cost_score(self, project: Project) -> int:
        """计算成本维度得分"""
        score = 100

        # 通过预算使用率推算
        budget_pct = float(getattr(project, "budget_used_pct", 0) or 0)
        progress_pct = float(project.progress_pct or 0)

        if progress_pct > 0 and budget_pct > 0:
            cost_efficiency = budget_pct / max(progress_pct, 1) * 100
            if cost_efficiency > 110:
                score -= int((cost_efficiency - 100) * 1.5)
            elif cost_efficiency > 100:
                score -= int((cost_efficiency - 100) * 0.8)

        # 成本类预警扣分
        cost_alerts = (
            self.db.query(AlertRecord)
            .join(AlertRule)
            .filter(
                AlertRecord.project_id == project.id,
                AlertRecord.status == "PENDING",
                AlertRule.rule_type.in_(["BUDGET_OVERRUN", "COST_VARIANCE"]),
            )
            .count()
        )
        score -= cost_alerts * 10

        return max(score, 0)

    def _calc_resource_score(self, project: Project) -> int:
        """计算资源维度得分"""
        score = 100

        # 缺料预警扣分
        shortage_alerts = (
            self.db.query(AlertRecord)
            .join(AlertRule)
            .filter(
                AlertRecord.project_id == project.id,
                AlertRecord.status == "PENDING",
                AlertRule.rule_type == "MATERIAL_SHORTAGE",
            )
            .count()
        )
        score -= shortage_alerts * 12

        # 严重缺料额外扣分
        critical_shortage = (
            self.db.query(AlertRecord)
            .join(AlertRule)
            .filter(
                AlertRecord.project_id == project.id,
                AlertRecord.status == "PENDING",
                AlertRule.rule_type == "MATERIAL_SHORTAGE",
                AlertRecord.alert_level == AlertLevelEnum.CRITICAL.value,
            )
            .count()
        )
        score -= critical_shortage * 10

        return max(score, 0)

    def _calc_quality_score(self, project: Project) -> int:
        """计算质量维度得分"""
        score = 100

        # 未关闭阻塞问题扣分
        blockers = (
            self.db.query(Issue)
            .filter(
                Issue.project_id == project.id,
                Issue.issue_type == IssueTypeEnum.BLOCKER,
                Issue.status.in_(["OPEN", "IN_PROGRESS"]),
            )
            .count()
        )
        score -= blockers * 20

        # 高优先级问题扣分
        high_issues = (
            self.db.query(Issue)
            .filter(
                Issue.project_id == project.id,
                Issue.priority.in_(["HIGH", "URGENT"]),
                Issue.status.in_(["OPEN", "IN_PROGRESS"]),
            )
            .count()
        )
        score -= high_issues * 8

        # 未处理预警扣分
        pending_alerts = (
            self.db.query(AlertRecord)
            .filter(
                AlertRecord.project_id == project.id,
                AlertRecord.status == "PENDING",
            )
            .count()
        )
        score -= pending_alerts * 5

        return max(score, 0)

    def _get_dimension_actions(
        self, dimension: str, score: int, project: Project
    ) -> List[Dict[str, Any]]:
        """根据维度和得分生成改进建议"""
        actions = []

        if dimension == "schedule":
            if score < 40:
                actions.append(
                    {
                        "title": "紧急重排项目计划",
                        "description": "进度严重滞后，建议立即召开项目复盘会议，重新评估里程碑和关键路径，"
                        "必要时申请资源增援或调整交付范围。",
                        "impact": "high",
                        "effort": "high",
                        "category": "reschedule",
                    }
                )
            if score < 70:
                actions.append(
                    {
                        "title": "解决阻塞任务",
                        "description": "清理当前阻塞的任务，协调跨部门资源，确保关键路径畅通。",
                        "impact": "high",
                        "effort": "medium",
                        "category": "unblock",
                    }
                )
                actions.append(
                    {
                        "title": "加速逾期里程碑",
                        "description": "针对已逾期的关键里程碑制定追赶计划，分配额外资源确保快速完成。",
                        "impact": "medium",
                        "effort": "medium",
                        "category": "accelerate",
                    }
                )

        elif dimension == "cost":
            if score < 50:
                actions.append(
                    {
                        "title": "成本超支审查",
                        "description": "成本偏差较大，建议进行成本审查，识别超支原因，制定成本控制计划。",
                        "impact": "high",
                        "effort": "medium",
                        "category": "cost_control",
                    }
                )
            if score < 70:
                actions.append(
                    {
                        "title": "优化资源配置降低成本",
                        "description": "审查当前资源使用效率，减少不必要的开支，优化采购策略。",
                        "impact": "medium",
                        "effort": "low",
                        "category": "optimize",
                    }
                )

        elif dimension == "resource":
            if score < 50:
                actions.append(
                    {
                        "title": "紧急处理缺料问题",
                        "description": "存在严重缺料预警，建议立即联系供应商加急供货，或寻找替代方案。",
                        "impact": "high",
                        "effort": "high",
                        "category": "material",
                    }
                )
            if score < 70:
                actions.append(
                    {
                        "title": "完善物料跟踪机制",
                        "description": "加强物料到货跟踪，提前预警可能的缺料风险，建立安全库存。",
                        "impact": "medium",
                        "effort": "low",
                        "category": "tracking",
                    }
                )

        elif dimension == "quality":
            if score < 50:
                actions.append(
                    {
                        "title": "集中解决阻塞问题",
                        "description": "存在多个阻塞问题未解决，建议组织专项攻关，集中力量消除阻塞。",
                        "impact": "high",
                        "effort": "high",
                        "category": "quality_fix",
                    }
                )
            if score < 70:
                actions.append(
                    {
                        "title": "处理高优先级问题",
                        "description": "优先处理高优先级未解决问题，避免问题累积影响项目交付。",
                        "impact": "medium",
                        "effort": "medium",
                        "category": "issue_resolve",
                    }
                )

        return actions

    def _get_success_cases(self, project_id: int) -> List[Dict[str, Any]]:
        """
        查找历史改进成功案例：
        健康度从 H3/H2 恢复到 H1 的项目。
        """
        # 查找有过健康度恢复记录的快照
        from app.models.project import ProjectStatusLog

        recovered = (
            self.db.query(ProjectStatusLog)
            .filter(
                ProjectStatusLog.old_health.in_(["H2", "H3"]),
                ProjectStatusLog.new_health == "H1",
                ProjectStatusLog.change_type == "HEALTH_AUTO_CALCULATED",
            )
            .order_by(ProjectStatusLog.changed_at.desc())
            .limit(5)
            .all()
        )

        cases = []
        for log in recovered:
            p = self.db.query(Project).filter(Project.id == log.project_id).first()
            if p and p.id != project_id:
                cases.append(
                    {
                        "project_id": p.id,
                        "project_name": p.project_name,
                        "from_health": log.old_health,
                        "to_health": log.new_health,
                        "recovered_at": log.changed_at.isoformat() if log.changed_at else None,
                        "note": log.change_note,
                    }
                )
        return cases
