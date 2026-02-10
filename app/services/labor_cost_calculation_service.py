# -*- coding: utf-8 -*-
"""
[DEPRECATED] 人工成本计算辅助服务

此模块已合并到 app.services.labor_cost.utils 中。
也可从 app.services.labor_cost_service 导入 LaborCostCalculationService。
请直接从 app.services.labor_cost.utils 或 app.services.labor_cost 导入相关函数。
保留此文件仅为向后兼容。
"""
import warnings

from app.services.labor_cost.utils import (
 query_approved_timesheets,
 delete_existing_costs,
  group_timesheets_by_user,
 find_existing_cost,
 update_existing_cost,
 create_new_cost,
 check_budget_alert,
 process_user_costs,
 LaborCostCalculationService,
)

warnings.warn(
 "labor_cost_calculation_service 模块已废弃，请改用 "
 "app.services.labor_cost.utils",
 DeprecationWarning,
 stacklevel=2,
)

__all__ = [
 "query_approved_timesheets",
 "delete_existing_costs",
 "group_timesheets_by_user",
 "find_existing_cost",
 "update_existing_cost",
 "create_new_cost",
 "check_budget_alert",
 "process_user_costs",
 "LaborCostCalculationService",
]
