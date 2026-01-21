# -*- coding: utf-8 -*-
"""
战略审视管理

提供战略审视记录的 CRUD 操作
"""

"""
战略管理服务 - 战略审视与例行管理
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.strategy import StrategyCalendarEvent, StrategyReview
from app.schemas.strategy import (
    CalendarMonthResponse,
    CalendarYearResponse,
    DimensionHealthDetail,
    HealthScoreResponse,
    RoutineManagementCycleItem,
    RoutineManagementCycleResponse,
    StrategyCalendarEventCreate,
    StrategyCalendarEventResponse,
    StrategyCalendarEventUpdate,
    StrategyReviewCreate,
    StrategyReviewResponse,
    StrategyReviewUpdate,
)



# ============================================
# 战略审视管理
# ============================================

def create_strategy_review(
    db: Session,
    data: StrategyReviewCreate,
    created_by: int
) -> StrategyReview:
    """
    创建战略审视记录

    Args:
        db: 数据库会话
        data: 创建数据
        created_by: 创建人 ID

    Returns:
        StrategyReview: 创建的审视记录
    """
    # 自动计算健康度评分
    from .health_calculator import (
        calculate_dimension_health,
        calculate_strategy_health,
    )

    overall_health = calculate_strategy_health(db, data.strategy_id)

    financial_health = calculate_dimension_health(db, data.strategy_id, "FINANCIAL")
    customer_health = calculate_dimension_health(db, data.strategy_id, "CUSTOMER")
    internal_health = calculate_dimension_health(db, data.strategy_id, "INTERNAL")
    learning_health = calculate_dimension_health(db, data.strategy_id, "LEARNING")

    review = StrategyReview(
        strategy_id=data.strategy_id,
        review_date=data.review_date or date.today(),
        review_period=data.review_period,
        review_type=data.review_type,
        health_score=overall_health,
        financial_score=financial_health.get("score"),
        customer_score=customer_health.get("score"),
        internal_score=internal_health.get("score"),
        learning_score=learning_health.get("score"),
        summary=data.summary,
        achievements=data.achievements,
        issues=data.issues,
        action_items=data.action_items,
        next_steps=data.next_steps,
        created_by=created_by,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def get_strategy_review(db: Session, review_id: int) -> Optional[StrategyReview]:
    """
    获取战略审视记录

    Args:
        db: 数据库会话
        review_id: 审视记录 ID

    Returns:
        Optional[StrategyReview]: 审视记录
    """
    return db.query(StrategyReview).filter(
        StrategyReview.id == review_id,
        StrategyReview.is_active == True
    ).first()


def list_strategy_reviews(
    db: Session,
    strategy_id: int,
    review_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
) -> tuple[List[StrategyReview], int]:
    """
    获取战略审视记录列表

    Args:
        db: 数据库会话
        strategy_id: 战略 ID
        review_type: 审视类型筛选
        skip: 跳过数量
        limit: 限制数量

    Returns:
        tuple: (审视记录列表, 总数)
    """
    query = db.query(StrategyReview).filter(
        StrategyReview.strategy_id == strategy_id,
        StrategyReview.is_active == True
    )

    if review_type:
        query = query.filter(StrategyReview.review_type == review_type)

    total = query.count()
    items = query.order_by(desc(StrategyReview.review_date)).offset(skip).limit(limit).all()

    return items, total


def update_strategy_review(
    db: Session,
    review_id: int,
    data: StrategyReviewUpdate
) -> Optional[StrategyReview]:
    """
    更新战略审视记录

    Args:
        db: 数据库会话
        review_id: 审视记录 ID
        data: 更新数据

    Returns:
        Optional[StrategyReview]: 更新后的审视记录
    """
    review = get_strategy_review(db, review_id)
    if not review:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(review, key, value)

    db.commit()
    db.refresh(review)
    return review


def delete_strategy_review(db: Session, review_id: int) -> bool:
    """
    删除战略审视记录（软删除）

    Args:
        db: 数据库会话
        review_id: 审视记录 ID

    Returns:
        bool: 是否删除成功
    """
    review = get_strategy_review(db, review_id)
    if not review:
        return False

    review.is_active = False
    db.commit()
    return True


def get_latest_review(db: Session, strategy_id: int) -> Optional[StrategyReviewResponse]:
    """
    获取最新的战略审视记录

    Args:
        db: 数据库会话
        strategy_id: 战略 ID

    Returns:
        Optional[StrategyReviewResponse]: 最新审视记录
    """
    review = db.query(StrategyReview).filter(
        StrategyReview.strategy_id == strategy_id,
        StrategyReview.is_active == True
    ).order_by(desc(StrategyReview.review_date)).first()

    if not review:
        return None

    return StrategyReviewResponse(
        id=review.id,
        strategy_id=review.strategy_id,
        review_date=review.review_date,
        review_period=review.review_period,
        review_type=review.review_type,
        health_score=review.health_score,
        financial_score=review.financial_score,
        customer_score=review.customer_score,
        internal_score=review.internal_score,
        learning_score=review.learning_score,
        summary=review.summary,
        achievements=review.achievements,
        issues=review.issues,
        action_items=review.action_items,
        next_steps=review.next_steps,
        created_by=review.created_by,
        is_active=review.is_active,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


