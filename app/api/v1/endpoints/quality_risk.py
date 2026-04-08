# -*- coding: utf-8 -*-
"""
Quality Risk 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for quality_risk
    from .qualityrisk import router
except ImportError:
    try:
        from .quality import router
    except ImportError:
        try:
            from .common.quality_risk import router
        except ImportError:
            try:
                from .admin.quality_risk import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter
                router = APIRouter()
                @router.get('/')
                def read_root():
                    return {'message': 'quality_risk module placeholder'}

__all__ = ['router']
