# -*- coding: utf-8 -*-
"""
成本管理 - 物料成本匹配

包含自动匹配物料成本功能
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.query_filters import apply_keyword_filter
from app.core import security
from app.models.sales import PurchaseMaterialCost
from app.models.user import User
from app.schemas.sales import (
    MaterialCostMatchRequest,
    MaterialCostMatchResponse,
    PurchaseMaterialCostResponse,
)

router = APIRouter()


@router.post("/purchase-material-costs/match", response_model=MaterialCostMatchResponse)
def match_material_cost(
    *,
    db: Session = Depends(deps.get_db),
    match_request: MaterialCostMatchRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    自动匹配物料成本（根据物料名称、规格等匹配历史采购价格）
    """
    # 查询启用的标准件成本清单
    query = db.query(PurchaseMaterialCost).filter(
        PurchaseMaterialCost.is_active,
        PurchaseMaterialCost.is_standard_part
    )

    # 匹配逻辑：优先精确匹配，其次模糊匹配
    matched_cost = None
    suggestions = []
    match_score = 0

    # 1. 精确匹配物料名称
    exact_match = query.filter(
        PurchaseMaterialCost.material_name == match_request.item_name
    ).order_by(desc(PurchaseMaterialCost.match_priority), desc(PurchaseMaterialCost.purchase_date)).first()

    if exact_match:
        matched_cost = exact_match
        match_score = 100
    else:
        # 2. 模糊匹配物料名称
        name_matches = (
            apply_keyword_filter(
                query,
                PurchaseMaterialCost,
                match_request.item_name,
                "material_name",
                use_ilike=False,
            )
            .order_by(desc(PurchaseMaterialCost.match_priority), desc(PurchaseMaterialCost.purchase_date))
            .limit(5)
            .all()
        )

        if name_matches:
            matched_cost = name_matches[0]
            match_score = 80
            suggestions = name_matches[1:5] if len(name_matches) > 1 else []
        else:
            # 3. 关键词匹配
            if match_request.item_name:
                keywords = match_request.item_name.split()
                for keyword in keywords:
                    if len(keyword) > 2:  # 只匹配长度大于2的关键词
                        keyword_matches = (
                            apply_keyword_filter(
                                query,
                                PurchaseMaterialCost,
                                keyword,
                                ["material_name", "match_keywords"],
                                use_ilike=False,
                            )
                            .order_by(desc(PurchaseMaterialCost.match_priority), desc(PurchaseMaterialCost.usage_count))
                            .limit(5)
                            .all()
                        )

                        if keyword_matches:
                            matched_cost = keyword_matches[0]
                            match_score = 60
                            suggestions = keyword_matches[1:5] if len(keyword_matches) > 1 else []
                            break

    # 如果匹配成功，更新使用次数
    if matched_cost:
        matched_cost.usage_count = (matched_cost.usage_count or 0) + 1
        matched_cost.last_used_at = datetime.now()
        db.add(matched_cost)
        db.commit()
        db.refresh(matched_cost)

    # 构建响应
    matched_cost_dict = None
    if matched_cost:
        matched_cost_dict = {
            **{c.name: getattr(matched_cost, c.name) for c in matched_cost.__table__.columns},
            "submitter_name": matched_cost.submitter.real_name if matched_cost.submitter else None
        }
        matched_cost_dict = PurchaseMaterialCostResponse(**matched_cost_dict)

    suggestions_list = []
    for sug in suggestions:
        sug_dict = {
            **{c.name: getattr(sug, c.name) for c in sug.__table__.columns},
            "submitter_name": sug.submitter.real_name if sug.submitter else None
        }
        suggestions_list.append(PurchaseMaterialCostResponse(**sug_dict))

    return MaterialCostMatchResponse(
        matched=matched_cost is not None,
        match_score=match_score if matched_cost else None,
        matched_cost=matched_cost_dict,
        suggestions=suggestions_list
    )
