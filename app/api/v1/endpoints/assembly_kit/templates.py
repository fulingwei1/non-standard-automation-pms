# -*- coding: utf-8 -*-
"""
装配模板管理 - 自动生成
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
    prefix="/assembly-kit/templates",
    tags=["templates"]
)

# 共 4 个路由

# ==================== 装配模板管理 ====================

@router.get("/templates", response_model=ResponseModel)
async def get_assembly_templates(
    db: Session = Depends(deps.get_db),
    equipment_type: Optional[str] = Query(None, description="设备类型筛选"),
    include_inactive: bool = Query(False)
):
    """获取装配模板列表"""
    query = db.query(AssemblyTemplate)
    if equipment_type:
        query = query.filter(AssemblyTemplate.equipment_type == equipment_type)
    if not include_inactive:
        query = query.filter(AssemblyTemplate.is_active == True)

    templates = query.order_by(AssemblyTemplate.is_default.desc(), AssemblyTemplate.created_at.desc()).all()

    return ResponseModel(
        code=200,
        message="success",
        data=[AssemblyTemplateResponse.model_validate(t) for t in templates]
    )


@router.post("/templates", response_model=ResponseModel)
async def create_assembly_template(
    template_data: AssemblyTemplateCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("assembly_kit:read"))
):
    """创建装配模板"""
    existing = db.query(AssemblyTemplate).filter(
        AssemblyTemplate.template_code == template_data.template_code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="模板编码已存在")

    template = AssemblyTemplate(**template_data.model_dump(), created_by=current_user.id)
    db.add(template)
    db.commit()
    db.refresh(template)

    return ResponseModel(
        code=200,
        message="创建成功",
        data=AssemblyTemplateResponse.model_validate(template)
    )


@router.put("/templates/{template_id}", response_model=ResponseModel)
async def update_assembly_template(
    template_id: int,
    template_data: AssemblyTemplateUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("assembly_kit:read"))
):
    """更新装配模板"""
    template = db.query(AssemblyTemplate).filter(AssemblyTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    update_data = template_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(template, key, value)
    template.updated_at = datetime.now()

    db.commit()
    db.refresh(template)

    return ResponseModel(code=200, message="更新成功", data=AssemblyTemplateResponse.model_validate(template))


@router.delete("/templates/{template_id}", response_model=MessageResponse)
async def delete_assembly_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("assembly_kit:read"))
):
    """删除装配模板"""
    template = db.query(AssemblyTemplate).filter(AssemblyTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 软删除
    template.is_active = False
    template.updated_at = datetime.now()
    db.commit()

    return MessageResponse(code=200, message="删除成功")

