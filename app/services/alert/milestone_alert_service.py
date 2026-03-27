# -*- coding: utf-8 -*-
"""
里程碑告警服务

功能：
1. 里程碑到期预警 — 距到期3天(WARNING) / 1天(CRITICAL) 分级预警
2. 里程碑风险前置识别 — 基于进度/资源状态预测可能延期
3. 预警推送 — 通知项目负责人 + 相关资源责任人
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.alert import AlertRecord, AlertRule
from app.models.enums import AlertLevelEnum, AlertRuleTypeEnum, AlertStatusEnum
from app.models.project import ProjectMilestone

logger = logging.getLogger(__name__)


class MilestoneAlertService:
    """里程碑告警服务"""

    # 分级预警阈值（天数 -> 级别）
    DUE_SOON_THRESHOLDS: List[Tuple[int, str]] = [
        (1, AlertLevelEnum.CRITICAL.value),  # 1天内到期 → CRITICAL
        (3, AlertLevelEnum.WARNING.value),   # 3天内到期 → WARNING
    ]

    def __init__(self, db: Session):
        self.db = db

    def check_milestone_alerts(self) -> int:
        """
        里程碑预警服务（主入口）
        每天执行一次，检查即将到期或已逾期的里程碑
        """
        try:
            today = date.today()

            # 获取即将到期和已逾期的里程碑
            upcoming_milestones = self._get_upcoming_milestones(today)
            overdue_milestones = self._get_overdue_milestones(today)

            # 获取或创建预警规则
            due_soon_rule = self._get_or_create_rule(
                rule_code="MILESTONE_DUE_SOON",
                rule_name="里程碑即将到期预警",
                rule_type=AlertRuleTypeEnum.MILESTONE_DUE_SOON.value,
                alert_level=AlertLevelEnum.WARNING.value,
                description="当里程碑将在3天/1天内到期时触发分级预警",
            )
            critical_rule = self._get_or_create_rule(
                rule_code="MILESTONE_OVERDUE",
                rule_name="里程碑逾期预警",
                rule_type=AlertRuleTypeEnum.MILESTONE_DUE.value,
                alert_level=AlertLevelEnum.CRITICAL.value,
                description="当里程碑已逾期时触发预警",
            )

            alert_count = 0

            # 处理即将到期的里程碑（分级: 1天/3天）
            alert_count += self._process_upcoming_milestones(
                upcoming_milestones, due_soon_rule, today, alert_count
            )

            # 处理已逾期的里程碑
            alert_count += self._process_overdue_milestones(
                overdue_milestones, critical_rule, today, alert_count
            )

            logger.info(f"里程碑预警完成，共生成 {alert_count} 条告警")
            return alert_count

        except Exception as e:
            logger.error(f"里程碑预警检查失败: {str(e)}")
            raise

    def check_milestone_risk_alerts(self) -> int:
        """
        里程碑风险前置识别（主入口）
        基于当前进度和资源状态预测可能延期的里程碑
        """
        try:
            today = date.today()
            risk_rule = self._get_or_create_rule(
                rule_code="MILESTONE_AT_RISK",
                rule_name="里程碑延期风险预警",
                rule_type=AlertRuleTypeEnum.MILESTONE_AT_RISK.value,
                alert_level=AlertLevelEnum.WARNING.value,
                description="基于进度/资源状态预测里程碑可能延期",
            )

            # 获取未来14天内到期且未完成的里程碑（排除已有DUE_SOON预警的）
            risk_window = today + timedelta(days=14)
            milestones = (
                self.db.query(ProjectMilestone)
                .filter(
                    and_(
                        ProjectMilestone.status.in_(["PENDING", "IN_PROGRESS"]),
                        ProjectMilestone.planned_date > today + timedelta(days=3),
                        ProjectMilestone.planned_date <= risk_window,
                    )
                )
                .all()
            )

            risk_count = 0
            for milestone in milestones:
                risk_score, risk_reasons = self._assess_milestone_risk(milestone, today)
                if risk_score >= 0.6:  # 风险评分 ≥ 60% 触发预警
                    if self._should_create_alert(milestone, "MILESTONE_RISK"):
                        alert_no = f'MR{today.strftime("%Y%m%d")}{str(risk_count + 1).zfill(4)}'
                        level = (
                            AlertLevelEnum.CRITICAL.value
                            if risk_score >= 0.8
                            else AlertLevelEnum.WARNING.value
                        )
                        reasons_text = "；".join(risk_reasons)
                        days_left = (milestone.planned_date - today).days

                        alert = AlertRecord(
                            alert_no=alert_no,
                            rule_id=risk_rule.id,
                            target_type="MILESTONE_RISK",
                            target_id=milestone.id,
                            target_no=milestone.milestone_code,
                            target_name=milestone.milestone_name,
                            project_id=milestone.project_id,
                            alert_level=level,
                            alert_title=f"里程碑延期风险：{milestone.milestone_name}",
                            alert_content=(
                                f"里程碑 {milestone.milestone_code} 距到期还有 {days_left} 天，"
                                f"风险评分 {risk_score * 100:.0f}%。风险因素：{reasons_text}"
                            ),
                            alert_data={
                                "risk_score": risk_score,
                                "risk_reasons": risk_reasons,
                                "days_left": days_left,
                                "milestone_status": milestone.status,
                            },
                            status=AlertStatusEnum.PENDING.value,
                            triggered_at=datetime.now(),
                            trigger_value=f"{risk_score:.2f}",
                            threshold_value="0.60",
                        )
                        self.db.add(alert)
                        self._dispatch_milestone_notification(alert, milestone)
                        risk_count += 1

            logger.info(f"里程碑风险预警完成，共生成 {risk_count} 条风险预警")
            return risk_count

        except Exception as e:
            logger.error(f"里程碑风险预警检查失败: {str(e)}")
            raise

    # ─── 内部方法：查询 ─────────────────────────────────────────────

    def _get_upcoming_milestones(self, today: date) -> List[ProjectMilestone]:
        """获取即将到期的里程碑（3天内）"""
        warning_date = today + timedelta(days=3)

        return (
            self.db.query(ProjectMilestone)
            .filter(
                and_(
                    ProjectMilestone.status != "COMPLETED",
                    ProjectMilestone.planned_date <= warning_date,
                    ProjectMilestone.planned_date >= today,
                )
            )
            .all()
        )

    def _get_overdue_milestones(self, today: date) -> List[ProjectMilestone]:
        """获取已逾期的里程碑"""
        return (
            self.db.query(ProjectMilestone)
            .filter(
                and_(ProjectMilestone.status != "COMPLETED", ProjectMilestone.planned_date < today)
            )
            .all()
        )

    # ─── 内部方法：规则管理 ─────────────────────────────────────────

    def _get_or_create_rule(
        self,
        rule_code: str,
        rule_name: str,
        rule_type: str,
        alert_level: str,
        description: str,
    ) -> AlertRule:
        """获取或创建预警规则（通用）"""
        rule = (
            self.db.query(AlertRule)
            .filter(and_(AlertRule.rule_code == rule_code, AlertRule.is_enabled))
            .first()
        )

        if not rule:
            rule = AlertRule(
                rule_code=rule_code,
                rule_name=rule_name,
                rule_type=rule_type,
                target_type="MILESTONE",
                condition_type="THRESHOLD",
                condition_operator="LT",
                threshold_value="3",
                alert_level=alert_level,
                is_enabled=True,
                is_system=True,
                notify_channels=["SYSTEM"],
                notify_roles=["PROJECT_MANAGER"],
                description=description,
            )
            self.db.add(rule)
            self.db.flush()

        return rule

    # ─── 内部方法：处理即将到期 ─────────────────────────────────────

    def _process_upcoming_milestones(
        self, milestones: List[ProjectMilestone], rule: AlertRule, today: date, start_count: int
    ) -> int:
        """处理即将到期的里程碑（分级预警：1天/3天）"""
        alert_count = start_count

        for milestone in milestones:
            if self._should_create_alert(milestone, "MILESTONE"):
                days_left = (milestone.planned_date - today).days

                # 根据剩余天数确定预警级别
                alert_level = AlertLevelEnum.WARNING.value
                for threshold_days, level in self.DUE_SOON_THRESHOLDS:
                    if days_left <= threshold_days:
                        alert_level = level
                        break

                alert_no = f'MS{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'

                urgency = "紧急" if days_left <= 1 else ""
                alert = AlertRecord(
                    alert_no=alert_no,
                    rule_id=rule.id,
                    target_type="MILESTONE",
                    target_id=milestone.id,
                    target_no=milestone.milestone_code,
                    target_name=milestone.milestone_name,
                    project_id=milestone.project_id,
                    alert_level=alert_level,
                    alert_title=f"{urgency}里程碑即将到期：{milestone.milestone_name}",
                    alert_content=(
                        f"里程碑 {milestone.milestone_code} 将在 {days_left} 天后到期"
                        f"（计划日期：{milestone.planned_date}）"
                    ),
                    alert_data={
                        "days_left": days_left,
                        "milestone_type": milestone.milestone_type,
                        "is_key": milestone.is_key,
                        "alert_category": "MILESTONE_DUE_SOON",
                    },
                    status=AlertStatusEnum.PENDING.value,
                    triggered_at=datetime.now(),
                    trigger_value=str(days_left),
                    threshold_value="3",
                )
                self.db.add(alert)
                self._dispatch_milestone_notification(alert, milestone)
                alert_count += 1

        return alert_count - start_count

    # ─── 内部方法：处理已逾期 ─────────────────────────────────────

    def _process_overdue_milestones(
        self, milestones: List[ProjectMilestone], rule: AlertRule, today: date, start_count: int
    ) -> int:
        """处理已逾期的里程碑"""
        alert_count = start_count

        for milestone in milestones:
            if self._should_create_alert(milestone, "MILESTONE"):
                days_overdue = (today - milestone.planned_date).days
                alert_no = f'MS{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'

                alert = AlertRecord(
                    alert_no=alert_no,
                    rule_id=rule.id,
                    target_type="MILESTONE",
                    target_id=milestone.id,
                    target_no=milestone.milestone_code,
                    target_name=milestone.milestone_name,
                    project_id=milestone.project_id,
                    alert_level=AlertLevelEnum.CRITICAL.value,
                    alert_title=f"里程碑已逾期：{milestone.milestone_name}",
                    alert_content=(
                        f"里程碑 {milestone.milestone_code} 已逾期 {days_overdue} 天"
                        f"（计划日期：{milestone.planned_date}）"
                    ),
                    alert_data={
                        "days_overdue": days_overdue,
                        "milestone_type": milestone.milestone_type,
                        "is_key": milestone.is_key,
                        "alert_category": "MILESTONE_OVERDUE",
                    },
                    status=AlertStatusEnum.PENDING.value,
                    triggered_at=datetime.now(),
                    trigger_value=str(days_overdue),
                    threshold_value="0",
                )
                self.db.add(alert)
                self._dispatch_milestone_notification(alert, milestone)
                alert_count += 1

        return alert_count - start_count

    # ─── 内部方法：风险评估 ─────────────────────────────────────────

    def _assess_milestone_risk(
        self, milestone: ProjectMilestone, today: date
    ) -> Tuple[float, List[str]]:
        """
        评估里程碑延期风险

        综合评分维度：
        1. 进度偏差 — 关联阶段的实际进度 vs 期望进度
        2. 前置里程碑逾期 — 同项目中更早的里程碑是否已逾期
        3. 里程碑状态 — PENDING(未启动) vs IN_PROGRESS
        4. 是否关键里程碑 — 关键里程碑权重更高
        """
        risk_score = 0.0
        reasons: List[str] = []
        days_left = (milestone.planned_date - today).days

        # 1. 检查前置里程碑是否逾期
        earlier_overdue = (
            self.db.query(func.count(ProjectMilestone.id))
            .filter(
                and_(
                    ProjectMilestone.project_id == milestone.project_id,
                    ProjectMilestone.planned_date < milestone.planned_date,
                    ProjectMilestone.planned_date < today,
                    ProjectMilestone.status != "COMPLETED",
                )
            )
            .scalar()
        )
        if earlier_overdue and earlier_overdue > 0:
            risk_score += 0.35
            reasons.append(f"有 {earlier_overdue} 个前置里程碑已逾期")

        # 2. 里程碑状态风险
        if milestone.status == "PENDING" and days_left <= 7:
            risk_score += 0.3
            reasons.append(f"距到期 {days_left} 天但仍未启动")
        elif milestone.status == "PENDING" and days_left <= 14:
            risk_score += 0.15
            reasons.append(f"距到期 {days_left} 天尚未启动")

        # 3. 检查关联阶段进度（如有 stage_code）
        if milestone.stage_code:
            from app.models.pmo.initiation_phase import PmoProjectPhase

            phase = (
                self.db.query(PmoProjectPhase)
                .filter(
                    and_(
                        PmoProjectPhase.project_id == milestone.project_id,
                        PmoProjectPhase.phase_code == milestone.stage_code,
                    )
                )
                .first()
            )
            if phase and phase.progress is not None:
                # 计算期望进度
                if phase.plan_start_date and phase.plan_end_date:
                    total = (phase.plan_end_date - phase.plan_start_date).days
                    elapsed = (today - phase.plan_start_date).days
                    if total > 0:
                        expected_progress = min(max((elapsed / total) * 100, 0), 100)
                        actual_progress = phase.progress or 0
                        gap = expected_progress - actual_progress
                        if gap > 20:
                            risk_score += 0.25
                            reasons.append(f"阶段进度落后 {gap:.0f}%（期望 {expected_progress:.0f}%，实际 {actual_progress}%）")
                        elif gap > 10:
                            risk_score += 0.1
                            reasons.append(f"阶段进度轻微落后 {gap:.0f}%")

        # 4. 关键里程碑加权
        if milestone.is_key and risk_score > 0:
            risk_score = min(risk_score * 1.2, 1.0)
            reasons.append("关键里程碑，风险权重上调")

        return min(risk_score, 1.0), reasons

    # ─── 内部方法：去重检查 ─────────────────────────────────────────

    def _should_create_alert(self, milestone: ProjectMilestone, target_type: str) -> bool:
        """检查是否应该创建告警（避免同日重复）"""
        today_start = datetime.combine(date.today(), datetime.min.time())
        existing_alert = (
            self.db.query(AlertRecord)
            .filter(
                and_(
                    AlertRecord.target_type == target_type,
                    AlertRecord.target_id == milestone.id,
                    AlertRecord.status == "PENDING",
                    AlertRecord.triggered_at >= today_start,
                )
            )
            .first()
        )

        return existing_alert is None

    # ─── 内部方法：通知推送 ─────────────────────────────────────────

    def _dispatch_milestone_notification(
        self, alert: AlertRecord, milestone: ProjectMilestone
    ) -> None:
        """
        为里程碑预警创建通知推送
        接收人：项目负责人 + 里程碑责任人
        """
        try:
            self.db.flush()  # 确保 alert.id 已生成

            recipient_ids = set()

            # 1. 里程碑责任人
            if milestone.owner_id:
                recipient_ids.add(milestone.owner_id)

            # 2. 项目负责人（通过 project 关系）
            if milestone.project_id:
                from app.models.project import Project

                project = (
                    self.db.query(Project)
                    .filter(Project.id == milestone.project_id)
                    .first()
                )
                if project:
                    # 项目经理
                    if hasattr(project, "pm_id") and project.pm_id:
                        recipient_ids.add(project.pm_id)
                    # 项目负责人
                    if hasattr(project, "owner_id") and project.owner_id:
                        recipient_ids.add(project.owner_id)

            if not recipient_ids:
                logger.debug(f"里程碑 {milestone.milestone_code} 无可通知的接收人")
                return

            from app.services.notification_dispatcher import NotificationDispatcher

            dispatcher = NotificationDispatcher(self.db)
            result = dispatcher.dispatch_alert_notifications(
                alert=alert,
                user_ids=list(recipient_ids),
                channels=["SYSTEM"],
                title=alert.alert_title,
                content=alert.alert_content,
            )
            logger.info(
                f"里程碑预警通知已派发: alert_no={alert.alert_no}, "
                f"recipients={len(recipient_ids)}, result={result}"
            )
        except Exception as e:
            # 通知失败不影响主流程
            logger.warning(f"里程碑预警通知派发失败: {str(e)}")
