# -*- coding: utf-8 -*-
"""
Cost Variance Analysis 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for cost_variance_analysis
    from .costvarianceanalysis import router
except ImportError:
    try:
        from .cost import router
    except ImportError:
        try:
            from .common.cost_variance_analysis import router
        except ImportError:
            try:
                from .admin.cost_variance_analysis import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter
                router = APIRouter()
                @router.get('/')
                def read_root():
                    return {'message': 'cost_variance_analysis module placeholder'}

__all__ = ['router']
