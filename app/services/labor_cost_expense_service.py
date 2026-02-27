# -*- coding: utf-8 -*-
"""向后兼容 re-export wrapper — 实际实现在 labor_cost_service"""

from app.services.labor_cost_service import (  # noqa: F401
    LaborCostExpenseService,
    PresaleExpense,
)
