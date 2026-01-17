# -*- coding: utf-8 -*-
"""
物料需求计划(MRP) API endpoints

已拆分为模块化结构，详见 material_demands/ 目录：
- demands.py: 物料需求列表与库存对比
- generate.py: 自动生成采购需求
- schedule.py: 需求时间表
- forecast.py: 物料交期预测
"""

from .material_demands import router

__all__ = ["router"]
