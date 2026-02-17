# -*- coding: utf-8 -*-
"""
project_cost 兼容模块 - 从 project/financial.py 重新导出
"""
from app.models.project.financial import ProjectCost  # noqa: F401

__all__ = ["ProjectCost"]
