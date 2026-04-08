# -*- coding: utf-8 -*-
"""
Margin Prediction 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for margin_prediction
    from .marginprediction import router
except ImportError:
    try:
        from .margin import router
    except ImportError:
        try:
            from .common.margin_prediction import router
        except ImportError:
            try:
                from .admin.margin_prediction import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter
                router = APIRouter()
                @router.get('/')
                def read_root():
                    return {'message': 'margin_prediction module placeholder'}

__all__ = ['router']
