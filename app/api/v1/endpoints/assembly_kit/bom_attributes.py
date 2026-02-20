# -*- coding: utf-8 -*-
"""
BOM装配属性 - 自动生成
从 assembly_kit.py 拆分
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models import User
from app.schemas.assembly_kit import (
    BomAssemblyAttrsAutoRequest,
    BomAssemblyAttrsTemplateRequest,
    BomItemAssemblyAttrsBatchCreate,
    BomItemAssemblyAttrsUpdate,
)
from app.schemas.common import ResponseModel
from app.services.bom_attributes import BomAttributesService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/assembly-kit/bom-attributes",
    tags=["bom_attributes"]
)


@router.get("/bom/{bom_id}/assembly-attrs", response_model=ResponseModel)
async def get_bom_assembly_attrs(
    bom_id: int,
    db: Session = Depends(deps.get_db),
    stage_code: Optional[str] = Query(None, description="筛选装配阶段"),
    is_blocking: Optional[bool] = Query(None, description="筛选阻塞性物料")
):
    """获取BOM装配属性列表"""
    service = BomAttributesService(db)
    result = service.get_bom_assembly_attrs(bom_id, stage_code, is_blocking)
    return ResponseModel(code=200, message="success", data=result)


@router.post("/bom/{bom_id}/assembly-attrs/batch", response_model=ResponseModel)
async def batch_set_assembly_attrs(
    bom_id: int,
    batch_data: BomItemAssemblyAttrsBatchCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("assembly_kit:create"))
):
    """批量设置BOM装配属性"""
    service = BomAttributesService(db)
    result = service.batch_set_assembly_attrs(bom_id, batch_data.items)

    return ResponseModel(
        code=200,
        message=f"批量设置完成，新增 {result['created']} 条，更新 {result['updated']} 条",
        data=result
    )


@router.put("/bom/assembly-attrs/{attr_id}", response_model=ResponseModel)
async def update_assembly_attr(
    attr_id: int,
    attr_data: BomItemAssemblyAttrsUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("assembly_kit:update"))
):
    """更新单个物料装配属性"""
    service = BomAttributesService(db)
    update_data = attr_data.model_dump(exclude_unset=True)
    result = service.update_assembly_attr(attr_id, update_data)

    return ResponseModel(code=200, message="更新成功", data=result)


@router.post("/bom/{bom_id}/assembly-attrs/auto", response_model=ResponseModel)
async def auto_assign_assembly_attrs(
    bom_id: int,
    request: BomAssemblyAttrsAutoRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("assembly_kit:create"))
):
    """自动分配装配属性（基于物料分类映射）"""
    service = BomAttributesService(db)
    result = service.auto_assign_assembly_attrs(bom_id, request.overwrite)

    return ResponseModel(
        code=200,
        message=f"自动分配完成，处理 {result['assigned']} 条，跳过 {result['skipped']} 条",
        data=result
    )


@router.get("/bom/{bom_id}/assembly-attrs/recommendations", response_model=ResponseModel)
async def get_assembly_attr_recommendations(
    bom_id: int,
    db: Session = Depends(deps.get_db)
):
    """获取装配属性推荐结果（不应用，仅返回推荐）"""
    service = BomAttributesService(db)
    result = service.get_assembly_attr_recommendations(bom_id)

    return ResponseModel(
        code=200,
        message="推荐结果获取成功",
        data=result
    )


@router.post("/bom/{bom_id}/assembly-attrs/smart-recommend", response_model=ResponseModel)
async def smart_recommend_assembly_attrs(
    bom_id: int,
    request: BomAssemblyAttrsAutoRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("assembly_kit:create"))
):
    """智能推荐装配属性（多级推荐规则）"""
    service = BomAttributesService(db)
    result = service.smart_recommend_assembly_attrs(
        bom_id,
        request.overwrite,
        current_user.id
    )

    return ResponseModel(
        code=200,
        message=f"智能推荐完成，处理 {result['assigned']} 条，跳过 {result['skipped']} 条",
        data=result
    )


@router.post("/bom/{bom_id}/assembly-attrs/template", response_model=ResponseModel)
async def apply_assembly_template(
    bom_id: int,
    request: BomAssemblyAttrsTemplateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("assembly_kit:create"))
):
    """套用装配模板"""
    service = BomAttributesService(db)
    result = service.apply_assembly_template(bom_id, request.template_id, request.overwrite)

    return ResponseModel(
        code=200,
        message=f"模板套用完成，应用 {result['applied']} 条配置",
        data=result
    )
