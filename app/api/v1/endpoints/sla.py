# -*- coding: utf-8 -*-
"""
SLA管理 API endpoints

已拆分为模块化结构，详见 sla/ 目录：
- policies.py: SLA策略管理
- monitors.py: SLA监控记录
- statistics.py: SLA统计分析
"""

from .sla import router

__all__ = ["router"]
