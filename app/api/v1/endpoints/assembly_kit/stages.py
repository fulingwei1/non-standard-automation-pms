# -*- coding: utf-8 -*-
"""
装配阶段管理 - 自动生成
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
    prefix="/assembly-kit/stages",
    tags=["stages"]
)

# 共 2 个路由

# ==================== 装配阶段管理 ====================

@router.get("/stages", response_model=ResponseModel)
async def get_assembly_stages(
    db: Session = Depends(deps.get_db),
    include_inactive: bool = Query(False, description="是否包含已禁用阶段")
):
    """获取所有装配阶段"""
    query = db.query(AssemblyStage)
    if not include_inactive:
        query = query.filter(AssemblyStage.is_active == True)
    stages = query.order_by(AssemblyStage.stage_order).all()

    return ResponseModel(
        code=200,
        message="success",
        data=[AssemblyStageResponse.model_validate(s) for s in stages]
    )


@router.put("/stages/{stage_code}", response_model=ResponseModel)
async def update_assembly_stage(
    stage_code: str,
    stage_data: AssemblyStageUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("assembly_kit:update"))
):
    """更新装配阶段"""
    stage = db.query(AssemblyStage).filter(AssemblyStage.stage_code == stage_code).first()
    if not stage:
        raise HTTPException(status_code=404, detail=f"装配阶段 {stage_code} 不存在")

    update_data = stage_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(stage, key, value)
    stage.updated_at = datetime.now()

    db.commit()
    db.refresh(stage)

    return ResponseModel(
        code=200,
        message="更新成功",
        data=AssemblyStageResponse.model_validate(stage)
    )



