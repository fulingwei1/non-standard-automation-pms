# -*- coding: utf-8 -*-
"""
物料CRUD端点
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.material import (
    MaterialCreate,
    MaterialResponse,
    MaterialUpdate,
)
from app.services.material_service import MaterialService

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[MaterialResponse])
def read_materials(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="每页数量",
    ),
    keyword: Optional[str] = Query(None, description="关键词搜索（物料编码/名称）"),
    category_id: Optional[int] = Query(None, description="分类ID筛选"),
    material_type: Optional[str] = Query(None, description="物料类型筛选"),
    is_key_material: Optional[bool] = Query(None, description="是否关键物料"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> Any:
    """获取物料列表（支持分页、搜索、筛选）"""
    service = MaterialService(db)
    result = service.list_materials(
        page=page,
        page_size=page_size,
        keyword=keyword,
        category_id=category_id,
        material_type=material_type,
        is_key_material=is_key_material,
        is_active=is_active,
    )
    return PaginatedResponse(**result)


@router.get("/{material_id}", response_model=MaterialResponse)
def read_material(
    *,
    db: Session = Depends(deps.get_db),
    material_id: int,
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> Any:
    """获取物料详情"""
    service = MaterialService(db)
    return service.get(material_id)


@router.post("/", response_model=MaterialResponse)
def create_material(
    *,
    db: Session = Depends(deps.get_db),
    material_in: MaterialCreate,
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> Any:
    """
    创建新物料

    如果未提供物料编码，系统将根据物料类别自动生成 MAT-{类别}-xxxxx 格式的编码
    """
    service = MaterialService(db)

    # 如果没有提供物料编码，自动生成
    if not material_in.material_code:
        material_in.material_code = service.generate_code(material_in.category_id)

    # 业务逻辑（唯一性检查、外键检查）将在 Service 层处理或通过 check_unique 参数
    return service.create(
        material_in, check_unique={"material_code": material_in.material_code}
    )


@router.put("/{material_id}", response_model=MaterialResponse)
def update_material(
    *,
    db: Session = Depends(deps.get_db),
    material_id: int,
    material_in: MaterialUpdate,
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> Any:
    """更新物料信息"""
    service = MaterialService(db)
    return service.update(material_id, material_in)
