# -*- coding: utf-8 -*-
"""
战略审视管理

提供战略审视记录的 CRUD 操作
"""

import json
from datetime import date
from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.common.query_filters import apply_pagination
from app.models.strategy import StrategyReview
from app.schemas.strategy import (
    StrategyReviewCreate,
    StrategyReviewResponse,
    StrategyReviewUpdate,
)

# ============================================
# 战略审视管理
# ============================================


def _safe_json_loads(val):
    """安全解析 JSON 字符串"""
    if val is None:
        return None
    if isinstance(val, (dict, list)):
        return val
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return None


def _review_to_response(review: StrategyReview) -> StrategyReviewResponse:
    """将 Model 转为 Response"""
    return StrategyReviewResponse(
        id=review.id,
        strategy_id=review.strategy_id,
        review_type=review.review_type,
        review_date=review.review_date,
        review_period=review.review_period,
        reviewer_id=review.reviewer_id,
        health_score=review.health_score,
        financial_score=review.financial_score,
        customer_score=review.customer_score,
        internal_score=review.internal_score,
        learning_score=review.learning_score,
        findings=_safe_json_loads(review.findings),
        achievements=_safe_json_loads(review.achievements),
        recommendations=_safe_json_loads(review.recommendations),
        decisions=_safe_json_loads(review.decisions),
        action_items=_safe_json_loads(review.action_items),
        meeting_minutes=review.meeting_minutes,
        attendees=_safe_json_loads(review.attendees),
        meeting_duration=review.meeting_duration,
        next_review_date=review.next_review_date,
        is_active=review.is_active,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


def create_strategy_review(
    db: Session, data: StrategyReviewCreate, created_by: int
) -> StrategyReview:
    review = StrategyReview(
        strategy_id=data.strategy_id,
        review_type=data.review_type,
        review_date=data.review_date or date.today(),
        review_period=data.review_period,
        reviewer_id=data.reviewer_id or created_by,
        health_score=data.health_score,
        financial_score=data.financial_score,
        customer_score=data.customer_score,
        internal_score=data.internal_score,
        learning_score=data.learning_score,
        findings=json.dumps(data.findings, ensure_ascii=False) if data.findings else None,
        achievements=json.dumps(data.achievements, ensure_ascii=False) if data.achievements else None,
        recommendations=json.dumps(data.recommendations, ensure_ascii=False) if data.recommendations else None,
        decisions=json.dumps(data.decisions, ensure_ascii=False) if data.decisions else None,
        action_items=json.dumps(data.action_items, ensure_ascii=False) if data.action_items else None,
        meeting_minutes=data.meeting_minutes,
        attendees=json.dumps(data.attendees, ensure_ascii=False) if data.attendees else None,
        meeting_duration=data.meeting_duration,
        next_review_date=data.next_review_date,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def get_strategy_review(db: Session, review_id: int) -> Optional[StrategyReview]:
    return (
        db.query(StrategyReview)
        .filter(StrategyReview.id == review_id, StrategyReview.is_active)
        .first()
    )


def list_strategy_reviews(
    db: Session, strategy_id: int, review_type: Optional[str] = None, skip: int = 0, limit: int = 20
) -> tuple[List[StrategyReview], int]:
    query = db.query(StrategyReview).filter(
        StrategyReview.strategy_id == strategy_id, StrategyReview.is_active
    )

    if review_type:
        query = query.filter(StrategyReview.review_type == review_type)

    total = query.count()
    items = apply_pagination(query.order_by(desc(StrategyReview.review_date)), skip, limit).all()

    return items, total


def update_strategy_review(
    db: Session, review_id: int, data: StrategyReviewUpdate
) -> Optional[StrategyReview]:
    review = get_strategy_review(db, review_id)
    if not review:
        return None

    update_data = data.model_dump(exclude_unset=True)

    # JSON 字段处理
    for json_field in ("findings", "achievements", "recommendations", "decisions", "action_items", "attendees"):
        if json_field in update_data and update_data[json_field] is not None:
            update_data[json_field] = json.dumps(update_data[json_field], ensure_ascii=False)

    for key, value in update_data.items():
        setattr(review, key, value)

    db.commit()
    db.refresh(review)
    return review


def delete_strategy_review(db: Session, review_id: int) -> bool:
    review = get_strategy_review(db, review_id)
    if not review:
        return False

    review.is_active = False
    db.commit()
    return True


def get_latest_review(db: Session, strategy_id: int) -> Optional[StrategyReviewResponse]:
    review = (
        db.query(StrategyReview)
        .filter(StrategyReview.strategy_id == strategy_id, StrategyReview.is_active)
        .order_by(desc(StrategyReview.review_date))
        .first()
    )

    if not review:
        return None

    return _review_to_response(review)
