# -*- coding: utf-8 -*-
"""
BOM装配属性 - 自动生成
从 assembly_kit.py 拆分
"""

# -*- coding: utf-8 -*-
"""
齐套分析模块 API 端点

基于装配工艺路径的智能齐套分析系统
"""

import json
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.api import deps
from app.core import security
from app.models import (
    AssemblyStage, AssemblyTemplate, CategoryStageMapping,
    BomItemAssemblyAttrs, MaterialReadiness, ShortageDetail,
    ShortageAlertRule, SchedulingSuggestion,
    Project, Machine, BomHeader, BomItem, Material, MaterialCategory,
    User
)
from app.models.enums import (
    AssemblyStageEnum, ImportanceLevelEnum, ShortageAlertLevelEnum,
    SuggestionTypeEnum, SuggestionStatusEnum
)
from app.schemas.assembly_kit import (
    # Stage
    AssemblyStageCreate, AssemblyStageUpdate, AssemblyStageResponse,
    # Template
    AssemblyTemplateCreate, AssemblyTemplateUpdate, AssemblyTemplateResponse,
    # Category Mapping
    CategoryStageMappingCreate, CategoryStageMappingUpdate, CategoryStageMappingResponse,
    # BOM Assembly Attrs
    BomItemAssemblyAttrsCreate, BomItemAssemblyAttrsBatchCreate,
    BomItemAssemblyAttrsUpdate, BomItemAssemblyAttrsResponse,
    BomAssemblyAttrsAutoRequest, BomAssemblyAttrsTemplateRequest,
    # Readiness
    MaterialReadinessCreate, MaterialReadinessResponse, MaterialReadinessDetailResponse, StageKitRate,
    # Shortage
    ShortageDetailResponse, ShortageAlertItem, ShortageAlertListResponse,
    # Alert Rule
    ShortageAlertRuleCreate, ShortageAlertRuleUpdate, ShortageAlertRuleResponse,
    # Suggestion
    SchedulingSuggestionResponse, SchedulingSuggestionAccept, SchedulingSuggestionReject,
    # Dashboard
    AssemblyDashboardResponse, AssemblyDashboardStats, AssemblyDashboardStageStats
)
from app.schemas.common import ResponseModel, MessageResponse

router = APIRouter()



from fastapi import APIRouter

router = APIRouter(
    prefix="/assembly-kit/bom-attributes",
    tags=["bom_attributes"]
)

# 共 7 个路由

# ==================== BOM装配属性 ====================

@router.get("/bom/{bom_id}/assembly-attrs", response_model=ResponseModel)
async def get_bom_assembly_attrs(
    bom_id: int,
    db: Session = Depends(deps.get_db),
    stage_code: Optional[str] = Query(None, description="筛选装配阶段"),
    is_blocking: Optional[bool] = Query(None, description="筛选阻塞性物料")
):
    """获取BOM装配属性列表"""
    # 验证BOM存在
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")

    query = db.query(BomItemAssemblyAttrs).filter(BomItemAssemblyAttrs.bom_id == bom_id)
    if stage_code:
        query = query.filter(BomItemAssemblyAttrs.assembly_stage == stage_code)
    if is_blocking is not None:
        query = query.filter(BomItemAssemblyAttrs.is_blocking == is_blocking)

    attrs = query.order_by(BomItemAssemblyAttrs.assembly_stage, BomItemAssemblyAttrs.stage_order).all()

    # 关联物料信息
    result = []
    for attr in attrs:
        data = BomItemAssemblyAttrsResponse.model_validate(attr)
        bom_item = db.query(BomItem).filter(BomItem.id == attr.bom_item_id).first()
        if bom_item:
            material = db.query(Material).filter(Material.id == bom_item.material_id).first()
            if material:
                data.material_code = material.code
                data.material_name = material.name
            data.required_qty = bom_item.quantity
        stage = db.query(AssemblyStage).filter(AssemblyStage.stage_code == attr.assembly_stage).first()
        if stage:
            data.stage_name = stage.stage_name
        result.append(data)

    return ResponseModel(code=200, message="success", data=result)


@router.post("/bom/{bom_id}/assembly-attrs/batch", response_model=ResponseModel)
async def batch_set_assembly_attrs(
    bom_id: int,
    batch_data: BomItemAssemblyAttrsBatchCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("assembly_kit:create"))
):
    """批量设置BOM装配属性"""
    # 验证BOM存在
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")

    created_count = 0
    updated_count = 0

    for item in batch_data.items:
        if item.bom_id != bom_id:
            continue

        existing = db.query(BomItemAssemblyAttrs).filter(
            BomItemAssemblyAttrs.bom_item_id == item.bom_item_id
        ).first()

        if existing:
            # 更新
            for key, value in item.model_dump().items():
                setattr(existing, key, value)
            existing.updated_at = datetime.now()
            updated_count += 1
        else:
            # 创建
            attr = BomItemAssemblyAttrs(**item.model_dump())
            db.add(attr)
            created_count += 1

    db.commit()

    return ResponseModel(
        code=200,
        message=f"批量设置完成，新增 {created_count} 条，更新 {updated_count} 条",
        data={"created": created_count, "updated": updated_count}
    )


@router.put("/bom/assembly-attrs/{attr_id}", response_model=ResponseModel)
async def update_assembly_attr(
    attr_id: int,
    attr_data: BomItemAssemblyAttrsUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("assembly_kit:update"))
):
    """更新单个物料装配属性"""
    attr = db.query(BomItemAssemblyAttrs).filter(BomItemAssemblyAttrs.id == attr_id).first()
    if not attr:
        raise HTTPException(status_code=404, detail="装配属性不存在")

    update_data = attr_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(attr, key, value)
    attr.updated_at = datetime.now()

    db.commit()
    db.refresh(attr)

    return ResponseModel(code=200, message="更新成功", data=BomItemAssemblyAttrsResponse.model_validate(attr))


@router.post("/bom/{bom_id}/assembly-attrs/auto", response_model=ResponseModel)
async def auto_assign_assembly_attrs(
    bom_id: int,
    request: BomAssemblyAttrsAutoRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("assembly_kit:create"))
):
    """自动分配装配属性（基于物料分类映射）"""
    # 验证BOM存在
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")

    # 获取BOM明细
    bom_items = db.query(BomItem).filter(BomItem.bom_header_id == bom_id).all()

    assigned_count = 0
    skipped_count = 0

    for bom_item in bom_items:
        # 检查是否已有配置
        existing = db.query(BomItemAssemblyAttrs).filter(
            BomItemAssemblyAttrs.bom_item_id == bom_item.id
        ).first()

        if existing and not request.overwrite:
            skipped_count += 1
            continue

        # 获取物料分类
        material = db.query(Material).filter(Material.id == bom_item.material_id).first()
        if not material or not material.category_id:
            skipped_count += 1
            continue

        # 获取映射配置
        mapping = db.query(CategoryStageMapping).filter(
            CategoryStageMapping.category_id == material.category_id
        ).first()

        if not mapping:
            # 使用默认阶段
            stage_code = "MECH"
            is_blocking = True
            can_postpone = False
        else:
            stage_code = mapping.stage_code
            is_blocking = mapping.is_blocking
            can_postpone = mapping.can_postpone

        if existing:
            existing.assembly_stage = stage_code
            existing.is_blocking = is_blocking
            existing.can_postpone = can_postpone
            existing.updated_at = datetime.now()
        else:
            attr = BomItemAssemblyAttrs(
                bom_item_id=bom_item.id,
                bom_id=bom_id,
                assembly_stage=stage_code,
                importance_level="NORMAL",
                is_blocking=is_blocking,
                can_postpone=can_postpone
            )
            db.add(attr)

        assigned_count += 1

    db.commit()

    return ResponseModel(
        code=200,
        message=f"自动分配完成，处理 {assigned_count} 条，跳过 {skipped_count} 条",
        data={"assigned": assigned_count, "skipped": skipped_count}
    )


@router.get("/bom/{bom_id}/assembly-attrs/recommendations", response_model=ResponseModel)
async def get_assembly_attr_recommendations(
    bom_id: int,
    db: Session = Depends(deps.get_db)
):
    """获取装配属性推荐结果（不应用，仅返回推荐）"""
    from app.services.assembly_attr_recommender import AssemblyAttrRecommender
    
    # 验证BOM存在
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")

    # 获取BOM明细
    bom_items = db.query(BomItem).filter(BomItem.bom_header_id == bom_id).all()

    # 批量推荐
    recommendations = AssemblyAttrRecommender.batch_recommend(db, bom_id, bom_items)

    # 构建响应
    result = []
    for bom_item in bom_items:
        material = db.query(Material).filter(Material.id == bom_item.material_id).first()
        if not material:
            continue
        
        rec = recommendations.get(bom_item.id)
        if rec:
            result.append({
                "bom_item_id": bom_item.id,
                "material_code": material.code,
                "material_name": material.name,
                "recommended_stage": rec.stage_code,
                "recommended_blocking": rec.is_blocking,
                "recommended_postpone": rec.can_postpone,
                "recommended_importance": rec.importance_level,
                "confidence": rec.confidence,
                "source": rec.source,
                "reason": rec.reason
            })

    return ResponseModel(
        code=200,
        message="推荐结果获取成功",
        data={"recommendations": result, "total": len(result)}
    )


@router.post("/bom/{bom_id}/assembly-attrs/smart-recommend", response_model=ResponseModel)
async def smart_recommend_assembly_attrs(
    bom_id: int,
    request: BomAssemblyAttrsAutoRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("assembly_kit:create"))
):
    """智能推荐装配属性（多级推荐规则）"""
    from app.services.assembly_attr_recommender import AssemblyAttrRecommender
    
    # 验证BOM存在
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")

    # 获取BOM明细
    bom_items = db.query(BomItem).filter(BomItem.bom_header_id == bom_id).all()

    # 批量推荐
    recommendations = AssemblyAttrRecommender.batch_recommend(db, bom_id, bom_items)

    assigned_count = 0
    skipped_count = 0
    recommendation_stats = {
        "HISTORY": 0,
        "CATEGORY": 0,
        "KEYWORD": 0,
        "SUPPLIER": 0,
        "DEFAULT": 0
    }

    for bom_item in bom_items:
        # 检查是否已有配置
        existing = db.query(BomItemAssemblyAttrs).filter(
            BomItemAssemblyAttrs.bom_item_id == bom_item.id
        ).first()

        if existing and not request.overwrite:
            skipped_count += 1
            continue

        # 获取推荐结果
        rec = recommendations.get(bom_item.id)
        if not rec:
            skipped_count += 1
            continue

        # 统计推荐来源
        recommendation_stats[rec.source] = recommendation_stats.get(rec.source, 0) + 1

        if existing:
            existing.assembly_stage = rec.stage_code
            existing.is_blocking = rec.is_blocking
            existing.can_postpone = rec.can_postpone
            existing.importance_level = rec.importance_level
            existing.setting_source = rec.source
            existing.updated_at = datetime.now()
        else:
            attr = BomItemAssemblyAttrs(
                bom_item_id=bom_item.id,
                bom_id=bom_id,
                assembly_stage=rec.stage_code,
                importance_level=rec.importance_level,
                is_blocking=rec.is_blocking,
                can_postpone=rec.can_postpone,
                setting_source=rec.source,
                created_by=current_user.id
            )
            db.add(attr)

        assigned_count += 1

    db.commit()

    return ResponseModel(
        code=200,
        message=f"智能推荐完成，处理 {assigned_count} 条，跳过 {skipped_count} 条",
        data={
            "assigned": assigned_count,
            "skipped": skipped_count,
            "recommendation_stats": recommendation_stats
        }
    )


@router.post("/bom/{bom_id}/assembly-attrs/template", response_model=ResponseModel)
async def apply_assembly_template(
    bom_id: int,
    request: BomAssemblyAttrsTemplateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("assembly_kit:create"))
):
    """套用装配模板"""
    # 验证BOM和模板存在
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")

    template = db.query(AssemblyTemplate).filter(AssemblyTemplate.id == request.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    if not template.stage_config:
        raise HTTPException(status_code=400, detail="模板配置为空")

    # 解析模板配置并应用
    # stage_config格式: {"category_code": {"stage": "MECH", "blocking": true, "postpone": false}}
    stage_config = template.stage_config

    bom_items = db.query(BomItem).filter(BomItem.bom_header_id == bom_id).all()
    applied_count = 0

    for bom_item in bom_items:
        material = db.query(Material).filter(Material.id == bom_item.material_id).first()
        if not material:
            continue

        # 查找模板中匹配的配置
        config = None
        if material.category_id:
            category = db.query(MaterialCategory).filter(MaterialCategory.id == material.category_id).first()
            if category and category.code in stage_config:
                config = stage_config[category.code]

        if not config:
            continue

        existing = db.query(BomItemAssemblyAttrs).filter(
            BomItemAssemblyAttrs.bom_item_id == bom_item.id
        ).first()

        if existing and not request.overwrite:
            continue

        if existing:
            existing.assembly_stage = config.get("stage", "MECH")
            existing.is_blocking = config.get("blocking", True)
            existing.can_postpone = config.get("postpone", False)
            existing.updated_at = datetime.now()
        else:
            attr = BomItemAssemblyAttrs(
                bom_item_id=bom_item.id,
                bom_id=bom_id,
                assembly_stage=config.get("stage", "MECH"),
                importance_level="NORMAL",
                is_blocking=config.get("blocking", True),
                can_postpone=config.get("postpone", False)
            )
            db.add(attr)

        applied_count += 1

    db.commit()

    return ResponseModel(
        code=200,
        message=f"模板套用完成，应用 {applied_count} 条配置",
        data={"applied": applied_count}
    )



