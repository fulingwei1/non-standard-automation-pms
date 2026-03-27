# -*- coding: utf-8 -*-
"""
预算执行预警服务

整合：
1. 预算执行率监控（已发生/已承诺/预计总成本 vs 预算）
2. 分级预警（黄80% / 橙90% / 红100%）
3. 成本趋势预测（执行速率 + 剩余工作量 + 历史偏差）
4. 预警推送（项目负责人 + 财务/PMO + 动作中心）
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.alert import AlertRecord, AlertRule
from app.models.budget import ProjectBudget
from app.models.enums import AlertLevelEnum, AlertRuleTypeEnum, AlertStatusEnum
from app.models.outsourcing import OutsourcingOrder
from app.models.project import Project, ProjectCost
from app.models.project.financial import FinancialProjectCost
from app.models.purchase import PurchaseOrder
from app.schemas.budget_alert import (
    BudgetAlertConfig,
    BudgetAlertInfo,
    BudgetMonitorSummary,
    BudgetStatusResponse,
    CostBreakdown,
    CostTrendPoint,
    CostTrendPrediction,
    ExecutionRates,
)

logger = logging.getLogger(__name__)

# 已完成/已到货的 PO 状态（成本已发生）
_PO_SETTLED_STATUSES = {"COMPLETED", "RECEIVED", "CLOSED", "SETTLED"}
# 已下单但未完成的 PO 状态（已承诺成本）
_PO_COMMITTED_STATUSES = {"APPROVED", "CONFIRMED", "IN_PROGRESS", "PARTIAL", "ORDERED"}


class BudgetAlertService:
    """预算执行预警服务"""

    def __init__(self, db: Session):
        self.db = db

    # ================================================================
    # 1. 核心入口 — 获取项目预算执行状态
    # ================================================================

    def get_budget_status(
        self,
        project_id: int,
        include_trend: bool = False,
        config: Optional[BudgetAlertConfig] = None,
    ) -> Optional[BudgetStatusResponse]:
        """
        获取单个项目的预算执行状态（主入口）

        Returns:
            BudgetStatusResponse 或 None（项目不存在/无预算）
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None

        budget_amount = self._get_budget_amount(project_id, project)
        if budget_amount <= 0:
            return None

        config = config or BudgetAlertConfig()

        # 成本分解
        actual_cost = self._get_actual_cost(project_id, project)
        committed_cost = self._get_committed_cost(project_id)
        forecast_remaining = self._estimate_remaining_cost(
            project, actual_cost, committed_cost, budget_amount
        )
        total_forecast = actual_cost + committed_cost + forecast_remaining

        cost_breakdown = CostBreakdown(
            actual_cost=Decimal(str(actual_cost)),
            committed_cost=Decimal(str(committed_cost)),
            forecast_remaining=Decimal(str(max(forecast_remaining, 0))),
            total_forecast=Decimal(str(total_forecast)),
        )

        # 执行率
        actual_rate = (actual_cost / budget_amount * 100) if budget_amount > 0 else 0
        committed_rate = (
            ((actual_cost + committed_cost) / budget_amount * 100) if budget_amount > 0 else 0
        )
        forecast_rate = (total_forecast / budget_amount * 100) if budget_amount > 0 else 0

        execution_rates = ExecutionRates(
            actual_rate=Decimal(str(round(actual_rate, 2))),
            committed_rate=Decimal(str(round(committed_rate, 2))),
            forecast_rate=Decimal(str(round(forecast_rate, 2))),
        )

        # 预警判定
        alert_info = self._determine_alert(
            actual_rate, committed_rate, forecast_rate, config
        )

        # 预测偏差
        forecast_variance = round((total_forecast - budget_amount) / budget_amount * 100, 2)

        # 趋势预测（可选）
        trend_prediction = None
        trend_data = None
        if include_trend:
            trend_data = self._get_monthly_trend(project_id)
            trend_prediction = self._predict_trend(
                project, actual_cost, budget_amount, trend_data
            )

        return BudgetStatusResponse(
            project_id=project_id,
            project_code=project.project_code,
            project_name=project.project_name,
            budget_amount=Decimal(str(budget_amount)),
            execution_rate=Decimal(str(round(actual_rate, 2))),
            forecast_variance=Decimal(str(forecast_variance)),
            alert_level=alert_info.alert_level,
            cost_breakdown=cost_breakdown,
            execution_rates=execution_rates,
            alert_info=alert_info,
            trend_prediction=trend_prediction,
            trend_data=trend_data,
        )

    # ================================================================
    # 2. 批量监控
    # ================================================================

    def monitor_all(
        self,
        project_ids: Optional[List[int]] = None,
        include_trend: bool = False,
        config: Optional[BudgetAlertConfig] = None,
    ) -> BudgetMonitorSummary:
        """批量监控项目预算执行"""
        if project_ids:
            projects = self.db.query(Project).filter(Project.id.in_(project_ids)).all()
        else:
            projects = self.db.query(Project).filter(Project.is_active).all()

        results: List[BudgetStatusResponse] = []
        counts = {"GREEN": 0, "YELLOW": 0, "ORANGE": 0, "RED": 0}

        for project in projects:
            status = self.get_budget_status(project.id, include_trend, config)
            if status:
                results.append(status)
                counts[status.alert_level] = counts.get(status.alert_level, 0) + 1

        return BudgetMonitorSummary(
            total_projects=len(results),
            green_count=counts["GREEN"],
            yellow_count=counts["YELLOW"],
            orange_count=counts["ORANGE"],
            red_count=counts["RED"],
            projects=results,
        )

    # ================================================================
    # 3. 检查并触发预警（含推送）
    # ================================================================

    def check_and_alert(
        self,
        project_id: int,
        trigger_source: Optional[str] = None,
        source_id: Optional[int] = None,
        config: Optional[BudgetAlertConfig] = None,
    ) -> Optional[AlertRecord]:
        """
        检查项目预算执行并在超阈值时创建预警记录 + 推送通知

        适合在成本归集后调用（采购入库/工时提交/费用报销时）。
        """
        status = self.get_budget_status(project_id, include_trend=True, config=config)
        if not status or status.alert_level == "GREEN":
            return None

        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None

        # 映射到系统 AlertLevel
        level_map = {
            "YELLOW": AlertLevelEnum.WARNING.value,
            "ORANGE": AlertLevelEnum.CRITICAL.value,
            "RED": AlertLevelEnum.URGENT.value,
        }
        alert_level = level_map.get(status.alert_level, AlertLevelEnum.WARNING.value)

        # 获取/创建预警规则
        alert_rule = self._get_or_create_budget_alert_rule()

        # 去重：同项目同级别 PENDING 预警不重复创建
        existing = (
            self.db.query(AlertRecord)
            .filter(
                AlertRecord.target_type == "PROJECT",
                AlertRecord.target_id == project_id,
                AlertRecord.rule_id == alert_rule.id,
                AlertRecord.alert_level == alert_level,
                AlertRecord.status == AlertStatusEnum.PENDING.value,
            )
            .first()
        )

        # 构建预警内容
        alert_title, alert_content = self._build_alert_message(status)

        if existing:
            # 更新内容和触发时间
            existing.alert_content = alert_content
            existing.alert_title = alert_title
            existing.triggered_at = datetime.now()
            existing.alert_data = self._build_alert_data(status)
            self.db.add(existing)
            return existing

        # 创建新预警
        from app.services.budget_execution_check_service import generate_alert_no

        alert_record = AlertRecord(
            alert_no=generate_alert_no(self.db),
            rule_id=alert_rule.id,
            target_type="PROJECT",
            target_id=project_id,
            target_no=project.project_code,
            target_name=project.project_name,
            project_id=project_id,
            alert_level=alert_level,
            alert_title=alert_title,
            alert_content=alert_content,
            alert_data=self._build_alert_data(status),
            status=AlertStatusEnum.PENDING.value,
            triggered_at=datetime.now(),
            trigger_value=str(round(float(status.execution_rate), 2)),
            threshold_value=str(
                self._threshold_for_level(status.alert_level, config or BudgetAlertConfig())
            ),
        )
        self.db.add(alert_record)
        self.db.flush()

        # 推送通知
        self._dispatch_notifications(alert_record, project, status)

        return alert_record

    # ================================================================
    # 内部方法 — 数据获取
    # ================================================================

    def _get_budget_amount(self, project_id: int, project: Project) -> float:
        """获取项目有效预算额"""
        budget = (
            self.db.query(ProjectBudget)
            .filter(
                ProjectBudget.project_id == project_id,
                ProjectBudget.is_active,
                ProjectBudget.status == "APPROVED",
            )
            .order_by(ProjectBudget.version.desc())
            .first()
        )
        return float(budget.total_amount) if budget else float(project.budget_amount or 0)

    def _get_actual_cost(self, project_id: int, project: Project) -> float:
        """已发生成本 = ProjectCost + FinancialProjectCost"""
        # 业务成本
        biz_total = (
            self.db.query(func.coalesce(func.sum(ProjectCost.amount), 0))
            .filter(ProjectCost.project_id == project_id)
            .scalar()
        )
        # 财务成本
        fin_total = (
            self.db.query(func.coalesce(func.sum(FinancialProjectCost.amount), 0))
            .filter(FinancialProjectCost.project_id == project_id)
            .scalar()
        )
        total = float(biz_total) + float(fin_total)
        # 如果项目上有冗余字段且更大，以其为准
        if project.actual_cost and float(project.actual_cost) > total:
            return float(project.actual_cost)
        return total

    def _get_committed_cost(self, project_id: int) -> float:
        """已承诺成本 = 已下单未完成的采购单 + 外协单金额"""
        # 采购已承诺
        po_committed = (
            self.db.query(func.coalesce(func.sum(PurchaseOrder.total_amount), 0))
            .filter(
                PurchaseOrder.project_id == project_id,
                PurchaseOrder.status.in_(list(_PO_COMMITTED_STATUSES)),
            )
            .scalar()
        )
        # 外协已承诺
        oo_committed = (
            self.db.query(func.coalesce(func.sum(OutsourcingOrder.total_amount), 0))
            .filter(
                OutsourcingOrder.project_id == project_id,
                OutsourcingOrder.status.in_(list(_PO_COMMITTED_STATUSES)),
            )
            .scalar()
        )
        return float(po_committed) + float(oo_committed)

    def _estimate_remaining_cost(
        self,
        project: Project,
        actual_cost: float,
        committed_cost: float,
        budget_amount: float,
    ) -> float:
        """
        估算剩余成本

        策略：基于完成进度线性外推
        - 已消耗 = 已发生 + 已承诺
        - 如果进度 > 0: 预计总成本 = 已消耗 / 进度%
        - 否则退化为预算剩余
        """
        consumed = actual_cost + committed_cost
        progress = float(project.progress_pct or 0)

        if progress > 0 and progress < 100:
            # 线性外推
            estimated_total = consumed / (progress / 100)
            remaining = max(estimated_total - consumed, 0)
        elif progress >= 100:
            remaining = 0
        else:
            # 无进度信息，使用预算剩余
            remaining = max(budget_amount - consumed, 0)

        return remaining

    # ================================================================
    # 内部方法 — 预警判定
    # ================================================================

    def _determine_alert(
        self,
        actual_rate: float,
        committed_rate: float,
        forecast_rate: float,
        config: BudgetAlertConfig,
    ) -> BudgetAlertInfo:
        """
        分级预警判定

        用三个维度中最高级别作为最终预警：
        - 已发生执行率
        - 已发生+已承诺执行率
        - 预计总成本执行率
        """
        yellow = float(config.yellow_threshold)
        orange = float(config.orange_threshold)
        red = float(config.red_threshold)

        def _rate_level(rate: float) -> int:
            if rate >= red:
                return 3  # RED
            elif rate >= orange:
                return 2  # ORANGE
            elif rate >= yellow:
                return 1  # YELLOW
            return 0  # GREEN

        levels = {
            "actual": _rate_level(actual_rate),
            "committed": _rate_level(committed_rate),
            "forecast": _rate_level(forecast_rate),
        }
        max_level = max(levels.values())
        level_names = {0: "GREEN", 1: "YELLOW", 2: "ORANGE", 3: "RED"}

        # 构建原因
        reasons: List[str] = []
        if levels["actual"] >= 1:
            reasons.append(f"已发生成本执行率 {actual_rate:.1f}%")
        if levels["committed"] >= 1:
            reasons.append(f"已发生+已承诺成本执行率 {committed_rate:.1f}%")
        if levels["forecast"] >= 1:
            reasons.append(f"预计总成本执行率 {forecast_rate:.1f}%")
        if not reasons:
            reasons.append("预算执行情况正常")

        # 建议措施
        actions: List[str] = []
        if max_level >= 3:
            actions.extend([
                "立即暂停非必要支出",
                "召开预算超支专题会议",
                "评估是否需要追加预算或缩减范围",
            ])
        elif max_level >= 2:
            actions.extend([
                "审查即将发生的大额支出",
                "与项目经理确认剩余工作量",
                "启动成本优化措施",
            ])
        elif max_level >= 1:
            actions.extend([
                "关注后续成本发生节奏",
                "检查是否有可延后的支出",
            ])

        return BudgetAlertInfo(
            alert_level=level_names[max_level],
            alert_reasons=reasons,
            recommended_actions=actions,
        )

    # ================================================================
    # 内部方法 — 成本趋势预测
    # ================================================================

    def _get_monthly_trend(self, project_id: int) -> List[CostTrendPoint]:
        """获取月度成本趋势"""
        # 业务成本按月
        biz_monthly = (
            self.db.query(
                func.to_char(ProjectCost.cost_date, "YYYY-MM").label("month"),
                func.sum(ProjectCost.amount).label("amount"),
            )
            .filter(ProjectCost.project_id == project_id, ProjectCost.cost_date.isnot(None))
            .group_by(func.to_char(ProjectCost.cost_date, "YYYY-MM"))
            .all()
        )

        # 财务成本按月
        fin_monthly = (
            self.db.query(
                func.coalesce(FinancialProjectCost.cost_month, func.to_char(FinancialProjectCost.cost_date, "YYYY-MM")).label("month"),
                func.sum(FinancialProjectCost.amount).label("amount"),
            )
            .filter(FinancialProjectCost.project_id == project_id)
            .group_by(
                func.coalesce(FinancialProjectCost.cost_month, func.to_char(FinancialProjectCost.cost_date, "YYYY-MM"))
            )
            .all()
        )

        # 合并
        monthly: Dict[str, float] = {}
        for row in biz_monthly:
            if row.month:
                monthly[row.month] = monthly.get(row.month, 0) + float(row.amount or 0)
        for row in fin_monthly:
            if row.month:
                monthly[row.month] = monthly.get(row.month, 0) + float(row.amount or 0)

        if not monthly:
            return []

        # 排序并计算累计
        sorted_months = sorted(monthly.keys())
        cumulative = Decimal("0")
        points: List[CostTrendPoint] = []
        for m in sorted_months:
            amt = Decimal(str(round(monthly[m], 2)))
            cumulative += amt
            points.append(CostTrendPoint(month=m, actual_cost=amt, cumulative_cost=cumulative))

        return points

    def _predict_trend(
        self,
        project: Project,
        actual_cost: float,
        budget_amount: float,
        trend_data: List[CostTrendPoint],
    ) -> Optional[CostTrendPrediction]:
        """
        成本趋势预测

        基于：
        - 当前执行速率（月均消耗）
        - 剩余工作量（按进度估算）
        - 历史类似项目偏差（同部门已完结项目）
        """
        if not trend_data or len(trend_data) < 2:
            return None

        # 月均消耗速率
        total_months = len(trend_data)
        total_actual = float(trend_data[-1].cumulative_cost)
        burn_rate = total_actual / total_months if total_months > 0 else 0

        if burn_rate <= 0:
            return None

        # 预测完工成本
        progress = float(project.progress_pct or 0)
        if progress > 0 and progress < 100:
            estimated_completion = total_actual / (progress / 100)
        else:
            # 基于月均速率 + 剩余月数
            remaining_budget = budget_amount - total_actual
            if project.planned_end_date and project.planned_start_date:
                total_duration_months = max(
                    (project.planned_end_date - project.planned_start_date).days / 30, 1
                )
                elapsed_months = max(
                    (date.today() - project.planned_start_date).days / 30, 1
                )
                remaining_months = max(total_duration_months - elapsed_months, 0)
                estimated_completion = total_actual + burn_rate * remaining_months
            else:
                estimated_completion = total_actual + remaining_budget

        # 预算耗尽月数
        months_to_exhaust = None
        if burn_rate > 0 and total_actual < budget_amount:
            months_to_exhaust = round((budget_amount - total_actual) / burn_rate, 1)

        # 趋势方向：对比最近3个月的月均与前期
        if len(trend_data) >= 4:
            recent_avg = sum(float(p.actual_cost) for p in trend_data[-3:]) / 3
            earlier_avg = sum(float(p.actual_cost) for p in trend_data[:-3]) / max(
                len(trend_data) - 3, 1
            )
            if recent_avg < earlier_avg * 0.9:
                direction = "IMPROVING"
            elif recent_avg > earlier_avg * 1.1:
                direction = "WORSENING"
            else:
                direction = "STABLE"
        else:
            direction = "STABLE"

        # 历史偏差：查询同部门已完结项目的平均 (actual/budget) 比
        historical_deviation = self._get_historical_deviation(project)

        # 置信度：数据越多越高，最高 90
        confidence = min(30 + total_months * 10, 90)

        return CostTrendPrediction(
            monthly_burn_rate=Decimal(str(round(burn_rate, 2))),
            estimated_completion_cost=Decimal(str(round(estimated_completion, 2))),
            months_to_budget_exhaust=(
                Decimal(str(months_to_exhaust)) if months_to_exhaust is not None else None
            ),
            historical_deviation_pct=(
                Decimal(str(round(historical_deviation, 2)))
                if historical_deviation is not None
                else None
            ),
            trend_direction=direction,
            confidence=Decimal(str(confidence)),
        )

    def _get_historical_deviation(self, project: Project) -> Optional[float]:
        """查同部门已完结项目的预算偏差均值"""
        if not project.dept_id:
            return None

        completed_projects = (
            self.db.query(Project)
            .filter(
                Project.dept_id == project.dept_id,
                Project.id != project.id,
                Project.status.in_(["COMPLETED", "CLOSED"]),
                Project.budget_amount > 0,
                Project.actual_cost > 0,
            )
            .limit(20)
            .all()
        )

        if not completed_projects:
            return None

        deviations = []
        for p in completed_projects:
            budget = float(p.budget_amount)
            actual = float(p.actual_cost)
            if budget > 0:
                deviations.append((actual - budget) / budget * 100)

        return sum(deviations) / len(deviations) if deviations else None

    # ================================================================
    # 内部方法 — 预警记录
    # ================================================================

    def _get_or_create_budget_alert_rule(self) -> AlertRule:
        """获取或创建预算超支预警规则"""
        rule = (
            self.db.query(AlertRule)
            .filter(AlertRule.rule_code == "BUDGET_EXECUTION", AlertRule.is_enabled)
            .first()
        )
        if not rule:
            # 尝试复用旧的 COST_OVERRUN 规则
            rule = (
                self.db.query(AlertRule)
                .filter(AlertRule.rule_code == "COST_OVERRUN", AlertRule.is_enabled)
                .first()
            )
        if not rule:
            rule = AlertRule(
                rule_code="BUDGET_EXECUTION",
                rule_name="预算执行预警",
                rule_type=AlertRuleTypeEnum.COST_OVERRUN.value,
                target_type="PROJECT",
                condition_type="THRESHOLD",
                condition_operator="GT",
                threshold_value="80",
                alert_level=AlertLevelEnum.WARNING.value,
                is_enabled=True,
                is_system=True,
                description="当项目预算执行率超过阈值时触发分级预警（黄80%/橙90%/红100%）",
                notify_channels=["SYSTEM", "EMAIL"],
                notify_roles=["PROJECT_MANAGER", "FINANCE", "PMO"],
            )
            self.db.add(rule)
            self.db.flush()
        return rule

    def _build_alert_message(self, status: BudgetStatusResponse) -> Tuple[str, str]:
        """构建预警标题和内容"""
        level_labels = {
            "YELLOW": "黄色预警",
            "ORANGE": "橙色预警",
            "RED": "红色预警（已超支）",
        }
        label = level_labels.get(status.alert_level, "预警")
        title = f"预算执行{label}：{status.project_name}"

        lines = [
            f"项目 {status.project_code} 预算执行{label}",
            f"预算总额：{status.budget_amount:,.2f}",
            f"已发生成本：{status.cost_breakdown.actual_cost:,.2f}（执行率 {status.execution_rates.actual_rate}%）",
            f"已承诺成本：{status.cost_breakdown.committed_cost:,.2f}",
            f"预计总成本：{status.cost_breakdown.total_forecast:,.2f}（偏差 {status.forecast_variance}%）",
        ]
        if status.alert_info.alert_reasons:
            lines.append("预警原因：" + "；".join(status.alert_info.alert_reasons))

        return title, "\n".join(lines)

    def _build_alert_data(self, status: BudgetStatusResponse) -> dict:
        """构建预警数据（JSON 存储在 alert_data 字段）"""
        return {
            "budget_amount": float(status.budget_amount),
            "actual_cost": float(status.cost_breakdown.actual_cost),
            "committed_cost": float(status.cost_breakdown.committed_cost),
            "forecast_remaining": float(status.cost_breakdown.forecast_remaining),
            "total_forecast": float(status.cost_breakdown.total_forecast),
            "execution_rate": float(status.execution_rate),
            "committed_rate": float(status.execution_rates.committed_rate),
            "forecast_rate": float(status.execution_rates.forecast_rate),
            "forecast_variance": float(status.forecast_variance),
            "alert_level": status.alert_level,
        }

    def _threshold_for_level(self, level: str, config: BudgetAlertConfig) -> float:
        mapping = {
            "YELLOW": float(config.yellow_threshold),
            "ORANGE": float(config.orange_threshold),
            "RED": float(config.red_threshold),
        }
        return mapping.get(level, 80)

    # ================================================================
    # 内部方法 — 推送通知
    # ================================================================

    def _dispatch_notifications(
        self,
        alert_record: AlertRecord,
        project: Project,
        status: BudgetStatusResponse,
    ) -> None:
        """
        推送预警通知：
        1. 项目负责人 — 站内信 + 邮件
        2. 财务/PMO — 站内信
        3. 动作中心待办
        """
        try:
            from app.services.notification_dispatcher import NotificationDispatcher

            dispatcher = NotificationDispatcher(self.db)

            # 收集通知目标用户
            recipient_ids: List[int] = []

            # (a) 项目经理
            if project.pm_id:
                recipient_ids.append(project.pm_id)

            # (b) 部门负责人（代表 PMO）
            if project.dept_id:
                from app.models.department import Department

                dept = self.db.query(Department).filter(Department.id == project.dept_id).first()
                if dept and hasattr(dept, "manager_id") and dept.manager_id:
                    if dept.manager_id not in recipient_ids:
                        recipient_ids.append(dept.manager_id)

            # 为每个接收人创建系统通知（动作中心待办）
            for uid in recipient_ids:
                dispatcher.create_system_notification(
                    recipient_id=uid,
                    notification_type="BUDGET_ALERT",
                    title=alert_record.alert_title,
                    content=alert_record.alert_content,
                    source_type="alert",
                    source_id=alert_record.id,
                    link_url=f"/projects/{project.id}/costs/budget",
                    priority="URGENT" if status.alert_level == "RED" else "HIGH",
                    extra_data=self._build_alert_data(status),
                )

            logger.info(
                "Budget alert dispatched: project=%s level=%s recipients=%s",
                project.project_code,
                status.alert_level,
                recipient_ids,
            )
        except Exception:
            logger.exception("Failed to dispatch budget alert notifications")
