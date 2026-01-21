# -*- coding: utf-8 -*-
"""
绩效管理服务 - 历史绩效
"""
from datetime import date
from typing import Any, Dict, List

from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from app.models.performance import MonthlyWorkSummary

from .calculation import calculate_final_score, get_score_level


def get_historical_performance(
    db: Session,
    employee_id: int,
    months: int = 3
) -> List[Dict[str, Any]]:
    """
    获取员工的历史绩效记录

    Args:
        db: 数据库会话
        employee_id: 员工ID
        months: 查询最近几个月

    Returns:
        历史绩效列表
    """
    # 计算开始周期
    today = date.today()
    periods = []
    for i in range(months):
        period_date = today - relativedelta(months=i+1)
        periods.append(period_date.strftime("%Y-%m"))

    # 查询工作总结
    summaries = db.query(MonthlyWorkSummary).filter(
        MonthlyWorkSummary.employee_id == employee_id,
        MonthlyWorkSummary.period.in_(periods),
        MonthlyWorkSummary.status == 'COMPLETED'
    ).order_by(MonthlyWorkSummary.period.desc()).all()

    history = []
    for summary in summaries:
        score_result = calculate_final_score(
            db, summary.id, summary.period
        )

        if score_result:
            history.append({
                'period': summary.period,
                'final_score': score_result['final_score'],
                'level': get_score_level(score_result['final_score']),
                'dept_score': score_result['dept_score'],
                'project_score': score_result['project_score']
            })

    return history
