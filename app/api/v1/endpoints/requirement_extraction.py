# -*- coding: utf-8 -*-
"""
Requirement Extraction 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for requirement_extraction
    from .requirementextraction import router
except ImportError:
    try:
        from .requirement import router
    except ImportError:
        try:
            from .common.requirement_extraction import router
        except ImportError:
            try:
                from .admin.requirement_extraction import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter
                router = APIRouter()
                @router.get('/')
                def read_root():
                    return {'message': 'requirement_extraction module placeholder'}

__all__ = ['router']
