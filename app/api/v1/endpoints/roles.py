# -*- coding: utf-8 -*-
"""
Roles 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Roles is typically in access control or auth related areas
    from .access_control.roles import router
except ImportError:
    try:
        from .auth.roles import router
    except ImportError:
        try:
            from .permissions.roles import router
        except ImportError:
            try:
                from .user.roles import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter, HTTPException

                router = APIRouter(prefix="/roles", tags=["roles"])

                def _not_implemented():
                    raise HTTPException(status_code=404, detail="Roles API not implemented")

                @router.get('/')
                def read_root():
                    _not_implemented()

                @router.get('/permissions')
                def list_permissions():
                    _not_implemented()

                @router.post('/')
                def create_role(payload: dict | None = None):
                    _not_implemented()

                # 静态路由必须放在动态路由前，避免被 /{role_id} 误吞
                @router.get('/templates')
                def role_templates():
                    _not_implemented()

                @router.get('/{role_id}')
                def get_role(role_id: int):
                    _not_implemented()

                @router.put('/{role_id}')
                def update_role(role_id: int, payload: dict | None = None):
                    _not_implemented()

                @router.delete('/{role_id}')
                def delete_role(role_id: int):
                    _not_implemented()

__all__ = ['router']
