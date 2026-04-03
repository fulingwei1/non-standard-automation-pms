# -*- coding: utf-8 -*-
"""
经验教训自动提取服务
项目结项时自动从风险/问题/变更/进度日志中提取知识
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func
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
from app.models.project_risk import ProjectRisk


class KnowledgeExtractionService:
    """经验教训自动提取服务"""

    def __init__(self, db: Session):
        self.db = db

    # ── 入口 ──────────────────────────────────────────

    def extract_all(
        self,
        project_id: int,
        *,
        extract_risks: bool = True,
        extract_issues: bool = True,
        extract_ecns: bool = True,
        extract_logs: bool = True,
        auto_publish: bool = False,
        created_by: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        项目结项时一键提取所有经验知识

        Returns:
            {"total_extracted": N, "risk_entries": N, ...., "entries": [...]}
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"项目 {project_id} 不存在")

        entries: List[KnowledgeEntry] = []
        counts = {"risk_entries": 0, "issue_entries": 0, "change_entries": 0, "delay_entries": 0}

        if extract_risks:
            risk_entries = self._extract_from_risks(project, created_by)
            entries.extend(risk_entries)
            counts["risk_entries"] = len(risk_entries)

        if extract_issues:
            issue_entries = self._extract_from_issues(project, created_by)
            entries.extend(issue_entries)
            counts["issue_entries"] = len(issue_entries)

        if extract_ecns:
            ecn_entries = self._extract_from_ecns(project, created_by)
            entries.extend(ecn_entries)
            counts["change_entries"] = len(ecn_entries)

        if extract_logs:
            log_entries = self._extract_from_stage_delays(project, created_by)
            entries.extend(log_entries)
            counts["delay_entries"] = len(log_entries)

        # 设置状态
        target_status = KnowledgeStatusEnum.PUBLISHED if auto_publish else KnowledgeStatusEnum.DRAFT
        for entry in entries:
            entry.status = target_status

        # 批量写入
        self.db.add_all(entries)
        self.db.flush()

        return {
            "project_id": project_id,
            "total_extracted": len(entries),
            **counts,
            "entries": entries,
        }

    # ── 从风险记录提取：已发生风险 + 应对措施 ──────────

    def _extract_from_risks(
        self, project: Project, created_by: Optional[int]
    ) -> List[KnowledgeEntry]:
        """提取已发生的风险及其应对措施"""
        risks = (
            self.db.query(ProjectRisk)
            .filter(
                ProjectRisk.project_id == project.id,
                ProjectRisk.is_occurred.is_(True),
            )
            .all()
        )

        entries = []
        for risk in risks:
            # 跳过无应对措施的记录
            if not risk.mitigation_plan and not risk.contingency_plan:
                continue

            # 去重：同一来源记录只提取一次
            existing = (
                self.db.query(KnowledgeEntry)
                .filter(
                    KnowledgeEntry.source_record_type == "project_risks",
                    KnowledgeEntry.source_record_id == risk.id,
                )
                .first()
            )
            if existing:
                continue

            solution_parts = []
            if risk.mitigation_plan:
                solution_parts.append(f"应对措施：{risk.mitigation_plan}")
            if risk.contingency_plan:
                solution_parts.append(f"应急计划：{risk.contingency_plan}")

            entry = KnowledgeEntry(
                entry_code=self._generate_code(),
                knowledge_type=KnowledgeTypeEnum.RISK_RESPONSE,
                source_type=KnowledgeSourceEnum.RISK,
                title=f"[风险经验] {risk.risk_name}",
                summary=f"项目 {project.project_code} 中发生的{risk.risk_type.value if hasattr(risk.risk_type, 'value') else risk.risk_type}风险及应对经验",
                problem_description=risk.description,
                solution="\n".join(solution_parts),
                impact=risk.actual_impact,
                root_cause=None,
                prevention=risk.mitigation_plan,
                source_project_id=project.id,
                source_record_id=risk.id,
                source_record_type="project_risks",
                project_type=project.project_type,
                product_category=project.product_category,
                industry=project.industry,
                customer_id=project.customer_id,
                risk_type=risk.risk_type.value if hasattr(risk.risk_type, "value") else str(risk.risk_type),
                tags=self._build_risk_tags(risk, project),
                ai_generated=True,
                ai_confidence=0.85,
                created_by=created_by,
            )
            entries.append(entry)

        return entries

    # ── 从问题记录提取：典型问题 + 解决方案 ──────────

    def _extract_from_issues(
        self, project: Project, created_by: Optional[int]
    ) -> List[KnowledgeEntry]:
        """提取已解决的典型问题及解决方案"""
        issues = (
            self.db.query(Issue)
            .filter(
                Issue.project_id == project.id,
                Issue.status.in_(["RESOLVED", "VERIFIED", "CLOSED"]),
                Issue.solution.isnot(None),
                Issue.solution != "",
            )
            .all()
        )

        entries = []
        for issue in issues:
            existing = (
                self.db.query(KnowledgeEntry)
                .filter(
                    KnowledgeEntry.source_record_type == "issues",
                    KnowledgeEntry.source_record_id == issue.id,
                )
                .first()
            )
            if existing:
                continue

            entry = KnowledgeEntry(
                entry_code=self._generate_code(),
                knowledge_type=KnowledgeTypeEnum.ISSUE_SOLUTION,
                source_type=KnowledgeSourceEnum.ISSUE,
                title=f"[问题方案] {issue.title}",
                summary=f"项目 {project.project_code} 中 {issue.category or '通用'} 类问题的解决方案",
                problem_description=issue.description,
                solution=issue.solution,
                root_cause=issue.root_cause,
                impact=f"严重程度: {issue.severity or 'N/A'}, 影响范围: {issue.impact_scope or 'N/A'}",
                prevention=None,
                source_project_id=project.id,
                source_record_id=issue.id,
                source_record_type="issues",
                project_type=project.project_type,
                product_category=project.product_category,
                industry=project.industry,
                customer_id=project.customer_id,
                issue_category=issue.category,
                tags=self._build_issue_tags(issue, project),
                ai_generated=True,
                ai_confidence=0.80,
                created_by=created_by,
            )
            entries.append(entry)

        return entries

    # ── 从变更单提取：高频变更类型 + 原因分析 ──────────

    def _extract_from_ecns(
        self, project: Project, created_by: Optional[int]
    ) -> List[KnowledgeEntry]:
        """按变更类型聚合，提取高频变更的原因分析"""
        ecns = (
            self.db.query(Ecn)
            .filter(
                Ecn.project_id == project.id,
                Ecn.status.in_(["CLOSED", "EXECUTING", "APPROVED"]),
            )
            .all()
        )

        if not ecns:
            return []

        # 按变更类型分组
        type_groups: Dict[str, List[Ecn]] = {}
        for ecn in ecns:
            key = ecn.ecn_type or "OTHER"
            type_groups.setdefault(key, []).append(ecn)

        entries = []
        for ecn_type, group in type_groups.items():
            if len(group) < 1:
                continue

            # 收集原因和方案
            reasons = [e.change_reason for e in group if e.change_reason]
            solutions = [e.solution for e in group if e.solution]
            rca_list = [e.root_cause_analysis for e in group if e.root_cause_analysis]

            summary_reasons = "\n".join(f"- {r}" for r in reasons[:5])
            summary_solutions = "\n".join(f"- {s}" for s in solutions[:5])
            summary_rca = "\n".join(f"- {r}" for r in rca_list[:5])

            # 成本/工期影响汇总
            total_cost = sum(float(e.cost_impact or 0) for e in group)
            total_days = sum(int(e.schedule_impact_days or 0) for e in group)

            entry = KnowledgeEntry(
                entry_code=self._generate_code(),
                knowledge_type=KnowledgeTypeEnum.CHANGE_PATTERN,
                source_type=KnowledgeSourceEnum.ECN,
                title=f"[变更分析] {project.project_code} - {ecn_type}类变更（共{len(group)}次）",
                summary=f"项目 {project.project_code} 中 {ecn_type} 类变更共发生 {len(group)} 次，"
                        f"累计影响成本 ¥{total_cost:,.0f}，影响工期 {total_days} 天",
                problem_description=f"高频变更原因：\n{summary_reasons}" if summary_reasons else None,
                solution=f"解决方案汇总：\n{summary_solutions}" if summary_solutions else None,
                root_cause=f"根因分析：\n{summary_rca}" if summary_rca else None,
                impact=f"累计成本影响: ¥{total_cost:,.0f}, 累计工期影响: {total_days}天",
                prevention=f"建议在项目初期加强 {ecn_type} 方面的评审，减少后期变更",
                source_project_id=project.id,
                source_record_id=group[0].id,
                source_record_type="ecn",
                project_type=project.project_type,
                product_category=project.product_category,
                industry=project.industry,
                customer_id=project.customer_id,
                change_type=ecn_type,
                tags=self._build_ecn_tags(ecn_type, group, project),
                ai_generated=True,
                ai_confidence=0.75,
                created_by=created_by,
            )
            entries.append(entry)

        return entries

    # ── 从进度日志提取：关键节点延误原因 ──────────────

    def _extract_from_stage_delays(
        self, project: Project, created_by: Optional[int]
    ) -> List[KnowledgeEntry]:
        """从阶段记录中提取延误信息"""
        stages = (
            self.db.query(ProjectStage)
            .filter(ProjectStage.project_id == project.id)
            .all()
        )

        entries = []
        for stage in stages:
            if not stage.planned_end_date or not stage.actual_end_date:
                continue
            delay_days = (stage.actual_end_date - stage.planned_end_date).days
            if delay_days <= 0:
                continue  # 未延误

            existing = (
                self.db.query(KnowledgeEntry)
                .filter(
                    KnowledgeEntry.source_record_type == "project_stages",
                    KnowledgeEntry.source_record_id == stage.id,
                )
                .first()
            )
            if existing:
                continue

            entry = KnowledgeEntry(
                entry_code=self._generate_code(),
                knowledge_type=KnowledgeTypeEnum.DELAY_CAUSE,
                source_type=KnowledgeSourceEnum.LOG,
                title=f"[延误分析] {project.project_code} - {stage.stage_name}延误{delay_days}天",
                summary=f"项目 {project.project_code} 的 {stage.stage_name}（{stage.stage_code}）"
                        f"阶段延误 {delay_days} 天，计划结束 {stage.planned_end_date}，实际结束 {stage.actual_end_date}",
                problem_description=f"阶段 {stage.stage_code} {stage.stage_name} 延误 {delay_days} 天",
                solution=None,
                impact=f"延误天数: {delay_days}天",
                source_project_id=project.id,
                source_record_id=stage.id,
                source_record_type="project_stages",
                project_type=project.project_type,
                product_category=project.product_category,
                industry=project.industry,
                customer_id=project.customer_id,
                applicable_stages=[stage.stage_code],
                tags=[stage.stage_code, stage.stage_name, "延误", project.project_type or "通用"],
                ai_generated=True,
                ai_confidence=0.90,
                created_by=created_by,
            )
            entries.append(entry)

        return entries

    # ── 工具方法 ──────────────────────────────────────

    def _generate_code(self) -> str:
        """生成知识编号 KE-YYYYMMDD-NNN"""
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

    def _build_risk_tags(self, risk: ProjectRisk, project: Project) -> list:
        tags = ["风险经验"]
        rt = risk.risk_type.value if hasattr(risk.risk_type, "value") else str(risk.risk_type)
        tags.append(rt)
        if risk.risk_level:
            tags.append(risk.risk_level)
        if project.project_type:
            tags.append(project.project_type)
        if project.product_category:
            tags.append(project.product_category)
        return tags

    def _build_issue_tags(self, issue: Issue, project: Project) -> list:
        tags = ["问题方案"]
        if issue.category:
            tags.append(issue.category)
        if issue.severity:
            tags.append(issue.severity)
        if project.project_type:
            tags.append(project.project_type)
        if project.product_category:
            tags.append(project.product_category)
        return tags

    def _build_ecn_tags(self, ecn_type: str, group: list, project: Project) -> list:
        tags = ["变更分析", ecn_type]
        if len(group) >= 3:
            tags.append("高频变更")
        if project.project_type:
            tags.append(project.project_type)
        if project.product_category:
            tags.append(project.product_category)
        return tags
