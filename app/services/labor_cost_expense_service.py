# -*- coding: utf-8 -*-
"""
[DEPRECATED] 工时费用化处理服务

此模块已合并到 app.services.labor_cost_service 中。
请直接从 app.services.labor_cost_service 导入 LaborCostExpenseService 和 PresaleExpense。
保留此文件仅为向后兼容。
"""
import warnings

from app.services.labor_cost_service import ( # noqa: F401
   LaborCostExpenseService,
 PresaleExpense,
)

warnings.warn(
 "labor_cost_expense_service 模块已废弃，请改用 "
 "app.services.labor_cost_service",
  DeprecationWarning,
 stacklevel=2,
)

__all__ = [
  "LaborCostExpenseService",
 "PresaleExpense",
]
