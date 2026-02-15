# -*- coding: utf-8 -*-
"""
项目成本管理模块（重构版本）

路由: /projects/{project_id}/costs/
- GET / - 获取项目成本列表（支持分页、搜索、排序、筛选）
- POST / - 添加成本记录
- GET /{cost_id} - 获取成本详情
- PUT /{cost_id} - 更新成本
- DELETE /{cost_id} - 删除成本（由CRUD基类提供）
- GET /summary - 成本汇总
- GET /cost-analysis - 成本对比分析
- GET /revenue-detail - 收入详情
- GET /profit-analysis - 利润分析
- POST /calculate-labor-cost - 计算人工成本
- GET /execution - 预算执行分析
- GET /trend - 预算趋势分析
- POST /generate-cost-review - 生成成本复盘报告
- POST /check-budget-alert - 检查预算预警
- POST /{cost_id}/allocate - 成本分摊
"""

from fastapi import APIRouter

from .alert import router as alert_router
from .allocation import router as allocation_router
from .analysis import router as analysis_router
from .budget import router as budget_router
from .cost_prediction_ai import router as cost_prediction_ai_router
from .crud import router as crud_router
from .evm import router as evm_router
from .forecast import router as forecast_router
from .labor import router as labor_router
from .review import router as review_router
from .summary import router as summary_router

router = APIRouter()

# 注意：路由顺序很重要！
# 静态路径（如 /summary）必须在动态路径（如 /{cost_id}）之前注册
# 否则 /summary 会被 /{cost_id} 匹配，导致 "summary" 被解析为整数失败

# 先注册自定义端点（静态路径）
router.include_router(summary_router, tags=["projects-costs-summary"])
router.include_router(analysis_router, tags=["projects-costs-analysis"])
router.include_router(forecast_router, tags=["projects-costs-forecast"])
router.include_router(budget_router, tags=["projects-costs-budget"])
router.include_router(labor_router, tags=["projects-costs-labor"])
router.include_router(review_router, tags=["projects-costs-review"])
router.include_router(alert_router, tags=["projects-costs-alert"])
router.include_router(evm_router, tags=["projects-costs-evm"])
router.include_router(cost_prediction_ai_router, tags=["projects-costs-prediction-ai"])

# 再注册CRUD路由（由基类提供）- 动态路径
router.include_router(crud_router, tags=["projects-costs-crud"])

# 最后注册成本分摊路由（需要 cost_id 参数）
router.include_router(allocation_router, tags=["projects-costs-allocation"])
