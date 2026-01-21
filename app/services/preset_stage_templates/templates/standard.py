# -*- coding: utf-8 -*-
"""
标准全流程模板（9大阶段）

TPL_STANDARD - 标准全流程（新产品完整流程）

注意：此文件已拆分为多个模块文件，位于 standard/ 目录下
此文件仅用于向后兼容，重新导出模板
"""

# 从拆分后的包重新导出
from .standard import STANDARD_TEMPLATE, STANDARD_STAGES

__all__ = ["STANDARD_TEMPLATE", "STANDARD_STAGES"]
