# -*- coding: utf-8 -*-
"""
中标率预测服务 - 分析和验证
"""
from datetime import date, timedelta
from typing import Any, Dict, Optional

from app.models.enums import LeadOutcomeEnum, WinProbabilityLevelEnum
from app.models.project import Project


def get_win_rate_distribution(
    service: "WinRatePredictionService",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict[str, Any]:
    """获取中标率分布统计

    Returns:
        按概率等级分组的线索数量分布
    """
    query = service.db.query(Project).filter(
        Project.predicted_win_rate.isnot(None)
    )

    if start_date:
        query = query.filter(Project.created_at >= start_date)
    if end_date:
        query = query.filter(Project.created_at < end_date)

    projects = query.all()

    distribution = {
        WinProbabilityLevelEnum.VERY_HIGH.value: {'count': 0, 'won': 0},
        WinProbabilityLevelEnum.HIGH.value: {'count': 0, 'won': 0},
        WinProbabilityLevelEnum.MEDIUM.value: {'count': 0, 'won': 0},
        WinProbabilityLevelEnum.LOW.value: {'count': 0, 'won': 0},
        WinProbabilityLevelEnum.VERY_LOW.value: {'count': 0, 'won': 0}
    }

    for project in projects:
        rate = project.predicted_win_rate
        if rate >= 0.80:
            level = WinProbabilityLevelEnum.VERY_HIGH.value
        elif rate >= 0.60:
            level = WinProbabilityLevelEnum.HIGH.value
        elif rate >= 0.40:
            level = WinProbabilityLevelEnum.MEDIUM.value
        elif rate >= 0.20:
            level = WinProbabilityLevelEnum.LOW.value
        else:
            level = WinProbabilityLevelEnum.VERY_LOW.value

        distribution[level]['count'] += 1
        if project.outcome == LeadOutcomeEnum.WON.value:
            distribution[level]['won'] += 1

    # 计算各等级实际中标率
    for level in distribution:
        count = distribution[level]['count']
        won = distribution[level]['won']
        distribution[level]['actual_win_rate'] = round(won / count, 3) if count > 0 else 0

    return distribution


def validate_model_accuracy(
    service: "WinRatePredictionService",
    lookback_months: int = 12
) -> Dict[str, Any]:
    """验证预测模型准确度

    对比预测中标率与实际中标情况
    """
    cutoff_date = date.today() - timedelta(days=30 * lookback_months)

    projects = service.db.query(Project).filter(
        Project.predicted_win_rate.isnot(None),
        Project.created_at >= cutoff_date,
        Project.outcome.in_([LeadOutcomeEnum.WON.value, LeadOutcomeEnum.LOST.value])
    ).all()

    if not projects:
        return {'error': '无足够数据进行验证'}

    # 计算预测准确度
    correct_predictions = 0
    total = len(projects)

    for project in projects:
        predicted_win = project.predicted_win_rate >= 0.5
        actual_win = project.outcome == LeadOutcomeEnum.WON.value

        if predicted_win == actual_win:
            correct_predictions += 1

    accuracy = correct_predictions / total

    # 计算 Brier 分数（越低越好）
    brier_score = sum(
        (p.predicted_win_rate - (1 if p.outcome == LeadOutcomeEnum.WON.value else 0)) ** 2
        for p in projects
    ) / total

    return {
        'total_samples': total,
        'accuracy': round(accuracy, 3),
        'brier_score': round(brier_score, 4),
        'period_months': lookback_months
    }
