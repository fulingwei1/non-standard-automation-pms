# -*- coding: utf-8 -*-
"""
Sales Teams 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for sales_teams
    from .salesteams import router
except ImportError:
    try:
        from .sales import router
    except ImportError:
        try:
            from .common.sales_teams import router
        except ImportError:
            try:
                from .admin.sales_teams import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter
                router = APIRouter()
                @router.get('/')
                def read_root():
                    return {'message': 'sales_teams module placeholder'}

__all__ = ['router']
