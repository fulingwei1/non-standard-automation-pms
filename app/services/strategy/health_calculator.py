# -*- coding: utf-8 -*-
"""
战略管理服务 - 健康度计算器
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.strategy import CSF, KPI, Strategy


def calculate_kpi_completion_rate(kpi: KPI) -> Optional[float]:
    """
    计算单个 KPI 的完成率

    Args:
        kpi: KPI 对象

    Returns:
        Optional[float]: 完成率（0-100）
    """
    if kpi.target_value is None or kpi.target_value == 0:
        return None

    if kpi.current_value is None:
        return 0

    if kpi.direction == "UP":
        # 越大越好
        rate = float(kpi.current_value) / float(kpi.target_value) * 100
    else:
        # 越小越好
        if float(kpi.current_value) == 0:
            rate = 100 if float(kpi.target_value) == 0 else 200
        else:
            rate = float(kpi.target_value) / float(kpi.current_value) * 100

    return min(rate, 150)  # 最高 150%


def get_health_level(score: int) -> str:
    """
    根据健康度分数获取等级

    Args:
        score: 健康度分数（0-100）

    Returns:
        str: 健康等级
    """
    if score >= 90:
        return "EXCELLENT"
    elif score >= 70:
        return "GOOD"
    elif score >= 50:
        return "WARNING"
    else:
        return "DANGER"


def calculate_kpi_health(db: Session, kpi_id: int) -> Dict[str, Any]:
    """
    计算单个 KPI 的健康度

    Args:
        db: 数据库会话
        kpi_id: KPI ID

    Returns:
        Dict: 健康度数据
    """
    kpi = db.query(KPI).filter(KPI.id == kpi_id, KPI.is_active == True).first()
    if not kpi:
        return {"score": None, "level": None, "completion_rate": None}

    completion_rate = calculate_kpi_completion_rate(kpi)
    if completion_rate is None:
        return {"score": None, "level": None, "completion_rate": None}

    # 根据完成率计算健康度分数
    if completion_rate >= 100:
        score = 100
    elif completion_rate >= 80:
        score = int(80 + (completion_rate - 80))
    elif completion_rate >= 60:
        score = int(60 + (completion_rate - 60))
    else:
        score = int(completion_rate)

    return {
        "score": score,
        "level": get_health_level(score),
        "completion_rate": completion_rate,
    }


def calculate_csf_health(db: Session, csf_id: int) -> Dict[str, Any]:
    """
    计算 CSF 的健康度（基于关联 KPI 的加权平均）

    Args:
        db: 数据库会话
        csf_id: CSF ID

    Returns:
        Dict: 健康度数据
    """
    csf = db.query(CSF).filter(CSF.id == csf_id, CSF.is_active == True).first()
    if not csf:
        return {"score": None, "level": None, "kpi_completion_rate": None}

    kpis = db.query(KPI).filter(
        KPI.csf_id == csf_id,
        KPI.is_active == True
    ).all()

    if not kpis:
        return {"score": None, "level": None, "kpi_completion_rate": None}

    total_weight = 0
    weighted_score = 0
    total_completion = 0
    valid_kpi_count = 0

    for kpi in kpis:
        health_data = calculate_kpi_health(db, kpi.id)
        if health_data["score"] is not None:
            weight = float(kpi.weight or 1)
            total_weight += weight
            weighted_score += health_data["score"] * weight
            if health_data["completion_rate"] is not None:
                total_completion += health_data["completion_rate"]
                valid_kpi_count += 1

    if total_weight == 0:
        return {"score": None, "level": None, "kpi_completion_rate": None}

    score = int(weighted_score / total_weight)
    avg_completion = total_completion / valid_kpi_count if valid_kpi_count > 0 else None

    return {
        "score": score,
        "level": get_health_level(score),
        "kpi_completion_rate": avg_completion,
    }


def calculate_dimension_health(db: Session, strategy_id: int, dimension: str) -> Dict[str, Any]:
    """
    计算维度的健康度（基于关联 CSF 的加权平均）

    Args:
        db: 数据库会话
        strategy_id: 战略 ID
        dimension: BSC 维度

    Returns:
        Dict: 健康度数据
    """
    csfs = db.query(CSF).filter(
        CSF.strategy_id == strategy_id,
        CSF.dimension == dimension,
        CSF.is_active == True
    ).all()

    if not csfs:
        return {"score": None, "level": None}

    total_weight = 0
    weighted_score = 0

    for csf in csfs:
        health_data = calculate_csf_health(db, csf.id)
        if health_data["score"] is not None:
            weight = float(csf.weight or 1)
            total_weight += weight
            weighted_score += health_data["score"] * weight

    if total_weight == 0:
        return {"score": None, "level": None}

    score = int(weighted_score / total_weight)

    return {
        "score": score,
        "level": get_health_level(score),
    }


def calculate_strategy_health(db: Session, strategy_id: int) -> Optional[int]:
    """
    计算战略整体健康度（四维度加权平均）

    Args:
        db: 数据库会话
        strategy_id: 战略 ID

    Returns:
        Optional[int]: 健康度分数（0-100）
    """
    strategy = db.query(Strategy).filter(
        Strategy.id == strategy_id,
        Strategy.is_active == True
    ).first()
    if not strategy:
        return None

    # 默认四维度权重
    dimension_weights = {
        "FINANCIAL": 25,
        "CUSTOMER": 25,
        "INTERNAL": 25,
        "LEARNING": 25,
    }

    total_weight = 0
    weighted_score = 0

    for dimension, default_weight in dimension_weights.items():
        health_data = calculate_dimension_health(db, strategy_id, dimension)
        if health_data["score"] is not None:
            # 计算该维度的实际权重（基于 CSF 权重总和）
            csf_weights = db.query(func.sum(CSF.weight)).filter(
                CSF.strategy_id == strategy_id,
                CSF.dimension == dimension,
                CSF.is_active == True
            ).scalar() or 0

            weight = float(csf_weights) if csf_weights > 0 else default_weight
            total_weight += weight
            weighted_score += health_data["score"] * weight

    if total_weight == 0:
        return None

    return int(weighted_score / total_weight)


def get_health_trend(
    db: Session,
    strategy_id: int,
    periods: int = 6
) -> List[Dict[str, Any]]:
    """
    获取健康度趋势

    Args:
        db: 数据库会话
        strategy_id: 战略 ID
        periods: 期数

    Returns:
        List[Dict]: 趋势数据
    """
    from app.models.strategy import StrategyReview

    reviews = db.query(StrategyReview).filter(
        StrategyReview.strategy_id == strategy_id,
        StrategyReview.is_active == True
    ).order_by(StrategyReview.review_date.desc()).limit(periods).all()

    return [
        {
            "date": review.review_date,
            "period": review.review_period,
            "overall_score": review.health_score,
            "financial_score": review.financial_score,
            "customer_score": review.customer_score,
            "internal_score": review.internal_score,
            "learning_score": review.learning_score,
        }
        for review in reversed(reviews)
    ]


def get_dimension_health_details(
    db: Session,
    strategy_id: int
) -> List[Dict[str, Any]]:
    """
    获取各维度健康度详情

    Args:
        db: 数据库会话
        strategy_id: 战略 ID

    Returns:
        List[Dict]: 各维度健康度详情
    """
    dimension_names = {
        "FINANCIAL": "财务维度",
        "CUSTOMER": "客户维度",
        "INTERNAL": "内部运营维度",
        "LEARNING": "学习成长维度",
    }

    details = []
    for dimension, name in dimension_names.items():
        health_data = calculate_dimension_health(db, strategy_id, dimension)

        # 统计该维度的 CSF 和 KPI 数量
        csf_count = db.query(CSF).filter(
            CSF.strategy_id == strategy_id,
            CSF.dimension == dimension,
            CSF.is_active == True
        ).count()

        kpi_count = db.query(KPI).join(CSF).filter(
            CSF.strategy_id == strategy_id,
            CSF.dimension == dimension,
            CSF.is_active == True,
            KPI.is_active == True
        ).count()

        # 统计 KPI 完成情况
        kpis = db.query(KPI).join(CSF).filter(
            CSF.strategy_id == strategy_id,
            CSF.dimension == dimension,
            CSF.is_active == True,
            KPI.is_active == True
        ).all()

        on_track = 0
        at_risk = 0
        off_track = 0

        for kpi in kpis:
            kpi_health = calculate_kpi_health(db, kpi.id)
            if kpi_health["completion_rate"] is not None:
                if kpi_health["completion_rate"] >= 80:
                    on_track += 1
                elif kpi_health["completion_rate"] >= 50:
                    at_risk += 1
                else:
                    off_track += 1

        # 计算 KPI 完成率
        kpi_completion_rate = (on_track / kpi_count * 100) if kpi_count > 0 else 0.0

        details.append({
            "dimension": dimension,
            "dimension_name": name,
            "score": health_data["score"],
            "level": health_data["level"],
            "health_level": health_data["level"],  # 兼容 schema 字段名
            "csf_count": csf_count,
            "kpi_count": kpi_count,
            "kpi_completion_rate": kpi_completion_rate,
            "kpi_on_track": on_track,
            "kpi_at_risk": at_risk,
            "kpi_off_track": off_track,
        })

    return details
