# -*- coding: utf-8 -*-
"""
工程师绩效数据自动采集服务
从各个系统自动提取绩效评价所需的数据

向后兼容：保持原有的 PerformanceDataCollector 类接口
"""

from sqlalchemy.orm import Session

from .aggregator import PerformanceDataAggregator
from .base import PerformanceDataCollectorBase

# 向后兼容：使用 PerformanceDataAggregator 作为主类
PerformanceDataCollector = PerformanceDataAggregator

__all__ = [
    'PerformanceDataCollector',
    'PerformanceDataCollectorBase',
    'PerformanceDataAggregator',
]
