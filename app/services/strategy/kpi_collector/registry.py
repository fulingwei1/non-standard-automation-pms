# -*- coding: utf-8 -*-
"""
KPI数据采集器 - 注册器
"""
from typing import Callable, Dict, Optional

# 数据采集器注册表
_collectors: Dict[str, Callable] = {}


def register_collector(module: str):
    """装饰器：注册数据采集器"""
    def decorator(func: Callable):
        _collectors[module] = func
        return func
    return decorator


def get_collector(module: str) -> Optional[Callable]:
    """获取数据采集器"""
    return _collectors.get(module)
