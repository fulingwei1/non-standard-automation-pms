# -*- coding: utf-8 -*-
"""
团队奖金计算器
计算团队总奖金并分配
"""

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.bonus import BonusRule, TeamBonusAllocation
from app.models.performance import ProjectContribution
from app.models.project import Project, ProjectMember
from app.services.bonus.base import BonusCalculatorBase


class TeamBonusCalculator(BonusCalculatorBase):
    """团队奖金计算器"""

    def __init__(self, db: Session):
        super().__init__(db)

    def calculate(
        self,
        project: Project,
        bonus_rule: BonusRule,
        period_id: Optional[int] = None
    ) -> TeamBonusAllocation:
        """
        计算团队总奖金并分配

        Args:
            project: 项目
            bonus_rule: 奖金规则
            period_id: 周期ID（可选）

        Returns:
            TeamBonusAllocation: 团队奖金分配记录
        """
        # 计算团队总奖金（基于项目金额）
        project_amount = project.contract_amount or Decimal('0')
        coefficient = bonus_rule.coefficient or Decimal('0')
        total_bonus = project_amount * (coefficient / Decimal('100'))

        # 获取项目成员贡献
        query = self.db.query(ProjectContribution).filter(
            ProjectContribution.project_id == project.id
        )
        if period_id:
            query = query.filter(ProjectContribution.period_id == period_id)
        contributions = query.all()

        # 按贡献分配
        allocation_detail = []
        # 使用工时占比作为贡献度
        total_contribution = sum(
            float(c.hours_percentage) if c.hours_percentage else 0
            for c in contributions
        )

        if total_contribution > 0:
            for contrib in contributions:
                contribution_score = float(contrib.hours_percentage) if contrib.hours_percentage else 0
                ratio = contribution_score / total_contribution
                amount = total_bonus * Decimal(str(ratio))

                allocation_detail.append({
                    "user_id": contrib.user_id,
                    "contribution_score": contribution_score,
                    "ratio": float(ratio),
                    "amount": float(amount)
                })
        else:
            # 如果没有贡献记录，平均分配
            members = self.db.query(ProjectMember).filter(
                ProjectMember.project_id == project.id
            ).all()
            if members:
                avg_amount = total_bonus / Decimal(str(len(members)))
                for member in members:
                    allocation_detail.append({
                        "user_id": member.user_id,
                        "contribution_score": 0,
                        "ratio": 1.0 / len(members),
                        "amount": float(avg_amount)
                    })

        # 创建团队奖金分配记录
        team_allocation = TeamBonusAllocation(
            project_id=project.id,
            period_id=period_id,
            total_bonus_amount=total_bonus,
            allocation_method='BY_CONTRIBUTION' if total_contribution > 0 else 'EQUAL',
            allocation_detail=allocation_detail,
            status='PENDING'
        )

        return team_allocation
