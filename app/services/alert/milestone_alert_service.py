# -*- coding: utf-8 -*-
"""
里程碑告警服务

将原来133行的复杂函数拆分为多个小函数，提高可维护性和可测试性
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.alert import AlertRecord, AlertRule
from app.models.enums import AlertLevelEnum, AlertRuleTypeEnum, AlertStatusEnum
from app.models.project import ProjectMilestone

logger = logging.getLogger(__name__)


class MilestoneAlertService:
    """里程碑告警服务"""

    def __init__(self, db: Session):
        self.db = db

    def check_milestone_alerts(self):
        """
        里程碑预警服务
        每天执行一次，检查即将到期或已逾期的里程碑
        """
        try:
            today = date.today()

            # 获取即将到期和已逾期的里程碑
            upcoming_milestones = self._get_upcoming_milestones(today)
            overdue_milestones = self._get_overdue_milestones(today)

            # 获取或创建预警规则
            warning_rule = self._get_or_create_warning_rule()
            critical_rule = self._get_or_create_critical_rule()

            alert_count = 0

            # 处理即将到期的里程碑
            alert_count += self._process_upcoming_milestones(upcoming_milestones, warning_rule, today, alert_count)

            # 处理已逾期的里程碑
            alert_count += self._process_overdue_milestones(overdue_milestones, critical_rule, today, alert_count)

            logger.info(f"里程碑预警完成，共生成 {alert_count} 条告警")
            return alert_count

        except Exception as e:
            logger.error(f"里程碑预警检查失败: {str(e)}")
            raise

    def _get_upcoming_milestones(self, today: date) -> List[ProjectMilestone]:
        """获取即将到期的里程碑（3天内）"""
        warning_date = today + timedelta(days=3)

        return self.db.query(ProjectMilestone).filter(
            and_(
                ProjectMilestone.status != 'COMPLETED',
                ProjectMilestone.planned_date <= warning_date,
                ProjectMilestone.planned_date >= today
            )
        ).all()

    def _get_overdue_milestones(self, today: date) -> List[ProjectMilestone]:
        """获取已逾期的里程碑"""
        return self.db.query(ProjectMilestone).filter(
            and_(
                ProjectMilestone.status != 'COMPLETED',
                ProjectMilestone.planned_date < today
            )
        ).all()

    def _get_or_create_warning_rule(self) -> AlertRule:
        """获取或创建即将到期预警规则"""
        warning_rule = self.db.query(AlertRule).filter(
            and_(
                AlertRule.rule_code == 'MILESTONE_WARNING',
                AlertRule.is_enabled == True
            )
        ).first()

        if not warning_rule:
            warning_rule = AlertRule(
                rule_code='MILESTONE_WARNING',
                rule_name='里程碑即将到期预警',
                rule_type=AlertRuleTypeEnum.MILESTONE_DUE.value,
                target_type='MILESTONE',
                condition_type='THRESHOLD',
                condition_operator='LT',
                threshold_value='3',
                alert_level=AlertLevelEnum.WARNING.value,
                is_enabled=True,
                is_system=True,
                description='当里程碑将在3天内到期时触发预警'
            )
            self.db.add(warning_rule)
            self.db.flush()

        return warning_rule

    def _get_or_create_critical_rule(self) -> AlertRule:
        """获取或创建逾期预警规则"""
        critical_rule = self.db.query(AlertRule).filter(
            and_(
                AlertRule.rule_code == 'MILESTONE_OVERDUE',
                AlertRule.is_enabled == True
            )
        ).first()

        if not critical_rule:
            critical_rule = AlertRule(
                rule_code='MILESTONE_OVERDUE',
                rule_name='里程碑逾期预警',
                rule_type=AlertRuleTypeEnum.MILESTONE_DUE.value,
                target_type='MILESTONE',
                condition_type='THRESHOLD',
                condition_operator='LT',
                threshold_value='0',
                alert_level=AlertLevelEnum.CRITICAL.value,
                is_enabled=True,
                is_system=True,
                description='当里程碑已逾期时触发预警'
            )
            self.db.add(critical_rule)
            self.db.flush()

        return critical_rule

    def _process_upcoming_milestones(self, milestones: List[ProjectMilestone],
                                   rule: AlertRule, today: date, start_count: int) -> int:
        """处理即将到期的里程碑"""
        alert_count = start_count

        for milestone in milestones:
            if self._should_create_alert(milestone, 'MILESTONE'):
                days_left = (milestone.planned_date - today).days
                alert_no = f'MS{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'

                self._create_milestone_alert(
                    alert_no=alert_no,
                    rule=rule,
                    milestone=milestone,
                    days_diff=days_left,
                    is_overdue=False
                )

                alert_count += 1

        return alert_count - start_count

    def _process_overdue_milestones(self, milestones: List[ProjectMilestone],
                                  rule: AlertRule, today: date, start_count: int) -> int:
        """处理已逾期的里程碑"""
        alert_count = start_count

        for milestone in milestones:
            if self._should_create_alert(milestone, 'MILESTONE'):
                days_overdue = (today - milestone.planned_date).days
                alert_no = f'MS{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'

                self._create_milestone_alert(
                    alert_no=alert_no,
                    rule=rule,
                    milestone=milestone,
                    days_diff=days_overdue,
                    is_overdue=True
                )

                alert_count += 1

        return alert_count - start_count

    def _should_create_alert(self, milestone: ProjectMilestone, target_type: str) -> bool:
        """检查是否应该创建告警（避免重复）"""
        existing_alert = self.db.query(AlertRecord).filter(
            and_(
                AlertRecord.target_type == target_type,
                AlertRecord.target_id == milestone.id,
                AlertRecord.status == 'PENDING'
            )
        ).first()

        return existing_alert is None

    def _create_milestone_alert(self, alert_no: str, rule: AlertRule,
                              milestone: ProjectMilestone, days_diff: int, is_overdue: bool):
        """创建里程碑告警"""
        if is_overdue:
            alert_title = f'里程碑已逾期：{milestone.milestone_name}'
            alert_content = (f'里程碑 {milestone.milestone_code} 已逾期 {days_diff} 天'
                            f'（计划日期：{milestone.planned_date}）')
            alert_level = AlertLevelEnum.CRITICAL.value
        else:
            alert_title = f'里程碑即将到期：{milestone.milestone_name}'
            alert_content = (f'里程碑 {milestone.milestone_code} 将在 {days_diff} 天后到期'
                            f'（计划日期：{milestone.planned_date}）')
            alert_level = AlertLevelEnum.WARNING.value

        alert = AlertRecord(
            alert_no=alert_no,
            rule_id=rule.id,
            target_type='MILESTONE',
            target_id=milestone.id,
            target_no=milestone.milestone_code,
            target_name=milestone.milestone_name,
            project_id=milestone.project_id,
            alert_level=alert_level,
            alert_title=alert_title,
            alert_content=alert_content,
            status=AlertStatusEnum.PENDING.value,
            triggered_at=datetime.now()
        )

        self.db.add(alert)
