# -*- coding: utf-8 -*-
"""
AI Strategy 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for ai_strategy
    from .ai_strategy.ai_strategy import router
except ImportError:
    try:
        from .ai import router
    except ImportError:
        try:
            from .strategy import router
        except ImportError:
            try:
                from .ai_assistant import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter
                router = APIRouter()
                @router.get('/')
                def read_root():
                    return {'message': 'ai_strategy module placeholder'}

__all__ = ['router']