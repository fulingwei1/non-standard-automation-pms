# -*- coding: utf-8 -*-
"""
状态处理器模块

按业务领域拆分的状态变更处理器：
- contract_handler: 合同签订事件处理
- material_handler: BOM和物料事件处理
- acceptance_handler: 验收事件处理
- ecn_handler: ECN变更事件处理

注意：所有导入延迟执行，避免与 status_transition_service 的循环依赖
"""

# 不在模块级别导入，避免循环依赖
# 如果需要使用这些类，请直接从子模块导入：
#   from app.services.status_handlers.contract_handler import ContractStatusHandler


def register_all_handlers():
    """注册所有的状态变更处理器"""
    # 延迟导入，避免循环依赖
    from app.services.status_handlers.milestone_handler import register_milestone_handlers

    register_milestone_handlers()
    # 未来可以在这里添加更多注册函数
    # register_contract_handlers() etc.


# 为了保持向后兼容，提供延迟加载的接口
def get_contract_handler():
    """延迟加载 ContractStatusHandler"""
    from app.services.status_handlers.contract_handler import ContractStatusHandler
    return ContractStatusHandler


def get_material_handler():
    """延迟加载 MaterialStatusHandler"""
    from app.services.status_handlers.material_handler import MaterialStatusHandler
    return MaterialStatusHandler


def get_acceptance_handler():
    """延迟加载 AcceptanceStatusHandler"""
    from app.services.status_handlers.acceptance_handler import AcceptanceStatusHandler
    return AcceptanceStatusHandler


def get_ecn_handler():
    """延迟加载 ECNStatusHandler"""
    from app.services.status_handlers.ecn_handler import ECNStatusHandler
    return ECNStatusHandler


def get_milestone_handler():
    """延迟加载 MilestoneStatusHandler"""
    from app.services.status_handlers.milestone_handler import MilestoneStatusHandler
    return MilestoneStatusHandler


__all__ = [
    "register_all_handlers",
    "get_contract_handler",
    "get_material_handler",
    "get_acceptance_handler",
    "get_ecn_handler",
    "get_milestone_handler",
]

