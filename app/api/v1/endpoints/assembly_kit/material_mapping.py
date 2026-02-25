# -*- coding: utf-8 -*-
"""
物料分类映射 - 自动生成
从 assembly_kit.py 拆分
"""

# -*- coding: utf-8 -*-
"""
齐套分析模块 API 端点

基于装配工艺路径的智能齐套分析系统
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models import (
    AssemblyStage,
    CategoryStageMapping,
    MaterialCategory,
    User,
)
from app.schemas.assembly_kit import (  # Stage; Template; Category Mapping; BOM Assembly Attrs; Readiness; Shortage; Alert Rule; Suggestion; Dashboard
    CategoryStageMappingCreate,
    CategoryStageMappingResponse,
    CategoryStageMappingUpdate,
)
from app.schemas.common import MessageResponse, ResponseModel

router = APIRouter()



from fastapi import APIRouter
from app.utils.db_helpers import get_or_404

router = APIRouter(
    prefix="/assembly-kit/material-mapping",
    tags=["material_mapping"]
)

# 共 4 个路由

# ==================== 物料分类映射 ====================

@router.get("/category-mappings", response_model=ResponseModel)
async def get_category_mappings(
    db: Session = Depends(deps.get_db),
    category_id: Optional[int] = Query(None, description="物料分类ID"),
    stage_code: Optional[str] = Query(None, description="装配阶段编码")
):
    """获取物料分类映射列表"""
    query = db.query(CategoryStageMapping)
    if category_id:
        query = query.filter(CategoryStageMapping.category_id == category_id)
    if stage_code:
        query = query.filter(CategoryStageMapping.stage_code == stage_code)

    mappings = query.all()

    # 关联物料分类和阶段名称
    result = []
    for m in mappings:
        data = CategoryStageMappingResponse.model_validate(m)
        category = db.query(MaterialCategory).filter(MaterialCategory.id == m.category_id).first()
        stage = db.query(AssemblyStage).filter(AssemblyStage.stage_code == m.stage_code).first()
        data.category_name = category.name if category else None
        data.stage_name = stage.stage_name if stage else None
        result.append(data)

    return ResponseModel(code=200, message="success", data=result)


@router.post("/category-mappings", response_model=ResponseModel)
async def create_category_mapping(
    mapping_data: CategoryStageMappingCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("assembly_kit:create"))
):
    """创建物料分类映射"""
    # 检查是否已存在
    existing = db.query(CategoryStageMapping).filter(
        CategoryStageMapping.category_id == mapping_data.category_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该物料分类已存在映射配置")

    mapping = CategoryStageMapping(**mapping_data.model_dump())
    db.add(mapping)
    db.commit()
    db.refresh(mapping)

    return ResponseModel(
        code=200,
        message="创建成功",
        data=CategoryStageMappingResponse.model_validate(mapping)
    )


@router.put("/category-mappings/{mapping_id}", response_model=ResponseModel)
async def update_category_mapping(
    mapping_id: int,
    mapping_data: CategoryStageMappingUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("assembly_kit:update"))
):
    """更新物料分类映射"""
    mapping = get_or_404(db, CategoryStageMapping, mapping_id, "映射配置不存在")

    update_data = mapping_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(mapping, key, value)
    mapping.updated_at = datetime.now()

    db.commit()
    db.refresh(mapping)

    return ResponseModel(code=200, message="更新成功", data=CategoryStageMappingResponse.model_validate(mapping))


@router.delete("/category-mappings/{mapping_id}", response_model=MessageResponse)
async def delete_category_mapping(
    mapping_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("assembly_kit:delete"))
):
    """删除物料分类映射"""
    mapping = get_or_404(db, CategoryStageMapping, mapping_id, "映射配置不存在")

    db.delete(mapping)
    db.commit()

    return MessageResponse(code=200, message="删除成功")



