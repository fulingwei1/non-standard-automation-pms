# -*- coding: utf-8 -*-
"""
销售漏斗综合 API
GET /sales/funnel — 统一返回各阶段商机数量/金额、转化率、赢单率、漏斗健康度
"""

from datetime import date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.sales_permissions import filter_sales_data_by_scope
from app.models.sales import Contract, Lead, Opportunity, Quote
from app.models.enums.sales import OpportunityStageEnum
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()

# 漏斗阶段顺序（用于转化率计算）
_ACTIVE_STAGES = [
    OpportunityStageEnum.DISCOVERY,
    OpportunityStageEnum.QUALIFICATION,
    OpportunityStageEnum.PROPOSAL,
    OpportunityStageEnum.NEGOTIATION,
    OpportunityStageEnum.CLOSING,
    OpportunityStageEnum.WON,
]

_STAGE_NAMES = {
    OpportunityStageEnum.DISCOVERY: "初步接触",
    OpportunityStageEnum.QUALIFICATION: "需求挖掘",
    OpportunityStageEnum.PROPOSAL: "方案介绍",
    OpportunityStageEnum.NEGOTIATION: "价格谈判",
    OpportunityStageEnum.CLOSING: "成交促成",
    OpportunityStageEnum.WON: "赢单",
}

# 行业基准转化率，用于健康度评估
_BENCHMARK_RATES = {
    OpportunityStageEnum.DISCOVERY: 65.0,
    OpportunityStageEnum.QUALIFICATION: 60.0,
    OpportunityStageEnum.PROPOSAL: 70.0,
    OpportunityStageEnum.NEGOTIATION: 65.0,
    OpportunityStageEnum.CLOSING: 80.0,
}


@router.get("/funnel", response_model=ResponseModel, summary="销售漏斗综合数据")
def get_sales_funnel_overview(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    owner_id: Optional[int] = Query(None, description="销售人员 ID"),
    customer_id: Optional[int] = Query(None, description="客户 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    销售漏斗综合数据

    返回：
    - stages: 各阶段商机数量、金额、转化率
    - win_rate: 赢单率统计
    - health: 漏斗健康度指标
    - pipeline_summary: 线索→商机→报价→合同 总览
    """
    start_dt = start_date or (date.today() - timedelta(days=90))
    end_dt = end_date or date.today()
    end_dt_next = end_dt + timedelta(days=1)

    # ---------- 1. 商机阶段统计 ----------
    opp_base = db.query(Opportunity).filter(
        Opportunity.created_at >= start_dt,
        Opportunity.created_at < end_dt_next,
    )
    opp_base = filter_sales_data_by_scope(opp_base, current_user, db, Opportunity, "owner_id")
    if owner_id:
        opp_base = opp_base.filter(Opportunity.owner_id == owner_id)
    if customer_id:
        opp_base = opp_base.filter(Opportunity.customer_id == customer_id)

    # 按阶段统计数量和金额
    stage_stats_rows = (
        db.query(
            Opportunity.stage,
            func.count(Opportunity.id).label("cnt"),
            func.coalesce(func.sum(Opportunity.est_amount), 0).label("amount"),
        )
        .filter(Opportunity.id.in_(opp_base.with_entities(Opportunity.id).subquery().select()))
        .group_by(Opportunity.stage)
        .all()
    )
    stage_map = {row.stage: {"count": row.cnt, "amount": float(row.amount)} for row in stage_stats_rows}

    # 构建 stages 列表（累计到达 = 当前 + 后续阶段）
    stages_result = []
    prev_reached = None
    for i, stage in enumerate(_ACTIVE_STAGES):
        # 累计到达该阶段的商机数 = 该阶段及其后续阶段之和
        reached = sum(
            stage_map.get(s.value, {}).get("count", 0)
            for s in _ACTIVE_STAGES[i:]
        )
        current_count = stage_map.get(stage.value, {}).get("count", 0)
        current_amount = stage_map.get(stage.value, {}).get("amount", 0)

        # 阶段间转化率
        if prev_reached and prev_reached > 0:
            conversion = round(reached / prev_reached * 100, 1)
        else:
            conversion = 100.0 if i == 0 else 0.0

        stages_result.append({
            "stage": stage.value,
            "stage_name": _STAGE_NAMES.get(stage, stage.value),
            "current_count": current_count,
            "reached_count": reached,
            "amount": current_amount,
            "conversion_rate": conversion,
        })
        prev_reached = reached

    # ---------- 2. 赢单率 ----------
    total_closed = (
        stage_map.get(OpportunityStageEnum.WON.value, {}).get("count", 0)
        + stage_map.get(OpportunityStageEnum.LOST.value, {}).get("count", 0)
    )
    # LOST 不在 _ACTIVE_STAGES，单独查
    lost_count = (
        db.query(func.count(Opportunity.id))
        .filter(
            Opportunity.id.in_(opp_base.with_entities(Opportunity.id).subquery().select()),
            Opportunity.stage == OpportunityStageEnum.LOST.value,
        )
        .scalar() or 0
    )
    total_closed += lost_count  # 修正：加上 lost
    total_closed -= stage_map.get(OpportunityStageEnum.LOST.value, {}).get("count", 0)  # 避免重复计
    won_count = stage_map.get(OpportunityStageEnum.WON.value, {}).get("count", 0)
    won_amount = stage_map.get(OpportunityStageEnum.WON.value, {}).get("amount", 0)
    # 简化: total_closed = won + lost
    total_closed = won_count + lost_count
    win_rate = round(won_count / total_closed * 100, 1) if total_closed > 0 else 0.0

    # 平均销售周期（赢单商机的 created_at → updated_at）
    won_opps = opp_base.filter(Opportunity.stage == OpportunityStageEnum.WON.value).all()
    if won_opps:
        cycle_days = [
            (o.updated_at.date() - o.created_at.date()).days
            for o in won_opps if o.updated_at and o.created_at
        ]
        avg_cycle = round(sum(cycle_days) / len(cycle_days), 1) if cycle_days else 0
    else:
        avg_cycle = 0

    # ---------- 3. Pipeline 金额 ----------
    active_opp_ids = [
        o.id for o in opp_base.filter(
            Opportunity.stage.notin_([OpportunityStageEnum.WON.value, OpportunityStageEnum.LOST.value])
        ).all()
    ]
    if active_opp_ids:
        pipe_row = db.query(
            func.sum(Opportunity.est_amount).label("total"),
            func.sum(Opportunity.est_amount * Opportunity.probability / 100).label("weighted"),
        ).filter(Opportunity.id.in_(active_opp_ids)).first()
        pipeline_total = float(pipe_row.total or 0)
        pipeline_weighted = float(pipe_row.weighted or 0)
    else:
        pipeline_total = 0
        pipeline_weighted = 0

    # ---------- 4. 漏斗健康度 ----------
    health_issues = []
    health_score = 100
    for stage_item in stages_result:
        stage_enum = OpportunityStageEnum(stage_item["stage"])
        benchmark = _BENCHMARK_RATES.get(stage_enum)
        if benchmark and stage_item["conversion_rate"] < benchmark - 10:
            health_issues.append({
                "stage": stage_item["stage"],
                "stage_name": stage_item["stage_name"],
                "issue": "conversion_low",
                "current": stage_item["conversion_rate"],
                "benchmark": benchmark,
            })
            health_score -= 15

    if win_rate < 20 and total_closed > 0:
        health_issues.append({"issue": "win_rate_low", "current": win_rate, "benchmark": 20.0})
        health_score -= 20

    health_score = max(health_score, 0)
    health_level = "healthy" if health_score >= 80 else ("warning" if health_score >= 50 else "critical")

    # ---------- 5. 线索→合同 总览（兼容原 /statistics/funnel） ----------
    def _count_with_scope(model, owner_field="owner_id"):
        q = db.query(model).filter(
            model.created_at >= start_dt,
            model.created_at < end_dt_next,
        )
        q = filter_sales_data_by_scope(q, current_user, db, model, owner_field)
        if owner_id:
            q = q.filter(getattr(model, owner_field) == owner_id)
        return q.count()

    leads_count = _count_with_scope(Lead)
    opps_count = opp_base.count()
    quotes_count = _count_with_scope(Quote)
    contracts_count = _count_with_scope(Contract, "sales_owner_id")

    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": start_dt.isoformat(), "end": end_dt.isoformat()},
            "stages": stages_result,
            "win_rate": {
                "won": won_count,
                "lost": lost_count,
                "total_closed": total_closed,
                "rate": win_rate,
                "won_amount": won_amount,
                "avg_cycle_days": avg_cycle,
            },
            "pipeline": {
                "total_value": pipeline_total,
                "weighted_value": pipeline_weighted,
                "active_opportunities": len(active_opp_ids),
            },
            "health": {
                "score": health_score,
                "level": health_level,
                "issues": health_issues,
            },
            "pipeline_summary": {
                "leads": leads_count,
                "opportunities": opps_count,
                "quotes": quotes_count,
                "contracts": contracts_count,
            },
        },
    )
