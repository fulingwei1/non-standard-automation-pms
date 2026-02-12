# -*- coding: utf-8 -*-
"""
数据完整性检查模块
提供工程师数据完整性检查功能
"""

from typing import Any, Dict


from app.models.engineer_performance import (
    CollaborationRating,
    DesignReview,
    EngineerProfile,
    KnowledgeContribution,
)
from app.models.performance import PerformancePeriod
from app.models.project import Project, ProjectMember
from app.models.project_evaluation import ProjectEvaluation
from app.models.work_log import WorkLog


class DataCheckMixin:
    """数据完整性检查功能混入类"""

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
