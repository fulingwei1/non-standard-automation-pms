# -*- coding: utf-8 -*-
"""
调度器管理 API endpoints

已拆分为模块化结构，详见 scheduler/ 目录：
- status.py: 调度器状态、任务列表、手动触发、服务列表
- metrics.py: 运行指标（JSON和Prometheus格式）
- configs.py: 定时任务配置管理
"""

from .scheduler import router

__all__ = ["router"]
