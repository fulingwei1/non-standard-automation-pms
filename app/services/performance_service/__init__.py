# -*- coding: utf-8 -*-
"""
绩效管理服务模块

聚合所有绩效管理相关的服务，保持向后兼容
"""
from .base import PerformanceService
from .calculation import (
    calculate_final_score,
    calculate_quarterly_score,
    get_score_level,
)
from .evaluation import create_evaluation_tasks
from .history import get_historical_performance
from .roles import get_manageable_employees, get_user_manager_roles

__all__ = ["PerformanceService"]

# 将方法添加到类中，保持向后兼容
def _patch_methods():
    """将模块函数作为静态方法添加到类中"""
    PerformanceService.get_user_manager_roles = staticmethod(get_user_manager_roles)
    PerformanceService.get_manageable_employees = staticmethod(get_manageable_employees)
    PerformanceService.create_evaluation_tasks = staticmethod(create_evaluation_tasks)
    PerformanceService.calculate_final_score = staticmethod(calculate_final_score)
    PerformanceService.calculate_quarterly_score = staticmethod(calculate_quarterly_score)
    PerformanceService.get_score_level = staticmethod(get_score_level)
    PerformanceService.get_historical_performance = staticmethod(get_historical_performance)

_patch_methods()
