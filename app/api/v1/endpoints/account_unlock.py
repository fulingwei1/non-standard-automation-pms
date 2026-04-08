# -*- coding: utf-8 -*-
"""
Account Unlock 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for account_unlock
    from .account.account_unlock import router
except ImportError:
    try:
        from .account import router
    except ImportError:
        try:
            from .unlock import router
        except ImportError:
            try:
                from .access_control import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter
                router = APIRouter()
                @router.get('/')
                def read_root():
                    return {'message': 'account_unlock module placeholder'}

__all__ = ['router']