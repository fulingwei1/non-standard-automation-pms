# -*- coding: utf-8 -*-
"""
自动风险识别服务

基于项目数据自动检测四类风险：进度/成本/资源/质量。
检测后可自动创建 ProjectRisk 记录并触发通知。
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.acceptance import AcceptanceOrder
from app.models.production.quality_inspection import QualityInspection, ReworkOrder
from app.models.project import (
    Project,
    ProjectCost,
    ProjectMilestone,
    ProjectStage,
    ProjectStageResourcePlan,
    ResourceConflict,
)
from app.models.project.team import ProjectMember
from app.models.project_risk import ProjectRisk, RiskStatusEnum, RiskTypeEnum
from app.models.purchase import PurchaseOrder
from app.schemas.auto_risk import AutoRiskItem, AutoRiskScanResult, AutoRiskType
from app.utils.db_helpers import get_or_404, save_obj

logger = logging.getLogger(__name__)

# ── 风险子类型 → 大类映射 ──────────────────────────────────────────
_CATEGORY_MAP: Dict[AutoRiskType, str] = {
    AutoRiskType.MILESTONE_OVERDUE: "SCHEDULE",
    AutoRiskType.STAGE_DELAY_TREND: "SCHEDULE",
    AutoRiskType.CRITICAL_PATH_DELAY: "SCHEDULE",
    AutoRiskType.BUDGET_OVERRUN: "COST",
    AutoRiskType.COST_GROWTH_ABNORMAL: "COST",
    AutoRiskType.PURCHASE_OVER_BUDGET: "COST",
    AutoRiskType.KEY_PERSON_OVERLOAD: "RESOURCE",
    AutoRiskType.RESOURCE_CONFLICT_UNRESOLVED: "RESOURCE",
    AutoRiskType.SINGLE_SKILL_DEPENDENCY: "RESOURCE",
    AutoRiskType.DEFECT_RATE_RISING: "QUALITY",
    AutoRiskType.REWORK_COUNT_INCREASE: "QUALITY",
    AutoRiskType.ACCEPTANCE_PASS_RATE_DROP: "QUALITY",
}

# 大类 → ProjectRisk.risk_type
_RISK_TYPE_MAP: Dict[str, RiskTypeEnum] = {
    "SCHEDULE": RiskTypeEnum.SCHEDULE,
    "COST": RiskTypeEnum.COST,
    "RESOURCE": RiskTypeEnum.TECHNICAL,  # 资源风险归入 TECHNICAL
    "QUALITY": RiskTypeEnum.QUALITY,
}


class AutoRiskService:
    """自动风险识别服务"""

    def __init__(self, db: Session):
        self.db = db
        self.today = date.today()

    # ====================================================================
    # 公共入口
    # ====================================================================

    def scan_project(
        self,
        project_id: int,
        categories: Optional[List[str]] = None,
        min_confidence: float = 0.6,
        auto_create: bool = True,
    ) -> AutoRiskScanResult:
        """
        对指定项目执行自动风险扫描。

        Args:
            project_id: 项目 ID
            categories: 要扫描的类别列表，默认全部
            min_confidence: 最低置信度阈值
            auto_create: 是否自动创建 ProjectRisk 记录

        Returns:
            AutoRiskScanResult
        """
        project = get_or_404(self.db, Project, project_id, detail="项目不存在")
        all_categories = categories or ["SCHEDULE", "COST", "RESOURCE", "QUALITY"]

        detected: List[AutoRiskItem] = []

        detector_map = {
            "SCHEDULE": self._detect_schedule_risks,
            "COST": self._detect_cost_risks,
            "RESOURCE": self._detect_resource_risks,
            "QUALITY": self._detect_quality_risks,
        }

        for cat in all_categories:
            cat = cat.upper()
            detector = detector_map.get(cat)
            if detector:
                try:
                    items = detector(project)
                    detected.extend(items)
                except Exception:
                    logger.exception("检测 %s 风险时出错, project_id=%s", cat, project_id)

        # 过滤低置信度
        detected = [r for r in detected if r.confidence >= min_confidence]

        # 去重：同一项目、同一 risk_type 且已有 IDENTIFIED 状态的风险不再重复创建
        detected = self._deduplicate(project_id, detected)

        # 自动创建风险记录
        created_ids: List[int] = []
        if auto_create and detected:
            created_ids = self._create_risk_records(project, detected)

        # 汇总
        summary: Dict[str, int] = {}
        for r in detected:
            summary[r.risk_category] = summary.get(r.risk_category, 0) + 1

        return AutoRiskScanResult(
            project_id=project_id,
            scanned_at=datetime.now(),
            total_risks_found=len(detected),
            auto_risks=detected,
            created_risk_ids=created_ids,
            summary=summary,
        )

    # ====================================================================
    # 1. 进度风险检测
    # ====================================================================

    def _detect_schedule_risks(self, project: Project) -> List[AutoRiskItem]:
        risks: List[AutoRiskItem] = []

        # --- 1a 里程碑逾期 ---
        overdue_milestones = (
            self.db.query(ProjectMilestone)
            .filter(
                and_(
                    ProjectMilestone.project_id == project.id,
                    ProjectMilestone.planned_date < self.today,
                    ProjectMilestone.status != "COMPLETED",
                    ProjectMilestone.actual_date.is_(None),
                )
            )
            .all()
        )
        for ms in overdue_milestones:
            days_overdue = (self.today - ms.planned_date).days
            confidence = min(0.5 + days_overdue * 0.05, 1.0)
            prob, impact = self._score_by_overdue(days_overdue, ms.is_key)
            risks.append(
                AutoRiskItem(
                    risk_type=AutoRiskType.MILESTONE_OVERDUE,
                    risk_category="SCHEDULE",
                    risk_level=self._level(prob * impact),
                    confidence=round(confidence, 2),
                    risk_name=f"里程碑逾期: {ms.milestone_name}",
                    evidence=f"计划日期 {ms.planned_date}, 已逾期 {days_overdue} 天"
                    + (", 关键里程碑" if ms.is_key else ""),
                    suggestion="立即评估延期原因并制定赶工计划，必要时调整后续里程碑",
                    probability=prob,
                    impact=impact,
                    related_entity_type="milestone",
                    related_entity_id=ms.id,
                )
            )

        # --- 1b 阶段延期趋势 ---
        active_stages = (
            self.db.query(ProjectStage)
            .filter(
                and_(
                    ProjectStage.project_id == project.id,
                    ProjectStage.status == "IN_PROGRESS",
                    ProjectStage.planned_end_date.isnot(None),
                )
            )
            .all()
        )
        for stage in active_stages:
            if not stage.planned_start_date or not stage.planned_end_date:
                continue
            total_days = (stage.planned_end_date - stage.planned_start_date).days or 1
            elapsed_days = (self.today - stage.planned_start_date).days
            time_pct = elapsed_days / total_days * 100
            progress_pct = stage.progress_pct or 0

            # 时间进度比进展快20%+就有风险
            gap = time_pct - progress_pct
            if gap >= 20:
                confidence = min(0.5 + gap * 0.01, 0.95)
                prob = min(int(gap / 15) + 2, 5)
                impact = 3 if stage.stage_order <= 5 else 4
                risks.append(
                    AutoRiskItem(
                        risk_type=AutoRiskType.STAGE_DELAY_TREND,
                        risk_category="SCHEDULE",
                        risk_level=self._level(prob * impact),
                        confidence=round(confidence, 2),
                        risk_name=f"阶段延期趋势: {stage.stage_name}",
                        evidence=(
                            f"时间消耗 {time_pct:.0f}%, 进度仅 {progress_pct}%, "
                            f"偏差 {gap:.0f}%"
                        ),
                        suggestion="分析进度滞后原因，考虑增加资源投入或调整阶段计划",
                        probability=prob,
                        impact=impact,
                        related_entity_type="stage",
                        related_entity_id=stage.id,
                    )
                )

        # --- 1c 关键路径延误（项目整体层面） ---
        if project.planned_end_date and not project.actual_end_date:
            remaining_days = (project.planned_end_date - self.today).days
            progress = float(project.progress_pct or 0)
            remaining_work = 100 - progress
            if remaining_days > 0 and remaining_work > 0:
                needed_rate = remaining_work / remaining_days
                # 如果需要的日均进度 > 2%（正常约 0.5-1%），则有风险
                if needed_rate > 2.0:
                    confidence = min(0.5 + (needed_rate - 2.0) * 0.1, 0.95)
                    prob = min(int(needed_rate), 5)
                    impact = 4
                    risks.append(
                        AutoRiskItem(
                            risk_type=AutoRiskType.CRITICAL_PATH_DELAY,
                            risk_category="SCHEDULE",
                            risk_level=self._level(prob * impact),
                            confidence=round(confidence, 2),
                            risk_name="关键路径延误风险",
                            evidence=(
                                f"剩余 {remaining_days} 天需完成 {remaining_work:.0f}% 工作量, "
                                f"需日均 {needed_rate:.1f}% 进度"
                            ),
                            suggestion="评估关键路径活动，协调资源加速推进或与客户协商调整交付日期",
                            probability=prob,
                            impact=impact,
                        )
                    )
            elif remaining_days <= 0 and progress < 100:
                risks.append(
                    AutoRiskItem(
                        risk_type=AutoRiskType.CRITICAL_PATH_DELAY,
                        risk_category="SCHEDULE",
                        risk_level="CRITICAL",
                        confidence=0.95,
                        risk_name="项目已超期",
                        evidence=(
                            f"计划结束日期 {project.planned_end_date}, "
                            f"已超期 {abs(remaining_days)} 天, 当前进度 {progress:.0f}%"
                        ),
                        suggestion="立即启动应急预案，与客户沟通延期方案",
                        probability=5,
                        impact=5,
                    )
                )

        return risks

    # ====================================================================
    # 2. 成本风险检测
    # ====================================================================

    def _detect_cost_risks(self, project: Project) -> List[AutoRiskItem]:
        risks: List[AutoRiskItem] = []
        budget = float(project.budget_amount or 0)
        actual = float(project.actual_cost or 0)

        if budget <= 0:
            return risks

        # --- 2a 预算执行率超标 ---
        exec_rate = actual / budget * 100
        progress = float(project.progress_pct or 0) or 1.0

        # 成本进度比 > 1.2 表示成本消耗速度明显快于项目进度
        cost_progress_ratio = exec_rate / progress if progress > 0 else 0
        if exec_rate > 80 or cost_progress_ratio > 1.2:
            if exec_rate >= 100:
                prob, impact, confidence = 5, 5, 0.95
            elif exec_rate >= 90:
                prob, impact, confidence = 4, 4, 0.85
            elif cost_progress_ratio > 1.5:
                prob, impact, confidence = 4, 4, 0.80
            else:
                prob, impact, confidence = 3, 3, 0.70

            risks.append(
                AutoRiskItem(
                    risk_type=AutoRiskType.BUDGET_OVERRUN,
                    risk_category="COST",
                    risk_level=self._level(prob * impact),
                    confidence=confidence,
                    risk_name="预算执行率超标",
                    evidence=(
                        f"预算 {budget:,.0f}, 已用 {actual:,.0f} ({exec_rate:.1f}%), "
                        f"项目进度 {progress:.0f}%, 成本进度比 {cost_progress_ratio:.2f}"
                    ),
                    suggestion="审查后续支出计划，识别成本节约机会，必要时申请追加预算",
                    probability=prob,
                    impact=impact,
                )
            )

        # --- 2b 成本增长速率异常 ---
        # 近30天 vs 前30天的成本增长对比
        d30 = self.today - timedelta(days=30)
        d60 = self.today - timedelta(days=60)

        recent_cost = (
            self.db.query(func.coalesce(func.sum(ProjectCost.amount), 0))
            .filter(
                and_(
                    ProjectCost.project_id == project.id,
                    ProjectCost.cost_date >= d30,
                )
            )
            .scalar()
        )
        prev_cost = (
            self.db.query(func.coalesce(func.sum(ProjectCost.amount), 0))
            .filter(
                and_(
                    ProjectCost.project_id == project.id,
                    ProjectCost.cost_date >= d60,
                    ProjectCost.cost_date < d30,
                )
            )
            .scalar()
        )
        recent_cost = float(recent_cost or 0)
        prev_cost = float(prev_cost or 0)

        if prev_cost > 0 and recent_cost > prev_cost * 1.5:
            growth_rate = (recent_cost - prev_cost) / prev_cost * 100
            confidence = min(0.6 + growth_rate / 500, 0.95)
            prob = min(int(growth_rate / 30) + 2, 5)
            risks.append(
                AutoRiskItem(
                    risk_type=AutoRiskType.COST_GROWTH_ABNORMAL,
                    risk_category="COST",
                    risk_level=self._level(prob * 3),
                    confidence=round(confidence, 2),
                    risk_name="成本增长速率异常",
                    evidence=(
                        f"近30天成本 {recent_cost:,.0f}, "
                        f"前30天 {prev_cost:,.0f}, 增长 {growth_rate:.0f}%"
                    ),
                    suggestion="排查异常支出项目，确认是否为阶段性正常波动或异常开支",
                    probability=prob,
                    impact=3,
                )
            )

        # --- 2c 采购订单总额超项目预算占比 ---
        # 统计项目下所有未取消的采购订单总额
        if budget > 0:
            total_po_amount = (
                self.db.query(func.coalesce(func.sum(PurchaseOrder.total_amount), 0))
                .filter(
                    and_(
                        PurchaseOrder.project_id == project.id,
                        PurchaseOrder.status != "CANCELLED",
                    )
                )
                .scalar()
            )
            total_po_amount = float(total_po_amount or 0)
            po_budget_ratio = total_po_amount / budget * 100

            # 采购总额超过项目预算 70% 时预警
            if po_budget_ratio > 70:
                if po_budget_ratio >= 100:
                    prob, confidence = 5, 0.95
                elif po_budget_ratio >= 90:
                    prob, confidence = 4, 0.85
                else:
                    prob, confidence = 3, 0.70

                risks.append(
                    AutoRiskItem(
                        risk_type=AutoRiskType.PURCHASE_OVER_BUDGET,
                        risk_category="COST",
                        risk_level=self._level(prob * 3),
                        confidence=confidence,
                        risk_name="采购总额占预算比例过高",
                        evidence=(
                            f"项目预算 {budget:,.0f}, 采购总额 {total_po_amount:,.0f}, "
                            f"占比 {po_budget_ratio:.1f}%"
                        ),
                        suggestion="审核采购价格合理性，与供应商重新谈判或寻求替代方案",
                        probability=prob,
                        impact=3,
                    )
                )

        return risks

    # ====================================================================
    # 3. 资源风险检测
    # ====================================================================

    def _detect_resource_risks(self, project: Project) -> List[AutoRiskItem]:
        risks: List[AutoRiskItem] = []

        # --- 3a 关键人员负荷过高 ---
        # 查找当前时段内，同一人员跨项目总分配 > 120%
        overloaded = (
            self.db.query(
                ProjectStageResourcePlan.assigned_employee_id,
                func.sum(ProjectStageResourcePlan.allocation_pct),
            )
            .filter(
                and_(
                    ProjectStageResourcePlan.project_id == project.id,
                    ProjectStageResourcePlan.assignment_status == "ASSIGNED",
                    ProjectStageResourcePlan.planned_start <= self.today,
                    ProjectStageResourcePlan.planned_end >= self.today,
                    ProjectStageResourcePlan.assigned_employee_id.isnot(None),
                )
            )
            .group_by(ProjectStageResourcePlan.assigned_employee_id)
            .all()
        )

        # 再查每个人在所有项目中的总分配
        for emp_id, proj_alloc in overloaded:
            total_alloc = (
                self.db.query(func.sum(ProjectStageResourcePlan.allocation_pct))
                .filter(
                    and_(
                        ProjectStageResourcePlan.assigned_employee_id == emp_id,
                        ProjectStageResourcePlan.assignment_status == "ASSIGNED",
                        ProjectStageResourcePlan.planned_start <= self.today,
                        ProjectStageResourcePlan.planned_end >= self.today,
                    )
                )
                .scalar()
            )
            total_alloc = float(total_alloc or 0)
            if total_alloc > 120:
                confidence = min(0.6 + (total_alloc - 120) / 200, 0.95)
                prob = min(int((total_alloc - 100) / 30) + 2, 5)
                risks.append(
                    AutoRiskItem(
                        risk_type=AutoRiskType.KEY_PERSON_OVERLOAD,
                        risk_category="RESOURCE",
                        risk_level=self._level(prob * 3),
                        confidence=round(confidence, 2),
                        risk_name=f"关键人员负荷过高 (员工ID: {emp_id})",
                        evidence=f"当前总分配比例 {total_alloc:.0f}%, 超过 120% 阈值",
                        suggestion="重新评估任务优先级，考虑分担工作或延后非关键任务",
                        probability=prob,
                        impact=3,
                        related_entity_type="employee",
                        related_entity_id=emp_id,
                    )
                )

        # --- 3b 资源冲突未解决 ---
        unresolved_conflicts = (
            self.db.query(ResourceConflict)
            .filter(
                and_(
                    ResourceConflict.is_resolved == 0,
                    ResourceConflict.overlap_end >= self.today,
                )
            )
            .all()
        )
        # 只关注与本项目相关的冲突
        project_plan_ids = {
            p.id
            for p in self.db.query(ProjectStageResourcePlan.id)
            .filter(ProjectStageResourcePlan.project_id == project.id)
            .all()
        }
        for conflict in unresolved_conflicts:
            if conflict.plan_a_id in project_plan_ids or conflict.plan_b_id in project_plan_ids:
                severity_score = {"LOW": 2, "MEDIUM": 3, "HIGH": 4}.get(conflict.severity, 2)
                days_unresolved = (self.today - conflict.overlap_start).days if conflict.overlap_start <= self.today else 0
                confidence = min(0.6 + days_unresolved * 0.02, 0.95)
                risks.append(
                    AutoRiskItem(
                        risk_type=AutoRiskType.RESOURCE_CONFLICT_UNRESOLVED,
                        risk_category="RESOURCE",
                        risk_level=self._level(severity_score * 3),
                        confidence=round(confidence, 2),
                        risk_name=f"资源冲突未解决 (员工ID: {conflict.employee_id})",
                        evidence=(
                            f"重叠期 {conflict.overlap_start}~{conflict.overlap_end}, "
                            f"超额分配 {conflict.over_allocation}%, 严重度 {conflict.severity}"
                        ),
                        suggestion="协调相关项目经理重新安排资源，或申请替代人员",
                        probability=severity_score,
                        impact=3,
                        related_entity_type="resource_conflict",
                        related_entity_id=conflict.id,
                    )
                )

        # --- 3c 核心技能单一依赖 ---
        # 如果某个角色在项目中只有1人且是关键角色
        role_counts = (
            self.db.query(
                ProjectMember.role_code,
                func.count(ProjectMember.id),
            )
            .filter(
                and_(
                    ProjectMember.project_id == project.id,
                    ProjectMember.is_active == True,
                )
            )
            .group_by(ProjectMember.role_code)
            .all()
        )
        critical_roles = {"PM", "TECH_LEAD", "ARCHITECT", "QA_LEAD", "DEV_LEAD"}
        for role_code, count in role_counts:
            if count == 1 and role_code in critical_roles:
                risks.append(
                    AutoRiskItem(
                        risk_type=AutoRiskType.SINGLE_SKILL_DEPENDENCY,
                        risk_category="RESOURCE",
                        risk_level="MEDIUM",
                        confidence=0.70,
                        risk_name=f"核心角色单一依赖: {role_code}",
                        evidence=f"角色 {role_code} 仅有1人承担, 无后备",
                        suggestion="安排备选人员或知识转移，降低人员离岗风险",
                        probability=3,
                        impact=3,
                    )
                )

        return risks

    # ====================================================================
    # 4. 质量风险检测
    # ====================================================================

    def _detect_quality_risks(self, project: Project) -> List[AutoRiskItem]:
        risks: List[AutoRiskItem] = []

        # --- 4a 缺陷率上升 ---
        d30 = self.today - timedelta(days=30)
        d60 = self.today - timedelta(days=60)

        # 需要通过 work_order 关联到项目，这里简化为直接查质检记录
        recent_inspections = (
            self.db.query(
                func.sum(QualityInspection.inspection_qty),
                func.sum(QualityInspection.defect_qty),
            )
            .filter(QualityInspection.inspection_date >= d30)
            .first()
        )
        prev_inspections = (
            self.db.query(
                func.sum(QualityInspection.inspection_qty),
                func.sum(QualityInspection.defect_qty),
            )
            .filter(
                and_(
                    QualityInspection.inspection_date >= d60,
                    QualityInspection.inspection_date < d30,
                )
            )
            .first()
        )

        recent_qty = float(recent_inspections[0] or 0)
        recent_defect = float(recent_inspections[1] or 0)
        prev_qty = float(prev_inspections[0] or 0)
        prev_defect = float(prev_inspections[1] or 0)

        if recent_qty > 0 and prev_qty > 0:
            recent_rate = recent_defect / recent_qty * 100
            prev_rate = prev_defect / prev_qty * 100
            if recent_rate > prev_rate * 1.3 and recent_rate > 5:
                increase = recent_rate - prev_rate
                confidence = min(0.6 + increase / 50, 0.95)
                prob = min(int(recent_rate / 5) + 2, 5)
                risks.append(
                    AutoRiskItem(
                        risk_type=AutoRiskType.DEFECT_RATE_RISING,
                        risk_category="QUALITY",
                        risk_level=self._level(prob * 3),
                        confidence=round(confidence, 2),
                        risk_name="缺陷率上升",
                        evidence=(
                            f"近30天缺陷率 {recent_rate:.1f}% (前30天 {prev_rate:.1f}%), "
                            f"上升 {increase:.1f}个百分点"
                        ),
                        suggestion="分析缺陷类型分布，加强过程检验，组织质量改善会议",
                        probability=prob,
                        impact=3,
                    )
                )

        # --- 4b 返工次数增加 ---
        recent_rework = (
            self.db.query(func.count(ReworkOrder.id))
            .filter(ReworkOrder.created_at >= d30)
            .scalar()
        ) or 0
        prev_rework = (
            self.db.query(func.count(ReworkOrder.id))
            .filter(
                and_(
                    ReworkOrder.created_at >= d60,
                    ReworkOrder.created_at < d30,
                )
            )
            .scalar()
        ) or 0

        if recent_rework > prev_rework * 1.5 and recent_rework >= 3:
            confidence = min(0.6 + (recent_rework - prev_rework) * 0.05, 0.95)
            prob = min(int(recent_rework / 3) + 2, 5)
            risks.append(
                AutoRiskItem(
                    risk_type=AutoRiskType.REWORK_COUNT_INCREASE,
                    risk_category="QUALITY",
                    risk_level=self._level(prob * 3),
                    confidence=round(confidence, 2),
                    risk_name="返工次数增加",
                    evidence=f"近30天返工 {recent_rework} 次, 前30天 {prev_rework} 次",
                    suggestion="排查返工根因，强化首检和过程控制，必要时暂停生产排查",
                    probability=prob,
                    impact=3,
                )
            )

        # --- 4c 验收一次通过率下降 ---
        recent_acceptance = (
            self.db.query(AcceptanceOrder)
            .filter(
                and_(
                    AcceptanceOrder.project_id == project.id,
                    AcceptanceOrder.created_at >= d60,
                )
            )
            .all()
        )
        if len(recent_acceptance) >= 2:
            recent_items = [a for a in recent_acceptance if a.created_at >= datetime.combine(d30, datetime.min.time())]
            prev_items = [a for a in recent_acceptance if a.created_at < datetime.combine(d30, datetime.min.time())]

            if recent_items and prev_items:
                recent_pass = sum(1 for a in recent_items if a.status == "PASSED") / len(recent_items) * 100
                prev_pass = sum(1 for a in prev_items if a.status == "PASSED") / len(prev_items) * 100

                if prev_pass > 0 and recent_pass < prev_pass * 0.8:
                    drop = prev_pass - recent_pass
                    confidence = min(0.6 + drop / 100, 0.90)
                    prob = min(int(drop / 15) + 2, 5)
                    risks.append(
                        AutoRiskItem(
                            risk_type=AutoRiskType.ACCEPTANCE_PASS_RATE_DROP,
                            risk_category="QUALITY",
                            risk_level=self._level(prob * 4),
                            confidence=round(confidence, 2),
                            risk_name="验收一次通过率下降",
                            evidence=(
                                f"近期通过率 {recent_pass:.0f}% "
                                f"(之前 {prev_pass:.0f}%), 下降 {drop:.0f}%"
                            ),
                            suggestion="加强出厂前内部验收，复盘未通过项分析根因",
                            probability=prob,
                            impact=4,
                        )
                    )

        return risks

    # ====================================================================
    # 去重 & 创建记录
    # ====================================================================

    def _deduplicate(
        self, project_id: int, items: List[AutoRiskItem]
    ) -> List[AutoRiskItem]:
        """跳过已存在同类型且尚未关闭的自动识别风险"""
        existing_names = set(
            r.risk_name
            for r in self.db.query(ProjectRisk.risk_name)
            .filter(
                and_(
                    ProjectRisk.project_id == project_id,
                    ProjectRisk.status.notin_([RiskStatusEnum.CLOSED, RiskStatusEnum.MITIGATED]),
                    ProjectRisk.description.like("%[系统识别]%"),
                )
            )
            .all()
        )
        return [item for item in items if item.risk_name not in existing_names]

    def _create_risk_records(
        self, project: Project, items: List[AutoRiskItem]
    ) -> List[int]:
        """将检测到的风险批量写入 ProjectRisk 表"""
        from app.services.project_risk.project_risk_service import ProjectRiskService

        risk_svc = ProjectRiskService(self.db)
        created_ids: List[int] = []

        for item in items:
            risk_code = risk_svc.generate_risk_code(project.id)
            risk_type = _RISK_TYPE_MAP.get(item.risk_category, RiskTypeEnum.TECHNICAL)

            risk = ProjectRisk(
                risk_code=risk_code,
                project_id=project.id,
                risk_name=item.risk_name,
                description=(
                    f"[系统识别] 置信度: {item.confidence:.0%}\n"
                    f"证据: {item.evidence}\n"
                    f"建议: {item.suggestion}"
                ),
                risk_type=risk_type,
                probability=item.probability,
                impact=item.impact,
                mitigation_plan=item.suggestion,
                status=RiskStatusEnum.IDENTIFIED,
                owner_id=project.pm_id,
                owner_name=project.pm_name,
                created_by_name="系统自动识别",
            )
            risk.calculate_risk_score()
            save_obj(self.db, risk)
            created_ids.append(risk.id)

        return created_ids

    # ====================================================================
    # 辅助方法
    # ====================================================================

    @staticmethod
    def _level(score: int) -> str:
        if score <= 4:
            return "LOW"
        elif score <= 9:
            return "MEDIUM"
        elif score <= 15:
            return "HIGH"
        return "CRITICAL"

    @staticmethod
    def _score_by_overdue(days: int, is_key: bool) -> tuple:
        """根据逾期天数和是否关键里程碑返回 (概率, 影响)"""
        if days <= 3:
            prob = 3
        elif days <= 7:
            prob = 4
        else:
            prob = 5

        if is_key:
            impact = min(prob + 1, 5)
        else:
            impact = max(prob - 1, 2)

        return prob, impact
