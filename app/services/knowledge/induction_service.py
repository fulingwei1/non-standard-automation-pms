# -*- coding: utf-8 -*-
"""
最佳实践自动归纳服务
基于高绩效、按时交付、预算控制良好的项目提取共同特征
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.ecn.core import Ecn
from app.models.issue import Issue
from app.models.knowledge_base import (
    KnowledgeEntry,
    KnowledgeSourceEnum,
    KnowledgeStatusEnum,
    KnowledgeTypeEnum,
)
from app.models.project.core import Project
from app.models.project.lifecycle import ProjectStage
from app.models.project_review import ProjectReview


class BestPracticeInductionService:
    """最佳实践自动归纳服务"""

    def __init__(self, db: Session):
        self.db = db

    def induce(self, *, created_by: Optional[int] = None) -> Dict[str, Any]:
        """
        分析所有已结项项目，归纳最佳实践

        Returns:
            {"total_projects_analyzed": N, "best_practices_generated": N, "entries": [...]}
        """
        # 获取已完成/结项的项目（stage = S9 或 status 含 CLOSED/COMPLETED）
        projects = (
            self.db.query(Project)
            .filter(Project.stage.in_(["S9", "CLOSED", "COMPLETED"]))
            .all()
        )
        if not projects:
            # 退而求其次，取有复盘的项目
            review_project_ids = (
                self.db.query(ProjectReview.project_id)
                .filter(ProjectReview.status == "PUBLISHED")
                .distinct()
                .all()
            )
            pid_list = [r[0] for r in review_project_ids]
            if pid_list:
                projects = self.db.query(Project).filter(Project.id.in_(pid_list)).all()

        if not projects:
            return {
                "total_projects_analyzed": 0,
                "high_perf_projects": 0,
                "on_time_projects": 0,
                "budget_controlled_projects": 0,
                "best_practices_generated": 0,
                "entries": [],
            }

        # 分析每个项目的绩效指标
        scored: List[Dict[str, Any]] = []
        for p in projects:
            score_info = self._score_project(p)
            scored.append({"project": p, **score_info})

        high_perf = [s for s in scored if s["is_high_perf"]]
        on_time = [s for s in scored if s["on_time"]]
        budget_ok = [s for s in scored if s["budget_controlled"]]

        entries: List[KnowledgeEntry] = []

        # 1. 高绩效项目共同特征
        if len(high_perf) >= 1:
            entry = self._build_high_perf_entry(high_perf, created_by)
            if entry:
                entries.append(entry)

        # 2. 按时交付项目的管理做法
        if len(on_time) >= 1:
            entry = self._build_on_time_entry(on_time, created_by)
            if entry:
                entries.append(entry)

        # 3. 预算控制良好的项目经验
        if len(budget_ok) >= 1:
            entry = self._build_budget_entry(budget_ok, created_by)
            if entry:
                entries.append(entry)

        self.db.add_all(entries)
        self.db.flush()

        return {
            "total_projects_analyzed": len(projects),
            "high_perf_projects": len(high_perf),
            "on_time_projects": len(on_time),
            "budget_controlled_projects": len(budget_ok),
            "best_practices_generated": len(entries),
            "entries": entries,
        }

    # ── 项目评分 ────────────────────────────────────

    def _score_project(self, project: Project) -> Dict[str, Any]:
        """评估单个项目的绩效维度"""
        # 进度：有无延误
        stages = (
            self.db.query(ProjectStage)
            .filter(ProjectStage.project_id == project.id)
            .all()
        )
        total_delay = 0
        for s in stages:
            if s.planned_end_date and s.actual_end_date:
                d = (s.actual_end_date - s.planned_end_date).days
                if d > 0:
                    total_delay += d

        on_time = total_delay <= 7  # 容忍 7 天

        # 预算
        review = (
            self.db.query(ProjectReview)
            .filter(ProjectReview.project_id == project.id)
            .first()
        )
        budget_controlled = False
        satisfaction = 0
        if review:
            if review.budget_amount and review.actual_cost:
                variance_pct = (
                    abs(float(review.actual_cost) - float(review.budget_amount))
                    / float(review.budget_amount)
                    * 100
                )
                budget_controlled = variance_pct <= 10
            else:
                budget_controlled = True  # 无数据默认通过
            satisfaction = review.customer_satisfaction or 0

        # 质量：问题数少
        issue_count = (
            self.db.query(func.count(Issue.id))
            .filter(Issue.project_id == project.id)
            .scalar()
            or 0
        )
        low_issues = issue_count <= 5

        # 变更数少
        ecn_count = (
            self.db.query(func.count(Ecn.id))
            .filter(Ecn.project_id == project.id)
            .scalar()
            or 0
        )
        low_changes = ecn_count <= 3

        is_high_perf = on_time and budget_controlled and (satisfaction >= 4 or low_issues)

        return {
            "on_time": on_time,
            "total_delay": total_delay,
            "budget_controlled": budget_controlled,
            "satisfaction": satisfaction,
            "issue_count": issue_count,
            "ecn_count": ecn_count,
            "low_issues": low_issues,
            "low_changes": low_changes,
            "is_high_perf": is_high_perf,
        }

    # ── 生成最佳实践条目 ─────────────────────────────

    def _build_high_perf_entry(
        self, items: List[Dict], created_by: Optional[int]
    ) -> Optional[KnowledgeEntry]:
        """高绩效项目共同特征"""
        project_codes = [i["project"].project_code for i in items[:10]]
        avg_satisfaction = sum(i["satisfaction"] for i in items) / len(items)
        avg_issues = sum(i["issue_count"] for i in items) / len(items)

        # 提取共同项目类型
        types = [i["project"].project_type for i in items if i["project"].project_type]
        common_type = max(set(types), key=types.count) if types else "通用"

        detail_lines = []
        for i in items[:10]:
            p = i["project"]
            detail_lines.append(
                f"- {p.project_code} ({p.project_name}): "
                f"延误{i['total_delay']}天, 问题{i['issue_count']}个, "
                f"满意度{i['satisfaction']}"
            )

        return KnowledgeEntry(
            entry_code=self._generate_code(),
            knowledge_type=KnowledgeTypeEnum.BEST_PRACTICE,
            source_type=KnowledgeSourceEnum.REVIEW,
            title=f"[最佳实践] 高绩效项目共同特征分析（{len(items)}个项目）",
            summary=(
                f"基于 {len(items)} 个高绩效项目分析，平均满意度 {avg_satisfaction:.1f}，"
                f"平均问题数 {avg_issues:.1f}。项目类型以 {common_type} 为主。"
            ),
            detail=f"涉及项目：\n" + "\n".join(detail_lines),
            problem_description=None,
            solution=(
                f"高绩效项目的共同管理特征：\n"
                f"1. 进度控制严格，延误普遍≤7天\n"
                f"2. 预算偏差控制在10%以内\n"
                f"3. 客户满意度平均 {avg_satisfaction:.1f}/5\n"
                f"4. 问题数量平均仅 {avg_issues:.0f} 个"
            ),
            project_type=common_type,
            tags=["最佳实践", "高绩效", common_type],
            ai_generated=True,
            ai_confidence=0.80,
            created_by=created_by,
        )

    def _build_on_time_entry(
        self, items: List[Dict], created_by: Optional[int]
    ) -> Optional[KnowledgeEntry]:
        """按时交付项目的管理做法"""
        project_codes = [i["project"].project_code for i in items[:10]]

        detail_lines = []
        for i in items[:10]:
            p = i["project"]
            detail_lines.append(
                f"- {p.project_code}: 延误{i['total_delay']}天, "
                f"变更{i['ecn_count']}次"
            )

        avg_ecn = sum(i["ecn_count"] for i in items) / len(items)

        return KnowledgeEntry(
            entry_code=self._generate_code(),
            knowledge_type=KnowledgeTypeEnum.BEST_PRACTICE,
            source_type=KnowledgeSourceEnum.REVIEW,
            title=f"[最佳实践] 按时交付项目经验总结（{len(items)}个项目）",
            summary=f"基于 {len(items)} 个按时交付项目分析，平均变更次数 {avg_ecn:.1f}",
            detail="涉及项目：\n" + "\n".join(detail_lines),
            solution=(
                f"按时交付项目的管理做法：\n"
                f"1. 变更控制严格，平均变更仅 {avg_ecn:.1f} 次\n"
                f"2. 阶段进度偏差控制在7天以内\n"
                f"3. 关键节点提前预警，及时调整资源"
            ),
            prevention="建议在项目启动阶段即建立进度基线和预警机制",
            tags=["最佳实践", "按时交付", "进度管理"],
            ai_generated=True,
            ai_confidence=0.75,
            created_by=created_by,
        )

    def _build_budget_entry(
        self, items: List[Dict], created_by: Optional[int]
    ) -> Optional[KnowledgeEntry]:
        """预算控制良好的项目经验"""
        detail_lines = []
        for i in items[:10]:
            p = i["project"]
            detail_lines.append(
                f"- {p.project_code}: 问题{i['issue_count']}个, "
                f"变更{i['ecn_count']}次"
            )

        return KnowledgeEntry(
            entry_code=self._generate_code(),
            knowledge_type=KnowledgeTypeEnum.BEST_PRACTICE,
            source_type=KnowledgeSourceEnum.REVIEW,
            title=f"[最佳实践] 预算控制优秀项目经验（{len(items)}个项目）",
            summary=f"基于 {len(items)} 个预算控制良好的项目分析，成本偏差均≤10%",
            detail="涉及项目：\n" + "\n".join(detail_lines),
            solution=(
                "预算控制良好的项目经验：\n"
                "1. 变更审批流程严格执行，避免无序变更\n"
                "2. 采购阶段提前锁定关键物料价格\n"
                "3. 定期进行成本跟踪和预警\n"
                "4. 问题及时处理，减少返工成本"
            ),
            prevention="建议项目启动时建立成本基线和月度成本审查机制",
            tags=["最佳实践", "预算控制", "成本管理"],
            ai_generated=True,
            ai_confidence=0.75,
            created_by=created_by,
        )

    def _generate_code(self) -> str:
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"KE-{today}-"
        last = (
            self.db.query(KnowledgeEntry)
            .filter(KnowledgeEntry.entry_code.like(f"{prefix}%"))
            .order_by(KnowledgeEntry.entry_code.desc())
            .first()
        )
        if last:
            seq = int(last.entry_code.split("-")[-1]) + 1
        else:
            seq = 1
        return f"{prefix}{seq:03d}"
