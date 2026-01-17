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
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

logger = logging.getLogger(__name__)
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models import (
    AssemblyStage,
    AssemblyTemplate,
    BomHeader,
    BomItem,
    BomItemAssemblyAttrs,
    CategoryStageMapping,
    Machine,
    Material,
    MaterialCategory,
    MaterialReadiness,
    Project,
    SchedulingSuggestion,
    ShortageAlertRule,
    ShortageDetail,
    User,
)
from app.models.enums import (
    AssemblyStageEnum,
    ImportanceLevelEnum,
    ShortageAlertLevelEnum,
    SuggestionStatusEnum,
    SuggestionTypeEnum,
)
from app.schemas.assembly_kit import (  # Stage; Template; Category Mapping; BOM Assembly Attrs; Readiness; Shortage; Alert Rule; Suggestion; Dashboard
    AssemblyDashboardResponse,
    AssemblyDashboardStageStats,
    AssemblyDashboardStats,
    AssemblyStageCreate,
    AssemblyStageResponse,
    AssemblyStageUpdate,
    AssemblyTemplateCreate,
    AssemblyTemplateResponse,
    AssemblyTemplateUpdate,
    BomAssemblyAttrsAutoRequest,
    BomAssemblyAttrsTemplateRequest,
    BomItemAssemblyAttrsBatchCreate,
    BomItemAssemblyAttrsCreate,
    BomItemAssemblyAttrsResponse,
    BomItemAssemblyAttrsUpdate,
    CategoryStageMappingCreate,
    CategoryStageMappingResponse,
    CategoryStageMappingUpdate,
    MaterialReadinessCreate,
    MaterialReadinessDetailResponse,
    MaterialReadinessResponse,
    SchedulingSuggestionAccept,
    SchedulingSuggestionReject,
    SchedulingSuggestionResponse,
    ShortageAlertItem,
    ShortageAlertListResponse,
    ShortageAlertRuleCreate,
    ShortageAlertRuleResponse,
    ShortageAlertRuleUpdate,
    ShortageDetailResponse,
    StageKitRate,
)
from app.schemas.common import MessageResponse, ResponseModel

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



