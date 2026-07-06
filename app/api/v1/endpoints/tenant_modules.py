# -*- coding: utf-8 -*-
"""租户模块开通管理 API。

- 超管：查看/设置任意租户的模块开通（/tenants/{id}/modules）。
- 租户用户：查看自己租户的生效模块（/my/modules），供前端菜单闸门使用。
模块清单权威来源：app/modules/registry.py。
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_super_admin
from app.core import security
from app.models.user import User
from app.services.tenant_module_service import TenantModuleService

router = APIRouter()


class ModuleStateResponse(BaseModel):
    key: str
    name: str
    always_on: bool
    depends_on: List[str]
    enabled: bool
    status: Optional[str] = None
    expires_at: Optional[datetime] = None


class ModuleSetRequest(BaseModel):
    status: str  # ENABLED / DISABLED / TRIAL
    expires_at: Optional[datetime] = None


@router.get("/my/modules", response_model=List[ModuleStateResponse])
def list_my_modules(
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """当前租户的模块生效快照（前端菜单/路由闸门数据源）。"""
    return TenantModuleService(db).list_effective_modules(current_user.tenant_id)


@router.get("/tenants/{tenant_id}/modules", response_model=List[ModuleStateResponse])
def list_tenant_modules(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    return TenantModuleService(db).list_effective_modules(tenant_id)


@router.put("/tenants/{tenant_id}/modules/{module_key}", response_model=ModuleStateResponse)
def set_tenant_module(
    tenant_id: int,
    module_key: str,
    payload: ModuleSetRequest,
    db: Session = Depends(get_db),
    operator: User = Depends(require_super_admin),
):
    svc = TenantModuleService(db)
    try:
        svc.set_module(
            tenant_id,
            module_key,
            payload.status,
            expires_at=payload.expires_at,
            operator_id=operator.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return next(m for m in svc.list_effective_modules(tenant_id) if m["key"] == module_key)
