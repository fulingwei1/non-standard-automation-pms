# -*- coding: utf-8 -*-
"""
齐套率与物料保障 API endpoints

已拆分为模块化结构，详见 kit_rate/ 目录：
- utils.py: 齐套率计算工具函数
- machine.py: 机台级齐套率、物料状态
- project.py: 项目级齐套率、物料汇总、缺料清单
- dashboard.py: 齐套看板、趋势分析
"""

from .kit_rate import router

__all__ = ["router"]
