# -*- coding: utf-8 -*-
"""
数据完整性保障服务
提供数据缺失提醒、数据质量报告、自动修复建议
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.models.engineer_performance import (
    CollaborationRating,
    DesignReview,
    EngineerProfile,
    KnowledgeContribution,
)
from app.models.performance import PerformancePeriod, PerformanceResult
from app.models.project import Project, ProjectMember
from app.models.project_evaluation import ProjectEvaluation
from app.models.work_log import WorkLog


class DataIntegrityService:
    """数据完整性保障服务"""

    def __init__(self, db: Session):
        self.db = db

    def check_data_completeness(
        self,
        engineer_id: int,
        period_id: int
    ) -> Dict[str, Any]:
        """
        检查工程师数据完整性

        Returns:
            数据完整性报告
        """
        period = self.db.query(PerformancePeriod).filter(
            PerformancePeriod.id == period_id
        ).first()

        if not period:
            raise ValueError(f"考核周期不存在: {period_id}")

        profile = self.db.query(EngineerProfile).filter(
            EngineerProfile.user_id == engineer_id
        ).first()

        if not profile:
            return {
                'engineer_id': engineer_id,
                'period_id': period_id,
                'completeness_score': 0.0,
                'missing_items': ['工程师档案不存在'],
                'warnings': [],
                'suggestions': []
            }

        missing_items = []
        warnings = []
        suggestions = []

        # 1. 检查工作日志
        work_logs = self.db.query(WorkLog).filter(
            WorkLog.user_id == engineer_id,
            WorkLog.work_date.between(period.start_date, period.end_date),
            WorkLog.status == 'SUBMITTED'
        ).count()

        if work_logs == 0:
            missing_items.append("工作日志缺失")
            suggestions.append("建议工程师填写工作日志，以便提取自我评价数据")

        # 2. 检查项目参与情况
        projects = self.db.query(Project).join(
            ProjectMember, Project.id == ProjectMember.project_id
        ).filter(
            ProjectMember.user_id == engineer_id,
            Project.created_at.between(period.start_date, period.end_date)
        ).count()

        if projects == 0:
            warnings.append("考核周期内未参与任何项目")
            suggestions.append("检查项目成员分配是否正确")

        # 3. 检查项目评价（针对参与的项目）
        project_ids = [
            pm.project_id for pm in self.db.query(ProjectMember.project_id).filter(
                ProjectMember.user_id == engineer_id
            ).all()
        ]

        if project_ids:
            missing_evaluations = self.db.query(ProjectEvaluation).filter(
                ProjectEvaluation.project_id.in_(project_ids),
                ProjectEvaluation.status != 'CONFIRMED'
            ).count()

            if missing_evaluations > 0:
                warnings.append(f"{missing_evaluations}个参与项目的评价未完成")
                suggestions.append("项目管理部经理需要完成项目难度和工作量评价")

        # 4. 检查设计评审记录（机械/电气工程师）
        if profile.job_type in ['mechanical', 'electrical']:
            reviews = self.db.query(DesignReview).filter(
                DesignReview.designer_id == engineer_id,
                DesignReview.review_date.between(period.start_date, period.end_date)
            ).count()

            if reviews == 0:
                warnings.append("设计评审记录缺失")
                suggestions.append("确保设计评审流程完整，记录评审结果")

        # 5. 检查跨部门协作评价
        collab_ratings = self.db.query(CollaborationRating).filter(
            CollaborationRating.ratee_id == engineer_id,
            CollaborationRating.period_id == period_id,
            CollaborationRating.total_score.isnot(None)
        ).count()

        if collab_ratings < 3:
            warnings.append(f"跨部门协作评价不足（当前{collab_ratings}个，建议至少3个）")
            suggestions.append("系统将自动抽取合作人员进行评价")

        # 6. 检查知识贡献
        contributions = self.db.query(KnowledgeContribution).filter(
            KnowledgeContribution.contributor_id == engineer_id,
            KnowledgeContribution.created_at.between(period.start_date, period.end_date)
        ).count()

        if contributions == 0:
            warnings.append("知识贡献记录缺失")
            suggestions.append("鼓励工程师提交技术文档、模板或模块")

        # 计算完整性得分
        total_checks = 6
        passed_checks = total_checks - len(missing_items) - len(warnings)
        completeness_score = (passed_checks / total_checks) * 100

        return {
            'engineer_id': engineer_id,
            'period_id': period_id,
            'completeness_score': round(completeness_score, 2),
            'missing_items': missing_items,
            'warnings': warnings,
            'suggestions': suggestions,
            'work_logs_count': work_logs,
            'projects_count': projects,
            'collab_ratings_count': collab_ratings,
            'contributions_count': contributions
        }

    def generate_data_quality_report(
        self,
        period_id: int,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        生成数据质量报告

        Args:
            period_id: 考核周期ID
            department_id: 部门ID（可选，如果指定则只统计该部门）

        Returns:
            数据质量报告
        """
        period = self.db.query(PerformancePeriod).filter(
            PerformancePeriod.id == period_id
        ).first()

        if not period:
            raise ValueError(f"考核周期不存在: {period_id}")

        # 获取工程师列表
        query = self.db.query(EngineerProfile)
        if department_id:
            from app.models.organization import Employee
            from app.models.user import User
            employees = self.db.query(Employee).filter(
                Employee.department_id == department_id
            ).all()
            employee_ids = [e.id for e in employees]
            user_ids = [
                u.id for u in self.db.query(User).filter(
                    User.employee_id.in_(employee_ids)
                ).all()
            ]
            query = query.filter(EngineerProfile.user_id.in_(user_ids))

        engineers = query.all()

        total_engineers = len(engineers)
        if total_engineers == 0:
            return {
                'period_id': period_id,
                'department_id': department_id,
                'total_engineers': 0,
                'reports': []
            }

        reports = []
        completeness_scores = []

        for engineer in engineers:
            report = self.check_data_completeness(engineer.user_id, period_id)
            reports.append(report)
            completeness_scores.append(report['completeness_score'])

        avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0.0

        # 统计缺失项
        all_missing = []
        all_warnings = []
        for report in reports:
            all_missing.extend(report['missing_items'])
            all_warnings.extend(report['warnings'])

        missing_summary = {}
        for item in all_missing:
            missing_summary[item] = missing_summary.get(item, 0) + 1

        warnings_summary = {}
        for item in all_warnings:
            warnings_summary[item] = warnings_summary.get(item, 0) + 1

        return {
            'period_id': period_id,
            'department_id': department_id,
            'total_engineers': total_engineers,
            'average_completeness_score': round(avg_completeness, 2),
            'missing_items_summary': missing_summary,
            'warnings_summary': warnings_summary,
            'reports': reports
        }

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

    def suggest_auto_fixes(
        self,
        engineer_id: int,
        period_id: int
    ) -> List[Dict[str, Any]]:
        """
        提供自动修复建议

        Args:
            engineer_id: 工程师ID
            period_id: 考核周期ID

        Returns:
            自动修复建议列表
        """
        suggestions = []
        report = self.check_data_completeness(engineer_id, period_id)

        # 1. 如果缺少跨部门协作评价，建议自动抽取
        if report['collab_ratings_count'] < 3:
            suggestions.append({
                'type': 'auto_select_collaborators',
                'action': '自动抽取合作人员进行评价',
                'description': '系统可以自动从项目成员中抽取5个合作人员进行匿名评价',
                'can_auto_fix': True
            })

        # 2. 如果缺少工作日志，建议提醒工程师
        if report['work_logs_count'] == 0:
            suggestions.append({
                'type': 'remind_work_log',
                'action': '提醒工程师填写工作日志',
                'description': '可以发送提醒通知，督促工程师填写工作日志',
                'can_auto_fix': False
            })

        # 3. 如果项目评价缺失，建议提醒项目管理部经理
        if '项目评价未完成' in str(report.get('warnings', [])):
            suggestions.append({
                'type': 'remind_project_evaluation',
                'action': '提醒项目管理部经理完成项目评价',
                'description': '可以发送提醒通知，督促项目管理部经理完成项目难度和工作量评价',
                'can_auto_fix': False
            })

        return suggestions

    def auto_fix_data_issues(
        self,
        engineer_id: int,
        period_id: int,
        fix_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        自动修复数据问题

        Args:
            engineer_id: 工程师ID
            period_id: 考核周期ID
            fix_types: 要修复的问题类型列表（如果为None则修复所有可自动修复的问题）

        Returns:
            修复结果
        """
        fixes_applied = []
        fixes_failed = []

        suggestions = self.suggest_auto_fixes(engineer_id, period_id)

        for suggestion in suggestions:
            if not suggestion.get('can_auto_fix', False):
                continue

            if fix_types and suggestion['type'] not in fix_types:
                continue

            try:
                if suggestion['type'] == 'auto_select_collaborators':
                    # 自动抽取合作人员
                    from app.services.collaboration_rating_service import (
                        CollaborationRatingService,
                    )
                    collab_service = CollaborationRatingService(self.db)

                    collaborators = collab_service.auto_select_collaborators(
                        engineer_id, period_id, target_count=5
                    )
                    if collaborators:
                        collab_service.create_rating_invitations(
                            engineer_id, period_id, collaborators
                        )
                        fixes_applied.append({
                            'type': suggestion['type'],
                            'action': suggestion['action'],
                            'result': f'已自动抽取{len(collaborators)}个合作人员'
                        })
                    else:
                        fixes_failed.append({
                            'type': suggestion['type'],
                            'reason': '未找到合适的合作人员'
                        })
            except Exception as e:
                fixes_failed.append({
                    'type': suggestion['type'],
                    'reason': str(e)
                })

        return {
            'engineer_id': engineer_id,
            'period_id': period_id,
            'fixes_applied': fixes_applied,
            'fixes_failed': fixes_failed,
            'total_applied': len(fixes_applied),
            'total_failed': len(fixes_failed)
        }

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

        # 这里应该集成通知系统（邮件/系统消息）
        # 目前只返回提醒列表，实际发送需要集成通知服务
        for reminder in reminders:
            try:
                # TODO: 集成通知服务发送提醒
                # notification_service.send_reminder(reminder)
                sent_count += 1
            except Exception:
                failed_count += 1

        return {
            'period_id': period_id,
            'total_reminders': len(reminders),
            'sent_count': sent_count,
            'failed_count': failed_count,
            'reminders': reminders
        }

    def export_data_quality_report(
        self,
        period_id: int,
        department_id: Optional[int] = None,
        format: str = 'json'
    ) -> Dict[str, Any]:
        """
        导出数据质量报告

        Args:
            period_id: 考核周期ID
            department_id: 部门ID（可选）
            format: 导出格式（json/excel/pdf）

        Returns:
            报告数据（格式根据format参数）
        """
        report = self.generate_data_quality_report(period_id, department_id)

        if format == 'json':
            return report
        elif format == 'excel':
            # TODO: 使用openpyxl或pandas生成Excel
            return {
                'format': 'excel',
                'message': 'Excel导出功能待实现',
                'data': report
            }
        elif format == 'pdf':
            # TODO: 使用reportlab或weasyprint生成PDF
            return {
                'format': 'pdf',
                'message': 'PDF导出功能待实现',
                'data': report
            }
        else:
            return report
