# -*- coding: utf-8 -*-
"""
绩效管理服务 - 分数计算
"""
from datetime import date
from typing import Any, Dict, Optional

from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from app.models.performance import (
    EvaluationStatusEnum,
    EvaluationWeightConfig,
    EvaluatorTypeEnum,
    MonthlyWorkSummary,
    PerformanceEvaluationRecord,
)


def calculate_final_score(
    db: Session,
    summary_id: int,
    period: str
) -> Optional[Dict[str, Any]]:
    """
    计算员工的最终绩效分数

    算法：
    1. 获取该周期的权重配置
    2. 计算部门经理评分 * 部门权重%
    3. 计算所有项目经理评分的加权平均 * 项目权重%
    4. 最终分数 = 部门分数 + 项目分数

    Args:
        db: 数据库会话
        summary_id: 工作总结ID
        period: 评价周期

    Returns:
        {
            'final_score': float,  # 最终分数
            'dept_score': Optional[float],  # 部门经理评分
            'project_score': Optional[float],  # 项目经理加权平均分
            'dept_weight': int,  # 部门权重%
            'project_weight': int,  # 项目权重%
            'details': List[dict]  # 各评价详情
        }
    """
    # 1. 获取权重配置
    year, month = map(int, period.split('-'))
    period_date = date(year, month, 1)

    weight_config = db.query(EvaluationWeightConfig).filter(
        EvaluationWeightConfig.effective_date <= period_date
    ).order_by(EvaluationWeightConfig.effective_date.desc()).first()

    if not weight_config:
        # 使用默认权重 50:50
        dept_weight = 50
        project_weight = 50
    else:
        dept_weight = weight_config.dept_manager_weight
        project_weight = weight_config.project_manager_weight

    # 2. 获取所有评价记录
    evaluations = db.query(PerformanceEvaluationRecord).filter(
        PerformanceEvaluationRecord.summary_id == summary_id,
        PerformanceEvaluationRecord.status == EvaluationStatusEnum.COMPLETED
    ).all()

    if not evaluations:
        return None

    # 3. 分离部门和项目评价
    dept_evaluations = [e for e in evaluations if e.evaluator_type == EvaluatorTypeEnum.DEPT_MANAGER]
    project_evaluations = [e for e in evaluations if e.evaluator_type == EvaluatorTypeEnum.PROJECT_MANAGER]

    # 4. 计算部门经理分数
    dept_score = None
    if dept_evaluations:
        # 通常只有一个部门经理评价
        dept_score = float(dept_evaluations[0].score)

    # 5. 计算项目经理加权平均分
    project_score = None
    if project_evaluations:
        # 使用项目权重进行加权平均
        total_weight = sum([e.project_weight or 0 for e in project_evaluations])
        if total_weight > 0:
            weighted_sum = sum([e.score * (e.project_weight or 0) for e in project_evaluations])
            project_score = float(weighted_sum) / total_weight
        else:
            # 如果没有设置项目权重，使用简单平均
            project_score = float(sum([e.score for e in project_evaluations])) / len(project_evaluations)

    # 6. 计算最终分数
    final_score = 0.0

    if dept_score is not None:
        final_score += dept_score * (dept_weight / 100.0)

    if project_score is not None:
        final_score += project_score * (project_weight / 100.0)

    # 7. 如果只有部门评价或只有项目评价，使用该评价的100%
    if dept_score is not None and project_score is None:
        final_score = dept_score
    elif dept_score is None and project_score is not None:
        final_score = project_score

    # 8. 构建详情
    details = []
    for e in evaluations:
        details.append({
            'evaluator_type': e.evaluator_type,
            'evaluator_id': e.evaluator_id,
            'project_id': e.project_id,
            'project_weight': e.project_weight,
            'score': e.score,
            'comment': e.comment,
            'evaluated_at': e.evaluated_at
        })

    return {
        'final_score': round(final_score, 2),
        'dept_score': dept_score,
        'project_score': round(project_score, 2) if project_score else None,
        'dept_weight': dept_weight,
        'project_weight': project_weight,
        'details': details
    }


def calculate_quarterly_score(
    db: Session,
    employee_id: int,
    end_period: str
) -> Optional[float]:
    """
    计算季度绩效分数（最近3个月的加权平均）

    Args:
        db: 数据库会话
        employee_id: 员工ID
        end_period: 结束周期 (YYYY-MM)

    Returns:
        季度平均分数
    """
    year, month = map(int, end_period.split('-'))
    end_date = date(year, month, 1)

    # 计算前3个月
    periods = []
    for i in range(3):
        period_date = end_date - relativedelta(months=i)
        periods.append(period_date.strftime("%Y-%m"))

    # 获取这3个月的工作总结
    summaries = db.query(MonthlyWorkSummary).filter(
        MonthlyWorkSummary.employee_id == employee_id,
        MonthlyWorkSummary.period.in_(periods),
        MonthlyWorkSummary.status == 'COMPLETED'
    ).all()

    if not summaries:
        return None

    # 计算每个月的最终分数
    monthly_scores = []
    for summary in summaries:
        score_result = calculate_final_score(
            db, summary.id, summary.period
        )
        if score_result and score_result['final_score'] > 0:
            monthly_scores.append(score_result['final_score'])

    if not monthly_scores:
        return None

    # 计算平均分
    quarterly_avg = sum(monthly_scores) / len(monthly_scores)
    return round(quarterly_avg, 2)


def get_score_level(score: float) -> str:
    """
    根据分数获取等级

    Args:
        score: 分数 (60-100)

    Returns:
        等级: A+/A/B+/B/C+/C/D
    """
    if score >= 95:
        return 'A+'
    elif score >= 90:
        return 'A'
    elif score >= 85:
        return 'B+'
    elif score >= 80:
        return 'B'
    elif score >= 75:
        return 'C+'
    elif score >= 70:
        return 'C'
    else:
        return 'D'
