# -*- coding: utf-8 -*-
"""
项目执行阶段定义模块
包含 S09-S20 的所有执行阶段

此模块已拆分为多个子模块：
- project_initiation: 项目启动和设计阶段 (S09-S12)
- procurement_assembly: 采购和装配阶段 (S13-S16)
- testing_acceptance: 调试和验收阶段 (S17-S20)
"""

from typing import Any, Dict, List

from .procurement_assembly import PROCUREMENT_ASSEMBLY_STAGES
from .project_initiation import PROJECT_INITIATION_STAGES
from .testing_acceptance import TESTING_ACCEPTANCE_STAGES

# 项目执行阶段 (S09-S20) - 聚合所有阶段
EXECUTION_STAGES: List[Dict[str, Any]] = (
    PROJECT_INITIATION_STAGES
    + PROCUREMENT_ASSEMBLY_STAGES
    + TESTING_ACCEPTANCE_STAGES
)

__all__ = [
    "EXECUTION_STAGES",
    "PROJECT_INITIATION_STAGES",
    "PROCUREMENT_ASSEMBLY_STAGES",
    "TESTING_ACCEPTANCE_STAGES",
]
