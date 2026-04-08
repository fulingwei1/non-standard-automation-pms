# -*- coding: utf-8 -*-
"""
Labor Cost Detail 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Look for labor cost related modules in likely locations
    from .cost_endpoints.labor_cost_detail import router
except ImportError:
    try:
        from .costs.labor_cost_detail import router
    except ImportError:
        try:
            from .production.labor_cost_detail import router
        except ImportError:
            try:
                from .timesheet.labor_cost_detail import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter
                router = APIRouter()
                @router.get('/')
                def read_root():
                    return {'message': 'labor_cost_detail module placeholder'}

__all__ = ['router']