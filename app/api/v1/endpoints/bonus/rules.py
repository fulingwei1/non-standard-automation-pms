# -*- coding: utf-8 -*-
"""
奖金规则管理 - 自动生成
从 bonus.py 拆分
"""

# -*- coding: utf-8 -*-
"""
奖金激励模块 API 端点
"""

from typing import Any, Optional, Tuple

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query, paginate_list
from app.core import security
from app.models.bonus import (
    BonusCalculation,
    BonusRule,
)
from app.models.user import User
from app.schemas.bonus import (
    BonusRuleCreate,
    BonusRuleListResponse,
    BonusRuleResponse,
    BonusRuleUpdate,
)
from app.schemas.common import ResponseModel

router = APIRouter()



from fastapi import APIRouter

router = APIRouter(
    prefix="/bonus/rules",
    tags=["rules"]
)

# 共 7 个路由

# ==================== 奖金规则管理 ====================

@router.post("/rules", response_model=ResponseModel[BonusRuleResponse], status_code=status.HTTP_201_CREATED)
def create_bonus_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_in: BonusRuleCreate,
    current_user: User = Depends(security.require_permission("hr:read")),
) -> Any:
    """
    创建奖金规则（仅人力资源经理可配置）
    """
    # 检查规则编码是否已存在
    existing = db.query(BonusRule).filter(BonusRule.rule_code == rule_in.rule_code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"规则编码 {rule_in.rule_code} 已存在"
        )

    rule = BonusRule(**rule_in.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)

    return ResponseModel(code=200, message="创建成功", data=rule)


@router.get("/rules", response_model=BonusRuleListResponse, status_code=status.HTTP_200_OK)
def get_bonus_rules(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    bonus_type: Optional[str] = Query(None, description="奖金类型"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取奖金规则列表
    """
    query = db.query(BonusRule)

    if bonus_type:
        query = query.filter(BonusRule.bonus_type == bonus_type)
    if is_active is not None:
        query = query.filter(BonusRule.is_active == is_active)

    total = query.count()
    rules = query.order_by(desc(BonusRule.priority), desc(BonusRule.created_at)).offset(
        pagination.offset
    ).limit(pagination.limit).all()

    return BonusRuleListResponse(
        items=rules,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )


@router.get("/rules/{rule_id}", response_model=ResponseModel[BonusRuleResponse], status_code=status.HTTP_200_OK)
def get_bonus_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取奖金规则详情
    """
    rule = db.query(BonusRule).filter(BonusRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    return ResponseModel(code=200, data=rule)


@router.put("/rules/{rule_id}", response_model=ResponseModel[BonusRuleResponse], status_code=status.HTTP_200_OK)
def update_bonus_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_id: int,
    rule_in: BonusRuleUpdate,
    current_user: User = Depends(security.require_permission("hr:read")),
) -> Any:
    """
    更新奖金规则（仅人力资源经理可配置）
    """
    rule = db.query(BonusRule).filter(BonusRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    update_data = rule_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)

    db.commit()
    db.refresh(rule)

    return ResponseModel(code=200, message="更新成功", data=rule)


@router.delete("/rules/{rule_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def delete_bonus_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_id: int,
    current_user: User = Depends(security.require_permission("hr:read")),
) -> Any:
    """
    删除奖金规则（仅人力资源经理可配置）
    """
    rule = db.query(BonusRule).filter(BonusRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    # 检查是否有计算记录
    calc_count = db.query(BonusCalculation).filter(BonusCalculation.rule_id == rule_id).count()
    if calc_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该规则已有 {calc_count} 条计算记录，无法删除"
        )

    db.delete(rule)
    db.commit()

    return ResponseModel(code=200, message="删除成功")


@router.post("/rules/{rule_id}/activate", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def activate_bonus_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_id: int,
    current_user: User = Depends(security.require_permission("hr:read")),
) -> Any:
    """
    启用奖金规则（仅人力资源经理可配置）
    """
    rule = db.query(BonusRule).filter(BonusRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    rule.is_active = True
    db.commit()

    return ResponseModel(code=200, message="启用成功")


@router.post("/rules/{rule_id}/deactivate", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def deactivate_bonus_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_id: int,
    current_user: User = Depends(security.require_permission("hr:read")),
) -> Any:
    """
    停用奖金规则（仅人力资源经理可配置）
    """
    rule = db.query(BonusRule).filter(BonusRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    rule.is_active = False
    db.commit()

    return ResponseModel(code=200, message="停用成功")


def paginate_items(items: list, page: int, page_size: int) -> Tuple[list, int, int]:
    """
    对内存列表做分页，返回 (当前页数据, 总条数, 总页数)
    """
    page_items, total, pagination = paginate_list(items, page, page_size)
    pages = pagination.pages_for_total(total)
    return page_items, total, pages
