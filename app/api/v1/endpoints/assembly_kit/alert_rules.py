# -*- coding: utf-8 -*-
"""
预警规则 - 自动生成
从 assembly_kit.py 拆分
"""

# -*- coding: utf-8 -*-
"""
齐套分析模块 API 端点

基于装配工艺路径的智能齐套分析系统
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models import (
    ShortageAlertRule,
    User,
)
from app.schemas.assembly_kit import (  # Stage; Template; Category Mapping; BOM Assembly Attrs; Readiness; Shortage; Alert Rule; Suggestion; Dashboard
    ShortageAlertRuleCreate,
    ShortageAlertRuleResponse,
    ShortageAlertRuleUpdate,
)
from app.schemas.common import ResponseModel

router = APIRouter()



from fastapi import APIRouter

router = APIRouter(
    prefix="/assembly-kit/alert-rules",
    tags=["alert_rules"]
)

# 共 3 个路由

# ==================== 预警规则 ====================

@router.get("/alert-rules", response_model=ResponseModel)
async def get_alert_rules(
    db: Session = Depends(deps.get_db),
    include_inactive: bool = Query(False)
):
    """获取预警规则列表"""
    query = db.query(ShortageAlertRule)
    if not include_inactive:
        query = query.filter(ShortageAlertRule.is_active)

    rules = query.order_by(ShortageAlertRule.alert_level).all()

    return ResponseModel(
        code=200,
        message="success",
        data=[ShortageAlertRuleResponse.model_validate(r) for r in rules]
    )


@router.post("/alert-rules", response_model=ResponseModel)
async def create_alert_rule(
    rule_data: ShortageAlertRuleCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("assembly_kit:create"))
):
    """创建预警规则"""
    existing = db.query(ShortageAlertRule).filter(
        ShortageAlertRule.rule_code == rule_data.rule_code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="规则编码已存在")

    rule = ShortageAlertRule(**rule_data.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)

    return ResponseModel(
        code=200,
        message="创建成功",
        data=ShortageAlertRuleResponse.model_validate(rule)
    )


@router.put("/alert-rules/{rule_id}", response_model=ResponseModel)
async def update_alert_rule(
    rule_id: int,
    rule_data: ShortageAlertRuleUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("assembly_kit:update"))
):
    """更新预警规则"""
    rule = db.query(ShortageAlertRule).filter(ShortageAlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="预警规则不存在")

    update_data = rule_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)
    rule.updated_at = datetime.now()

    db.commit()
    db.refresh(rule)

    return ResponseModel(code=200, message="更新成功", data=ShortageAlertRuleResponse.model_validate(rule))



