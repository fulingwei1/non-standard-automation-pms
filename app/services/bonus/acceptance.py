# -*- coding: utf-8 -*-
"""
验收奖金触发器
验收完成后触发奖金计算
"""

from typing import Any, List

from sqlalchemy.orm import Session

from app.models.project import Project
from app.services.bonus.base import BonusCalculatorBase


class AcceptanceBonusTrigger(BonusCalculatorBase):
    """验收奖金触发器"""

    def __init__(self, db: Session):
        super().__init__(db)

    def trigger_calculation(
        self,
        project: Project,
        acceptance_order
    ) -> List[Any]:
        """
        验收完成后触发奖金计算（仅计算总奖金，不分配到个人）

        计算以下总奖金：
        1. 销售奖金总额（给销售部门/团队）
        2. 售前技术奖金总额（给售前技术支持部门）
        3. 项目奖金总额（给项目团队）

        注意：个人奖金分配需要通过Excel导入，不会自动创建个人奖金记录

        Args:
            project: 项目
            acceptance_order: 验收单

        Returns:
            List: 团队奖金分配记录列表
        """
        from app.services.acceptance_bonus_service import (
            calculate_presale_bonus,
            calculate_project_bonus,
            calculate_sales_bonus,
            get_active_rules,
        )

        allocations = []

        # 1. 计算销售奖金总额（团队奖金）
        sales_rules = get_active_rules(self.db, bonus_type='SALES_BASED')
        sales_allocation = calculate_sales_bonus(self.db, project, sales_rules)
        if sales_allocation:
            allocations.append(sales_allocation)

        # 2. 计算售前技术奖金总额（团队奖金）
        presale_rules = get_active_rules(self.db, bonus_type='PRESALE_BASED')
        presale_allocation = calculate_presale_bonus(self.db, project, presale_rules)
        if presale_allocation:
            allocations.append(presale_allocation)

        # 3. 计算项目奖金总额（团队奖金）
        project_rules = get_active_rules(self.db, bonus_type='PROJECT_BASED')
        project_allocation = calculate_project_bonus(self.db, project, project_rules)
        if project_allocation:
            allocations.append(project_allocation)

        # 提交所有团队奖金分配记录
        if allocations:
            self.db.flush()

        return allocations
