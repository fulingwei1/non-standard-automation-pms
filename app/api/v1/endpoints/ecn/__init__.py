# -*- coding: utf-8 -*-
"""
设计变更管理(ECN)模块路由聚合

将拆分后的各个子模块路由聚合到统一的router中
"""

# -*- coding: utf-8 -*-
"""
设计变更管理(ECN)模块路由聚合

将拆分后的各个子模块路由聚合到统一的router中
"""

from fastapi import APIRouter

# 创建主路由
router = APIRouter()

# 导入子路由
from . import (
    alerts,
    analysis,
    approval,
    core,
    cost_impact,
    evaluations,
    execution,
    impacts,
    integration,
    material_impact,
    state_machine,
    statistics,
    tasks,
    types,
)

# 聚合所有子路由（保持原有路由路径）
# 注意：路由的顺序很重要，更具体的路由应该放在前面

# 统计路由（/ecns/statistics 需要放在 /ecns/{ecn_id} 前面）
router.include_router(statistics.router, tags=["ecn-statistics"])

# 超时提醒路由（/ecns/overdue-alerts 需要放在 /ecns/{ecn_id} 前面）
router.include_router(alerts.router, tags=["ecn-alerts"])

# 核心CRUD路由
router.include_router(core.router, tags=["ecn-core"])

# 评估管理路由
router.include_router(evaluations.router, tags=["ecn-evaluations"])

# 审批管理路由已移至统一审批系统
# 使用 /api/v1/approvals 端点，entity_type=ECN
# 或使用下面的ECN专用审批端点
router.include_router(approval.router, tags=["ecn-approval"])

# 任务管理路由
router.include_router(tasks.router, tags=["ecn-tasks"])

# 受影响物料/订单路由
router.include_router(impacts.router, tags=["ecn-impacts"])

# 执行流程路由
router.include_router(execution.router, tags=["ecn-execution"])

# 状态机路由
router.include_router(state_machine.router, tags=["ecn-state-machine"])

# ECN类型配置路由
router.include_router(types.router, tags=["ecn-types"])

# 模块集成/同步路由
router.include_router(integration.router, tags=["ecn-integration"])

# 分析相关路由（BOM影响、责任分摊、RCA、知识库）
router.include_router(analysis.router, tags=["ecn-analysis"])

# 物料影响跟踪路由（影响分析/执行进度/相关人员/通知/处置）
router.include_router(material_impact.router, tags=["ecn-material-impact"])

# ECN成本影响跟踪路由（成本分析/执行跟踪/成本记录/预警）
router.include_router(cost_impact.router, tags=["ecn-cost-impact"])
