# -*- coding: utf-8 -*-
"""
战略管理服务 - 同比分析
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.common.query_filters import apply_pagination
from app.models.strategy import CSF, KPI, Strategy, StrategyComparison
from app.schemas.strategy.yoy_report import (
    CSFComparisonItem,
    DimensionComparisonDetail,
    KPIComparisonItem,
    YoYReportResponse,
)
from app.schemas.strategy import StrategyComparisonCreate


def create_strategy_comparison(
    db: Session,
    data: StrategyComparisonCreate,
    created_by: int
) -> StrategyComparison:
    """
    创建战略对比记录

    Args:
        db: 数据库会话
        data: 创建数据
        created_by: 创建人 ID

    Returns:
        StrategyComparison: 创建的对比记录
    """
    comparison = StrategyComparison(
        base_strategy_id=data.base_strategy_id,
        compare_strategy_id=data.compare_strategy_id,
        comparison_type=data.comparison_type,
        base_year=data.base_year,
        compare_year=data.compare_year,
        summary=data.summary,
        created_by=created_by,
    )
    db.add(comparison)
    db.commit()
    db.refresh(comparison)
    return comparison


def get_strategy_comparison(
    db: Session,
    comparison_id: int
) -> Optional[StrategyComparison]:
    """
    获取战略对比记录

    Args:
        db: 数据库会话
        comparison_id: 对比记录 ID

    Returns:
        Optional[StrategyComparison]: 对比记录
    """
    return db.query(StrategyComparison).filter(
        StrategyComparison.id == comparison_id,
        StrategyComparison.is_active
    ).first()


def list_strategy_comparisons(
    db: Session,
    base_strategy_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 20
) -> tuple[List[StrategyComparison], int]:
    """
    获取战略对比记录列表

    Args:
        db: 数据库会话
        base_strategy_id: 基准战略 ID 筛选
        skip: 跳过数量
        limit: 限制数量

    Returns:
        tuple: (对比记录列表, 总数)
    """
    query = db.query(StrategyComparison).filter(StrategyComparison.is_active)

    if base_strategy_id:
        query = query.filter(StrategyComparison.base_strategy_id == base_strategy_id)

    total = query.count()
    items = apply_pagination(query.order_by(StrategyComparison.created_at.desc()), skip, limit).all()

    return items, total


def delete_strategy_comparison(db: Session, comparison_id: int) -> bool:
    """
    删除战略对比记录（软删除）

    Args:
        db: 数据库会话
        comparison_id: 对比记录 ID

    Returns:
        bool: 是否删除成功
    """
    comparison = get_strategy_comparison(db, comparison_id)
    if not comparison:
        return False

    comparison.is_active = False
    db.commit()
    return True


def generate_yoy_report(
    db: Session,
    current_year: int,
    previous_year: Optional[int] = None
) -> YoYReportResponse:
    """
    生成同比报告

    Args:
        db: 数据库会话
        current_year: 当前年度
        previous_year: 对比年度（默认为上一年）

    Returns:
        YoYReportResponse: 同比报告
    """
    if previous_year is None:
        previous_year = current_year - 1

    # 获取两年的战略
    current_strategy = db.query(Strategy).filter(
        Strategy.year == current_year,
        Strategy.is_active
    ).first()

    previous_strategy = db.query(Strategy).filter(
        Strategy.year == previous_year,
        Strategy.is_active
    ).first()

    if not current_strategy or not previous_strategy:
        return YoYReportResponse(
            current_year=current_year,
            previous_year=previous_year,
            current_strategy_id=current_strategy.id if current_strategy else None,
            previous_strategy_id=previous_strategy.id if previous_strategy else None,
            dimensions=[],
            overall_health_change=None,
            generated_at=date.today(),
        )

    # 计算健康度变化
    from .health_calculator import calculate_strategy_health, calculate_dimension_health

    current_health = calculate_strategy_health(db, current_strategy.id)
    previous_health = calculate_strategy_health(db, previous_strategy.id)

    overall_change = None
    if current_health is not None and previous_health is not None:
        overall_change = current_health - previous_health

    # 各维度对比
    dimension_names = {
        "FINANCIAL": "财务维度",
        "CUSTOMER": "客户维度",
        "INTERNAL": "内部运营维度",
        "LEARNING": "学习成长维度",
    }

    dimensions = []
    for dim_code, dim_name in dimension_names.items():
        current_dim = calculate_dimension_health(db, current_strategy.id, dim_code)
        previous_dim = calculate_dimension_health(db, previous_strategy.id, dim_code)

        score_change = None
        if current_dim.get("score") is not None and previous_dim.get("score") is not None:
            score_change = current_dim["score"] - previous_dim["score"]

        # 获取 CSF 对比
        csf_comparisons = _compare_csfs(db, current_strategy.id, previous_strategy.id, dim_code)

        dimensions.append(DimensionComparisonDetail(
            dimension=dim_code,
            dimension_name=dim_name,
            current_score=current_dim.get("score"),
            previous_score=previous_dim.get("score"),
            score_change=score_change,
            csf_comparisons=csf_comparisons,
        ))

    return YoYReportResponse(
        current_year=current_year,
        previous_year=previous_year,
        current_strategy_id=current_strategy.id,
        previous_strategy_id=previous_strategy.id,
        dimensions=dimensions,
        overall_health_change=overall_change,
        generated_at=date.today(),
    )


def _compare_csfs(
    db: Session,
    current_strategy_id: int,
    previous_strategy_id: int,
    dimension: str
) -> List[CSFComparisonItem]:
    """
    对比两个战略的 CSF

    Args:
        db: 数据库会话
        current_strategy_id: 当前战略 ID
        previous_strategy_id: 对比战略 ID
        dimension: BSC 维度

    Returns:
        List[CSFComparisonItem]: CSF 对比列表
    """
    from .health_calculator import calculate_csf_health

    current_csfs = db.query(CSF).filter(
        CSF.strategy_id == current_strategy_id,
        CSF.dimension == dimension,
        CSF.is_active
    ).all()

    previous_csfs = db.query(CSF).filter(
        CSF.strategy_id == previous_strategy_id,
        CSF.dimension == dimension,
        CSF.is_active
    ).all()

    # 按编码匹配
    previous_map = {csf.code: csf for csf in previous_csfs}

    comparisons = []
    for current in current_csfs:
        previous = previous_map.get(current.code)

        current_health = calculate_csf_health(db, current.id)
        previous_health = calculate_csf_health(db, previous.id) if previous else {"score": None}

        score_change = None
        if current_health.get("score") is not None and previous_health.get("score") is not None:
            score_change = current_health["score"] - previous_health["score"]

        # 获取 KPI 对比
        kpi_comparisons = _compare_kpis(db, current.id, previous.id if previous else None)

        comparisons.append(CSFComparisonItem(
            csf_code=current.code,
            csf_name=current.name,
            current_score=current_health.get("score"),
            previous_score=previous_health.get("score"),
            score_change=score_change,
            is_new=previous is None,
            kpi_comparisons=kpi_comparisons,
        ))

    return comparisons


def _compare_kpis(
    db: Session,
    current_csf_id: int,
    previous_csf_id: Optional[int]
) -> List[KPIComparisonItem]:
    """
    对比两个 CSF 的 KPI

    Args:
        db: 数据库会话
        current_csf_id: 当前 CSF ID
        previous_csf_id: 对比 CSF ID

    Returns:
        List[KPIComparisonItem]: KPI 对比列表
    """
    from .health_calculator import calculate_kpi_completion_rate

    current_kpis = db.query(KPI).filter(
        KPI.csf_id == current_csf_id,
        KPI.is_active
    ).all()

    previous_kpis = []
    if previous_csf_id:
        previous_kpis = db.query(KPI).filter(
            KPI.csf_id == previous_csf_id,
            KPI.is_active
        ).all()

    # 按编码匹配
    previous_map = {kpi.code: kpi for kpi in previous_kpis}

    comparisons = []
    for current in current_kpis:
        previous = previous_map.get(current.code)

        current_rate = calculate_kpi_completion_rate(current)
        previous_rate = calculate_kpi_completion_rate(previous) if previous else None

        rate_change = None
        if current_rate is not None and previous_rate is not None:
            rate_change = float(current_rate - previous_rate)

        target_change = None
        if current.target_value is not None and previous and previous.target_value is not None:
            target_change = float(current.target_value - previous.target_value)

        comparisons.append(KPIComparisonItem(
            kpi_code=current.code,
            kpi_name=current.name,
            current_target=current.target_value,
            previous_target=previous.target_value if previous else None,
            target_change=Decimal(str(target_change)) if target_change else None,
            current_completion_rate=current_rate,
            previous_completion_rate=previous_rate,
            completion_rate_change=rate_change,
            is_new=previous is None,
        ))

    return comparisons


# ============================================
# 统计分析
# ============================================

def get_multi_year_trend(
    db: Session,
    years: int = 3
) -> Dict[str, Any]:
    """
    获取多年趋势数据

    Args:
        db: 数据库会话
        years: 年数

    Returns:
        Dict: 多年趋势数据
    """
    current_year = date.today().year
    from .health_calculator import calculate_strategy_health, calculate_dimension_health

    trend_data = []
    for year in range(current_year - years + 1, current_year + 1):
        strategy = db.query(Strategy).filter(
            Strategy.year == year,
            Strategy.is_active
        ).first()

        if not strategy:
            trend_data.append({
                "year": year,
                "overall_health": None,
                "financial": None,
                "customer": None,
                "internal": None,
                "learning": None,
            })
            continue

        overall = calculate_strategy_health(db, strategy.id)
        financial = calculate_dimension_health(db, strategy.id, "FINANCIAL")
        customer = calculate_dimension_health(db, strategy.id, "CUSTOMER")
        internal = calculate_dimension_health(db, strategy.id, "INTERNAL")
        learning = calculate_dimension_health(db, strategy.id, "LEARNING")

        trend_data.append({
            "year": year,
            "overall_health": overall,
            "financial": financial.get("score"),
            "customer": customer.get("score"),
            "internal": internal.get("score"),
            "learning": learning.get("score"),
        })

    return {
        "years": list(range(current_year - years + 1, current_year + 1)),
        "trend": trend_data,
    }


def get_kpi_achievement_comparison(
    db: Session,
    current_year: int,
    previous_year: Optional[int] = None
) -> Dict[str, Any]:
    """
    获取 KPI 达成率对比

    Args:
        db: 数据库会话
        current_year: 当前年度
        previous_year: 对比年度

    Returns:
        Dict: KPI 达成率对比
    """
    if previous_year is None:
        previous_year = current_year - 1

    from .health_calculator import calculate_kpi_completion_rate

    current_strategy = db.query(Strategy).filter(
        Strategy.year == current_year,
        Strategy.is_active
    ).first()

    previous_strategy = db.query(Strategy).filter(
        Strategy.year == previous_year,
        Strategy.is_active
    ).first()

    def get_kpi_stats(strategy_id: int) -> Dict[str, Any]:
        kpis = db.query(KPI).join(CSF).filter(
            CSF.strategy_id == strategy_id,
            CSF.is_active,
            KPI.is_active
        ).all()

        total = len(kpis)
        excellent = 0  # >= 100%
        good = 0       # >= 80%
        warning = 0    # >= 60%
        danger = 0     # < 60%

        for kpi in kpis:
            rate = calculate_kpi_completion_rate(kpi)
            if rate is None:
                continue
            if rate >= 100:
                excellent += 1
            elif rate >= 80:
                good += 1
            elif rate >= 60:
                warning += 1
            else:
                danger += 1

        return {
            "total": total,
            "excellent": excellent,
            "good": good,
            "warning": warning,
            "danger": danger,
            "excellent_rate": excellent / total * 100 if total > 0 else 0,
        }

    current_stats = get_kpi_stats(current_strategy.id) if current_strategy else None
    previous_stats = get_kpi_stats(previous_strategy.id) if previous_strategy else None

    return {
        "current_year": current_year,
        "previous_year": previous_year,
        "current": current_stats,
        "previous": previous_stats,
    }
