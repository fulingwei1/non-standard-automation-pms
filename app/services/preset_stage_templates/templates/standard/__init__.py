# -*- coding: utf-8 -*-
"""
标准全流程模板模块
包含 S1-S9 的所有阶段

此模块已拆分为多个子模块：
- planning: 规划和设计阶段 (S1-S3)
- production: 生产和验收阶段 (S4-S6)
- delivery: 交付和结项阶段 (S7-S9)
"""

from typing import Any, Dict, List

from .delivery import DELIVERY_STAGES
from .planning import PLANNING_STAGES
from .production import PRODUCTION_STAGES

# 标准全流程阶段 (S1-S9) - 聚合所有阶段
STANDARD_STAGES: List[Dict[str, Any]] = (
    PLANNING_STAGES
    + PRODUCTION_STAGES
    + DELIVERY_STAGES
)

# 标准全流程模板（9大阶段）
STANDARD_TEMPLATE: Dict[str, Any] = {
    "template_code": "TPL_STANDARD",
    "template_name": "标准全流程",
    "description": "适用于新产品开发的完整流程，包含售前支持、方案设计、采购、生产、调试、验收、交付全过程",
    "project_type": "NEW",
    "stages": STANDARD_STAGES,
}

__all__ = [
    "STANDARD_STAGES",
    "STANDARD_TEMPLATE",
    "PLANNING_STAGES",
    "PRODUCTION_STAGES",
    "DELIVERY_STAGES",
]
