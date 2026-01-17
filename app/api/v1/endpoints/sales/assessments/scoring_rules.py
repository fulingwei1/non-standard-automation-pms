# -*- coding: utf-8 -*-
"""
评分规则管理 API endpoints

包含评分规则的查询、创建、激活等端点
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales import ScoringRule
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.sales import ScoringRuleCreate, ScoringRuleResponse

router = APIRouter()


@router.get("/scoring-rules", response_model=List[ScoringRuleResponse])
def list_scoring_rules(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取评分规则列表"""
    rules = db.query(ScoringRule).order_by(desc(ScoringRule.created_at)).all()

    result = []
    for rule in rules:
        creator_name = None
        if rule.created_by:
            creator = db.query(User).filter(User.id == rule.created_by).first()
            creator_name = creator.real_name if creator else None

        result.append(ScoringRuleResponse(
            id=rule.id,
            version=rule.version,
            is_active=rule.is_active,
            description=rule.description,
            created_by=rule.created_by,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
            creator_name=creator_name
        ))

    return result


@router.post("/scoring-rules", response_model=ScoringRuleResponse, status_code=201)
def create_scoring_rule(
    *,
    db: Session = Depends(deps.get_db),
    request: ScoringRuleCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建评分规则"""
    # 检查版本号是否已存在
    existing = db.query(ScoringRule).filter(ScoringRule.version == request.version).first()
    if existing:
        raise HTTPException(status_code=400, detail="版本号已存在")

    rule = ScoringRule(
        version=request.version,
        rules_json=request.rules_json,
        description=request.description,
        created_by=current_user.id
    )

    db.add(rule)
    db.commit()
    db.refresh(rule)

    return ScoringRuleResponse(
        id=rule.id,
        version=rule.version,
        is_active=rule.is_active,
        description=rule.description,
        created_by=rule.created_by,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
        creator_name=current_user.real_name
    )


@router.put("/scoring-rules/{rule_id}/activate", response_model=ResponseModel)
def activate_scoring_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """激活评分规则版本"""
    rule = db.query(ScoringRule).filter(ScoringRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="评分规则不存在")

    # 取消其他规则的激活状态
    db.query(ScoringRule).update({ScoringRule.is_active: False})

    # 激活当前规则
    rule.is_active = True
    db.commit()

    return ResponseModel(message="评分规则已激活")
