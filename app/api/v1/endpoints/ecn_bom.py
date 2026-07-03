# -*- coding: utf-8 -*-
"""
Ecn Bom 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for ecn_bom
    from .ecnbom import router
except ImportError:
    try:
        from .common.ecn_bom import router
    except ImportError:
        try:
            from .admin.ecn_bom import router
        except ImportError:
            from fastapi import APIRouter

            router = APIRouter()

__all__ = ['router']
