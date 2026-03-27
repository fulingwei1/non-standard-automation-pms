# -*- coding: utf-8 -*-
"""
绩效分析服务

提供四大分析能力：
1. 项目绩效排行 — 基于健康度评分、预算执行率、进度偏差、风险数量
2. 团队效率分析 — 各部门项目平均健康度、预算偏差率、里程碑按时完成率
3. 项目经理绩效 — 负责项目整体表现、历史趋势、管理幅度
4. 改进效果追踪 — 健康度变化、预警关闭率、风险缓解效果

输出格式：performance_ranking[], team_efficiency{}, pm_performance{}
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.alert import AlertRecord, AlertRule, ProjectHealthSnapshot
from app.models.project import Project, ProjectMilestone, ProjectStatusLog

# 健康度等级 → 数值映射（复用 health_trend_service 的标准）
HEALTH_SCORE_MAP = {"H1": 90, "H2": 65, "H3": 35, "H4": 0}


class PerformanceAnalysisService:
    """绩效分析服务"""

    def __init__(self, db: Session):
        self.db = db

    # ================================================================
    #  1. 项目绩效排行
    # ================================================================
    def get_performance_ranking(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        dept_id: Optional[int] = None,
        project_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        项目绩效排行榜

        综合得分 = 健康度得分(40%) + 预算执行率得分(25%) + 进度偏差得分(25%) + 风险得分(10%)

        Returns:
            performance_ranking[]
        """
        query = self.db.query(Project).filter(
            Project.is_active == True,
            Project.is_archived == False,
        )

        if dept_id is not None:
            query = query.filter(Project.dept_id == dept_id)
        if project_type:
            query = query.filter(Project.project_type == project_type)
        if start_date:
            query = query.filter(Project.planned_start_date >= start_date)
        if end_date:
            query = query.filter(Project.planned_start_date <= end_date)

        projects = query.all()
        ranking = []

        for p in projects:
            health_score = self._health_score(p)
            budget_score = self._budget_score(p)
            schedule_score = self._schedule_score(p)
            risk_score = self._risk_score(p)

            composite = round(
                health_score * 0.40
                + budget_score * 0.25
                + schedule_score * 0.25
                + risk_score * 0.10,
                1,
            )

            ranking.append({
                "project_id": p.id,
                "project_code": p.project_code,
                "project_name": p.project_name,
                "dept_id": p.dept_id,
                "pm_id": p.pm_id,
                "pm_name": p.pm_name,
                "health": p.health,
                "health_score": health_score,
                "budget_score": budget_score,
                "schedule_score": schedule_score,
                "risk_score": risk_score,
                "composite_score": composite,
            })

        ranking.sort(key=lambda x: x["composite_score"], reverse=True)

        # 排名
        for idx, item in enumerate(ranking, 1):
            item["rank"] = idx

        return ranking[:limit]

    # ================================================================
    #  2. 团队效率分析
    # ================================================================
    def get_team_efficiency(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        project_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        各部门项目的效率分析

        Returns:
            team_efficiency {departments[], summary{}}
        """
        query = self.db.query(Project).filter(
            Project.is_active == True,
            Project.is_archived == False,
            Project.dept_id.isnot(None),
        )

        if project_type:
            query = query.filter(Project.project_type == project_type)
        if start_date:
            query = query.filter(Project.planned_start_date >= start_date)
        if end_date:
            query = query.filter(Project.planned_start_date <= end_date)

        projects = query.all()

        # 按部门分组
        dept_map: Dict[int, List[Project]] = {}
        for p in projects:
            dept_map.setdefault(p.dept_id, []).append(p)

        departments = []
        for dept_id, dept_projects in dept_map.items():
            dept_info = self._calc_dept_efficiency(dept_id, dept_projects)
            departments.append(dept_info)

        departments.sort(key=lambda x: x["avg_health_score"], reverse=True)

        # 全局汇总
        all_health = [d["avg_health_score"] for d in departments]
        summary = {
            "total_departments": len(departments),
            "total_projects": len(projects),
            "avg_health_score": round(sum(all_health) / len(all_health), 1) if all_health else 0,
        }

        return {"departments": departments, "summary": summary}

    # ================================================================
    #  3. 项目经理绩效
    # ================================================================
    def get_pm_performance(
        self,
        pm_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        项目经理绩效分析

        Returns:
            pm_performance {managers[], summary{}}
        """
        query = self.db.query(Project).filter(
            Project.is_active == True,
            Project.is_archived == False,
            Project.pm_id.isnot(None),
        )

        if pm_id is not None:
            query = query.filter(Project.pm_id == pm_id)
        if start_date:
            query = query.filter(Project.planned_start_date >= start_date)
        if end_date:
            query = query.filter(Project.planned_start_date <= end_date)

        projects = query.all()

        # 按 PM 分组
        pm_map: Dict[int, List[Project]] = {}
        for p in projects:
            pm_map.setdefault(p.pm_id, []).append(p)

        managers = []
        for mid, pm_projects in pm_map.items():
            pm_info = self._calc_pm_performance(mid, pm_projects)
            managers.append(pm_info)

        managers.sort(key=lambda x: x["avg_composite_score"], reverse=True)

        for idx, m in enumerate(managers, 1):
            m["rank"] = idx

        summary = {
            "total_managers": len(managers),
            "total_projects": sum(m["project_count"] for m in managers),
        }

        return {"managers": managers, "summary": summary}

    # ================================================================
    #  4. 改进效果追踪
    # ================================================================
    def get_improvement_tracking(
        self,
        project_id: Optional[int] = None,
        dept_id: Optional[int] = None,
        days: int = 90,
    ) -> Dict[str, Any]:
        """
        追踪改进措施效果

        Returns:
            improvement_tracking {health_changes[], alert_closure_rate{}, risk_mitigation{}}
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # ── 健康度变化追踪 ──
        health_changes = self._get_health_changes(project_id, dept_id, start_date, end_date)

        # ── 预警关闭率 ──
        alert_closure = self._get_alert_closure_rate(project_id, dept_id, start_date, end_date)

        # ── 风险缓解效果 ──
        risk_mitigation = self._get_risk_mitigation(project_id, dept_id, start_date, end_date)

        return {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat(), "days": days},
            "health_changes": health_changes,
            "alert_closure_rate": alert_closure,
            "risk_mitigation": risk_mitigation,
        }

    # ================================================================
    #  内部方法 — 评分计算
    # ================================================================

    def _health_score(self, project: Project) -> int:
        """健康度得分：直接映射 H1-H4 → 0-100"""
        return HEALTH_SCORE_MAP.get(project.health or "H1", 50)

    def _budget_score(self, project: Project) -> int:
        """
        预算执行率得分

        budget_used_pct = actual_cost / budget_amount * 100
        得分规则：
        - ≤100%: 100 分
        - 100%-110%: 线性递减 100→70
        - 110%-130%: 线性递减 70→30
        - >130%: 0 分
        """
        budget = float(project.budget_amount or 0)
        actual = float(project.actual_cost or 0)
        if budget <= 0:
            return 80  # 无预算信息，给中等分

        pct = (actual / budget) * 100
        if pct <= 100:
            return 100
        elif pct <= 110:
            return round(100 - (pct - 100) * 3)
        elif pct <= 130:
            return round(70 - (pct - 110) * 2)
        else:
            return 0

    def _schedule_score(self, project: Project) -> int:
        """
        进度偏差得分

        偏差 = 计划进度 - 实际进度
        得分规则：
        - 偏差 ≤ 0 (提前): 100
        - 偏差 0%-10%: 线性递减 100→70
        - 偏差 10%-25%: 线性递减 70→30
        - 偏差 >25%: 0
        """
        if not project.planned_start_date or not project.planned_end_date:
            return 80

        today = date.today()
        total_days = (project.planned_end_date - project.planned_start_date).days
        elapsed = (today - project.planned_start_date).days

        if total_days <= 0:
            return 80

        planned_pct = min(max((elapsed / total_days) * 100, 0), 100)
        actual_pct = float(project.progress_pct or 0)
        variance = planned_pct - actual_pct

        if variance <= 0:
            return 100
        elif variance <= 10:
            return round(100 - variance * 3)
        elif variance <= 25:
            return round(70 - (variance - 10) * 2.67)
        else:
            return 0

    def _risk_score(self, project: Project) -> int:
        """
        风险得分 — 基于未处理预警数量

        - 0 个预警: 100
        - 每个 WARNING: -10
        - 每个 CRITICAL: -20
        - 每个 URGENT: -30
        """
        alerts = (
            self.db.query(
                AlertRecord.alert_level,
                func.count(AlertRecord.id).label("cnt"),
            )
            .filter(
                AlertRecord.project_id == project.id,
                AlertRecord.status == "PENDING",
            )
            .group_by(AlertRecord.alert_level)
            .all()
        )

        score = 100
        level_penalty = {"INFO": 5, "WARNING": 10, "CRITICAL": 20, "URGENT": 30}
        for level, cnt in alerts:
            score -= level_penalty.get(level, 10) * cnt

        return max(score, 0)

    # ================================================================
    #  内部方法 — 部门效率
    # ================================================================

    def _calc_dept_efficiency(
        self, dept_id: int, projects: List[Project]
    ) -> Dict[str, Any]:
        """计算单个部门的效率指标"""
        # 部门名称（通过第一个项目的关系获取）
        dept_name = None
        first = projects[0]
        if first.department:
            dept_name = first.department.dept_name

        # 平均健康度
        health_scores = [HEALTH_SCORE_MAP.get(p.health or "H1", 50) for p in projects]
        avg_health = round(sum(health_scores) / len(health_scores), 1)

        # 预算偏差率
        total_budget = sum(float(p.budget_amount or 0) for p in projects)
        total_actual = sum(float(p.actual_cost or 0) for p in projects)
        budget_variance_pct = (
            round((total_actual - total_budget) / total_budget * 100, 1)
            if total_budget > 0
            else 0
        )

        # 里程碑按时完成率
        project_ids = [p.id for p in projects]
        milestone_stats = self._calc_milestone_on_time_rate(project_ids)

        return {
            "dept_id": dept_id,
            "dept_name": dept_name,
            "project_count": len(projects),
            "avg_health_score": avg_health,
            "health_distribution": self._health_distribution(projects),
            "budget_variance_pct": budget_variance_pct,
            "total_budget": total_budget,
            "total_actual_cost": total_actual,
            "milestone_on_time_rate": milestone_stats["on_time_rate"],
            "milestone_total": milestone_stats["total"],
            "milestone_on_time": milestone_stats["on_time"],
            "milestone_delayed": milestone_stats["delayed"],
        }

    def _health_distribution(self, projects: List[Project]) -> Dict[str, int]:
        """健康度分布统计"""
        dist = {"H1": 0, "H2": 0, "H3": 0, "H4": 0}
        for p in projects:
            h = p.health or "H1"
            if h in dist:
                dist[h] += 1
        return dist

    def _calc_milestone_on_time_rate(self, project_ids: List[int]) -> Dict[str, Any]:
        """计算里程碑按时完成率"""
        if not project_ids:
            return {"on_time_rate": 0, "total": 0, "on_time": 0, "delayed": 0}

        milestones = (
            self.db.query(ProjectMilestone)
            .filter(
                ProjectMilestone.project_id.in_(project_ids),
                ProjectMilestone.is_key == True,
                ProjectMilestone.status == "COMPLETED",
            )
            .all()
        )

        total = len(milestones)
        if total == 0:
            return {"on_time_rate": 0, "total": 0, "on_time": 0, "delayed": 0}

        on_time = 0
        for m in milestones:
            if m.actual_date and m.planned_date:
                if m.actual_date <= m.planned_date:
                    on_time += 1
            elif m.planned_date:
                # 已完成但无实际日期，视为按时
                on_time += 1

        delayed = total - on_time

        return {
            "on_time_rate": round(on_time / total * 100, 1),
            "total": total,
            "on_time": on_time,
            "delayed": delayed,
        }

    # ================================================================
    #  内部方法 — PM 绩效
    # ================================================================

    def _calc_pm_performance(
        self, pm_id: int, projects: List[Project]
    ) -> Dict[str, Any]:
        """计算单个 PM 的绩效"""
        pm_name = projects[0].pm_name
        if projects[0].manager:
            pm_name = projects[0].manager.real_name or pm_name

        # 各项目综合得分
        scores = []
        for p in projects:
            hs = self._health_score(p)
            bs = self._budget_score(p)
            ss = self._schedule_score(p)
            rs = self._risk_score(p)
            composite = round(hs * 0.40 + bs * 0.25 + ss * 0.25 + rs * 0.10, 1)
            scores.append(composite)

        avg_score = round(sum(scores) / len(scores), 1) if scores else 0

        # 历史健康度趋势（最近 6 个月的月度快照均值）
        project_ids = [p.id for p in projects]
        trend = self._get_pm_health_trend(project_ids)

        return {
            "pm_id": pm_id,
            "pm_name": pm_name,
            "project_count": len(projects),
            "avg_composite_score": avg_score,
            "health_distribution": self._health_distribution(projects),
            "projects": [
                {
                    "project_id": p.id,
                    "project_code": p.project_code,
                    "project_name": p.project_name,
                    "health": p.health,
                    "composite_score": scores[i],
                }
                for i, p in enumerate(projects)
            ],
            "monthly_trend": trend,
        }

    def _get_pm_health_trend(self, project_ids: List[int]) -> List[Dict[str, Any]]:
        """获取 PM 管理项目的月度健康度趋势"""
        if not project_ids:
            return []

        end_date = date.today()
        start_date = end_date - timedelta(days=180)

        rows = (
            self.db.query(
                func.strftime("%Y-%m", ProjectHealthSnapshot.snapshot_date).label("month"),
                func.avg(ProjectHealthSnapshot.health_score).label("avg_score"),
            )
            .filter(
                ProjectHealthSnapshot.project_id.in_(project_ids),
                ProjectHealthSnapshot.snapshot_date >= start_date,
                ProjectHealthSnapshot.snapshot_date <= end_date,
            )
            .group_by("month")
            .order_by("month")
            .all()
        )

        # 兼容 PostgreSQL（无 strftime），用 fallback
        if not rows:
            rows = (
                self.db.query(
                    func.to_char(ProjectHealthSnapshot.snapshot_date, "YYYY-MM").label("month"),
                    func.avg(ProjectHealthSnapshot.health_score).label("avg_score"),
                )
                .filter(
                    ProjectHealthSnapshot.project_id.in_(project_ids),
                    ProjectHealthSnapshot.snapshot_date >= start_date,
                    ProjectHealthSnapshot.snapshot_date <= end_date,
                )
                .group_by("month")
                .order_by("month")
                .all()
            )

        return [
            {"month": r.month, "avg_health_score": round(float(r.avg_score or 0), 1)}
            for r in rows
        ]

    # ================================================================
    #  内部方法 — 改进效果追踪
    # ================================================================

    def _get_health_changes(
        self,
        project_id: Optional[int],
        dept_id: Optional[int],
        start_date: date,
        end_date: date,
    ) -> List[Dict[str, Any]]:
        """获取时间范围内的健康度变化记录"""
        query = self.db.query(ProjectStatusLog).filter(
            ProjectStatusLog.change_type == "HEALTH_AUTO_CALCULATED",
            ProjectStatusLog.changed_at >= start_date,
            ProjectStatusLog.changed_at <= end_date,
        )

        if project_id is not None:
            query = query.filter(ProjectStatusLog.project_id == project_id)

        if dept_id is not None:
            query = query.join(Project, ProjectStatusLog.project_id == Project.id).filter(
                Project.dept_id == dept_id
            )

        logs = query.order_by(ProjectStatusLog.changed_at.desc()).limit(200).all()

        # 统计改善 / 恶化 / 不变
        improved = 0
        worsened = 0
        for log in logs:
            old = HEALTH_SCORE_MAP.get(log.old_health, 50)
            new = HEALTH_SCORE_MAP.get(log.new_health, 50)
            if new > old:
                improved += 1
            elif new < old:
                worsened += 1

        return {
            "total_changes": len(logs),
            "improved": improved,
            "worsened": worsened,
            "improvement_rate": round(improved / len(logs) * 100, 1) if logs else 0,
            "recent_changes": [
                {
                    "project_id": log.project_id,
                    "old_health": log.old_health,
                    "new_health": log.new_health,
                    "changed_at": log.changed_at.isoformat() if log.changed_at else None,
                    "note": log.change_note,
                }
                for log in logs[:20]
            ],
        }

    def _get_alert_closure_rate(
        self,
        project_id: Optional[int],
        dept_id: Optional[int],
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """预警关闭率统计"""
        base_q = self.db.query(AlertRecord).filter(
            AlertRecord.triggered_at >= start_date,
            AlertRecord.triggered_at <= end_date,
        )

        if project_id is not None:
            base_q = base_q.filter(AlertRecord.project_id == project_id)

        if dept_id is not None:
            base_q = base_q.join(Project, AlertRecord.project_id == Project.id).filter(
                Project.dept_id == dept_id
            )

        total = base_q.count()
        closed = base_q.filter(AlertRecord.status.in_(["RESOLVED", "CLOSED"])).count()
        pending = base_q.filter(AlertRecord.status == "PENDING").count()

        # 平均处理时长（已关闭的预警）
        resolved_alerts = (
            base_q.filter(
                AlertRecord.status.in_(["RESOLVED", "CLOSED"]),
                AlertRecord.handle_end_at.isnot(None),
                AlertRecord.triggered_at.isnot(None),
            ).all()
        )

        avg_hours = 0
        if resolved_alerts:
            total_hours = 0
            count = 0
            for a in resolved_alerts:
                if a.handle_end_at and a.triggered_at:
                    delta = a.handle_end_at - a.triggered_at
                    total_hours += delta.total_seconds() / 3600
                    count += 1
            avg_hours = round(total_hours / count, 1) if count > 0 else 0

        return {
            "total_alerts": total,
            "closed": closed,
            "pending": pending,
            "closure_rate": round(closed / total * 100, 1) if total > 0 else 0,
            "avg_resolution_hours": avg_hours,
        }

    def _get_risk_mitigation(
        self,
        project_id: Optional[int],
        dept_id: Optional[int],
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """风险缓解效果：对比期初与期末的预警活跃数"""
        mid_date = start_date + (end_date - start_date) / 2

        def _count_active(as_of: date) -> int:
            q = self.db.query(func.count(AlertRecord.id)).filter(
                AlertRecord.triggered_at <= as_of,
                AlertRecord.status == "PENDING",
            )
            if project_id is not None:
                q = q.filter(AlertRecord.project_id == project_id)
            if dept_id is not None:
                q = q.join(Project, AlertRecord.project_id == Project.id).filter(
                    Project.dept_id == dept_id
                )
            return q.scalar() or 0

        start_active = _count_active(start_date)
        mid_active = _count_active(mid_date)
        end_active = _count_active(end_date)

        # 按级别统计当前活跃预警
        level_q = (
            self.db.query(
                AlertRecord.alert_level,
                func.count(AlertRecord.id).label("cnt"),
            )
            .filter(AlertRecord.status == "PENDING")
        )
        if project_id is not None:
            level_q = level_q.filter(AlertRecord.project_id == project_id)
        if dept_id is not None:
            level_q = level_q.join(Project, AlertRecord.project_id == Project.id).filter(
                Project.dept_id == dept_id
            )
        level_dist = {r[0]: r[1] for r in level_q.group_by(AlertRecord.alert_level).all()}

        return {
            "period_start_active": start_active,
            "period_mid_active": mid_active,
            "period_end_active": end_active,
            "net_change": end_active - start_active,
            "mitigation_trend": (
                "improving" if end_active < start_active
                else "stable" if end_active == start_active
                else "worsening"
            ),
            "active_by_level": level_dist,
        }
