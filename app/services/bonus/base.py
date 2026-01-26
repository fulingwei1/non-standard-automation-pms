# -*- coding: utf-8 -*-
"""
奖金计算器基类
提供核心功能和工具方法
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.bonus import BonusCalculation, BonusRule
from app.models.enums import PerformanceLevelEnum


class BonusCalculatorBase:
    """奖金计算器基类"""

    def __init__(self, db: Session):
        self.db = db

    def generate_calculation_code(self) -> str:
        """生成计算单号"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"BC{timestamp}"

    def check_trigger_condition(
        self,
        bonus_rule: BonusRule,
        context: Dict[str, Any]
    ) -> bool:
        """
        检查触发条件是否满足

        Args:
            bonus_rule: 奖金规则
            context: 上下文数据（包含绩效结果、项目、里程碑等信息）

        Returns:
            bool: 是否满足触发条件
        """
        if not bonus_rule.trigger_condition:
            return True

        condition = bonus_rule.trigger_condition

        # 检查绩效等级
        if 'performance_level' in condition:
            performance_result = context.get('performance_result')
            if not performance_result:
                return False
            if performance_result.level != condition['performance_level']:
                return False

        # 检查最低分数
        if 'min_score' in condition:
            performance_result = context.get('performance_result')
            if not performance_result or not performance_result.total_score:
                return False
            if float(performance_result.total_score) < condition['min_score']:
                return False

        # 检查里程碑类型
        if 'milestone_type' in condition:
            milestone = context.get('milestone')
            if not milestone:
                return False
            if milestone.milestone_type != condition['milestone_type']:
                return False

        # 检查里程碑状态
        if 'milestone_status' in condition:
            milestone = context.get('milestone')
            if not milestone:
                return False
            if milestone.status != condition['milestone_status']:
                return False

        # 检查项目阶段
        if 'stage' in condition:
            project = context.get('project')
            if not project:
                return False
            if project.stage != condition['stage']:
                return False

        return True

    def get_coefficient_by_level(self, level: str) -> Decimal:
        """
        根据绩效等级获取系数

        Args:
            level: 绩效等级

        Returns:
            Decimal: 系数
        """
        coefficients = {
            PerformanceLevelEnum.EXCELLENT: Decimal('1.5'),
            PerformanceLevelEnum.GOOD: Decimal('1.2'),
            PerformanceLevelEnum.QUALIFIED: Decimal('1.0'),
            PerformanceLevelEnum.NEEDS_IMPROVEMENT: Decimal('0.8'),
            PerformanceLevelEnum.AVERAGE: Decimal('1.0'),
            PerformanceLevelEnum.POOR: Decimal('0.8'),
        }
        return coefficients.get(level, Decimal('1.0'))

    def get_role_coefficient(self, role_code: str, bonus_rule: BonusRule) -> Decimal:
        """
        根据角色获取系数

        Args:
            role_code: 角色编码
            bonus_rule: 奖金规则

        Returns:
            Decimal: 系数
        """
        # 默认角色系数（可在规则中配置）
        default_coefficients = {
            'PM': Decimal('1.5'),      # 项目经理
            'ME': Decimal('1.2'),     # 机械负责
            'EE': Decimal('1.2'),     # 电气负责
            'SW': Decimal('1.1'),     # 软件负责
            'DEBUG': Decimal('1.0'),   # 调试负责
            'QA': Decimal('1.0'),      # 质量负责
        }

        # 如果规则中有配置，使用规则配置
        if bonus_rule.trigger_condition and 'role_coefficients' in bonus_rule.trigger_condition:
            role_coefficients = bonus_rule.trigger_condition['role_coefficients']
            return Decimal(str(role_coefficients.get(role_code, 1.0)))

        return default_coefficients.get(role_code, Decimal('1.0'))

    def get_active_rules(
        self,
        bonus_type: Optional[str] = None
    ) -> List[BonusRule]:
        """
        获取启用的奖金规则

        Args:
            bonus_type: 奖金类型（可选）

        Returns:
            List[BonusRule]: 规则列表
        """
        query = self.db.query(BonusRule).filter(BonusRule.is_active == True)

        # 检查生效日期
        today = date.today()
        query = query.filter(
            (BonusRule.effective_start_date.is_(None)) |
            (BonusRule.effective_start_date <= today)
        )
        query = query.filter(
            (BonusRule.effective_end_date.is_(None)) |
            (BonusRule.effective_end_date >= today)
        )

        if bonus_type:
            query = query.filter(BonusRule.bonus_type == bonus_type)

        # 按优先级排序
        query = query.order_by(BonusRule.priority.desc())

        return query.all()
