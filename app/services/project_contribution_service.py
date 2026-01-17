# -*- coding: utf-8 -*-
"""
项目贡献度计算服务
自动统计任务、工时、交付物等指标，关联奖金数据
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, extract, func, or_
from sqlalchemy.orm import Session

from app.models.issue import Issue
from app.models.project import (
    Project,
    ProjectDocument,
    ProjectMember,
    ProjectMemberContribution,
)
from app.models.task_center import TaskUnified
from app.models.user import User
from app.services.project_bonus_service import ProjectBonusService


class ProjectContributionService:
    """项目贡献度服务"""

    def __init__(self, db: Session):
        self.db = db
        self.bonus_service = ProjectBonusService(db)

    def calculate_member_contribution(
        self,
        project_id: int,
        user_id: int,
        period: str  # YYYY-MM
    ) -> ProjectMemberContribution:
        """
        计算项目成员贡献度

        Args:
            project_id: 项目ID
            user_id: 用户ID
            period: 统计周期（YYYY-MM）

        Returns:
            贡献度记录
        """
        # 检查是否已存在
        contribution = self.db.query(ProjectMemberContribution).filter(
            ProjectMemberContribution.project_id == project_id,
            ProjectMemberContribution.user_id == user_id,
            ProjectMemberContribution.period == period
        ).first()

        if not contribution:
            contribution = ProjectMemberContribution(
                project_id=project_id,
                user_id=user_id,
                period=period
            )
            self.db.add(contribution)

        # 解析周期
        year, month = map(int, period.split('-'))
        period_start = date(year, month, 1)
        if month == 12:
            period_end = date(year + 1, 1, 1)
        else:
            period_end = date(year, month + 1, 1)

        # 统计任务
        tasks = self.db.query(TaskUnified).filter(
            TaskUnified.project_id == project_id,
            TaskUnified.assignee_id == user_id,
            TaskUnified.created_at >= datetime.combine(period_start, datetime.min.time()),
            TaskUnified.created_at < datetime.combine(period_end, datetime.min.time())
        ).all()

        contribution.task_count = len([t for t in tasks if t.status == 'COMPLETED'])
        contribution.task_hours = sum(
            float(t.estimated_hours or 0) for t in tasks
        )
        contribution.actual_hours = sum(
            float(t.actual_hours or 0) for t in tasks
        )

        # 统计交付物（文档）
        documents = self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.uploaded_by == user_id,
            ProjectDocument.created_at >= datetime.combine(period_start, datetime.min.time()),
            ProjectDocument.created_at < datetime.combine(period_end, datetime.min.time())
        ).all()

        contribution.deliverable_count = len(documents)

        # 统计问题
        issues = self.db.query(Issue).filter(
            Issue.project_id == project_id,
            Issue.reporter_id == user_id,
            Issue.report_date >= datetime.combine(period_start, datetime.min.time()),
            Issue.report_date < datetime.combine(period_end, datetime.min.time())
        ).all()

        contribution.issue_count = len(issues)
        contribution.issue_resolved = len([
            i for i in issues
            if i.status in ['RESOLVED', 'CLOSED', 'VERIFIED']
        ])

        # 关联奖金数据
        bonus_calculations = self.bonus_service.get_project_bonus_calculations(
            project_id,
            user_id=user_id
        )
        contribution.bonus_amount = sum(
            (calc.calculated_amount or Decimal('0')) for calc in bonus_calculations
        )

        # 计算贡献度评分（简单算法，可扩展）
        contribution.contribution_score = self._calculate_contribution_score(contribution)

        self.db.commit()
        self.db.refresh(contribution)

        return contribution

    def _calculate_contribution_score(self, contribution: ProjectMemberContribution) -> Decimal:
        """计算贡献度评分"""
        score = Decimal('0')

        # 任务完成数权重：30%
        if contribution.task_count > 0:
            score += Decimal(str(contribution.task_count)) * Decimal('0.3')

        # 实际工时权重：20%
        if contribution.actual_hours > 0:
            score += Decimal(str(contribution.actual_hours)) * Decimal('0.2') / Decimal('10')  # 归一化

        # 交付物数量权重：20%
        if contribution.deliverable_count > 0:
            score += Decimal(str(contribution.deliverable_count)) * Decimal('0.2')

        # 解决问题数权重：20%
        if contribution.issue_resolved > 0:
            score += Decimal(str(contribution.issue_resolved)) * Decimal('0.2')

        # 奖金金额权重：10%（归一化，假设最大奖金10万）
        if contribution.bonus_amount > 0:
            score += (contribution.bonus_amount / Decimal('100000')) * Decimal('10') * Decimal('0.1')

        return score

    def get_project_contributions(
        self,
        project_id: int,
        period: Optional[str] = None
    ) -> List[ProjectMemberContribution]:
        """
        获取项目贡献度列表

        Args:
            project_id: 项目ID
            period: 统计周期（可选，不指定则返回所有周期）

        Returns:
            贡献度列表
        """
        query = self.db.query(ProjectMemberContribution).filter(
            ProjectMemberContribution.project_id == project_id
        )

        if period:
            query = query.filter(ProjectMemberContribution.period == period)

        return query.order_by(
            ProjectMemberContribution.contribution_score.desc()
        ).all()

    def get_user_project_contributions(
        self,
        user_id: int,
        start_period: Optional[str] = None,
        end_period: Optional[str] = None
    ) -> List[ProjectMemberContribution]:
        """
        获取用户的项目贡献汇总

        Args:
            user_id: 用户ID
            start_period: 开始周期（可选）
            end_period: 结束周期（可选）

        Returns:
            贡献度列表
        """
        query = self.db.query(ProjectMemberContribution).filter(
            ProjectMemberContribution.user_id == user_id
        )

        if start_period:
            query = query.filter(ProjectMemberContribution.period >= start_period)

        if end_period:
            query = query.filter(ProjectMemberContribution.period <= end_period)

        return query.order_by(
            ProjectMemberContribution.period.desc(),
            ProjectMemberContribution.contribution_score.desc()
        ).all()

    def rate_member_contribution(
        self,
        project_id: int,
        user_id: int,
        period: str,
        pm_rating: int,
        rater_id: int
    ) -> ProjectMemberContribution:
        """
        项目经理评分

        Args:
            project_id: 项目ID
            user_id: 用户ID
            period: 统计周期
            pm_rating: 评分（1-5）
            rater_id: 评分人ID（应为项目经理）

        Returns:
            更新后的贡献度记录
        """
        if pm_rating < 1 or pm_rating > 5:
            raise ValueError("评分必须在1-5之间")

        contribution = self.db.query(ProjectMemberContribution).filter(
            ProjectMemberContribution.project_id == project_id,
            ProjectMemberContribution.user_id == user_id,
            ProjectMemberContribution.period == period
        ).first()

        if not contribution:
            # 如果不存在，先计算
            contribution = self.calculate_member_contribution(project_id, user_id, period)

        contribution.pm_rating = pm_rating

        # 更新贡献度评分（考虑PM评分）
        base_score = contribution.contribution_score or Decimal('0')
        pm_score = Decimal(str(pm_rating)) * Decimal('2')  # PM评分转换为0-10分
        contribution.contribution_score = (base_score * Decimal('0.7')) + (pm_score * Decimal('0.3'))

        self.db.commit()
        self.db.refresh(contribution)

        return contribution

    def generate_contribution_report(
        self,
        project_id: int,
        period: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成项目贡献度报告

        Args:
            project_id: 项目ID
            period: 统计周期（可选）

        Returns:
            报告数据
        """
        contributions = self.get_project_contributions(project_id, period)

        total_members = len(contributions)
        total_task_count = sum(c.task_count for c in contributions)
        total_hours = sum(float(c.actual_hours or 0) for c in contributions)
        total_bonus = sum(float(c.bonus_amount or 0) for c in contributions)

        # 按贡献度排序
        top_contributors = sorted(
            contributions,
            key=lambda c: float(c.contribution_score or 0),
            reverse=True
        )[:10]

        return {
            'project_id': project_id,
            'period': period,
            'total_members': total_members,
            'total_task_count': total_task_count,
            'total_hours': total_hours,
            'total_bonus': total_bonus,
            'contributions': [
                {
                    'user_id': c.user_id,
                    'user_name': (
                        (c.user.employee.name if hasattr(c.user, 'employee') and c.user.employee and hasattr(c.user.employee, 'name') else None) or
                        (c.user.real_name if hasattr(c.user, 'real_name') and c.user.real_name else None) or
                        (c.user.username if c.user and hasattr(c.user, 'username') and c.user.username else None) or
                        f'User {c.user_id}'
                    ) if c.user else f'User {c.user_id}',
                    'task_count': c.task_count,
                    'actual_hours': float(c.actual_hours or 0),
                    'deliverable_count': c.deliverable_count,
                    'issue_resolved': c.issue_resolved,
                    'bonus_amount': float(c.bonus_amount or 0),
                    'contribution_score': float(c.contribution_score or 0),
                    'pm_rating': c.pm_rating,
                }
                for c in contributions
            ],
            'top_contributors': [
                {
                    'user_id': c.user_id,
                    'user_name': (
                        (c.user.employee.name if hasattr(c.user, 'employee') and c.user.employee and hasattr(c.user.employee, 'name') else None) or
                        (c.user.real_name if hasattr(c.user, 'real_name') and c.user.real_name else None) or
                        (c.user.username if c.user and hasattr(c.user, 'username') and c.user.username else None) or
                        f'User {c.user_id}'
                    ) if c.user else f'User {c.user_id}',
                    'contribution_score': float(c.contribution_score or 0),
                }
                for c in top_contributors
            ],
        }
