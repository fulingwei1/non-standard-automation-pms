# -*- coding: utf-8 -*-
"""
销售仪表盘 API

GET /sales/dashboard - 返回个人业绩、团队排名、管道概览、预测数据
"""

from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.sales_permissions import filter_sales_data_by_scope
from app.models.organization import Department
from app.models.sales import Contract, Opportunity, Quote, SalesTarget
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


def _quarter_label(q: int) -> str:
    return f"Q{q}"


def _month_label(m: int) -> str:
    return f"{m}月"


def _get_current_year_quarter():
    today = date.today()
    return today.year, (today.month - 1) // 3 + 1


@router.get("/dashboard", response_model=ResponseModel)
def get_sales_dashboard(
    db: Session = Depends(deps.get_db),
    year: Optional[int] = Query(None, description="年份，默认当前年"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    销售仪表盘：个人业绩、团队排名、管道健康、季度预测
    """
    now = datetime.now()
    target_year = year or now.year
    year_start = datetime(target_year, 1, 1)
    year_end = datetime(target_year, 12, 31, 23, 59, 59)

    # ========== 1. 个人业绩 (personal) ==========
    personal = _build_personal(db, current_user, target_year, year_start, year_end)

    # ========== 2. 团队排名 (team_ranking) ==========
    team_ranking = _build_team_ranking(db, current_user, target_year, year_start, year_end)

    # ========== 3. 管道概览 (pipeline) ==========
    pipeline = _build_pipeline(db, current_user, year_start, year_end)

    # ========== 4. 季度预测 (forecast) ==========
    forecast = _build_forecast(db, current_user, target_year)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "personal": personal,
            "team_ranking": team_ranking,
            "pipeline": pipeline,
            "forecast": forecast,
        },
    )


def _build_personal(
    db: Session, user: User, target_year: int, year_start: datetime, year_end: datetime
) -> dict:
    """构建个人业绩数据"""
    # 查询个人赢单商机
    won_opps = (
        db.query(Opportunity)
        .filter(
            Opportunity.owner_id == user.id,
            Opportunity.stage == "WON",
            Opportunity.created_at >= year_start,
            Opportunity.created_at <= year_end,
        )
        .all()
    )
    achieved = sum(float(o.est_amount or 0) for o in won_opps)
    won_count = len(won_opps)

    # 管道中商机金额（非终态）
    active_stages = ["DISCOVERY", "QUALIFICATION", "PROPOSAL", "NEGOTIATION"]
    pipeline_opps = (
        db.query(func.coalesce(func.sum(Opportunity.est_amount), 0))
        .filter(
            Opportunity.owner_id == user.id,
            Opportunity.stage.in_(active_stages),
            Opportunity.created_at >= year_start,
            Opportunity.created_at <= year_end,
        )
        .scalar()
    )
    pipeline_value = float(pipeline_opps or 0)

    # 个人年度目标
    target_row = (
        db.query(SalesTarget)
        .filter(
            SalesTarget.user_id == user.id,
            SalesTarget.target_scope == "PERSONAL",
            SalesTarget.target_type == "CONTRACT_AMOUNT",
            SalesTarget.target_period == "YEARLY",
            SalesTarget.period_value == str(target_year),
            SalesTarget.status == "ACTIVE",
        )
        .first()
    )
    target = float(target_row.target_value) if target_row else 0
    quota_pct = round(achieved / target * 100, 1) if target > 0 else 0

    # 按月统计
    monthly = []
    for m in range(1, 13):
        m_start = datetime(target_year, m, 1)
        m_end = datetime(target_year, m + 1, 1) if m < 12 else datetime(target_year + 1, 1, 1)

        m_actual = (
            db.query(func.coalesce(func.sum(Opportunity.est_amount), 0))
            .filter(
                Opportunity.owner_id == user.id,
                Opportunity.stage == "WON",
                Opportunity.created_at >= m_start,
                Opportunity.created_at < m_end,
            )
            .scalar()
        )

        # 月度目标
        period_val = f"{target_year}-{m:02d}"
        m_target_row = (
            db.query(SalesTarget)
            .filter(
                SalesTarget.user_id == user.id,
                SalesTarget.target_scope == "PERSONAL",
                SalesTarget.target_type == "CONTRACT_AMOUNT",
                SalesTarget.target_period == "MONTHLY",
                SalesTarget.period_value == period_val,
                SalesTarget.status == "ACTIVE",
            )
            .first()
        )
        m_target = float(m_target_row.target_value) if m_target_row else round(target / 12, 2)

        monthly.append(
            {
                "month": _month_label(m),
                "target": m_target,
                "actual": float(m_actual or 0),
            }
        )

    return {
        "target": target,
        "achieved": achieved,
        "quota_pct": quota_pct,
        "won_count": won_count,
        "pipeline_value": pipeline_value,
        "monthly": monthly,
    }


def _build_team_ranking(
    db: Session, current_user: User, target_year: int, year_start: datetime, year_end: datetime
) -> list:
    """构建团队排名（同部门/全公司销售排名）"""
    # 按 owner_id 聚合赢单金额
    results = (
        db.query(
            Opportunity.owner_id,
            func.sum(Opportunity.est_amount).label("total_amount"),
            func.count(Opportunity.id).label("deal_count"),
        )
        .filter(
            Opportunity.stage == "WON",
            Opportunity.created_at >= year_start,
            Opportunity.created_at <= year_end,
        )
        .group_by(Opportunity.owner_id)
        .order_by(func.sum(Opportunity.est_amount).desc())
        .limit(20)
        .all()
    )

    ranking = []
    for row in results:
        user = db.query(User).filter(User.id == row.owner_id).first()
        if not user:
            continue

        amount = float(row.total_amount or 0)
        deals = int(row.deal_count or 0)

        # 查个人年度目标算达成率
        t = (
            db.query(SalesTarget)
            .filter(
                SalesTarget.user_id == row.owner_id,
                SalesTarget.target_scope == "PERSONAL",
                SalesTarget.target_type == "CONTRACT_AMOUNT",
                SalesTarget.target_period == "YEARLY",
                SalesTarget.period_value == str(target_year),
                SalesTarget.status == "ACTIVE",
            )
            .first()
        )
        t_val = float(t.target_value) if t else 0
        target_pct = round(amount / t_val * 100, 1) if t_val > 0 else 0

        ranking.append(
            {
                "name": user.real_name or user.username,
                "amount": amount,
                "deals": deals,
                "target_pct": target_pct,
            }
        )

    return ranking


def _build_pipeline(
    db: Session, current_user: User, year_start: datetime, year_end: datetime
) -> dict:
    """构建管道概览"""
    active_stages = ["DISCOVERY", "QUALIFICATION", "PROPOSAL", "NEGOTIATION"]

    # 应用数据权限
    base_query = db.query(Opportunity)
    base_query = filter_sales_data_by_scope(base_query, current_user, db, Opportunity, "owner_id")
    base_query = base_query.filter(
        Opportunity.created_at >= year_start,
        Opportunity.created_at <= year_end,
    )

    # 按阶段统计
    stages = []
    total_value = 0
    total_count = 0
    weighted_sum = 0

    stage_names = {
        "DISCOVERY": "初步接触",
        "QUALIFICATION": "需求确认",
        "PROPOSAL": "方案报价",
        "NEGOTIATION": "商务谈判",
    }

    for stage in active_stages:
        stage_opps = base_query.filter(Opportunity.stage == stage).all()
        count = len(stage_opps)
        value = sum(float(o.est_amount or 0) for o in stage_opps)
        prob_sum = sum(float(o.est_amount or 0) * (o.probability or 0) / 100 for o in stage_opps)

        total_value += value
        total_count += count
        weighted_sum += prob_sum

        stages.append(
            {
                "name": stage_names.get(stage, stage),
                "count": count,
                "value": value,
            }
        )

    # 健康分 = 加权金额占比 * 100
    health_score = round(weighted_sum / total_value * 100, 0) if total_value > 0 else 0

    return {
        "total_value": total_value,
        "health_score": int(health_score),
        "stages": stages,
    }


def _build_forecast(db: Session, current_user: User, target_year: int) -> dict:
    """构建季度预测"""
    quarters = []

    base_query = db.query(Opportunity)
    base_query = filter_sales_data_by_scope(base_query, current_user, db, Opportunity, "owner_id")

    for q in range(1, 5):
        q_start = datetime(target_year, (q - 1) * 3 + 1, 1)
        q_end_month = q * 3
        if q_end_month == 12:
            q_end = datetime(target_year + 1, 1, 1)
        else:
            q_end = datetime(target_year, q_end_month + 1, 1)

        # 实际赢单
        actual = (
            base_query.filter(
                Opportunity.stage == "WON",
                Opportunity.created_at >= q_start,
                Opportunity.created_at < q_end,
            )
            .with_entities(func.coalesce(func.sum(Opportunity.est_amount), 0))
            .scalar()
        )
        actual_val = float(actual or 0)

        # 预测 = 实际赢单 + 管道中商机 * 概率加权
        active_stages = ["DISCOVERY", "QUALIFICATION", "PROPOSAL", "NEGOTIATION"]
        pipeline_opps = base_query.filter(
            Opportunity.stage.in_(active_stages),
            Opportunity.expected_close_date >= q_start.date(),
            Opportunity.expected_close_date < q_end.date(),
        ).all()

        forecast_from_pipeline = sum(
            float(o.est_amount or 0) * (o.probability or 0) / 100 for o in pipeline_opps
        )
        forecast_val = actual_val + forecast_from_pipeline

        variance = round((actual_val - forecast_val) / forecast_val * 100, 1) if forecast_val > 0 else 0

        quarters.append(
            {
                "label": _quarter_label(q),
                "forecast": round(forecast_val, 2),
                "actual": round(actual_val, 2),
                "variance": variance,
            }
        )

    return {"quarters": quarters}
