# -*- coding: utf-8 -*-
"""
企业微信配置 - 自动生成
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
    prefix="/assembly-kit/wechat-config",
    tags=["wechat_config"]
)

# 共 2 个路由

# ==================== 企业微信配置 ====================

@router.get("/wechat/config", response_model=ResponseModel)
async def get_wechat_config(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("assembly_kit:read"))
):
    """获取企业微信配置（仅显示是否已配置，不返回敏感信息）"""
    from app.core.config import settings
    
    config = {
        "enabled": settings.WECHAT_ENABLED,
        "corp_id_configured": bool(settings.WECHAT_CORP_ID),
        "agent_id_configured": bool(settings.WECHAT_AGENT_ID),
        "secret_configured": bool(settings.WECHAT_SECRET),
        "fully_configured": all([
            settings.WECHAT_CORP_ID,
            settings.WECHAT_AGENT_ID,
            settings.WECHAT_SECRET
        ])
    }
    
    return ResponseModel(
        code=200,
        message="success",
        data=config
    )


@router.post("/wechat/test", response_model=ResponseModel)
async def test_wechat_connection(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("assembly_kit:read"))
):
    """测试企业微信连接"""
    from app.utils.wechat_client import WeChatClient
    from app.core.config import settings
    
    if not settings.WECHAT_ENABLED:
        raise HTTPException(status_code=400, detail="企业微信功能未启用")
    
    try:
        client = WeChatClient()
        token = client.get_access_token()
        
        return ResponseModel(
            code=200,
            message="企业微信连接成功",
            data={"access_token_obtained": bool(token)}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"配置不完整: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"连接失败: {str(e)}")



