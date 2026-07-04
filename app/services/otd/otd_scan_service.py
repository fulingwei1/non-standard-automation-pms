# -*- coding: utf-8 -*-
"""
OTD 项目交付智能体 - 每日扫描编排服务

照抄 app/services/project/project_risk_service.py 的 batch_calculate_risks 范式：
遍历执行中项目 → 逐个 10 维检测 → 聚合 severity → 产出 AlertRecord + 推送。

10 维风险检测（对应符哥要求的全部跟踪点 + 7 类预警）：
  1. 采购延期          PurchaseOrder.promised_date 逾期且未收货
  2. 图纸未冻结        TechnicalReview DDR 未通过（代理口径）
  3. 客户变更频繁      ChangeRequest(change_source=CUSTOMER) 近30天计数
  4. BOM 超预算        复用 BudgetAlertService（直接复用）
  5. 现场调试反复      Issue(ACCEPTANCE/QUALITY/TECHNICAL) 近30天计数
  6. 验收资料缺失      复用 ClosureReadinessService（直接复用）
  7. 回款临近条件不齐  ProjectPaymentPlan 临近 + 触发里程碑未完成
  8. 关键节点延期      ProjectMilestone(is_key) 逾期未完成
  9. 进度滞后          project_dashboard_service.calculate_progress_stats
 10. 毛利偏差          复用 ProfitAnalysisService（直接复用）

不新建任何表，不改任何 model。预警走现有 AlertRecord + send_notification_for_alert。
"""

import json
import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.alert import AlertRecord
from app.models.enums import AlertLevelEnum, AlertStatusEnum
from app.models.project import Project
from app.models.project.financial import ProjectMilestone, ProjectPaymentPlan

logger = logging.getLogger(__name__)

# 严重程度排序（数值越大越严重）
SEVERITY_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

# 扫描上限（同步扫描保护，与 ai_delivery.py 一致）
SCAN_LIMIT = 200

# OTD 扫描覆盖的项目生命周期阶段
# S1 需求进入（未真正开始交付）、S9 质保结项（已完结）不纳入交付风险扫描
STAGES_IN_DELIVERY = ["S2", "S3", "S4", "S5", "S6", "S7", "S8"]

# 同一项目同日 OTD 预警去重前缀
_ALERT_NO_PREFIX = "OTD"


class OTDScanService:
    """OTD 项目交付每日扫描编排服务"""

    def __init__(self, db: Session):
        self.db = db
        self._today = date.today()
        # 一次性加载阈值配置（DB 优先，无则 fallback 到代码默认值）
        from app.services.otd.threshold_service import get_active_config

        self.config = get_active_config(db)

    # ================================================================
    # 批量扫描入口（照抄 ProjectRiskService.batch_calculate_risks）
    # ================================================================

    def batch_scan(
        self,
        active_only: bool = True,
        project_ids: Optional[List[int]] = None,
        create_alerts: bool = True,
        create_snapshot: bool = False,
    ) -> Dict[str, Any]:
        """
        批量扫描所有执行中项目的 OTD 风险。

        Args:
            active_only: 仅扫描活跃项目（is_active=True）
            project_ids: 指定项目 ID 列表（优先于 active_only）
            create_alerts: 是否对 HIGH/CRITICAL 产出 AlertRecord 并推送
            create_snapshot: 是否落风险快照（用于趋势分析）。
                定时任务和手动 /scan/run 默认 True；只读 GET /scan 默认 False。

        Returns:
            {
                "scanned": N, "with_risk": N, "high_or_critical": N,
                "alerts_created": N, "snapshots_created": N,
                "projects": [...], "timestamp": ...
            }
        """
        query = self.db.query(Project)
        if project_ids:
            query = query.filter(Project.id.in_(project_ids))
        elif active_only:
            query = query.filter(Project.is_active.is_(True))

        # OTD 扫描范围：执行中项目 = 配置的生命周期阶段（默认 S2~S8）
        # （S1 需求进入未真正开始交付、S9 已结项，都不纳入交付风险扫描）
        # 注：Project.status 是 ST01 这类状态码（非 EXECUTING），用 stage 判断更准确。
        stages = self.config.stages_in_delivery or STAGES_IN_DELIVERY
        scan_limit = self.config.scan_limit or SCAN_LIMIT
        query = query.filter(Project.stage.in_(stages))
        query = query.order_by(Project.planned_end_date.asc()).limit(scan_limit)

        projects = query.all()
        results: List[Dict[str, Any]] = []
        with_risk = 0
        high_or_critical = 0
        alerts_created = 0
        snapshots_created = 0

        for project in projects:
            try:
                profile = self.scan_project(project.id)
                results.append(profile)
                if profile["risk_items"]:
                    with_risk += 1
                if profile["severity"] in ("HIGH", "CRITICAL"):
                    high_or_critical += 1
                    if create_alerts:
                        if self._create_alert(project, profile):
                            alerts_created += 1
                if create_snapshot:
                    if self._create_snapshot(project, profile):
                        snapshots_created += 1
            except Exception as e:
                logger.exception("OTD 扫描项目 %s 失败: %s", project.id, e)
                results.append(
                    {
                        "project_id": project.id,
                        "project_code": project.project_code,
                        "name": project.project_name,
                        "error": str(e),
                        "severity": "LOW",
                        "risk_items": [],
                    }
                )

        # 按严重程度降序
        results.sort(
            key=lambda x: SEVERITY_ORDER.get(x.get("severity", "LOW"), 0), reverse=True
        )

        return {
            "scanned": len(projects),
            "with_risk": with_risk,
            "high_or_critical": high_or_critical,
            "alerts_created": alerts_created,
            "snapshots_created": snapshots_created,
            "projects": results[:50],  # 返回前 50 条，避免响应过大
            "timestamp": datetime.now().isoformat(),
        }

    # ================================================================
    # 单项目扫描入口
    # ================================================================

    def scan_project(self, project_id: int) -> Dict[str, Any]:
        """
        对单个项目执行 10 维 OTD 风险检测。

        Returns:
            {
                "project_id", "project_code", "name", "stage", "progress",
                "planned_end", "severity", "risk_items": [...], "suggestion": str
            }
        """
        project = (
            self.db.query(Project).filter(Project.id == project_id).first()
        )
        if not project:
            return {
                "project_id": project_id,
                "project_code": None,
                "name": None,
                "severity": "LOW",
                "risk_items": [{"dim": "meta", "severity": "LOW",
                                "msg": "项目不存在"}],
            }

        risk_items: List[Dict[str, Any]] = []

        # 逐维检测，每维独立 _calc_xxx_factors
        for detector in (
            self._calc_procurement_delay_factors,
            self._calc_design_freeze_factors,
            self._calc_customer_change_factors,
            self._calc_budget_overrun_factors,
            self._calc_field_debug_factors,
            self._calc_acceptance_doc_factors,
            self._calc_payment_condition_factors,
            self._calc_key_milestone_factors,
            self._calc_progress_lag_factors,
            self._calc_margin_deviation_factors,
            self._calc_open_items_factors,
        ):
            try:
                factor = detector(project)
                if factor:
                    risk_items.append(factor)
            except Exception as e:
                # 单维失败不阻塞其他维度
                logger.warning(
                    "OTD 维度 %s 检测失败 项目 %s: %s",
                    getattr(detector, "__name__", "?"),
                    project_id,
                    e,
                )

        # 汇总 severity = 命中维度中的最高级
        severity = "LOW"
        for item in risk_items:
            if SEVERITY_ORDER.get(item.get("severity", "LOW"), 0) > SEVERITY_ORDER.get(
                severity, 0
            ):
                severity = item["severity"]

        profile = {
            "project_id": project.id,
            "project_code": project.project_code,
            "name": project.project_name,
            "stage": project.stage,
            "progress": float(project.progress_pct or 0),
            "planned_end": (
                project.planned_end_date.isoformat()
                if project.planned_end_date
                else None
            ),
            "severity": severity,
            "risk_items": risk_items,
            "suggestion": "",
        }

        # 可选 AI 归因（轻量，照抄 ai_delivery.py:60-64）
        profile["suggestion"] = self._ai_attribution(project, profile)

        return profile

    # ================================================================
    # 10 维检测器
    # ================================================================

    def _calc_procurement_delay_factors(self, project: Project) -> Optional[Dict]:
        """维度1：采购延期。PO.project_id 匹配；promised_date < today 且 received_qty < quantity。"""
        from app.models.purchase import PurchaseOrder, PurchaseOrderItem

        # 关联到项目的采购单明细
        rows = (
            self.db.query(PurchaseOrderItem, PurchaseOrder)
            .join(PurchaseOrder, PurchaseOrderItem.order_id == PurchaseOrder.id)
            .filter(
                PurchaseOrder.project_id == project.id,
                PurchaseOrderItem.promised_date.isnot(None),
                PurchaseOrderItem.promised_date < self._today,
                PurchaseOrderItem.received_qty < PurchaseOrderItem.quantity,
            )
            .all()
        )
        if not rows:
            return None

        # 取最大逾期天数
        max_overdue = max(
            (self._today - (item.promised_date or self._today)).days
            for item, _ in rows
        )
        if max_overdue > (self.config.procurement_overdue_critical_days or 30):
            sev = "CRITICAL"
        elif max_overdue > (self.config.procurement_overdue_high_days or 15):
            sev = "HIGH"
        elif max_overdue > (self.config.procurement_overdue_medium_days or 7):
            sev = "MEDIUM"
        else:
            sev = "LOW"

        return {
            "dim": "procurement_delay",
            "label": "采购延期",
            "severity": sev,
            "msg": f"{len(rows)} 项采购物料逾期，最长 {max_overdue} 天未到货",
            "evidence": {
                "overdue_items": len(rows),
                "max_overdue_days": max_overdue,
            },
        }

    def _calc_design_freeze_factors(self, project: Project) -> Optional[Dict]:
        """维度2：图纸未冻结（代理口径：TechnicalReview DDR 未通过）。"""
        from app.models.technical_review import TechnicalReview

        # 项目 DDR 评审是否通过（conclusion in 配置的通过结论集合 且 status=completed）
        pass_conclusions = self.config.design_review_pass_conclusions or [
            "pass",
            "pass_with_condition",
        ]
        ddr_passed = (
            self.db.query(func.count(TechnicalReview.id))
            .filter(
                TechnicalReview.project_id == project.id,
                TechnicalReview.review_type == "DDR",
                TechnicalReview.status == "completed",
                TechnicalReview.conclusion.in_(pass_conclusions),
            )
            .scalar()
            or 0
        )
        if ddr_passed > 0:
            return None  # DDR 已通过，视为图纸冻结

        stage = project.stage or ""
        check_from = self.config.design_freeze_check_from_stage or "S3"
        high_stage = self.config.design_freeze_high_stage or "S4"
        critical_stage = self.config.design_freeze_critical_stage or "S5"
        # 阶段门禁：早于 check_from 阶段未冻结是正常的，不报
        if not stage or stage < check_from:
            return None

        # 未冻结：按项目阶段判定严重度
        if stage >= critical_stage:
            sev = "CRITICAL"
        elif stage >= high_stage:
            sev = "HIGH"
        else:
            sev = "MEDIUM"

        return {
            "dim": "design_not_frozen",
            "label": "图纸未冻结",
            "severity": sev,
            "msg": "DDR 设计评审未通过（代理口径：无已通过的 DDR 评审记录）",
            "evidence": {
                "ddr_passed_count": ddr_passed,
                "stage": stage,
                "proxy": "用 TechnicalReview DDR 通过代替图纸冻结状态",
            },
        }

    def _calc_customer_change_factors(self, project: Project) -> Optional[Dict]:
        """维度3：客户变更频繁。ChangeRequest(change_source=CUSTOMER) 近期计数。"""
        from app.models.change_request import ChangeRequest

        short_days = self.config.change_window_short_days or 30
        long_days = self.config.change_window_long_days or 90
        critical_cnt = self.config.change_critical_count or 5
        high_cnt = self.config.change_high_count or 3

        since_short = self._today - timedelta(days=short_days)
        since_long = self._today - timedelta(days=long_days)

        count_short = (
            self.db.query(func.count(ChangeRequest.id))
            .filter(
                ChangeRequest.project_id == project.id,
                ChangeRequest.change_source == "CUSTOMER",
                ChangeRequest.created_at >= since_short,
            )
            .scalar()
            or 0
        )
        count_long = (
            self.db.query(func.count(ChangeRequest.id))
            .filter(
                ChangeRequest.project_id == project.id,
                ChangeRequest.change_source == "CUSTOMER",
                ChangeRequest.created_at >= since_long,
            )
            .scalar()
            or 0
        )

        if count_short == 0 and count_long == 0:
            return None

        if count_short >= critical_cnt:
            sev = "CRITICAL"
        elif count_short >= high_cnt:
            sev = "HIGH"
        elif count_long >= high_cnt:
            sev = "MEDIUM"
        else:
            sev = "LOW"

        return {
            "dim": "frequent_customer_change",
            "label": "客户变更频繁",
            "severity": sev,
            "msg": f"客户变更近{short_days}天 {count_short} 次 / 近{long_days}天 {count_long} 次",
            "evidence": {
                f"change_count_{short_days}d": count_short,
                f"change_count_{long_days}d": count_long,
            },
        }

    def _calc_budget_overrun_factors(self, project: Project) -> Optional[Dict]:
        """维度4：BOM 超预算。直接复用 BudgetAlertService.get_budget_status。"""
        from app.services.budget_alert_service import BudgetAlertService

        status = BudgetAlertService(self.db).get_budget_status(project.id)
        if not status or status.alert_level == "GREEN":
            return None

        level_map = {"YELLOW": "LOW", "ORANGE": "MEDIUM", "RED": "HIGH"}
        sev = level_map.get(status.alert_level, "LOW")

        return {
            "dim": "budget_overrun",
            "label": "BOM/成本超预算",
            "severity": sev,
            "msg": (
                f"预算执行率 {status.execution_rates.actual_rate}% / "
                f"预计 {status.execution_rates.forecast_rate}%（{status.alert_level}）"
            ),
            "evidence": {
                "alert_level": status.alert_level,
                "actual_rate": float(status.execution_rates.actual_rate),
                "forecast_rate": float(status.execution_rates.forecast_rate),
                "forecast_variance": float(status.forecast_variance),
            },
        }

    def _calc_field_debug_factors(self, project: Project) -> Optional[Dict]:
        """维度5：现场调试反复。Issue(category in 配置的分类) 近期计数。"""
        from app.models.issue import Issue

        window_days = self.config.debug_window_days or 30
        debug_categories = tuple(
            self.config.debug_categories or ("ACCEPTANCE", "QUALITY", "TECHNICAL")
        )
        high_cnt = self.config.debug_high_count or 5
        medium_cnt = self.config.debug_medium_count or 3

        since_window = self._today - timedelta(days=window_days)

        rows = (
            self.db.query(Issue)
            .filter(
                Issue.project_id == project.id,
                Issue.category.in_(debug_categories),
                Issue.created_at >= since_window,
            )
            .all()
        )
        if not rows:
            return None

        count = len(rows)
        blocking = sum(1 for r in rows if r.is_blocking)

        if blocking > 0 or count >= high_cnt:
            sev = "HIGH"
        elif count >= medium_cnt:
            sev = "MEDIUM"
        else:
            sev = "LOW"

        return {
            "dim": "field_debug_repeat",
            "label": "现场调试反复",
            "severity": sev,
            "msg": f"近{window_days}天调试类问题 {count} 个（阻塞 {blocking} 个）",
            "evidence": {
                f"issue_count_{window_days}d": count,
                "blocking_count": blocking,
                "categories": list(debug_categories),
            },
        }

    def _calc_acceptance_doc_factors(self, project: Project) -> Optional[Dict]:
        """维度6：验收资料缺失。直接复用 ClosureReadinessService.check_readiness。

        阶段门禁：仅在 S6（FAT）及以后阶段，或计划交付日 60 天内才检测。
        早期阶段（S2~S5）项目尚未到验收时点，结项检查必然一堆 missing，
        属正常状态而非风险。
        """
        stage = project.stage or ""
        near_window = self.config.acceptance_near_window_days or 60
        high_window = self.config.acceptance_high_window_days or 30
        check_from_stage = self.config.acceptance_check_from_stage or "S6"
        doc_keywords = self.config.acceptance_doc_keywords or [
            "交付物",
            "文档",
            "验收",
            "客户签署",
            "报告",
        ]

        near_check_window = bool(
            project.planned_end_date
            and (project.planned_end_date - self._today).days <= near_window
        )
        # 配置的起始阶段(默认 S6) 或临近交付才报
        if not (stage >= check_from_stage or near_check_window):
            return None

        from app.services.project.closure_readiness_service import (
            ClosureReadinessService,
        )

        readiness = ClosureReadinessService(self.db).check_readiness(project.id)
        missing = readiness.get("missing_items", [])

        # 仅关注配置关键词覆盖的资料
        doc_missing = [m for m in missing if any(k in m for k in doc_keywords)]
        if not doc_missing:
            return None

        # 临近交付（计划交付日在 high_window 内）仍缺资料 → HIGH
        near_delivery = bool(
            project.planned_end_date
            and (project.planned_end_date - self._today).days <= high_window
        )
        sev = "HIGH" if near_delivery else "MEDIUM"

        return {
            "dim": "acceptance_doc_missing",
            "label": "验收资料缺失",
            "severity": sev,
            "msg": f"结项检查缺失 {len(doc_missing)} 项资料",
            "evidence": {
                "missing": doc_missing[:5],
                "readiness_score": readiness.get("score"),
                "near_delivery": near_delivery,
            },
        }

    def _calc_payment_condition_factors(self, project: Project) -> Optional[Dict]:
        """维度7：回款节点临近但条件不齐。PaymentPlan.planned_date 在配置窗口内 且触发里程碑未完成。"""
        upcoming_days = self.config.payment_upcoming_days or 7
        window_end = self._today + timedelta(days=upcoming_days)
        payment_pending_statuses = (
            self.config.status_sets.get("payment_pending", ["PENDING", "INVOICED"])
            if self.config.status_sets
            else ["PENDING", "INVOICED"]
        )

        plans = (
            self.db.query(ProjectPaymentPlan)
            .filter(
                ProjectPaymentPlan.project_id == project.id,
                ProjectPaymentPlan.planned_date.isnot(None),
                ProjectPaymentPlan.planned_date.between(self._today, window_end),
                ProjectPaymentPlan.status.in_(payment_pending_statuses),
            )
            .all()
        )
        if not plans:
            return None

        unmet = []
        for plan in plans:
            # 触发里程碑未完成
            if plan.milestone_id:
                ms = (
                    self.db.query(ProjectMilestone)
                    .filter(ProjectMilestone.id == plan.milestone_id)
                    .first()
                )
                if ms and ms.status != "COMPLETED":
                    unmet.append(
                        {
                            "payment_no": plan.payment_no,
                            "planned_date": plan.planned_date.isoformat(),
                            "trigger_milestone": plan.trigger_milestone,
                            "milestone_status": ms.status,
                        }
                    )
            else:
                # 有明确 trigger_milestone 文本但无里程碑关联，视为条件待核
                if plan.trigger_milestone or plan.trigger_condition:
                    unmet.append(
                        {
                            "payment_no": plan.payment_no,
                            "planned_date": plan.planned_date.isoformat(),
                            "trigger_milestone": plan.trigger_milestone,
                            "milestone_status": "UNKNOWN",
                        }
                    )

        if not unmet:
            return None

        return {
            "dim": "payment_condition_unmet",
            "label": "回款临近条件不齐",
            "severity": "HIGH",
            "msg": f"{len(unmet)} 个临近回款节点的触发条件未满足",
            "evidence": {"unmet_plans": unmet[:3]},
        }

    def _calc_key_milestone_factors(self, project: Project) -> Optional[Dict]:
        """维度8：关键节点延期。ProjectMilestone(is_key) 逾期未完成。"""
        overdue_keys = (
            self.db.query(ProjectMilestone)
            .filter(
                ProjectMilestone.project_id == project.id,
                ProjectMilestone.is_key.is_(True),
                ProjectMilestone.planned_date.isnot(None),
                ProjectMilestone.planned_date < self._today,
                ProjectMilestone.status != "COMPLETED",
            )
            .all()
        )
        if not overdue_keys:
            return None

        max_overdue = max(
            (self._today - (m.planned_date or self._today)).days
            for m in overdue_keys
        )
        critical_days = self.config.key_milestone_critical_days or 30
        critical_count = self.config.key_milestone_critical_count or 2
        sev = (
            "CRITICAL"
            if max_overdue > critical_days or len(overdue_keys) >= critical_count
            else "HIGH"
        )

        return {
            "dim": "key_milestone_overdue",
            "label": "关键节点延期",
            "severity": sev,
            "msg": f"{len(overdue_keys)} 个关键里程碑逾期，最长 {max_overdue} 天",
            "evidence": {
                "overdue_key_count": len(overdue_keys),
                "max_overdue_days": max_overdue,
                "milestones": [
                    {"name": getattr(m, "name", None), "planned": m.planned_date.isoformat()}
                    for m in overdue_keys[:3]
                ],
            },
        }

    def _calc_progress_lag_factors(self, project: Project) -> Optional[Dict]:
        """维度9：进度滞后。复用 project_dashboard_service.calculate_progress_stats。"""
        from app.services.dashboard.project_dashboard_service import (
            calculate_progress_stats,
        )

        stats = calculate_progress_stats(project, self._today)
        deviation = stats.get("progress_deviation", 0)
        medium_thresh = float(self.config.progress_medium_threshold or -15)
        high_thresh = float(self.config.progress_high_threshold or -25)
        if deviation >= medium_thresh:
            return None

        if deviation < high_thresh:
            sev = "HIGH"
        else:
            sev = "MEDIUM"

        return {
            "dim": "progress_lag",
            "label": "进度滞后",
            "severity": sev,
            "msg": f"进度偏差 {deviation:.1f}%（计划 {stats.get('plan_progress', 0):.1f}% / 实际 {stats.get('actual_progress', 0):.1f}%）",
            "evidence": {
                "progress_deviation": deviation,
                "plan_progress": stats.get("plan_progress"),
                "actual_progress": stats.get("actual_progress"),
                "time_deviation_days": stats.get("time_deviation_days"),
            },
        }

    def _calc_margin_deviation_factors(self, project: Project) -> Optional[Dict]:
        """维度10：毛利偏差。直接复用 ProfitAnalysisService.get_margin_analysis。"""
        # 数据充分性门禁：合同金额<=0 或无成本记录时不报（数据不足，非真实偏差）
        contract_amount = float(project.contract_amount or 0)
        actual_cost = float(project.actual_cost or 0)
        if contract_amount <= 0 and actual_cost <= 0:
            return None

        from app.services.profit_analysis_service import ProfitAnalysisService

        analysis = ProfitAnalysisService(self.db).get_margin_analysis(project.id)
        if not analysis or "error" in analysis:
            return None

        gap = analysis.get("margin_gap", 0)
        medium_thresh = float(self.config.margin_medium_threshold or -3)
        high_thresh = float(self.config.margin_high_threshold or -5)
        critical_thresh = float(self.config.margin_critical_threshold or -10)
        if gap >= medium_thresh:
            return None

        if gap < critical_thresh:
            sev = "CRITICAL"
        elif gap < high_thresh:
            sev = "HIGH"
        else:
            sev = "MEDIUM"

        return {
            "dim": "margin_deviation",
            "label": "毛利偏差",
            "severity": sev,
            "msg": f"毛利偏差 {gap:.1f}%（当前 {analysis.get('current_margin_rate', 0):.1f}% vs 目标 {analysis.get('target_margin_rate', 0):.1f}%）",
            "evidence": {
                "margin_gap": gap,
                "current_margin_rate": analysis.get("current_margin_rate"),
                "forecast_margin_rate": analysis.get("forecast_margin_rate"),
                "target_margin_rate": analysis.get("target_margin_rate"),
            },
        }

    def _calc_open_items_factors(self, project: Project) -> Optional[Dict]:
        """维度11：未关闭事项。

        聚合项目维度所有"还没关闭"的事项：
          - 未关闭 Issue（status 不在 RESOLVED/COMPLETED/CLOSED）
          - 未关闭/未实施完的 ChangeRequest（status 不在 COMPLETED/CLOSED/REJECTED）
          - 未完成里程碑（status 不在 COMPLETED/DONE）
          - 未关闭验收单（AcceptanceOrder.status 为空或非 COMPLETED）

        严重度按"未关闭事项总数 + 是否有阻塞"判定。
        这是符哥原文明确要的"跟踪未关闭事项"维度。
        """
        from app.models.acceptance import AcceptanceOrder
        from app.models.change_request import ChangeRequest
        from app.models.issue import Issue

        status_sets = self.config.status_sets or {}
        issue_closed = set(status_sets.get("issue_closed", ["RESOLVED", "COMPLETED", "CLOSED", "DONE"]))
        change_closed = set(
            status_sets.get("change_closed", ["COMPLETED", "CLOSED", "REJECTED", "CANCELLED"])
        )

        # 1. 未关闭 Issue
        open_issues = (
            self.db.query(Issue)
            .filter(
                Issue.project_id == project.id,
                ~Issue.status.in_(issue_closed),
            )
            .all()
        )
        blocking_issues = sum(1 for i in open_issues if i.is_blocking)

        # 2. 未关闭 ChangeRequest
        open_changes = (
            self.db.query(ChangeRequest)
            .filter(
                ChangeRequest.project_id == project.id,
                ~ChangeRequest.status.in_(change_closed),
            )
            .count()
        )

        # 3. 未完成里程碑（复用 issue_closed 集合，里程碑完成态同义）
        open_milestones = (
            self.db.query(ProjectMilestone)
            .filter(
                ProjectMilestone.project_id == project.id,
                ~ProjectMilestone.status.in_(issue_closed),
            )
            .count()
        )

        # 4. 未关闭验收单
        open_acceptances = (
            self.db.query(AcceptanceOrder)
            .filter(
                AcceptanceOrder.project_id == project.id,
                ~AcceptanceOrder.status.in_(issue_closed),
            )
            .count()
        )

        total_open = (
            len(open_issues) + open_changes + open_milestones + open_acceptances
        )
        if total_open == 0:
            return None

        # 严重度：阻塞事项 > 0 或总数 ≥ high_count → HIGH；≥ medium_count → MEDIUM；否则 LOW
        high_count = self.config.open_items_high_count or 10
        medium_count = self.config.open_items_medium_count or 5
        if blocking_issues > 0 or total_open >= high_count:
            sev = "HIGH"
        elif total_open >= medium_count:
            sev = "MEDIUM"
        else:
            sev = "LOW"

        return {
            "dim": "open_items",
            "label": "未关闭事项",
            "severity": sev,
            "msg": (
                f"未关闭事项 {total_open} 项：问题 {len(open_issues)}（阻塞 {blocking_issues}）/ "
                f"变更 {open_changes} / 里程碑 {open_milestones} / 验收单 {open_acceptances}"
            ),
            "evidence": {
                "total_open": total_open,
                "open_issues": len(open_issues),
                "blocking_issues": blocking_issues,
                "open_changes": open_changes,
                "open_milestones": open_milestones,
                "open_acceptances": open_acceptances,
            },
        }

    # ================================================================
    # AI 归因（可选，照抄 ai_delivery.py:60-64 轻量范式）
    # ================================================================

    def _ai_attribution(self, project: Project, profile: Dict) -> str:
        """对 HIGH/CRITICAL 项目调 AI 一句话归因。失败静默返回空串。"""
        if profile["severity"] not in ("HIGH", "CRITICAL"):
            return ""
        if not profile["risk_items"]:
            return ""
        try:
            from app.services.ai_client_service import (
                AIClientService,
                is_mock_response,
            )

            risk_brief = "; ".join(
                f"{it['label']}({it['severity']}): {it['msg']}"
                for it in profile["risk_items"][:5]
            )
            resp = AIClientService().generate_solution(
                prompt=(
                    f"你是非标设备公司的 PMO 总监。项目 {project.project_code} "
                    f"({project.project_name}) 有以下 OTD 交付风险: {risk_brief}。"
                    f"用一句话(40字内)点出最该先干预什么。只输出这句话。"
                ),
                model="qwen3-coder-plus",
                temperature=0.3,
                max_tokens=120,
            )
            if is_mock_response(resp):
                return ""
            return (resp.get("content") or "").strip().split("\n")[0][:60]
        except Exception as e:
            logger.warning("OTD AI 归因失败 项目 %s: %s", project.id, e)
            return ""

    # ================================================================
    # 预警产出 + 推送（照抄 _send_risk_upgrade_notification 范式）
    # ================================================================

    def _create_alert(self, project: Project, profile: Dict) -> bool:
        """
        对 HIGH/CRITICAL 项目创建 AlertRecord + 即时推送（站内 + 邮件）。
        同项目同日去重。失败不影响主流程。返回是否新建。
        """
        try:
            severity = profile["severity"]
            today_str = self._today.strftime("%Y%m%d")

            # 同项目同日 OTD 预警去重
            existing = (
                self.db.query(AlertRecord)
                .filter(
                    AlertRecord.project_id == project.id,
                    AlertRecord.alert_no.like(f"{_ALERT_NO_PREFIX}-{project.id}-{today_str}%"),
                    AlertRecord.status.in_(["PENDING", "OPEN", "ACKNOWLEDGED"]),
                )
                .first()
            )
            if existing:
                return False

            # 取/建 OTD 系统 rule（rule_id 是 NOT NULL，必须填）
            rule_id = self._get_or_create_otd_rule()

            # 级别映射：CRITICAL → CRITICAL；HIGH → WARNING；其余降级不发
            if severity == "CRITICAL":
                alert_level = AlertLevelEnum.CRITICAL.value
            else:
                alert_level = AlertLevelEnum.WARNING.value

            alert_no = (
                f"{_ALERT_NO_PREFIX}-{project.id}-{today_str}-"
                f"{datetime.now().strftime('%H%M')}"
            )

            # 主因摘要
            top = sorted(
                profile["risk_items"],
                key=lambda x: SEVERITY_ORDER.get(x.get("severity", "LOW"), 0),
                reverse=True,
            )[:3]
            main_cause = "、".join(it["label"] for it in top)

            content_lines = [
                f"项目 {project.project_code} ({project.project_name}) "
                f"OTD 风险等级 {severity}，主要风险：{main_cause}。",
            ]
            for it in top:
                content_lines.append(f"  · {it['label']}({it['severity']}): {it['msg']}")
            if profile.get("suggestion"):
                content_lines.append(f"AI 建议：{profile['suggestion']}")
            content_lines.append("请及时关注并采取措施。")

            alert = AlertRecord(
                alert_no=alert_no,
                rule_id=rule_id,
                target_type="PROJECT",
                target_id=project.id,
                target_no=project.project_code,
                target_name=project.project_name,
                project_id=project.id,
                alert_level=alert_level,
                severity=severity,
                alert_title=f"[OTD] {project.project_name} 交付风险（{severity}）",
                alert_content="\n".join(content_lines),
                alert_data={
                    "source": "otd_scan",
                    "severity": severity,
                    "risk_items": profile["risk_items"],
                    "suggestion": profile.get("suggestion", ""),
                },
                status=AlertStatusEnum.PENDING.value,
                triggered_at=datetime.now(),
            )
            self.db.add(alert)
            self.db.flush()

            # 即时推送（站内 + 邮件，复用现有 dispatcher），失败吞掉
            from app.utils.scheduled_tasks.base import send_notification_for_alert

            send_notification_for_alert(self.db, alert, logger)
            return True
        except Exception as e:
            logger.error("创建 OTD 预警失败 项目 %s: %s", project.id, e)
            return False

    # OTD 系统 rule 编码（用于 rule_id NOT NULL 约束）
    _OTD_RULE_CODE = "OTD_DELIVERY_RISK"

    def _get_or_create_otd_rule(self) -> int:
        """
        幂等获取/创建 OTD 系统预警规则。

        AlertRecord.rule_id 是 NOT NULL，必须关联一条 AlertRule。
        OTD 智能体复用一个固定的系统级规则（is_system=True, target_type=PROJECT），
        首次扫描时自动创建，后续复用。零 migration（运行时建数据，不改 schema）。
        """
        from app.models.alert import AlertRule

        rule = (
            self.db.query(AlertRule)
            .filter(AlertRule.rule_code == self._OTD_RULE_CODE)
            .first()
        )
        if rule:
            return rule.id

        rule = AlertRule(
            rule_code=self._OTD_RULE_CODE,
            rule_name="OTD 项目交付风险预警",
            rule_type="CUSTOM",
            target_type="PROJECT",
            condition_type="CUSTOM",
            condition_expr="otd_scan_service 10 维检测聚合判定",
            alert_level="WARNING",
            advance_days=0,
            notify_channels=["SYSTEM", "EMAIL"],
            enforcement_mode="WARN",
            check_frequency="DAILY",
            is_enabled=True,
            is_system=True,
            is_active=True,
            description=(
                "OTD 项目交付智能体系统规则。覆盖 10 维交付风险："
                "采购延期/图纸未冻结/客户变更频繁/BOM超预算/调试反复/"
                "验收资料缺失/回款条件不齐/关键节点延期/进度滞后/毛利偏差。"
                "由 daily_otd_scan 定时任务和 /otd/scan/run 手动触发。"
            ),
            solution_guide="查看 /otd/scan/{project_id} 获取单项目全景与 AI 建议",
        )
        self.db.add(rule)
        self.db.flush()
        logger.info("已创建 OTD 系统预警规则 rule_id=%s", rule.id)
        return rule.id

    # ================================================================
    # 风险快照（用于趋势分析，照抄 ProjectRiskService.create_risk_snapshot 范式）
    # ================================================================

    # 维度名 → 快照列名映射（列式冗余，便于全局聚合）
    _DIM_HIT_FIELDS = {
        "procurement_delay": "procurement_delay_hit",
        "design_not_frozen": "design_not_frozen_hit",
        "frequent_customer_change": "customer_change_hit",
        "budget_overrun": "budget_overrun_hit",
        "field_debug_repeat": "field_debug_hit",
        "acceptance_doc_missing": "acceptance_doc_hit",
        "payment_condition_unmet": "payment_condition_hit",
        "key_milestone_overdue": "key_milestone_hit",
        "progress_lag": "progress_lag_hit",
        "margin_deviation": "margin_deviation_hit",
        "open_items": "open_items_hit",
    }

    def _create_snapshot(self, project: Project, profile: Dict) -> bool:
        """
        落一条 OTD 风险快照。

        同项目同日幂等：已存在则跳过（照抄 project_health_tasks.py:65-75）。
        失败不阻塞主流程（照抄 _create_alert 容错风格）。返回是否新建。
        """
        try:
            from app.models.otd_risk_snapshot import OTDRiskSnapshot

            # 同项目同日幂等去重
            existing = (
                self.db.query(OTDRiskSnapshot)
                .filter(
                    OTDRiskSnapshot.project_id == project.id,
                    OTDRiskSnapshot.snapshot_date == self._today,
                )
                .first()
            )
            if existing:
                return False

            risk_items = profile.get("risk_items", [])
            hit_dims = {it["dim"] for it in risk_items}
            high_count = sum(
                1
                for it in risk_items
                if it.get("severity") in ("HIGH", "CRITICAL")
            )

            # 构造列式命中标记
            hit_flags = {
                field: (dim in hit_dims)
                for dim, field in self._DIM_HIT_FIELDS.items()
            }

            snapshot = OTDRiskSnapshot(
                project_id=project.id,
                snapshot_date=self._today,
                severity=profile.get("severity", "LOW"),
                risk_items_count=len(risk_items),
                high_items_count=high_count,
                risk_items=risk_items,
                suggestion=profile.get("suggestion", ""),
                **hit_flags,
            )
            self.db.add(snapshot)
            self.db.flush()
            return True
        except Exception as e:
            logger.error("创建 OTD 快照失败 项目 %s: %s", project.id, e)
            return False
