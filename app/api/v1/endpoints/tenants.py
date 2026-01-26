# -*- coding: utf-8 -*-
"""
租户管理 API 端点

提供租户的 CRUD 操作和初始化功能。
仅平台管理员（超级管理员）可访问。
"""


from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.tenant import (
    TenantCreate,
    TenantInitRequest,
    TenantResponse,
    TenantUpdate,
)
from app.services.tenant_service import TenantService

router = APIRouter(prefix="/tenants", tags=["租户管理"])


def require_super_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """要求超级管理员权限"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )
    return current_user


@router.post("/", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_tenant(
    tenant_in: TenantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """创建租户"""
    service = TenantService(db)
    try:
        tenant = service.create_tenant(tenant_in)
        return ResponseModel(
            code=201,
            message="创建租户成功",
            data=TenantResponse.model_validate(tenant).model_dump()
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=ResponseModel)
def list_tenants(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: str | None = Query(None, description="状态筛选"),
    keyword: str | None = Query(None, description="关键词搜索"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """获取租户列表"""
    service = TenantService(db)
    result = service.list_tenants(page=page, page_size=page_size, status=status, keyword=keyword)

    # 转换为响应格式
    items = [TenantResponse.model_validate(t).model_dump() for t in result["items"]]

    return ResponseModel(
        code=200,
        message="获取成功",
        data={
            "items": items,
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"],
            "pages": result["pages"],
        }
    )


@router.get("/{tenant_id}", response_model=ResponseModel)
def get_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """获取租户详情"""
    service = TenantService(db)
    tenant = service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="租户不存在")

    return ResponseModel(
        code=200,
        message="获取成功",
        data=TenantResponse.model_validate(tenant).model_dump()
    )


@router.put("/{tenant_id}", response_model=ResponseModel)
def update_tenant(
    tenant_id: int,
    tenant_in: TenantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """更新租户"""
    service = TenantService(db)
    tenant = service.update_tenant(tenant_id, tenant_in)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="租户不存在")

    return ResponseModel(
        code=200,
        message="更新成功",
        data=TenantResponse.model_validate(tenant).model_dump()
    )


@router.delete("/{tenant_id}", response_model=ResponseModel)
def delete_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """删除租户（软删除）"""
    service = TenantService(db)
    success = service.delete_tenant(tenant_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="租户不存在")

    return ResponseModel(code=200, message="删除成功")


@router.post("/{tenant_id}/init", response_model=ResponseModel)
def init_tenant(
    tenant_id: int,
    init_data: TenantInitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """初始化租户数据（创建默认角色和管理员）"""
    service = TenantService(db)
    try:
        result = service.init_tenant(tenant_id, init_data)
        return ResponseModel(code=200, message="初始化成功", data=result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{tenant_id}/stats", response_model=ResponseModel)
def get_tenant_stats(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """获取租户统计信息"""
    service = TenantService(db)
    stats = service.get_tenant_stats(tenant_id)
    if not stats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="租户不存在")

    return ResponseModel(code=200, message="获取成功", data=stats)
