# -*- coding: utf-8 -*-
"""
项目奖金查询服务
支持查询项目相关的奖金规则、计算记录、发放记录
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.bonus import BonusCalculation, BonusDistribution, BonusRule
from app.models.project import Project
from app.models.user import User


class ProjectBonusService:
    """项目奖金服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_project_bonus_rules(
        self,
        project_id: int,
        is_active: bool = True
    ) -> List[BonusRule]:
        """
        获取项目适用的奖金规则

        Args:
            project_id: 项目ID
            is_active: 是否只返回启用的规则

        Returns:
            奖金规则列表
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return []

        query = self.db.query(BonusRule).filter(
            BonusRule.bonus_type.in_(['PROJECT_BASED', 'MILESTONE_BASED', 'STAGE_BASED'])
        )

        if is_active:
            query = query.filter(BonusRule.is_active)

        # 检查规则是否适用于此项目
        applicable_rules = []
        for rule in query.all():
            if self._is_rule_applicable(rule, project):
                applicable_rules.append(rule)

        return applicable_rules

    def _is_rule_applicable(self, rule: BonusRule, project: Project) -> bool:
        """检查规则是否适用于项目"""
        # 检查项目类型（如果规则有配置）
        if hasattr(rule, 'apply_to_projects') and rule.apply_to_projects:
            project_types = rule.apply_to_projects
            if isinstance(project_types, list) and len(project_types) > 0:
                # 如果项目有 project_type 字段，则检查
                if hasattr(project, 'project_type') and project.project_type:
                    if project.project_type not in project_types:
                        return False

        # 检查生效日期
        if hasattr(rule, 'effective_start_date') and rule.effective_start_date:
            if rule.effective_start_date > date.today():
                return False
        if hasattr(rule, 'effective_end_date') and rule.effective_end_date:
            if rule.effective_end_date < date.today():
                return False

        return True

    def get_project_bonus_calculations(
        self,
        project_id: int,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[BonusCalculation]:
        """
        获取项目奖金计算记录

        Args:
            project_id: 项目ID
            user_id: 用户ID（可选，筛选特定用户）
            status: 状态（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            奖金计算记录列表
        """
        query = self.db.query(BonusCalculation).filter(
            BonusCalculation.project_id == project_id
        )

        if user_id:
            query = query.filter(BonusCalculation.user_id == user_id)

        if status:
            query = query.filter(BonusCalculation.status == status)

        if start_date:
            query = query.filter(BonusCalculation.calculated_at >= datetime.combine(start_date, datetime.min.time()))

        if end_date:
            query = query.filter(BonusCalculation.calculated_at <= datetime.combine(end_date, datetime.max.time()))

        return query.order_by(BonusCalculation.calculated_at.desc()).all()

    def get_project_bonus_distributions(
        self,
        project_id: int,
        user_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[BonusDistribution]:
        """
        获取项目奖金发放记录

        Args:
            project_id: 项目ID
            user_id: 用户ID（可选）
            status: 发放状态（可选）

        Returns:
            奖金发放记录列表
        """
        # 先获取项目相关的计算记录
        calculation_ids = self.db.query(BonusCalculation.id).filter(
            BonusCalculation.project_id == project_id
        ).subquery()

        query = self.db.query(BonusDistribution).filter(
            BonusDistribution.calculation_id.in_(calculation_ids)
        )

        if user_id:
            query = query.filter(BonusDistribution.user_id == user_id)

        if status:
            query = query.filter(BonusDistribution.status == status)

        return query.order_by(BonusDistribution.distributed_at.desc()).all()

    def get_project_member_bonus_summary(
        self,
        project_id: int
    ) -> List[Dict[str, Any]]:
        """
        获取项目成员奖金汇总

        Args:
            project_id: 项目ID

        Returns:
            成员奖金汇总列表，包含：
            - user_id: 用户ID
            - user_name: 用户名
            - total_calculated: 总计算金额
            - total_distributed: 总发放金额
            - calculation_count: 计算记录数
            - distribution_count: 发放记录数
        """
        # 获取所有计算记录
        calculations = self.get_project_bonus_calculations(project_id)

        # 按用户汇总
        member_summary = {}
        for calc in calculations:
            user_id = calc.user_id
            if user_id not in member_summary:
                user = self.db.query(User).filter(User.id == user_id).first()
                member_summary[user_id] = {
                    'user_id': user_id,
                    'user_name': user.real_name or user.username if user else f'User {user_id}',
                    'total_calculated': Decimal('0'),
                    'total_distributed': Decimal('0'),
                    'calculation_count': 0,
                    'distribution_count': 0
                }

            member_summary[user_id]['total_calculated'] += calc.calculated_amount or Decimal('0')
            member_summary[user_id]['calculation_count'] += 1

        # 获取发放记录
        distributions = self.get_project_bonus_distributions(project_id)
        for dist in distributions:
            user_id = dist.user_id
            if user_id not in member_summary:
                user = self.db.query(User).filter(User.id == user_id).first()
                member_summary[user_id] = {
                    'user_id': user_id,
                    'user_name': user.real_name or user.username if user else f'User {user_id}',
                    'total_calculated': Decimal('0'),
                    'total_distributed': Decimal('0'),
                    'calculation_count': 0,
                    'distribution_count': 0
                }

            member_summary[user_id]['total_distributed'] += dist.distributed_amount or Decimal('0')
            member_summary[user_id]['distribution_count'] += 1

        return list(member_summary.values())

    def get_project_bonus_statistics(
        self,
        project_id: int
    ) -> Dict[str, Any]:
        """
        获取项目奖金统计信息

        Args:
            project_id: 项目ID

        Returns:
            统计信息字典，包含：
            - total_calculated: 总计算金额
            - total_distributed: 总发放金额
            - pending_amount: 待发放金额
            - calculation_count: 计算记录数
            - distribution_count: 发放记录数
            - member_count: 涉及成员数
        """
        calculations = self.get_project_bonus_calculations(project_id)
        distributions = self.get_project_bonus_distributions(project_id)

        total_calculated = sum(
            (calc.calculated_amount or Decimal('0')) for calc in calculations
        )
        total_distributed = sum(
            (dist.distributed_amount or Decimal('0')) for dist in distributions
        )

        # 获取涉及的用户数
        user_ids = set()
        for calc in calculations:
            user_ids.add(calc.user_id)
        for dist in distributions:
            user_ids.add(dist.user_id)

        return {
            'total_calculated': float(total_calculated),
            'total_distributed': float(total_distributed),
            'pending_amount': float(total_calculated - total_distributed),
            'calculation_count': len(calculations),
            'distribution_count': len(distributions),
            'member_count': len(user_ids)
        }
