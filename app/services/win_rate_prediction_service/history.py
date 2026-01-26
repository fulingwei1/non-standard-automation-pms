# -*- coding: utf-8 -*-
"""
中标率预测服务 - 历史数据获取
"""
from datetime import date, timedelta
from typing import Optional, Tuple

from sqlalchemy import case, func

from app.models.enums import LeadOutcomeEnum
from app.models.project import Customer, Project
from app.schemas.presales import DimensionScore


def get_salesperson_historical_win_rate(
    service: "WinRatePredictionService",
    salesperson_id: int,
    lookback_months: int = 24
) -> Tuple[float, int]:
    """获取销售人员历史中标率

    Args:
        service: WinRatePredictionService实例
        salesperson_id: 销售人员ID
        lookback_months: 回溯月数

    Returns:
        (中标率, 样本数)
    """
    cutoff_date = date.today() - timedelta(days=30 * lookback_months)

    stats = service.db.query(
        func.count(Project.id).label('total'),
        func.sum(case(
            (Project.outcome == LeadOutcomeEnum.WON.value, 1),
            else_=0
        )).label('won')
    ).filter(
        Project.salesperson_id == salesperson_id,
        Project.created_at >= cutoff_date,
        Project.outcome.in_([LeadOutcomeEnum.WON.value, LeadOutcomeEnum.LOST.value])
    ).first()

    total = stats.total or 0
    won = stats.won or 0

    if total == 0:
        return 0.20, 0  # 无数据时返回行业平均值

    return won / total, total


def get_customer_cooperation_history(
    service: "WinRatePredictionService",
    customer_id: Optional[int] = None,
    customer_name: Optional[str] = None
) -> Tuple[int, int]:
    """获取客户历史合作情况

    Returns:
        (总合作次数, 成功次数)
    """
    query = service.db.query(Project)

    if customer_id:
        query = query.filter(Project.customer_id == customer_id)
    elif customer_name:
        # 通过客户名称查找
        customer = service.db.query(Customer).filter(
            Customer.customer_name == customer_name
        ).first()
        if customer:
            query = query.filter(Project.customer_id == customer.id)
        else:
            return 0, 0
    else:
        return 0, 0

    total = query.count()
    won = query.filter(Project.outcome == LeadOutcomeEnum.WON.value).count()

    return total, won


def get_similar_leads_statistics(
    service: "WinRatePredictionService",
    dimension_scores: DimensionScore,
    score_tolerance: float = 10
) -> Tuple[int, float]:
    """获取相似线索统计

    Args:
        service: WinRatePredictionService实例
        dimension_scores: 五维评估分数
        score_tolerance: 分数容差

    Returns:
        (相似线索数, 相似线索中标率)
    """
    total_score = dimension_scores.total_score

    similar_leads = service.db.query(Project).filter(
        Project.evaluation_score.between(
            total_score - score_tolerance,
            total_score + score_tolerance
        ),
        Project.outcome.in_([LeadOutcomeEnum.WON.value, LeadOutcomeEnum.LOST.value])
    ).all()

    if not similar_leads:
        return 0, 0

    won = sum(1 for p in similar_leads if p.outcome == LeadOutcomeEnum.WON.value)
    return len(similar_leads), won / len(similar_leads)
