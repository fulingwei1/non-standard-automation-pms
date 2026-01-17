# -*- coding: utf-8 -*-
"""
绩效数据自动采集服务模块

此模块提供工程师绩效数据自动采集功能，从各个系统自动提取绩效评价所需的数据。

模块结构：
- constants: 关键词常量定义
- work_log: 工作日志数据采集
"""

# 从常量模块导出所有关键词
from .constants import (
    COLLABORATION_KEYWORDS,
    KNOWLEDGE_SHARING_PATTERNS,
    NEGATIVE_KEYWORDS,
    POSITIVE_KEYWORDS,
    PROBLEM_SOLVING_PATTERNS,
    TECH_BREAKTHROUGH_PATTERNS,
    TECH_KEYWORDS,
)

# 从工作日志模块导出采集函数
from .work_log import extract_self_evaluation_from_work_logs

__all__ = [
    # 常量
    'POSITIVE_KEYWORDS',
    'NEGATIVE_KEYWORDS',
    'TECH_KEYWORDS',
    'COLLABORATION_KEYWORDS',
    'PROBLEM_SOLVING_PATTERNS',
    'KNOWLEDGE_SHARING_PATTERNS',
    'TECH_BREAKTHROUGH_PATTERNS',
    # 函数
    'extract_self_evaluation_from_work_logs',
]
