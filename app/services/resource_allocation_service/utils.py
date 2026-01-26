# -*- coding: utf-8 -*-
"""
资源分配服务 - 工具函数
"""
from datetime import date
from typing import Tuple


def calculate_workdays(start_date: date, end_date: date) -> int:
    """计算工作日数量（简单实现，不考虑节假日）"""
    days = (end_date - start_date).days + 1
    # 简单计算：每周5个工作日
    weeks = days // 7
    workdays = weeks * 5 + min(days % 7, 5)
    return max(1, workdays)


def calculate_overlap_days(
    start1: date,
    end1: date,
    start2: date,
    end2: date
) -> int:
    """计算两个日期区间的重叠天数"""
    overlap_start = max(start1, start2)
    overlap_end = min(end1, end2)

    if overlap_start > overlap_end:
        return 0

    return (overlap_end - overlap_start).days + 1
