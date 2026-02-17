# -*- coding: utf-8 -*-
"""
KPI数据采集器 - 计算和采集
"""
import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.strategy import KPI, KPIDataSource

# 尝试导入 simpleeval，如果不存在则禁用公式计算
try:
    from simpleeval import simple_eval
    HAS_SIMPLEEVAL = True
except ImportError:
    HAS_SIMPLEEVAL = False

from .registry import get_collector


def calculate_formula(
    formula: str,
    params: Dict[str, Any]
) -> Optional[Decimal]:
    """
    计算公式（使用 simpleeval 安全执行）

    Args:
        formula: 公式字符串（如 "a / b * 100"）
        params: 参数字典（如 {"a": 10, "b": 20}）

    Returns:
        Optional[Decimal]: 计算结果

    Raises:
        RuntimeError: 如果 simpleeval 未安装
    """
    if not formula:
        return None

    if not HAS_SIMPLEEVAL:
        raise RuntimeError(
            "公式计算需要安装 simpleeval 库。请运行: pip install simpleeval"
        )

    try:
        # 将 Decimal 转换为 float 以便计算
        float_params = {
            k: float(v) if isinstance(v, Decimal) else v
            for k, v in params.items()
            if v is not None
        }

        # 使用 simpleeval 安全执行公式
        result = simple_eval(formula, names=float_params)

        return Decimal(str(result))
    except Exception:
        return None


def collect_kpi_value(
    db: Session,
    kpi_id: int,
    data_source_id: Optional[int] = None
) -> Optional[Decimal]:
    """
    采集单个 KPI 的值

    Args:
        db: 数据库会话
        kpi_id: KPI ID
        data_source_id: 指定数据源 ID（可选）

    Returns:
        Optional[Decimal]: 采集到的值
    """
    kpi = db.query(KPI).filter(KPI.id == kpi_id, KPI.is_active).first()
    if not kpi:
        return None

    # 获取数据源配置
    if data_source_id:
        data_source = db.query(KPIDataSource).filter(
            KPIDataSource.id == data_source_id,
            KPIDataSource.kpi_id == kpi_id,
            KPIDataSource.is_active
        ).first()
    else:
        # 使用主数据源
        data_source = db.query(KPIDataSource).filter(
            KPIDataSource.kpi_id == kpi_id,
            KPIDataSource.is_primary,
            KPIDataSource.is_active
        ).first()

    if not data_source:
        return None

    try:
        # 根据数据源类型采集
        if data_source.source_type == "AUTO":
            # 自动采集
            collector = get_collector(data_source.source_module)
            if not collector:
                return None

            filters = json.loads(data_source.filters) if data_source.filters else None
            value = collector(
                db,
                metric=data_source.metric,
                filters=filters,
                aggregation=data_source.aggregation or "COUNT"
            )

            # 如果有公式，进行计算
            if value is not None and data_source.formula:
                formula_params = json.loads(data_source.formula_params) if data_source.formula_params else {}
                formula_params["value"] = value
                value = calculate_formula(data_source.formula, formula_params)

        elif data_source.source_type == "FORMULA":
            # 纯公式计算
            formula_params = json.loads(data_source.formula_params) if data_source.formula_params else {}
            value = calculate_formula(data_source.formula, formula_params)

        else:
            # 手动采集，返回当前值
            value = kpi.current_value

        # 更新数据源执行信息
        data_source.last_executed_at = datetime.now()
        data_source.last_result = str(value) if value is not None else None
        data_source.last_error = None
        db.commit()

        return value

    except Exception as e:
        # 记录错误
        data_source.last_executed_at = datetime.now()
        data_source.last_error = str(e)
        db.commit()
        return None


def auto_collect_kpi(
    db: Session,
    kpi_id: int,
    recorded_by: Optional[int] = None
) -> Optional[KPI]:
    """
    自动采集并更新 KPI 值

    Args:
        db: 数据库会话
        kpi_id: KPI ID
        recorded_by: 记录人（系统采集时为空）

    Returns:
        Optional[KPI]: 更新后的 KPI
    """
    value = collect_kpi_value(db, kpi_id)
    if value is None:
        return None

    kpi = db.query(KPI).filter(KPI.id == kpi_id, KPI.is_active).first()
    if not kpi:
        return None

    # 更新当前值
    kpi.current_value = value
    kpi.last_collected_at = datetime.now()

    # 创建历史记录
    from app.services.strategy.kpi_service import create_kpi_snapshot
    create_kpi_snapshot(db, kpi_id, "AUTO", recorded_by)

    db.commit()
    db.refresh(kpi)
    return kpi


def batch_collect_kpis(
    db: Session,
    strategy_id: Optional[int] = None,
    frequency: Optional[str] = None
) -> Dict[str, Any]:
    """
    批量采集 KPI

    Args:
        db: 数据库会话
        strategy_id: 战略 ID（可选）
        frequency: 采集频率筛选（可选）

    Returns:
        Dict: 采集结果统计
    """
    from app.models.strategy import CSF

    query = db.query(KPI).filter(
        KPI.is_active,
        KPI.data_source_type == "AUTO"
    )

    if strategy_id:
        query = query.join(CSF).filter(
            CSF.strategy_id == strategy_id,
            CSF.is_active
        )

    if frequency:
        query = query.filter(KPI.frequency == frequency)

    kpis = query.all()

    success_count = 0
    failed_count = 0
    failed_kpis: List[Dict[str, Any]] = []

    for kpi in kpis:
        result = auto_collect_kpi(db, kpi.id)
        if result:
            success_count += 1
        else:
            failed_count += 1
            failed_kpis.append({"id": kpi.id, "code": kpi.code, "name": kpi.name})

    return {
        "total": len(kpis),
        "success": success_count,
        "failed": failed_count,
        "failed_kpis": failed_kpis,
        "collected_at": datetime.now(),
    }
