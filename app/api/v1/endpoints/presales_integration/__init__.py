# -*- coding: utf-8 -*-
"""
售前系统集成模块

拆分自原 presales_integration.py (772行)，按功能域分为：
- utils: 辅助工具函数（编号转换、中标率计算、建议生成）
- lead_conversion: 线索转项目
- win_rate: 中标率预测
- resource_analysis: 资源投入与浪费分析
- salesperson: 销售人员绩效分析
- dashboard: 售前分析仪表板
"""

from fastapi import APIRouter

from .dashboard import router as dashboard_router
from .lead_conversion import router as lead_router
from .resource_analysis import router as resource_router
from .salesperson import router as salesperson_router
from .win_rate import router as win_rate_router

router = APIRouter()

# 线索转项目
router.include_router(lead_router, tags=["线索转项目"])

# 中标率预测
router.include_router(win_rate_router, tags=["中标率预测"])

# 资源分析
router.include_router(resource_router, tags=["资源分析"])

# 销售人员绩效
router.include_router(salesperson_router, tags=["销售绩效"])

# 仪表板
router.include_router(dashboard_router, tags=["售前仪表板"])
