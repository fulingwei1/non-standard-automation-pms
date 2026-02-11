# -*- coding: utf-8 -*-
"""
缺失数据提醒模块
提供数据缺失提醒的查询和发送功能
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import and_

from app.models.engineer_performance import CollaborationRating, EngineerProfile
from app.models.performance import PerformancePeriod
from app.models.project import Project
from app.models.project_evaluation import ProjectEvaluation
from app.models.work_log import WorkLog

logger = logging.getLogger(__name__)


class RemindersMixin:
    """缺失数据提醒功能混入类"""

    def get_missing_data_reminders(
        self,
        period_id: int
    ) -> List[Dict[str, Any]]:
        """
        获取数据缺失提醒列表

        Args:
            period_id: 考核周期ID

        Returns:
            数据缺失提醒列表
        """
        period = self.db.query(PerformancePeriod).filter(
            PerformancePeriod.id == period_id
        ).first()

        if not period:
            return []

        reminders = []

        # 1. 检查未完成项目评价的项目
        projects_without_evaluation = self.db.query(Project).outerjoin(
            ProjectEvaluation, and_(
                Project.id == ProjectEvaluation.project_id,
                ProjectEvaluation.status == 'CONFIRMED'
            )
        ).filter(
            Project.created_at.between(period.start_date, period.end_date),
            ProjectEvaluation.id.is_(None)
        ).all()

        for project in projects_without_evaluation:
            reminders.append({
                'type': 'project_evaluation_missing',
                'priority': 'high',
                'message': f"项目 {project.project_code} 未完成评价",
                'project_id': project.id,
                'project_code': project.project_code,
                'project_name': project.project_name,
                'suggestion': '项目管理部经理需要完成项目难度和工作量评价'
            })

        # 2. 检查缺少跨部门协作评价的工程师
        engineers_without_collab = self.db.query(EngineerProfile).outerjoin(
            CollaborationRating, and_(
                EngineerProfile.user_id == CollaborationRating.ratee_id,
                CollaborationRating.period_id == period_id,
                CollaborationRating.total_score.isnot(None)
            )
        ).filter(
            CollaborationRating.id.is_(None)
        ).all()

        for engineer in engineers_without_collab:
            reminders.append({
                'type': 'collaboration_rating_missing',
                'priority': 'medium',
                'message': f"工程师 {engineer.user.name if engineer.user else 'Unknown'} 缺少跨部门协作评价",
                'engineer_id': engineer.user_id,
                'suggestion': '系统将自动抽取合作人员进行评价'
            })

        # 3. 检查缺少工作日志的工程师
        engineers_without_logs = self.db.query(EngineerProfile).outerjoin(
            WorkLog, and_(
                EngineerProfile.user_id == WorkLog.user_id,
                WorkLog.work_date.between(period.start_date, period.end_date),
                WorkLog.status == 'SUBMITTED'
            )
        ).filter(
            WorkLog.id.is_(None)
        ).all()

        for engineer in engineers_without_logs:
            reminders.append({
                'type': 'work_log_missing',
                'priority': 'low',
                'message': f"工程师 {engineer.user.name if engineer.user else 'Unknown'} 缺少工作日志",
                'engineer_id': engineer.user_id,
                'suggestion': '建议工程师填写工作日志，以便提取自我评价数据'
            })

        return reminders

    def send_data_missing_reminders(
        self,
        period_id: int,
        reminder_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        发送数据缺失提醒

        Args:
            period_id: 考核周期ID
            reminder_types: 提醒类型列表（如果为None则发送所有提醒）

        Returns:
            提醒发送结果
        """
        reminders = self.get_missing_data_reminders(period_id)

        if reminder_types:
            reminders = [r for r in reminders if r['type'] in reminder_types]

        sent_count = 0
        failed_count = 0

        # 使用统一通知服务发送提醒
        try:
            from app.services.unified_notification_service import get_notification_service
            from app.services.channel_handlers.base import (
                NotificationRequest,
                NotificationPriority as UnifiedPriority,
            )

            unified_service = get_notification_service(db)
            for reminder in reminders:
                try:
                    # 确定通知优先级
                    priority = UnifiedPriority.NORMAL
                    if reminder.get('priority') == 'high':
                        priority = UnifiedPriority.HIGH
                    elif reminder.get('priority') == 'urgent':
                        priority = UnifiedPriority.URGENT

                    # 发送通知
                    request = NotificationRequest(
                        recipient_id=reminder.get('engineer_id'),
                        notification_type="DEADLINE_REMINDER",
                        category="deadline",
                        title=f"数据填报提醒: {reminder.get('type', '未知类型')}",
                        content=reminder.get('message', '请及时完成数据填报'),
                        priority=priority,
                        extra_data={'reminder': reminder},
                    )
                    result = unified_service.send_notification(request)
                    if result.get("success"):
                        sent_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"发送提醒失败: {e}")
                    failed_count += 1
        except ImportError:
            logger.warning("通知服务未找到，跳过发送提醒")
            failed_count = len(reminders)

        return {
            'period_id': period_id,
            'total_reminders': len(reminders),
            'sent_count': sent_count,
            'failed_count': failed_count,
            'reminders': reminders
        }
