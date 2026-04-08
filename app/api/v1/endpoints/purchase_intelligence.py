# -*- coding: utf-8 -*-
"""
Purchase Intelligence 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for purchase_intelligence
    from .purchaseintelligence import router
except ImportError:
    try:
        from .purchase import router
    except ImportError:
        try:
            from .common.purchase_intelligence import router
        except ImportError:
            try:
                from .admin.purchase_intelligence import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter
                router = APIRouter()
                @router.get('/')
                def read_root():
                    return {'message': 'purchase_intelligence module placeholder'}

__all__ = ['router']
